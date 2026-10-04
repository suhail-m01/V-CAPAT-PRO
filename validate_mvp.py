"""Fast acceptance check for the deployable SIH26169 MVP source tree."""
from pathlib import Path
from vcapat.config.settings import Scenario
from vcapat.config.ps_compliance import evaluate
from vcapat.core.engine import Engine

root=Path(__file__).resolve().parent
cfg=Scenario.load(root/'scenarios'/'ps_compliant_reference.json')
checks=evaluate(cfg)
for c in checks: print(('PASS' if c.passed else 'FAIL'),'-',c.name,':',c.detail)
if not all(c.passed for c in checks): raise SystemExit(2)

# Mandatory submission/release assets that can be verified cross-platform.
assets=[
    (root/'docs'/'VCAPAT_PRO_Technical_Report_v1.1.pdf',100_000,'formal technical report PDF'),
    (root/'docs'/'VCAPAT_PRO_Technical_Report_v1.1.docx',100_000,'editable technical report source'),
    (root/'VCAPAT_PRO.spec',500,'onedir PyInstaller spec'),
    (root/'VCAPAT_PRO_onefile.spec',500,'onefile PyInstaller spec'),
    (root/'build_release.ps1',1_000,'Windows release gate'),
    (root/'.github'/'workflows'/'windows-release.yml',500,'Windows CI builder'),
]
for path,min_size,label in assets:
    ok=path.is_file() and path.stat().st_size>=min_size
    print(('PASS' if ok else 'FAIL'),'-',label,':',path.relative_to(root))
    if not ok:raise SystemExit(3)

web=(root/'vcapat'/'api'/'companion_web'/'templates'/'scenarios.html').read_text(encoding='utf-8')
if 'value="ai_auto"' not in web or 'value="tinyml"' not in web:
    raise SystemExit('Browser detector selector does not expose AI-assisted modes')
print('PASS - browser exposes ai_auto and tinyml detector modes')

engine=Engine(cfg)
for _ in range(120): engine.step()
locked=sum(r['lock_state']=='LOCKED' for r in engine.rows)
print(f'PASS - pipeline smoke test: {len(engine.rows)} frames, locked frames={locked}')
if locked==0: raise SystemExit('Pipeline never reached LOCKED state')
engine.close()
