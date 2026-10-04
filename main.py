"""V-CAPAT PRO entry point. See README for GUI, web, headless and release usage."""
from __future__ import annotations
import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from vcapat import __version__
from vcapat.config.settings import Scenario
from vcapat.core.engine import Engine
from vcapat.metrics.reporter import export_session
from vcapat.utils.paths import resource, writable_default_root

PRESETS = resource("scenarios")


def _self_test(output: Path) -> int:
    """Packaged-runtime smoke test used by Windows release verification.

    It deliberately checks bundled resources, the simulator/detector/tracker
    pipeline and evidence export.  It is a launch/integration test, not a claim
    that every stochastic scenario must satisfy every performance threshold.
    """
    required = [
        resource("scenarios", "easy_clear_circular.json"),
        resource("assets", "logo.png"),
        resource("assets", "sample_beacon.mp4"),
        resource("docs", "VCAPAT_PRO_Technical_Report_v1.1.pdf"),
    ]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        print("SELF-TEST FAIL: missing bundled resources:")
        for item in missing:
            print(" -", item)
        return 2

    engine = Engine(Scenario.load(required[0]))
    try:
        for _ in range(60):
            if engine.step() is None:
                break
        if engine.frame_id < 30:
            print(f"SELF-TEST FAIL: only {engine.frame_id} frames processed")
            return 3
        folder = Path(export_session(engine, output))
        must_exist = [folder / "summary.json", folder / "frames.csv", folder / "certificate.pdf"]
        missing_out = [str(p) for p in must_exist if not p.is_file() or p.stat().st_size == 0]
        if missing_out:
            print("SELF-TEST FAIL: evidence export incomplete:")
            for item in missing_out:
                print(" -", item)
            return 4
        print(f"SELF-TEST PASS: V-CAPAT PRO {__version__}; {engine.frame_id} frames; state={engine.tracker.state}")
        print("Evidence:", folder)
        return 0
    finally:
        engine.close()


def main():
    p = argparse.ArgumentParser(description="V-CAPAT PRO optical beacon acquisition laboratory")
    p.add_argument("--scenario", help="Explicit preset or saved scenario JSON; overrides persisted default")
    p.add_argument("--headless", action="store_true")
    p.add_argument("--web", action="store_true")
    p.add_argument("--self-test", action="store_true", help="Verify packaged resources, pipeline and evidence export, then exit")
    p.add_argument("--version", action="version", version=f"V-CAPAT PRO {__version__}")
    p.add_argument("--demo-video", type=int, metavar="SECONDS", help="Generate a scripted montage (5-240 s), not a certified test")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--frames", type=int, default=300)
    p.add_argument("--output", default=None)
    p.add_argument("--video")
    p.add_argument("--ground-truth")
    p.add_argument("--webcam", type=int)
    a = p.parse_args()

    output = Path(a.output) if a.output else (writable_default_root() / "reports" if getattr(sys, "frozen", False) else resource("reports"))
    output.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        handlers=[RotatingFileHandler(output / "application.log", maxBytes=1_000_000, backupCount=2)],
    )

    if a.self_test:
        raise SystemExit(_self_test(output / "self_test"))

    saved_default = output / "default_scenario.json"
    scenario_path = Path(a.scenario) if a.scenario else (saved_default if saved_default.is_file() else PRESETS / "ps_compliant_reference.json")
    scenario = Scenario.load(scenario_path)
    engine = Engine(scenario)
    try:
        if a.video or a.webcam is not None:
            from vcapat.io.ground_truth import load_ground_truth
            if a.video:
                engine.open_video(a.video, load_ground_truth(a.ground_truth) if a.ground_truth else None)
            else:
                engine.open_webcam(a.webcam)

        if a.demo_video is not None:
            from vcapat.io.demo_video import produce_demo
            result = produce_demo(
                output / "demo_montage.mp4",
                [PRESETS / x for x in ("easy_clear_circular.json", "medium_foggy_figure8.json", "handover_sequence.json")],
                a.demo_video,
            )
            print("Generated:", result)
        elif a.headless:
            for _ in range(a.frames):
                if engine.step() is None:
                    break
            folder = export_session(engine, output)
            print("Saved:", folder)
            print("Frames:", engine.frame_id, "State:", engine.tracker.state)
        elif a.web:
            from vcapat.api.rest_server import serve
            serve(engine, a.host, a.port, PRESETS, output)
        else:
            try:
                from vcapat.gui.main_window import run
            except ImportError as exc:
                raise SystemExit("Desktop UI requires PySide6. Install requirements.txt or use --web. " + str(exc))
            run(engine, PRESETS, output)
    finally:
        engine.close()


if __name__ == "__main__":
    main()
