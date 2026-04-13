#!/usr/bin/env python3
"""Freelance time tracking CLI.

A small command-line timer that records time spent on named projects and
produces colored per-project summaries for the current day and ISO week.
All session state is persisted as a JSON array in ``time_log.json`` inside
the current working directory so that subsequent invocations see prior
sessions.

The module exposes a single :func:`main` entry point that dispatches an
``argv`` list to one of five commands: ``start <project>``, ``stop``,
``status``, ``report day``, and ``report week``.
"""

import json
import os
import sys
from datetime import datetime, timedelta

# ANSI escape sequences used to color terminal tokens. Every colored token
# is wrapped between one of the open codes below and ``RESET`` so that the
# surrounding text stays in the terminal's default color.
CYAN = "\x1b[36m"
GREEN = "\x1b[32m"
RED = "\x1b[31m"
YELLOW = "\x1b[33m"
RESET = "\x1b[0m"

# Persistent log file name (resolved against the current working directory
# at every call, as required by the prompt).
LOG_FILE = "time_log.json"

# ISO 8601 timestamp format with second precision and no timezone suffix;
# all ``start`` and ``end`` fields in the log use this exact format.
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


def load_sessions():
    """Return the list of sessions currently stored in ``time_log.json``.

    If the log file does not exist yet, an empty list is returned and the
    file is left untouched; it will be created the first time a command
    needs to write data.
    """
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        return json.load(f)


def save_sessions(sessions):
    """Write ``sessions`` to ``time_log.json`` with ``indent=2`` and a
    trailing newline, overwriting any existing content."""
    with open(LOG_FILE, "w") as f:
        json.dump(sessions, f, indent=2)
        f.write("\n")


def now_dt():
    """Return the current local time truncated to second precision."""
    return datetime.now().replace(microsecond=0)


def format_ts(dt):
    """Render a ``datetime`` as an ISO 8601 second-precision string."""
    return dt.strftime(TIME_FORMAT)


def parse_ts(s):
    """Parse an ISO 8601 second-precision string back into a ``datetime``."""
    return datetime.strptime(s, TIME_FORMAT)


