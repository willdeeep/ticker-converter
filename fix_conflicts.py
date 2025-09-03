#!/usr/bin/env python3
"""
Platform Variable Fixer
======================

Fixes platform variable conflicts by using proper conditional assignment
instead of multiple definitions.
"""

import pathlib
import re

def fix_platform_variables():
    """Fix platform variable conflicts in Makefile.platform."""
    platform_file = pathlib.Path("make/Makefile.platform")
    
    if not platform_file.exists():
        print("❌ Makefile.platform not found")
        return
        
    content = platform_file.read_text()
    
    # Find all the conditional blocks and replace with single assignments
    replacements = [
        # Platform OS detection
        (
            r'ifeq \(\$\(DETECTED_OS\),Darwin\)\s*\n\s*PLATFORM_OS := macos.*?else\s*\n\s*PLATFORM_OS := windows.*?endif',
            'PLATFORM_OS ?= $(shell if [ "$(DETECTED_OS)" = "Darwin" ]; then echo "macos"; elif [ "$(DETECTED_OS)" = "Linux" ]; then echo "linux"; else echo "windows"; fi)'
        ),
        # Platform family detection  
        (
            r'ifeq \(\$\(DETECTED_OS\),Darwin\)\s*\n\s*PLATFORM_OS := macos\s*\n\s*PLATFORM_FAMILY := unix.*?else\s*\n\s*PLATFORM_OS := windows\s*\n\s*PLATFORM_FAMILY := windows.*?endif',
            '''# Platform detection using conditional assignment
PLATFORM_OS ?= $(shell \\
    if [ "$(DETECTED_OS)" = "Darwin" ]; then \\
        echo "macos"; \\
    elif [ "$(DETECTED_OS)" = "Linux" ]; then \\
        echo "linux"; \\
    else \\
        echo "windows"; \\
    fi)

PLATFORM_FAMILY ?= $(shell \\
    if [ "$(DETECTED_OS)" = "Darwin" ] || [ "$(DETECTED_OS)" = "Linux" ]; then \\
        echo "unix"; \\
    else \\
        echo "windows"; \\
    fi)'''
        )
    ]
    
    # Apply replacements
    modified_content = content
    for pattern, replacement in replacements:
        modified_content = re.sub(pattern, replacement, modified_content, flags=re.DOTALL | re.MULTILINE)
    
    # Write back if changes were made
    if modified_content != content:
        platform_file.write_text(modified_content)
        print("✅ Fixed platform variable conflicts")
    else:
        print("ℹ️ No platform variable changes needed")

def fix_env_variables():
    """Fix environment variable conflicts in Makefile.env."""
    env_file = pathlib.Path("make/Makefile.env")
    
    if not env_file.exists():
        print("❌ Makefile.env not found")
        return
        
    content = env_file.read_text()
    
    # Look for duplicate VENV_PATH definitions
    lines = content.split('\n')
    fixed_lines = []
    seen_vars = set()
    
    for line in lines:
        # Check for variable assignments
        var_match = re.match(r'^([A-Z_]+)\s*:?=', line.strip())
        if var_match:
            var_name = var_match.group(1)
            if var_name in seen_vars:
                # Skip duplicate definition
                continue
            seen_vars.add(var_name)
        
        fixed_lines.append(line)
    
    modified_content = '\n'.join(fixed_lines)
    
    if modified_content != content:
        env_file.write_text(modified_content)
        print("✅ Fixed environment variable conflicts")
    else:
        print("ℹ️ No environment variable changes needed")

def fix_common_variable_conflicts():
    """Fix common variable conflicts across modules."""
    
    # Variables that should only be defined in one place
    variable_ownership = {
        'SRC_DIR': 'make/Makefile.testing',  # Keep in testing
        'TEST_DIR': 'make/Makefile.testing',  # Keep in testing
        'VENV_PATH': 'make/Makefile.env',  # Keep in env
    }
    
    for var_name, owner_file in variable_ownership.items():
        print(f"🔧 Fixing {var_name} conflicts...")
        
        # Find all files that define this variable
        make_files = [pathlib.Path("Makefile")] + list(pathlib.Path("make").glob("Makefile.*"))
        
        for file_path in make_files:
            if not file_path.exists():
                continue
                
            content = file_path.read_text()
            lines = content.split('\n')
            
            # Remove variable definition if not the owner
            if str(file_path) != owner_file:
                modified_lines = []
                for line in lines:
                    if re.match(f'^{var_name}\\s*[:?]?=', line.strip()):
                        print(f"  Removing {var_name} from {file_path.name}")
                        continue  # Skip this line
                    modified_lines.append(line)
                
                modified_content = '\n'.join(modified_lines)
                if modified_content != content:
                    file_path.write_text(modified_content)

def main():
    """Main execution function."""
    print("🔧 **FIXING MAKEFILE VARIABLE CONFLICTS**")
    print("========================================")
    
    fix_platform_variables()
    fix_env_variables() 
    fix_common_variable_conflicts()
    
    print("\n✅ **VARIABLE CONFLICT FIXES COMPLETE**")
    print("Re-run diagnostic to verify fixes")

if __name__ == "__main__":
    main()
