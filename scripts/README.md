# Scripts Directory

## Purpose
A designated place to create temporary test scripts used to diagnose errors or verify proper functionality. This directory exists to prevent cluttering of the root directory or other important subdirectories with temporary, single-use files.

## Directory Guidelines

### `/scripts/` (Root)
- **Use Case**: Temporary diagnostic, testing, and proof-of-concept scripts
- **Git Status**: Tracked (but contents are temporary and disposable)
- **File Types**: `*.py`, `*.sh`, `*.sql`, or any other script formats needed for testing

## Critical Principles

### ⚠️ Nothing Vital Should Live Here
- **Disposable**: The entire contents of this directory should be deletable without breaking the application
- **Temporary**: All scripts are for short-term use during development and debugging
- **Non-Production**: No production functionality should depend on scripts in this directory

### ✅ Appropriate Uses
- **Debugging Scripts**: Quick scripts to diagnose specific issues
- **Proof of Concept**: Testing new ideas or approaches before implementation
- **Data Validation**: One-off scripts to check data integrity or API responses
- **Performance Testing**: Temporary benchmarking and profiling scripts
- **Development Utilities**: Helper scripts for development workflow

### ❌ Inappropriate Uses
- **Production Code**: Any functionality needed for application operation
- **Shared Utilities**: Reusable functions that other modules depend on
- **Configuration**: Application or deployment configuration files
- **Documentation**: Project documentation or important guides

## Current Scripts (Temporary)

### `demo_capabilities.py`
**Purpose**: Demonstrates Alpha Vantage API functionality across asset classes
**Usage**: `python scripts/demo_capabilities.py`
**Status**: Useful for testing API connections and showcasing features

### `examine_stored_data.py`
**Purpose**: Analyzes locally stored data files without making API calls
**Usage**: `python scripts/examine_stored_data.py`
**Status**: Data validation utility

### `cleanup_data.py`
**Purpose**: Manages stored data files by keeping only latest versions
**Usage**: `python scripts/cleanup_data.py`
**Status**: Maintenance utility

### Other Scripts
Various diagnostic and testing utilities for development purposes.

## Workflow Process

### 1. Create Script
Place temporary testing or diagnostic scripts in `/scripts/` during development

### 2. Test and Validate
Use scripts to solve problems or test concepts

### 3. Integration Decision
- **If Useful**: Move functionality to appropriate directory (`/src/`, `/api/`, `/dags/`)
- **If Temporary**: Leave in `/scripts/` and clean up when no longer needed
- **If Obsolete**: Delete the script

### 4. Avoid Duplication
Before creating new functionality, check if similar code already exists in production directories.

## Organization Guidelines

### File Naming
- Use descriptive names: `debug_api_connection.py` not `test.py`
- Include date if relevant: `performance_test_2025_08_16.py`
- Group related scripts with prefixes when helpful

### Documentation
- Add brief comments explaining what each script does
- Include date created and purpose
- Note if script addresses a specific issue

## Cleanup Guidelines

### Regular Maintenance
- Review scripts monthly and delete obsolete ones
- Archive useful scripts that might be needed later
- Document findings before deleting diagnostic scripts

### Before Feature Completion
- Move valuable functionality to appropriate directories
- Update project documentation based on script findings
- Clean up temporary scripts used during development

## Integration Notes
Any functionality developed in `/scripts/` that proves valuable should be:
1. **Refactored** for production use
2. **Moved** to the appropriate directory (`/src/`, `/api/`, `/dags/`)
3. **Integrated** with existing code patterns
4. **Tested** through the normal testing framework
5. **Documented** in the appropriate documentation

**Remember**: Scripts directory is a workspace, not a destination!
