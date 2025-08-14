#!/usr/bin/env python3
"""
Script to add type annotations to test functions.
This will add '-> None' to test functions missing return type annotations.
"""

import os
import re
import sys
from pathlib import Path


def add_type_annotations_to_file(file_path: Path) -> bool:
    """Add type annotations to test functions in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to match test functions without return type annotations
        # This matches: def test_function_name(params):
        pattern = r'^(\s*def\s+(?:test_|pytest_)[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\))(\s*):(\s*)$'
        
        def replacement(match):
            indent = match.group(1)
            colon_and_spaces = match.group(3)
            return f"{indent} -> None:{colon_and_spaces}"
        
        # Apply the replacement
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        # Also handle fixture functions and other common patterns
        fixture_pattern = r'^(\s*def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\))(\s*):(\s*)$'
        
        def fixture_replacement(match):
            line = match.group(0)
            # Skip if already has type annotation
            if ' -> ' in line:
                return line
            # Skip if it's a class method (has 'self' parameter)
            if 'self' in match.group(1):
                return line
            # Skip if it clearly returns something (has 'return' in docstring area)
            return line  # For now, be conservative
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to process test files."""
    base_path = Path("tests")

    if not base_path.exists():
        print("tests directory not found")
        return

    modified_files = []

    # Find all Python test files
    for py_file in base_path.rglob("*.py"):
        if py_file.name.startswith("test_") or "test" in str(py_file):
            if add_type_annotations_to_file(py_file):
                modified_files.append(py_file)

    print(f"Modified {len(modified_files)} files:")
    for f in modified_files:
        print(f"  {f}")


if __name__ == "__main__":
    main()
