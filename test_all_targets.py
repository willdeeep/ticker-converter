#!/usr/bin/env python3
"""
Comprehensive Makefile Target Testing Script

This script extracts all make targets from all Makefile modules and tests
each one to identify broken targets that don't exist or fail to execute.
"""

import subprocess
import re
import pathlib
from typing import List, Dict, Set, Tuple
import sys

class MakefileTargetTester:
    def __init__(self, base_dir: str = "."):
        self.base_dir = pathlib.Path(base_dir)
        self.makefile_paths = [
            self.base_dir / "Makefile",
            self.base_dir / "make" / "Makefile.platform",
            self.base_dir / "make" / "Makefile.env", 
            self.base_dir / "make" / "Makefile.install",
            self.base_dir / "make" / "Makefile.database",
            self.base_dir / "make" / "Makefile.airflow",
            self.base_dir / "make" / "Makefile.testing",
            self.base_dir / "make" / "Makefile.quality",
            self.base_dir / "make" / "Makefile.cleanup",
            self.base_dir / "make" / "Makefile.common"
        ]
        self.all_targets = set()
        self.broken_targets = []
        self.working_targets = []
        self.help_targets = set()
        
    def extract_targets_from_file(self, filepath: pathlib.Path) -> Set[str]:
        """Extract all target definitions from a Makefile."""
        if not filepath.exists():
            return set()
            
        targets = set()
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find target definitions (lines that start with word characters followed by colon)
            # Exclude variable assignments, internal targets, and special patterns
            for line in content.split('\n'):
                line = line.strip()
                # Skip comments, empty lines, and internal targets
                if (line.startswith('#') or not line or line.startswith('_') 
                    or line.startswith('.') or not line):
                    continue
                
                # Skip variable assignments (contains = before :)
                if '=' in line and ':' in line:
                    eq_pos = line.find('=')
                    colon_pos = line.find(':')
                    if eq_pos < colon_pos and eq_pos != -1:
                        continue
                
                # Look for target pattern: word followed by colon
                if ':' in line:
                    target_part = line.split(':')[0].strip()
                    # Skip if it contains variables or special characters indicating it's not a simple target
                    if ('$' in target_part or '(' in target_part or ')' in target_part 
                        or target_part.isupper() or len(target_part.split()) > 1):
                        continue
                    
                    # Valid target pattern
                    target_pattern = r'^([a-zA-Z][a-zA-Z0-9\-_]*)\s*$'
                    match = re.match(target_pattern, target_part)
                    if match:
                        target_name = match.group(1)
                        # Additional filters for targets that are definitely not Make targets
                        if not target_name.startswith('.') and not target_name.startswith('_'):
                            targets.add(target_name)
                        
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            
        return targets
    
    def extract_help_targets(self) -> Set[str]:
        """Extract targets mentioned in help documentation."""
        help_targets = set()
        help_script = self.base_dir / "make" / "help.sh"
        
        if help_script.exists():
            try:
                with open(help_script, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Look for target mentions in help text
                # Pattern: make target-name or "make target-name"
                # Exclude template patterns like help-<category>
                target_pattern = r'make\s+([a-zA-Z][a-zA-Z0-9\-_]*)'
                matches = re.findall(target_pattern, content)
                # Filter out template patterns
                filtered_matches = [m for m in matches if not ('<' in m or '>' in m or m.endswith('-'))]
                help_targets.update(filtered_matches)
                
            except Exception as e:
                print(f"Error reading help script: {e}")
                
        return help_targets
    
    def test_target(self, target: str) -> Tuple[bool, str, str]:
        """Test if a make target exists and can be executed."""
        # Skip interactive commands that require user input
        interactive_commands = {
            'clean-all', 'clean-interactive', 'clean-reset', 
            'db-restore', 'pre-commit'
        }
        
        if target in interactive_commands:
            # Test with dry-run for interactive commands
            try:
                result = subprocess.run(
                    ['make', '-n', target],
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False
                )
                
                if "No rule to make target" in result.stderr:
                    return False, "TARGET_NOT_FOUND", result.stderr.strip()
                else:
                    return True, "WORKING", "Interactive command (dry-run passed)"
                    
            except subprocess.TimeoutExpired:
                return False, "TIMEOUT", "Target test timed out"
            except Exception as e:
                return False, "ERROR", f"Error testing target: {e}"
        
        try:
            # First check if target exists using make -n (dry run)
            result = subprocess.run(
                ['make', '-n', target],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            
            # Check for "No rule to make target" error
            if "No rule to make target" in result.stderr:
                return False, "TARGET_NOT_FOUND", result.stderr.strip()
            
            # If dry run succeeds, target exists
            if result.returncode == 0:
                return True, "SUCCESS", "Target exists and dry-run successful"
            
            # Target exists but has issues
            return False, "TARGET_ERROR", result.stderr.strip()
            
        except subprocess.TimeoutExpired:
            return False, "TIMEOUT", "Target test timed out"
        except Exception as e:
            return False, "EXECUTION_ERROR", str(e)
    
    def run_comprehensive_test(self):
        """Run comprehensive target testing."""
        print("🚀 **MAKEFILE TARGET COMPREHENSIVE TESTING**")
        print("=" * 55)
        
        # Extract all targets from all Makefiles
        print("🔍 **EXTRACTING TARGETS FROM ALL MAKEFILES**")
        for makefile_path in self.makefile_paths:
            if makefile_path.exists():
                targets = self.extract_targets_from_file(makefile_path)
                self.all_targets.update(targets)
                print(f"   📄 {makefile_path.name}: {len(targets)} targets")
            else:
                print(f"   ❌ {makefile_path.name}: File not found")
        
        # Extract targets from help documentation
        help_targets = self.extract_help_targets()
        self.help_targets = help_targets
        print(f"   📖 help.sh: {len(help_targets)} documented targets")
        
        # Add help targets to test list
        self.all_targets.update(help_targets)
        
        print(f"\n📊 **TOTAL UNIQUE TARGETS TO TEST: {len(self.all_targets)}**\n")
        
        # Test each target
        print("🧪 **TESTING ALL TARGETS**")
        print("-" * 50)
        
        for i, target in enumerate(sorted(self.all_targets), 1):
            print(f"Testing {i:3d}/{len(self.all_targets)}: {target:<25} ", end="", flush=True)
            
            success, status, message = self.test_target(target)
            
            if success:
                print("✅ WORKING")
                self.working_targets.append(target)
            else:
                print(f"❌ {status}")
                self.broken_targets.append({
                    'target': target,
                    'status': status,
                    'message': message,
                    'in_help': target in self.help_targets
                })
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "=" * 70)
        print("📋 **COMPREHENSIVE TARGET TEST REPORT**")
        print("=" * 70)
        
        print(f"\n📊 **SUMMARY STATISTICS**")
        print(f"Total targets tested: {len(self.all_targets)}")
        print(f"Working targets: {len(self.working_targets)}")
        print(f"Broken targets: {len(self.broken_targets)}")
        print(f"Success rate: {(len(self.working_targets)/len(self.all_targets)*100):.1f}%")
        
        if self.broken_targets:
            print(f"\n🔴 **BROKEN TARGETS ({len(self.broken_targets)} total)**")
            print("-" * 60)
            
            # Group by error type
            by_status = {}
            for broken in self.broken_targets:
                status = broken['status']
                if status not in by_status:
                    by_status[status] = []
                by_status[status].append(broken)
            
            for status, targets in by_status.items():
                print(f"\n❌ **{status} ({len(targets)} targets)**")
                for target in targets:
                    help_indicator = " 📖" if target['in_help'] else ""
                    print(f"   • {target['target']}{help_indicator}")
                    if target['message'] and len(target['message']) < 100:
                        print(f"     └─ {target['message']}")
            
            print(f"\n🔧 **PRIORITY FIXES NEEDED**")
            print("-" * 30)
            
            # High priority: targets mentioned in help
            help_broken = [t for t in self.broken_targets if t['in_help']]
            if help_broken:
                print("📖 **Documented targets that are broken:**")
                for target in help_broken:
                    print(f"   • {target['target']} ({target['status']})")
            
            # Missing targets
            missing_targets = [t for t in self.broken_targets if t['status'] == 'TARGET_NOT_FOUND']
            if missing_targets:
                print(f"\n🚫 **Missing target definitions ({len(missing_targets)} targets):**")
                for target in missing_targets:
                    print(f"   • {target['target']}")
        
        else:
            print("\n✅ **ALL TARGETS WORKING PERFECTLY!**")
        
        print(f"\n📝 **FIX RECOMMENDATIONS**")
        print("-" * 30)
        
        if not self.broken_targets:
            print("✅ No fixes needed - all targets are working!")
        else:
            print("1. **Priority 1**: Fix targets mentioned in help documentation")
            print("2. **Priority 2**: Add missing target definitions")  
            print("3. **Priority 3**: Fix targets with execution errors")
            print("4. **Verification**: Re-run this script after fixes")
        
        print(f"\n🎯 **NEXT STEPS**")
        print("-" * 15)
        if self.broken_targets:
            print("1. Review broken targets list above")
            print("2. Add missing target definitions to appropriate Makefile modules")
            print("3. Fix target implementation issues")
            print("4. Re-run test script to verify fixes")
            print("5. Update help documentation if needed")
        else:
            print("🎉 All targets are working! Makefile system is complete.")

def main():
    tester = MakefileTargetTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
