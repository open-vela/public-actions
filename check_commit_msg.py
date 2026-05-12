#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check whether any commit message within a range contains Chinese characters.

The previous implementation used ``git log --pretty=format:%H%x00%B`` and split
the output by newline, but ``%B`` (commit body) itself contains newlines. As a
result the multi-line body was broken into separate entries and the entries
without a NUL separator were silently dropped, causing Chinese in the body to
go undetected.

This version enumerates commits explicitly with ``git rev-list`` and reads each
commit message independently with ``git log -1 --format=%B``, so the full
message (including the body) is always checked.
"""
import argparse
import re
import subprocess
import sys

# CJK Unified Ideographs covers the common set of Chinese characters.
CHINESE_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fff]')


def contains_chinese(text: str) -> bool:
    """Return True if ``text`` contains any Chinese character."""
    return bool(text and CHINESE_CHAR_PATTERN.search(text))


def run_git(args):
    """Run a git command and return its stdout as text.

    Exits the process with an error message when git fails so that CI surfaces
    the failure clearly.
    """
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
    except FileNotFoundError:
        print(
            "Error: 'git' command not found. Please ensure Git is installed "
            "and on PATH.",
            file=sys.stderr,
        )
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(
            f"Error: 'git {' '.join(args)}' failed.\n{exc.stderr}",
            file=sys.stderr,
        )
        sys.exit(1)
    return result.stdout


def get_commit_hashes(commit_range: str):
    """Return the list of commit hashes contained in ``commit_range``."""
    output = run_git(["rev-list", commit_range]).strip()
    if not output:
        return []
    return output.splitlines()


def get_commit_message(commit_hash: str) -> str:
    """Return the full commit message (subject + body) for ``commit_hash``."""
    return run_git(["log", "-1", "--format=%B", commit_hash])


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether any commit message in the given range contains "
            "Chinese characters."
        ),
    )
    parser.add_argument(
        "commit_range",
        help="Git commit range to inspect, e.g. 'main..HEAD' or 'A..B'.",
    )
    args = parser.parse_args()

    print(f"--- Checking commit range: {args.commit_range} ---")

    hashes = get_commit_hashes(args.commit_range)
    if not hashes:
        print("No commits to check.")
        sys.exit(0)

    found_error = False
    for commit_hash in hashes:
        message = get_commit_message(commit_hash)
        if contains_chinese(message):
            found_error = True
            print("\n❌ Check failed: commit message contains Chinese characters.")
            print(f"   Commit Hash: {commit_hash}")
            # Truncate to keep log output readable.
            print(f"   Message (truncated): {message.strip()[:100]}...")

    if found_error:
        print("\n--- Check failed ---")
        sys.exit(1)
    print("\n✅ All commit messages pass: no Chinese characters detected.")
    print("--- Check passed ---")
    sys.exit(0)


if __name__ == "__main__":
    main()
