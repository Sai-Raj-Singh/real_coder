#!/usr/bin/env python3
import dataclasses
import json
import sys
from enum import Enum
from pathlib import Path
from typing import List

class TestStatus(Enum):
    """The test status enum."""
    PASSED = 1
    FAILED = 2
    SKIPPED = 3
    ERROR = 4

@dataclasses.dataclass
class TestResult:
    """The test result dataclass."""
    name: str
    status: TestStatus

### DO NOT MODIFY THE CODE ABOVE ###
### Implement the parsing logic below ###

def parse_test_output(stdout_content: str, stderr_content: str) -> List[TestResult]:
    """
    Parse `go test -v ./...` output and extract a TestResult for every
    test (including subtests) that the Go test runner reported.

    Go's verbose test output emits one line per finished test of the form
    `--- PASS: TestName (0.00s)`, `--- FAIL: TestName (0.00s)`, or
    `--- SKIP: TestName (0.00s)`. Subtests are reported with their parent
    path joined by '/', e.g. `--- PASS: TestParent/Subtest (0.00s)`, and
    may be indented. Build failures, import errors, and panics produce no
    `---` lines at all; in that case this function returns an empty list
    so the evaluation harness treats the run as having produced no tests.
    """
    import re

    result_line = re.compile(r'^\s*---\s+(PASS|FAIL|SKIP):\s+(\S+)\s+\(')
    status_map = {
        'PASS': TestStatus.PASSED,
        'FAIL': TestStatus.FAILED,
        'SKIP': TestStatus.SKIPPED,
    }

    # TestHelper_FailurePath is an internal subprocess helper used by the
    # failure-path tests: the parent tests re-exec the test binary with an
    # env var set and observe the child's captured output. In the normal
    # (non-subprocess) go test run the helper detects that the env var is
    # absent and calls t.Skip, which surfaces as a SKIP line. The helper
    # is an implementation detail of the test harness — not a prompt
    # requirement — so filter it out entirely so it contaminates neither
    # before.json nor after.json.
    excluded_names = {'TestHelper_FailurePath'}

    results: List[TestResult] = []
    seen = set()

    # Scan both streams: Go test normally writes results to stdout, but some
    # build environments merge streams. Looking at both makes the parser
    # robust to that without duplicating entries (deduped via `seen`).
    for stream in (stdout_content, stderr_content):
        if not stream:
            continue
        for line in stream.splitlines():
            match = result_line.match(line)
            if not match:
                continue
            status_token = match.group(1)
            name = match.group(2)
            if name in excluded_names:
                continue
            if name in seen:
                continue
            seen.add(name)
            results.append(TestResult(name=name, status=status_map[status_token]))

    return results

### Implement the parsing logic above ###
### DO NOT MODIFY THE CODE BELOW ###

def export_to_json(results: List[TestResult], output_path: Path) -> None:
    json_results = {
        'tests': [
            {'name': result.name, 'status': result.status.name} for result in results
        ]
    }
    with open(output_path, 'w') as f:
        json.dump(json_results, f, indent=2)

def main(stdout_path: Path, stderr_path: Path, output_path: Path) -> None:
    with open(stdout_path) as f:
        stdout_content = f.read()
    with open(stderr_path) as f:
        stderr_content = f.read()

    results = parse_test_output(stdout_content, stderr_content)
    export_to_json(results, output_path)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: python parsing.py <stdout_file> <stderr_file> <output_json>')
        sys.exit(1)

    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))