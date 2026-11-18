"""Run product tests and persist actual results separately from design fixtures."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import platform
import re
import sys
import time
import tkinter
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def record(self, test, status):
        self.records.append({"test": test.id(), "status": status})

    def addSuccess(self, test):
        super().addSuccess(test)
        self.record(test, "PASS")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.record(test, "FAIL")

    def addError(self, test, err):
        super().addError(test, err)
        self.record(test, "ERROR")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.record(test, "SKIP")


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    started = time.perf_counter()
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(suite)
    cases = json.loads((ROOT / "docs" / "development" / "test_cases.json").read_text(encoding="utf-8"))
    for case in cases:
        suffix = case["id"].replace("TC-", "")
        matching = [record for record in result.records if re.search(r"\.test_TC_" + re.escape(suffix) + r"_", record["test"])]
        case["status"] = "PASS" if matching and all(r["status"] == "PASS" for r in matching) else "NOT_RUN"
        if any(r["status"] in {"FAIL", "ERROR"} for r in matching):
            case["status"] = "FAIL"
        case["evidence"] = [r["test"] for r in matching]
    report = {
        "executed_at_kst": datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "tk": tkinter.TkVersion,
        "os": platform.platform(),
        "command": "python -X utf8 tools/run_tests.py",
        "duration_seconds": round(time.perf_counter() - started, 3),
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "passed_design_cases": sum(case["status"] == "PASS" for case in cases),
        "case_count": len(cases),
        "verification_method": "unittest; real Tk widgets/event loop; subprocess restart; geometry bounds",
        "visual_screenshot_review": "NOT_VERIFIED: native computer-use connection unavailable",
        "tests": result.records,
        "cases": cases,
    }
    out = ROOT / "docs" / "results"
    out.mkdir(exist_ok=True)
    (out / "테스트결과.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = "\n".join(f'| {case["id"]} | {case["purpose"]} | {case["status"]} | {"<br>".join(case["evidence"])} |' for case in cases)
    summary = f'''# 제품 자동 시험 결과

- 실행 시각: {report["executed_at_kst"]}
- 환경: Python {report["python"]} / Tk {report["tk"]} / {report["os"]}
- 실행 명령: `{report["command"]}`
- 결과: {result.testsRun}개 시험, 실패 {len(result.failures)}, 오류 {len(result.errors)}, 건너뜀 {len(result.skipped)}
- 설계 시험 사례 연결: {report["passed_design_cases"]} / {len(cases)} 통과

도메인·서비스 단위 시험, 실제 Tk 위젯과 이벤트 루프를 사용한 GUI 통합 시험, 별도 프로세스 재시작과 최소 창 크기의 위젯 배치를 자동 검증했다. 시험 중 실제 계좌·외부 은행·프린터는 사용하지 않는다.

화면 캡처를 통한 육안 검토는 컴퓨터 제어 연결 문제로 수행하지 못했다. 창 배치의 자동 검사는 위젯 표시 여부와 경계 안 배치를 확인한 결과이며 화면 캡처 검토를 대신했다고 주장하지 않는다. 설계 당시의 수동 기록 양식은 별도 수동 확인에 사용한다.

전체 개별 시험과 기대 결과는 [테스트결과.json](테스트결과.json)에 있다. 아래 상태는 실제 자동 실행 결과이다.

| 설계 TC | 목적 | 자동 결과 | 실행 근거 |
| --- | --- | --- | --- |
{rows}
'''
    (out / "테스트결과.md").write_text(summary, encoding="utf-8")
    print(f'\nDesign cases: {report["passed_design_cases"]}/{len(cases)} PASS; report: {out}')
    return 0 if result.wasSuccessful() and report["passed_design_cases"] == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
