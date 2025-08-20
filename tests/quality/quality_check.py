#!/usr/bin/env python3
"""Comprehensive code quality checks for standardized validation.

This script runs multiple code quality tools in sequence.
TODO: Integrate these quality checks into the main test CLI for unified execution.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str, cwd: Path | None = None) -> bool:
    """Run a command and return success status."""
    print(f"🔍 {description}...")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)

    if result.returncode == 0:
        print(f"✅ {description} passed!")
        return True
    else:
        print(f"❌ {description} failed:")
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        return False


def main() -> int:
    """Run all code quality checks."""
    project_root = Path(__file__).parent.parent.parent
    success = True

    print("🚀 Running comprehensive code quality checks...\n")

    # 1. MyPy type checking
    mypy_cmd = [sys.executable, "-m", "mypy", "src/", "--strict", "--show-error-codes"]
    if not run_command(mypy_cmd, "MyPy type checking", project_root):
        success = False

    print()

    # 2. Pylint code quality
    pylint_cmd = [
        sys.executable,
        "-m",
        "pylint",
        "src/ticker_converter/",
        "--score=yes",
    ]
    if not run_command(pylint_cmd, "Pylint code quality check", project_root):
        success = False

    print()

    # 3. Test suite
    test_cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]
    if not run_command(test_cmd, "Test suite execution", project_root):
        success = False

    print("\n" + "=" * 60)
    if success:
        print("🎉 All code quality checks passed successfully!")
        print("✅ MyPy: Type checking clean")
        print("✅ Pylint: Code quality standards met")
        print("✅ Tests: All tests passing")
    else:
        print("❌ Some code quality checks failed")
        print("Please review the output above and fix any issues")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
