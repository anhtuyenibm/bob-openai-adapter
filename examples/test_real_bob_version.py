"""
Optional smoke test for a real Bob installation.

This test intentionally calls only:

    bob -v

It does not send a prompt to Bob and does not require BOBSHELL_API_KEY.
By default the test is skipped so ordinary unit-test runs do not fail on
machines where Bob is not installed.

Run it explicitly with:

    RUN_REAL_BOB_TESTS=1 python test_real_bob_version.py

Optionally override the executable path/name:

    RUN_REAL_BOB_TESTS=1 BOB_COMMAND=/path/to/bob python test_real_bob_version.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


RUN_ENV_VAR = "RUN_REAL_BOB_TESTS"
BOB_COMMAND_ENV_VAR = "BOB_COMMAND"


def test_real_bob_version() -> None:
    """Verify that the real Bob command is installed and responds to `-v`."""
    if os.getenv(RUN_ENV_VAR) != "1":
        print(f"SKIP test_real_bob_version: set {RUN_ENV_VAR}=1 to run")
        return

    bob_command = os.getenv(BOB_COMMAND_ENV_VAR, "bob")

    if shutil.which(bob_command) is None:
        raise AssertionError(
            f"Bob command not found: {bob_command!r}. "
            f"Set {BOB_COMMAND_ENV_VAR} to the Bob executable path if needed."
        )

    result = subprocess.run(
        [bob_command, "-v"],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )

    combined_output = (result.stdout + result.stderr).strip()
    assert result.returncode == 0, (
        f"Expected `bob -v` to exit with rc=0, got rc={result.returncode}. "
        f"Output: {combined_output!r}"
    )
    assert combined_output, "Expected `bob -v` to print version/help text"

    print("PASS test_real_bob_version")
    print(combined_output.splitlines()[0])


def main() -> int:
    try:
        test_real_bob_version()
        return 0
    except Exception as exc:
        print(f"FAIL test_real_bob_version: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
