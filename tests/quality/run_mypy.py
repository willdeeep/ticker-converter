#!/usr/bin/env python3
"""Standardized mypy type checking for code quality validation.

This script provides consistent mypy execution for the project's src layout.
TODO: Integrate this mypy execution into the main test CLI for unified quality checks.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run mypy on source code with proper configuration."""
    project_root = Path(__file__).parent.parent.parent
    
    # Run mypy on src directory only (avoids import path conflicts)
    print("🔍 Running mypy type checking on source code...")
    cmd = [
        sys.executable, "-m", "mypy", 
        "src/", 
        "--strict",
        "--show-error-codes",
        "--pretty"
    ]
    
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, check=False)
    
    if result.returncode == 0:
        print("✅ MyPy type checking passed successfully!")
        print(f"📊 Checked source files in src/ directory")
    else:
        print("❌ MyPy type checking found issues:")
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
