#!/usr/bin/env python3
"""Quality gate validation script for development workflow automation.

This script provides quick quality validation that can be used in:
- Pre-commit hooks
- Development workflow automation
- CI/CD pipeline validation
- Local development quality checks

Usage:
    python scripts/quality_gate.py          # Run all quality checks
    python scripts/quality_gate.py --fast   # Run quick checks only (no tests)
    python scripts/quality_gate.py --help   # Show usage information
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


class Colors:
    """ANSI color codes for terminal output."""

    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    RED = "\033[0;31m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"  # No Color


def run_command(cmd: List[str], description: str, cwd: Path) -> bool:
    """Run a command and return success status with colored output."""
    print(f"{Colors.CYAN}🔍 {description}...{Colors.NC}")

    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)

    if result.returncode == 0:
        print(f"{Colors.GREEN}✅ {description}: PASSED{Colors.NC}")
        return True
    else:
        print(f"{Colors.RED}❌ {description}: FAILED{Colors.NC}")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")
        return False


def check_formatting(project_root: Path) -> bool:
    """Check code formatting with Black."""
    return run_command(
        [sys.executable, "-m", "black", "--check", "."],
        "Code formatting (Black)",
        project_root,
    )


def check_imports(project_root: Path) -> bool:
    """Check import sorting with isort."""
    return run_command(
        [sys.executable, "-m", "isort", "--check-only", "."],
        "Import sorting (isort)",
        project_root,
    )


def check_pylint(project_root: Path) -> bool:
    """Check code quality with Pylint."""
    cmd = [
        sys.executable,
        "-m",
        "pylint",
        "src/ticker_converter/",
        "dags/",
        "--score=yes",
    ]
    result = subprocess.run(
        cmd, cwd=project_root, capture_output=True, text=True, check=False
    )

    if result.returncode == 0 and "10.00/10" in result.stdout:
        print(f"{Colors.GREEN}✅ Code quality (Pylint): 10.00/10 PASSED{Colors.NC}")
        return True
    else:
        print(
            f"{Colors.RED}❌ Code quality (Pylint): FAILED (must be 10.00/10){Colors.NC}"
        )
        print(result.stdout)
        return False


def check_mypy(project_root: Path) -> bool:
    """Check type annotations with MyPy."""
    return run_command(
        [sys.executable, "-m", "mypy", "src/ticker_converter/"],
        "Type checking (MyPy)",
        project_root,
    )


def check_tests(project_root: Path) -> bool:
    """Run test suite with coverage validation."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "--cov=ticker_converter",
        "--cov-report=term-missing",
        "--cov-fail-under=67",
        "--ignore=tests/integration",
        "-q",
    ]
    return run_command(cmd, "Test suite with 67%+ coverage", project_root)


def main() -> int:
    """Run quality gate validation."""
    parser = argparse.ArgumentParser(
        description="Quality gate validation for development workflow"
    )
    parser.add_argument(
        "--fast", action="store_true", help="Run fast checks only (skip test execution)"
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    checks_passed = []

    print(f"{Colors.BLUE}🚀 Quality Gate Validation{Colors.NC}")
    print(
        f"{Colors.CYAN}{'Fast mode' if args.fast else 'Full validation'}: Black → isort → Pylint → MyPy{' → Tests' if not args.fast else ''}{Colors.NC}"
    )
    print()

    # Run all quality checks
    checks = [
        ("formatting", check_formatting),
        ("imports", check_imports),
        ("pylint", check_pylint),
        ("mypy", check_mypy),
    ]

    if not args.fast:
        checks.append(("tests", check_tests))

    for _, check_func in checks:
        success = check_func(project_root)
        checks_passed.append(success)
        print()

    # Summary
    all_passed = all(checks_passed)

    print("=" * 70)
    if all_passed:
        print(f"{Colors.GREEN}🎉 All Quality Gates PASSED!{Colors.NC}")
        print(f"{Colors.CYAN}✓ Code formatting: Black compliant{Colors.NC}")
        print(f"{Colors.CYAN}✓ Import sorting: isort compliant{Colors.NC}")
        print(f"{Colors.CYAN}✓ Code quality: Pylint 10.00/10{Colors.NC}")
        print(f"{Colors.CYAN}✓ Type safety: MyPy clean{Colors.NC}")
        if not args.fast:
            print(
                f"{Colors.CYAN}✓ Test coverage: 67%+ with all tests passing{Colors.NC}"
            )
        print(f"{Colors.GREEN}🚀 Ready for commit and pull request!{Colors.NC}")
    else:
        failed_count = sum(1 for passed in checks_passed if not passed)
        print(f"{Colors.RED}❌ {failed_count} quality gate(s) failed{Colors.NC}")
        print(f"{Colors.YELLOW}💡 Quick fixes:{Colors.NC}")
        print(f"{Colors.CYAN}  - Formatting/import issues: make lint-fix{Colors.NC}")
        print(f"{Colors.CYAN}  - Full quality validation: make quality{Colors.NC}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
