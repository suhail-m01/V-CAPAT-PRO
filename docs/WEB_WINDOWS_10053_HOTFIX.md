# Windows Web Dashboard WinError 10053 Hotfix (v1.1.1)

## Symptom
When running `python main.py --web` on Windows, the terminal could repeatedly print `ConnectionAbortedError: [WinError 10053]` from `wfile.write()` while serving `/api/frame` JPEGs.

## Cause
The live browser dashboard refreshes image frames. Browsers may cancel an older in-flight JPEG request when a newer frame is requested or when a page is navigated/closed. Windows reports that expected client disconnect as WinError 10053. The tracking engine itself was still running.

## Fix
- The HTTP response writer now treats client-side socket disconnects as normal and closes only that request without a traceback.
- Browser frame refresh now avoids starting a replacement image request while the previous image is still loading, reducing canceled requests and network churn.

## Verification
Start with `python main.py --web`, open `http://127.0.0.1:8000`, and navigate between Live Tracking, Video Benchmark and Analysis. The dashboard should keep updating without repeated WinError 10053 tracebacks.