def split_duration(total_seconds):
    """Split a duration in seconds into integer ``(hours, minutes, seconds)``."""
    total_seconds = int(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return hours, minutes, seconds


def find_running(sessions):
    """Return the first session whose ``end`` field is ``None``, or ``None``
    if no timer is currently running."""
    for session in sessions:
        if session.get("end") is None:
            return session
    return None


def cmd_start(project):
    """Handle ``start <project>``.

    Appends a new running session unless another timer is already active,
    in which case the log file is left untouched and an error is reported
    on stderr.
    """
    sessions = load_sessions()
    running = find_running(sessions)
    if running is not None:
        # A timer is already active: emit the error entirely in red and
        # leave ``time_log.json`` unchanged.
        sys.stderr.write(
            f"{RED}Error: a timer is already running for project "
            f"'{running['project']}'{RESET}\n"
        )
        return 1
    sessions.append({"project": project, "start": format_ts(now_dt()), "end": None})
    save_sessions(sessions)
    sys.stdout.write(f"Started timer for {CYAN}{project}{RESET}\n")
    return 0


def cmd_stop():
    """Handle ``stop``.

    Closes the single running session by stamping its ``end`` field with
    the current local time and writing the updated log back to disk. If no
    timer is running, an error is reported on stderr.
    """
    sessions = load_sessions()
    running = find_running(sessions)
    if running is None:
        sys.stderr.write(f"{RED}Error: no timer is currently running{RESET}\n")
        return 1
    end = now_dt()
    running["end"] = format_ts(end)
    save_sessions(sessions)
    start = parse_ts(running["start"])
    h, m, s = split_duration((end - start).total_seconds())
    sys.stdout.write(
        f"Stopped timer for {CYAN}{running['project']}{RESET} "
        f"{GREEN}({h}h {m}m {s}s){RESET}\n"
    )
    return 0


def cmd_status():
    """Handle ``status``.

    Prints the currently running project and its elapsed duration, or a
    yellow ``No timer running`` line when nothing is active.
    """
    sessions = load_sessions()
    running = find_running(sessions)
    if running is None:
        sys.stdout.write(f"{YELLOW}No timer running{RESET}\n")
        return 0
    start = parse_ts(running["start"])
    h, m, s = split_duration((now_dt() - start).total_seconds())
    sys.stdout.write(
        f"Running: {CYAN}{running['project']}{RESET} for "
        f"{GREEN}{h}h {m}m {s}s{RESET}\n"
    )
    return 0


def aggregate_range(sessions, start_bound, end_bound):
    """Sum per-project seconds for sessions whose ``start`` falls inside
    the inclusive ``[start_bound, end_bound]`` window.

    Sessions that are still running (``end`` is ``None``) are treated as
    ending at the current local time when computing their duration, per
    the prompt's report semantics.
    """
    totals = {}
    now = now_dt()
    for session in sessions:
        start = parse_ts(session["start"])
        # Reports filter by the ``start`` field only — a session that
        # began before the window but is still running is intentionally
        # excluded from today's/this-week's totals.
        if start < start_bound or start > end_bound:
            continue
        if session.get("end") is None:
            end = now
        else:
            end = parse_ts(session["end"])
        seconds = (end - start).total_seconds()
        totals[session["project"]] = totals.get(session["project"], 0) + seconds
    return totals


def print_report_table(totals):
    """Render the per-project summary table used by both report commands.

    Rows are sorted by hours descending with ties broken by project name
    ascending. The header and TOTAL lines are emitted entirely in yellow;
    each data row colors the project name cyan and the two-decimal hours
    value green.
    """
    # Sort descending by hours, then ascending by project name on ties.
    items = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
    rows = [(name, secs / 3600.0) for name, secs in items]
    hours_strs = [f"{h:.2f}" for _, h in rows]
    total_hours = sum(h for _, h in rows)
    total_str = f"{total_hours:.2f}"

    # Column widths are derived from the longest project name and the
    # longest formatted hours value so the table stays aligned regardless
    # of the actual data.
    name_col = max(len("Project"), max(len(name) for name, _ in rows)) + 2
    hours_col = max(len("Hours"), max(len(v) for v in hours_strs + [total_str]))
    table_width = name_col + hours_col

    header = f"{'Project':<{name_col}}{'Hours':>{hours_col}}"
    sys.stdout.write(f"{YELLOW}{header}{RESET}\n")
    sys.stdout.write("-" * table_width + "\n")

    for (name, _), hv in zip(rows, hours_strs):
        # Padding must sit outside the color escapes so only the project
        # name and hours token themselves are colored.
        name_padding = " " * (name_col - len(name))
        hours_padding = " " * (hours_col - len(hv))
        sys.stdout.write(
            f"{CYAN}{name}{RESET}{name_padding}{hours_padding}{GREEN}{hv}{RESET}\n"
        )

    total_line = f"{'TOTAL':<{name_col}}{total_str:>{hours_col}}"
    sys.stdout.write(f"{YELLOW}{total_line}{RESET}\n")


def cmd_report_day():
    """Handle ``report day`` — summarize sessions whose ``start`` falls on
    the current local calendar date."""
    sessions = load_sessions()
    today = datetime.now().date()
    start_bound = datetime.combine(today, datetime.min.time())
    end_bound = datetime.combine(today, datetime.max.time()).replace(microsecond=0)
    totals = aggregate_range(sessions, start_bound, end_bound)
    if not totals:
        sys.stdout.write(f"{YELLOW}No sessions recorded for today{RESET}\n")
        return 0
    print_report_table(totals)
    return 0


def cmd_report_week():
    """Handle ``report week`` — summarize sessions whose ``start`` falls in
    the current ISO calendar week (Monday 00:00:00 through Sunday
    23:59:59, local time)."""
    sessions = load_sessions()
    today = datetime.now().date()
    # ``weekday()`` returns 0 for Monday and 6 for Sunday, so subtracting
    # it from today always lands on the Monday of the current ISO week.
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    start_bound = datetime.combine(monday, datetime.min.time())
    end_bound = datetime.combine(sunday, datetime.max.time()).replace(microsecond=0)
    totals = aggregate_range(sessions, start_bound, end_bound)
    if not totals:
        sys.stdout.write(f"{YELLOW}No sessions recorded for this week{RESET}\n")
        return 0
    print_report_table(totals)
    return 0


def invalid_usage():
    """Emit the red ``Error: invalid usage`` line and return exit code 2.

    Called for any ``argv`` that does not exactly match one of the five
    valid invocations; never touches ``time_log.json``.
    """
    sys.stderr.write(f"{RED}Error: invalid usage{RESET}\n")
    return 2


def main(argv):
    """Dispatch ``argv`` to the matching command handler.

    ``argv`` is expected to be ``sys.argv[1:]`` (i.e., without the program
    name). The return value is the process exit code: ``0`` on success,
    ``1`` on a runtime precondition failure (duplicate timer, stop with no
    running timer), and ``2`` on any invalid invocation.
    """
    if not argv:
        return invalid_usage()
    command = argv[0]
    if command == "start":
        # ``start`` requires exactly one non-empty project argument.
        if len(argv) != 2 or not argv[1]:
            return invalid_usage()
        return cmd_start(argv[1])
    if command == "stop":
        if len(argv) != 1:
            return invalid_usage()
        return cmd_stop()
    if command == "status":
        if len(argv) != 1:
            return invalid_usage()
        return cmd_status()
    if command == "report":
        if len(argv) != 2:
            return invalid_usage()
        if argv[1] == "day":
            return cmd_report_day()
        if argv[1] == "week":
            return cmd_report_week()
        return invalid_usage()
    return invalid_usage()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
