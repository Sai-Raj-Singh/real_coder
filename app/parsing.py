#!/usr/bin/env python3

import dataclasses
import json
import re
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

# Matches pytest verbose per-test outcome lines, e.g.
#   tests/test_api.py::test_create_poll_returns_poll_id PASSED           [  3%]
#   tests/test_api.py::test_get_poll_nonexistent_returns_404 FAILED      [ 33%]
# The trailing "[ 33%]" column and any decorative characters are optional.
_PYTEST_LINE = re.compile(
    r'^(?P<path>\S+?\.py)::(?P<name>[^\s\[]+(?:\[[^\]]*\])?)\s+'
    r'(?P<status>PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b'
)

_STATUS_MAP = {
    'PASSED': TestStatus.PASSED,
    'XPASS': TestStatus.PASSED,
    'FAILED': TestStatus.FAILED,
    'XFAIL': TestStatus.FAILED,
    'ERROR': TestStatus.ERROR,
    'SKIPPED': TestStatus.SKIPPED,
}


def _strip_ansi(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', text)


def parse_test_output(stdout_content: str, stderr_content: str) -> List[TestResult]:
    """
    Parse pytest verbose output and extract per-test results.
    Deduplicates by fully-qualified test identifier.
    """
    results: List[TestResult] = []
    seen: set = set()

    combined = _strip_ansi(stdout_content) + '\n' + _strip_ansi(stderr_content)
    for raw_line in combined.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        m = _PYTEST_LINE.match(line.lstrip())
        if not m:
            continue
        name = f"{m.group('path')}::{m.group('name')}"
        if name in seen:
            continue
        seen.add(name)
        status = _STATUS_MAP.get(m.group('status'), TestStatus.ERROR)
        results.append(TestResult(name=name, status=status))

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
