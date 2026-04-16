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
    Parse `cargo test` output and extract per-test results.

    Recognises the per-binary "Running ... (target/.../<stem>-<hash>)" header
    used by Cargo so that tests from different binaries are namespaced as
    "<stem>::<test_name>" and never collide.
    """
    import re

    binary_re = re.compile(r'\(target/[^)]*?/([^/]+)-[0-9a-f]{8,}\)')
    test_re = re.compile(r'^test\s+(\S+)\s+\.\.\.\s+(ok|passed|FAILED|ignored)\s*$')

    results: List[TestResult] = []
    seen = set()
    current_binary = ''

    combined = (stdout_content or '') + '\n' + (stderr_content or '')

    for raw_line in combined.splitlines():
        line = raw_line.rstrip()

        m = binary_re.search(line)
        if m:
            current_binary = m.group(1)
            continue

        stripped = line.lstrip()
        if not stripped.startswith('test '):
            continue

        m = test_re.match(stripped)
        if not m:
            continue

        name = m.group(1)
        status_str = m.group(2)
        full_name = '{}::{}'.format(current_binary, name) if current_binary else name

        if full_name in seen:
            continue
        seen.add(full_name)

        if status_str == 'ok' or status_str == 'passed':
            status = TestStatus.PASSED
        elif status_str == 'FAILED':
            status = TestStatus.FAILED
        else:
            status = TestStatus.SKIPPED

        results.append(TestResult(name=full_name, status=status))

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