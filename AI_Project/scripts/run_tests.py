"""Run each unittest in a separate process, with a deadline and reports."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def worker(test_id, output):
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
        result = unittest.TestResult()
        unittest.defaultTestLoader.loadTestsFromName(test_id).run(result)
    status = "passed"
    detail = ""
    if result.errors:
        status, detail = "error", "\n".join(text for _, text in result.errors)
    elif result.failures or result.unexpectedSuccesses:
        status = "failed"
        detail = "\n".join(text for _, text in result.failures) or "Unexpected success"
    elif result.skipped or result.expectedFailures:
        status = "skipped"
        detail = "\n".join(text for _, text in result.skipped + result.expectedFailures)
    Path(output).write_text(json.dumps({
        "status": status, "detail": detail, "log": captured.getvalue()
    }), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pattern", default="test_*.py")
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--output", type=Path, default=ROOT / "reports")
    parser.add_argument("--worker", nargs=2, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(*args.worker)
        return 0
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "backend/tests"), pattern=args.pattern, top_level_dir=str(ROOT)
    )
    if unittest.defaultTestLoader.errors:
        parser.error("\n".join(unittest.defaultTestLoader.errors))
    tests = list(flatten(suite))
    if not tests:
        parser.error("No tests discovered")
    records = []
    with tempfile.TemporaryDirectory(prefix="test-harness-") as temporary:
        for index, test in enumerate(tests):
            output = Path(temporary) / f"{index}.json"
            start = time.perf_counter()
            try:
                process = subprocess.run(
                    [sys.executable, str(Path(__file__).resolve()), "--worker", test.id(), str(output)],
                    cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=args.timeout,
                )
                if process.returncode != 0 or not output.exists():
                    record = {"status": "error", "detail": process.stdout + process.stderr}
                else:
                    record = json.loads(output.read_text(encoding="utf-8"))
            except subprocess.TimeoutExpired:
                record = {"status": "timeout", "detail": f"Exceeded {args.timeout}s"}
            record.update(id=test.id(), duration=time.perf_counter() - start)
            records.append(record)
            print(f"{record['status'].upper():8} {test.id()}")
    args.output.mkdir(parents=True, exist_ok=True)
    counts = {status: sum(r["status"] == status for r in records)
              for status in ("passed", "failed", "error", "timeout", "skipped")}
    (args.output / "results.json").write_text(json.dumps({
        "summary": counts, "tests": records,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    xml = ET.Element("testsuite", name="backend", tests=str(len(records)),
                     failures=str(counts["failed"]), errors=str(counts["error"] + counts["timeout"]),
                     skipped=str(counts["skipped"]), time=str(sum(r["duration"] for r in records)))
    for record in records:
        classname, _, name = record["id"].rpartition(".")
        case = ET.SubElement(xml, "testcase", classname=classname, name=name,
                             time=f"{record['duration']:.6f}")
        tag = {"failed": "failure", "error": "error", "timeout": "error", "skipped": "skipped"}.get(record["status"])
        if tag:
            ET.SubElement(case, tag, type=record["status"]).text = record["detail"]
        if record.get("log"):
            ET.SubElement(case, "system-out").text = record["log"]
    ET.ElementTree(xml).write(args.output / "junit.xml", encoding="utf-8", xml_declaration=True)
    print(f"Reports: {args.output.resolve()}")
    return int(any(counts[key] for key in ("failed", "error", "timeout")))


if __name__ == "__main__":
    sys.exit(main())
