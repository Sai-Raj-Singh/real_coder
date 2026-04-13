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

import re

def parse_test_output(stdout_content: str, stderr_content: str) -> List[TestResult]:
    """
    Parse pytest verbose output and extract test results.
    
    Parses lines like:
        tests/test_app.py::test_create_app_exposes_required_routes PASSED
        tests/test_loaders.py::test_load_expected_packets_missing_column FAILED
        tests/test_retry_queue.py::test_retry_single_item_idempotent SKIPPED
        tests/test_source_scanner.py::test_parse_document_filename_invalid_sets_error ERROR
    """
    results = []
    seen = {}
    ordered_names = []
    combined = stdout_content + "\n" + stderr_content

    # Matches lines like:
    #   tests/test_cli.py::TestMainSignature::test_main_importable PASSED
    #   tests/test_cli.py::test_parse_args <- ../app/tests/test_cli.py PASSED
    pattern = re.compile(
        r"(tests/[^\s:]+(?:::[^\s]+)+)(?:\s+<-[^\n]+)?\s+(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)",
        re.MULTILINE,
    )
    for match in pattern.finditer(combined):
        test_name = match.group(1).strip()
        status_str = match.group(2).upper()
        if status_str == "XPASS":
            status_str = "PASSED"
        elif status_str == "XFAIL":
            status_str = "FAILED"
        if status_str in ("ERROR", "SKIPPED"):
            status_str = "FAILED"
        status = TestStatus[status_str]
        if test_name not in seen:
            ordered_names.append(test_name)
        seen[test_name] = status

    for test_name in ordered_names:
        results.append(TestResult(name=test_name, status=seen[test_name]))

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