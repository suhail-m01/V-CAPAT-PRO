param(
    [ValidateSet('onedir','onefile','both')]
    [string]$Mode = 'both',
    [switch]$SkipTests
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$Version = '1.1.4'

function Test-SupportedPython {
    param([string]$Exe, [string]$Selector = '')
    $Check = "import sys,struct; ok=(sys.version_info[:2] in ((3,11),(3,12))) and (struct.calcsize('P')*8 == 64); raise SystemExit(0 if ok else 1)"
    try {
        if ($Selector) { & $Exe $Selector -c $Check 2>$null }
        else { & $Exe -c $Check 2>$null }
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

function New-SupportedVenv {
    if (Test-SupportedPython 'py' '-3.11') {
        Write-Host '[1/8] Creating Python 3.11 x64 virtual environment...'
        & py -3.11 -m venv .venv
    } elseif (Test-SupportedPython 'py' '-3.12') {
        Write-Host '[1/8] Creating Python 3.12 x64 virtual environment...'
        & py -3.12 -m venv .venv
    } elseif (Test-SupportedPython 'python') {
        Write-Host '[1/8] Creating virtual environment from supported Python...'
        & python -m venv .venv
    } else {
        throw 'Python 3.11 or 3.12 x64 is required. Install one from python.org and ensure py/python is available.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
}

function Assert-ReleaseInputs {
    $Required = @(
        'main.py',
        'VCAPAT_PRO.spec',
        'VCAPAT_PRO_onefile.spec',
        'packaging\version_info.txt',
        'assets\icon.ico',
        'docs\VCAPAT_PRO_Technical_Report_v1.1.pdf',
        'docs\VCAPAT_PRO_Technical_Report_v1.1.docx',
        'docs\User_Manual.md',
        'docs\PS_Compliance_Matrix.md',
        'scripts\verify_release.py'
    )
    foreach ($Item in $Required) {
        if (-not (Test-Path $Item)) { throw "Required release input is missing: $Item" }
    }
}

function Remove-PathWithRetry {
    param([string]$Path, [int]$Attempts = 5)
    if (-not (Test-Path $Path)) { return }
    for ($i=1; $i -le $Attempts; $i++) {
        try {
            Remove-Item -Recurse -Force $Path -ErrorAction Stop
            return
        } catch {
            if ($i -eq $Attempts) { throw }
            Start-Sleep -Seconds 2
        }
    }
}

function Compress-WithRetry {
    param([string]$SourcePattern, [string]$Destination, [int]$Attempts = 6)
    for ($i=1; $i -le $Attempts; $i++) {
        try {
            if (Test-Path $Destination) { Remove-Item -Force $Destination -ErrorAction SilentlyContinue }
            Compress-Archive -Path $SourcePattern -DestinationPath $Destination -Force -ErrorAction Stop
            return
        } catch {
            if ($i -eq $Attempts) { throw }
            Write-Host "Archive attempt $i failed because Windows still has a file open. Retrying..."
            Get-Process VCAPAT_PRO -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 3
        }
    }
}

Assert-ReleaseInputs

$VenvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (Test-Path $VenvPython) {
    if (-not (Test-SupportedPython $VenvPython)) {
        throw 'Existing .venv is not Python 3.11/3.12 x64. Delete only the .venv folder and rerun the build.'
    }
    Write-Host '[1/8] Reusing existing supported virtual environment...'
} else { New-SupportedVenv }

$Python = (Resolve-Path $VenvPython).Path
& $Python -c "import sys,struct; print('Using Python {} ({}-bit) from {}'.format(sys.version.split()[0], struct.calcsize('P')*8, sys.executable))"
if ($LASTEXITCODE -ne 0) { throw 'Unable to start virtual-environment Python.' }

Write-Host '[2/8] Installing runtime/build dependencies...'
& $Python -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) { throw 'pip/setuptools/wheel upgrade failed.' }
& $Python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Runtime dependency installation failed.' }
& $Python -m pip install 'pyinstaller>=6.10,<7'
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller installation failed.' }

Write-Host '[3/8] Dependency import check...'
& $Python -c "import cv2,numpy,PySide6,matplotlib,qrcode,sgp4; print('Runtime imports OK')"
if ($LASTEXITCODE -ne 0) { throw 'Runtime dependency import check failed.' }

if (-not $SkipTests) {
    Write-Host '[4/8] Running automated tests and PS validation...'
    & $Python -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Automated tests failed; release build stopped.' }
    & $Python validate_mvp.py
    if ($LASTEXITCODE -ne 0) { throw 'MVP validation failed; release build stopped.' }
} else { Write-Host '[4/8] Tests skipped by explicit request.' }

Write-Host '[5/8] Cleaning previous generated artifacts...'
# IMPORTANT: packaging/version_info.txt is source metadata and is never deleted.
Get-Process VCAPAT_PRO -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Remove-PathWithRetry 'build\pyinstaller'
Remove-PathWithRetry 'build\pyinstaller_onefile'
Remove-PathWithRetry 'build\release_smoke_onedir'
Remove-PathWithRetry 'build\release_smoke_onefile'
Remove-PathWithRetry 'dist'
Remove-PathWithRetry 'release'
New-Item -ItemType Directory -Force 'build\pyinstaller','release' | Out-Null
Assert-ReleaseInputs

$Built = @()
if ($Mode -eq 'onedir' -or $Mode -eq 'both') {
    Write-Host '[6/8] Building Windows onedir executable...'
    & $Python -m PyInstaller --noconfirm --clean --distpath dist --workpath build\pyinstaller VCAPAT_PRO.spec
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller onedir build failed.' }
    $Exe = (Resolve-Path 'dist\VCAPAT_PRO\VCAPAT_PRO.exe').Path
    & $Python scripts\verify_release.py $Exe --output build\release_smoke_onedir
    if ($LASTEXITCODE -ne 0) { throw 'Onedir executable smoke test failed.' }
    Get-Process VCAPAT_PRO -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2

    $Package = "release\VCAPAT_PRO_v${Version}_Windows_x64"
    New-Item -ItemType Directory -Force $Package | Out-Null
    Copy-Item -Recurse -Force 'dist\VCAPAT_PRO\*' $Package
    New-Item -ItemType Directory -Force "$Package\submission_docs" | Out-Null
    Copy-Item -Force 'docs\VCAPAT_PRO_Technical_Report_v1.1.pdf' "$Package\submission_docs\"
    Copy-Item -Force 'docs\VCAPAT_PRO_Technical_Report_v1.1.docx' "$Package\submission_docs\"
    Copy-Item -Force 'docs\User_Manual.md' "$Package\submission_docs\"
    Copy-Item -Force 'docs\PS_Compliance_Matrix.md' "$Package\submission_docs\"
    Copy-Item -Force 'README.md' "$Package\README.md"
    $Zip = "release\VCAPAT_PRO_v${Version}_Windows_x64.zip"
    Compress-WithRetry "$Package\*" $Zip
    $Built += $Zip
}

if ($Mode -eq 'onefile' -or $Mode -eq 'both') {
    Write-Host '[6/8] Building Windows single-file executable...'
    Remove-PathWithRetry 'build\pyinstaller_onefile'
    & $Python -m PyInstaller --noconfirm --clean --distpath dist\onefile --workpath build\pyinstaller_onefile VCAPAT_PRO_onefile.spec
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller onefile build failed.' }
    $Exe = (Resolve-Path 'dist\onefile\VCAPAT_PRO.exe').Path
    & $Python scripts\verify_release.py $Exe --output build\release_smoke_onefile
    if ($LASTEXITCODE -ne 0) { throw 'Onefile executable smoke test failed.' }
    Get-Process VCAPAT_PRO -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2

    $Folder = "release\VCAPAT_PRO_v${Version}_OneFile"
    New-Item -ItemType Directory -Force $Folder | Out-Null
    Copy-Item -Force $Exe "$Folder\VCAPAT_PRO.exe"
    Copy-Item -Force 'docs\VCAPAT_PRO_Technical_Report_v1.1.pdf' "$Folder\Technical_Report.pdf"
    Copy-Item -Force 'docs\User_Manual.md' "$Folder\User_Manual.md"
    $Zip = "release\VCAPAT_PRO_v${Version}_OneFile.zip"
    Compress-WithRetry "$Folder\*" $Zip
    $Built += $Zip
}

Write-Host '[7/8] Computing SHA-256 checksums...'
$Lines = @()
foreach ($Artifact in $Built) {
    $Hash = (Get-FileHash $Artifact -Algorithm SHA256).Hash
    $Lines += "$Hash  $([IO.Path]::GetFileName($Artifact))"
}
$Lines | Set-Content -Encoding ASCII 'release\SHA256SUMS.txt'

Write-Host '[8/8] Release build complete.'
Write-Host 'Artifacts:'
$Built | ForEach-Object { Write-Host " - $_" }
Write-Host ' - release\SHA256SUMS.txt'
