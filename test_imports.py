#!/usr/bin/env python3
"""Script to test all Python imports in the project for fatal errors."""

import importlib.util
import sys
from pathlib import Path


def find_python_files(root_path: Path) -> list[Path]:
    """Find all Python files in the project."""
    python_files = []

    # Exclude certain directories
    excluded_dirs = {
        ".venv",
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "htmlcov",
        "node_modules",
    }

    for py_file in root_path.rglob("*.py"):
        # Skip if any parent directory is in excluded list
        if any(part in excluded_dirs for part in py_file.parts):
            continue
        python_files.append(py_file)

    return sorted(python_files)


def test_file_import(file_path: Path, project_root: Path) -> dict[str, any]:
    """Test if a Python file can be imported without fatal errors."""
    result = {
        "file": str(file_path.relative_to(project_root)),
        "success": False,
        "error": None,
        "error_type": None,
    }

    try:
        # Create module name from file path
        relative_path = file_path.relative_to(project_root)
        module_name = str(relative_path.with_suffix("")).replace("/", ".")

        # Load the module spec
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            result["error"] = "Could not create module spec"
            result["error_type"] = "spec_error"
            return result

        # Create and execute the module
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result["success"] = True

    except SyntaxError as e:
        result["error"] = f"Syntax error: {e}"
        result["error_type"] = "syntax_error"
    except ModuleNotFoundError as e:
        result["error"] = f"Module not found: {e}"
        result["error_type"] = "module_not_found"
    except ImportError as e:
        result["error"] = f"Import error: {e}"
        result["error_type"] = "import_error"
    except (AttributeError, TypeError, ValueError) as e:
        result["error"] = f"Other error: {type(e).__name__}: {e}"
        result["error_type"] = "other_error"

    return result


def main():
    """Main function to test all imports."""
    project_root = Path(__file__).parent
    print(f"Testing imports in: {project_root}")
    print("=" * 80)

    # Find all Python files
    python_files = find_python_files(project_root)
    print(f"Found {len(python_files)} Python files to test")
    print()

    # Test each file
    results = []
    success_count = 0

    for file_path in python_files:
        result = test_file_import(file_path, project_root)
        results.append(result)

        if result["success"]:
            success_count += 1
            print(f"✅ {result['file']}")
        else:
            print(f"❌ {result['file']}")
            print(f"   Error: {result['error']}")
            print()

    # Summary
    print("=" * 80)
    print("SUMMARY:")
    print(f"Total files: {len(python_files)}")
    print(f"Successful imports: {success_count}")
    print(f"Failed imports: {len(python_files) - success_count}")

    # Group errors by type
    error_types = {}
    for result in results:
        if not result["success"]:
            error_type = result["error_type"]
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(result)

    if error_types:
        print("\nERROR BREAKDOWN:")
        for error_type, failed_results in error_types.items():
            print(f"\n{error_type.upper()} ({len(failed_results)} files):")
            for result in failed_results:
                print(f"  - {result['file']}: {result['error']}")

    # Return exit code
    return 0 if success_count == len(python_files) else 1


if __name__ == "__main__":
    sys.exit(main())
