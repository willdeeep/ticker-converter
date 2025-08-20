#!/usr/bin/env python3
"""Comprehensive code quality checks for standardized validation.

This script provides the same quality validation as 'make quality'
but can be run directly or integrated into other automation workflows.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description, cwd=None) -> bool:
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
    """Run comprehensive quality gate validation."""
    project_root = Path(__file__).parent.parent.parent
    success = True

    print("🚀 Running comprehensive quality gate validation...")
    print(
        "📋 Quality Gate Pipeline: Black → isort → Pylint → MyPy → Tests with Coverage"
    )
    print()

    # 1. Black code formatting check
    print("Step 1/5: Code Formatting (Black)...")
    black_cmd = [sys.executable, "-m", "black", "--check", "."]
    if not run_command(black_cmd, "Black formatting validation", project_root):
        print("💡 Fix with: make lint-fix")
        success = False
    print()

    # 2. isort import sorting check
    print("Step 2/5: Import Sorting (isort)...")
    isort_cmd = [sys.executable, "-m", "isort", "--check-only", "."]
    if not run_command(isort_cmd, "Import sorting validation", project_root):
        print("💡 Fix with: make lint-fix")
        success = False
    print()

    # 3. Pylint code quality
    print("Step 3/5: Code Quality (Pylint)...")
    pylint_cmd = [
        sys.executable,
        "-m",
        "pylint",
        "src/ticker_converter/",
        "dags/",
        "--score=yes",
    ]
    result = subprocess.run(
        pylint_cmd, cwd=project_root, capture_output=True, text=True, check=False
    )
    if result.returncode == 0 and "10.00/10" in result.stdout:
        print("✅ Pylint score: 10.00/10 PASSED")
    else:
        print("❌ Pylint score: FAILED (must be 10.00/10)")
        print(result.stdout)
        success = False
    print()

    # 4. MyPy type checking
    print("Step 4/5: Type Checking (MyPy)...")
    mypy_cmd = [sys.executable, "-m", "mypy", "src/ticker_converter/"]
    if not run_command(mypy_cmd, "MyPy type checking", project_root):
        success = False
    print()

    # 5. Test suite with coverage
    print("Step 5/5: Test Suite with Coverage...")
    test_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "--cov=ticker_converter",
        "--cov-report=term-missing",
        "--cov-fail-under=67",
        "--ignore=tests/integration",
        "-v",
    ]
    if not run_command(test_cmd, "Test suite with 67%+ coverage", project_root):
        print("💡 Fix failing tests or improve coverage to 67%+")
        success = False

    print("\n" + "=" * 70)
    if success:
        print("🎉 All Quality Gates PASSED!")
        print("✅ Code formatting: Black compliant")
        print("✅ Import sorting: isort compliant")
        print("✅ Code quality: Pylint 10.00/10")
        print("✅ Type safety: MyPy clean")
        print("✅ Test coverage: 67%+ with all tests passing")
        print("🚀 Ready for commit and pull request!")
    else:
        print("❌ Some quality gates failed")
        print("Please review the output above and fix any issues")
        print("💡 Quick fixes:")
        print("  - Formatting issues: make lint-fix")
        print("  - Quality issues: make quality")
        print("  - Full validation: make quality")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
