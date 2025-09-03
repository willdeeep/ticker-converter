#!/usr/bin/env python3
"""
Makefile Conflict Diagnostic Tool
===============================

Analyzes all Makefile modules to identify duplicate target definitions
that cause Make warnings and conflicts.
"""

import re
import pathlib
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import subprocess

class MakefileConflictDiagnostic:
    def __init__(self, make_dir: str = "make"):
        self.make_dir = pathlib.Path(make_dir)
        self.main_makefile = pathlib.Path("Makefile")
        self.target_definitions = defaultdict(list)  # target_name -> [(file, line_num, definition)]
        self.conflicts = []
        self.all_commands = []
        
    def analyze_all_makefiles(self) -> None:
        """Analyze all Makefile modules for target conflicts."""
        print("🔍 **MAKEFILE CONFLICT DIAGNOSTIC**")
        print("="*50)
        
        # Analyze main Makefile
        if self.main_makefile.exists():
            self._analyze_makefile(self.main_makefile)
            
        # Analyze all module files
        for makefile_path in sorted(self.make_dir.glob("Makefile.*")):
            self._analyze_makefile(makefile_path)
            
        # Identify conflicts
        self._identify_conflicts()
        
        # Test with actual Make command
        self._test_make_warnings()
        
    def _analyze_makefile(self, file_path: pathlib.Path) -> None:
        """Analyze a single Makefile for target definitions."""
        try:
            content = file_path.read_text()
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # Match target definitions: "target_name:"
                target_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_-]*)\s*:\s*(.*)$', line.strip())
                if target_match:
                    target_name = target_match.group(1)
                    dependencies = target_match.group(2).strip()
                    
                    # Skip .PHONY declarations
                    if target_name == '.PHONY':
                        continue
                        
                    self.target_definitions[target_name].append({
                        'file': file_path.name,
                        'line': line_num,
                        'definition': line.strip(),
                        'dependencies': dependencies
                    })
                    
        except Exception as e:
            print(f"⚠️ Error analyzing {file_path}: {e}")
            
    def _identify_conflicts(self) -> None:
        """Identify targets defined in multiple files."""
        print(f"\n📊 **ANALYSIS RESULTS**")
        print(f"Total unique targets found: {len(self.target_definitions)}")
        
        conflicts_found = 0
        for target_name, definitions in self.target_definitions.items():
            if len(definitions) > 1:
                conflicts_found += 1
                self.conflicts.append({
                    'target': target_name,
                    'definitions': definitions
                })
                
        print(f"Conflicting targets found: {conflicts_found}")
        
    def _test_make_warnings(self) -> None:
        """Test actual Make command to capture warnings."""
        print(f"\n🧪 **MAKE WARNING TEST**")
        try:
            # Run a simple make command to capture warnings
            result = subprocess.run(
                ['make', '-n', 'help'], 
                cwd=pathlib.Path.cwd(),
                capture_output=True, 
                text=True,
                check=False
            )
            
            if result.stderr:
                print("Make warnings detected:")
                for line in result.stderr.split('\n'):
                    if 'warning:' in line and ('overriding' in line or 'ignoring' in line):
                        print(f"  {line}")
            else:
                print("✅ No Make warnings detected")
                
        except Exception as e:
            print(f"⚠️ Error testing Make warnings: {e}")
            
    def generate_conflict_report(self) -> None:
        """Generate detailed conflict report."""
        print(f"\n📋 **DETAILED CONFLICT REPORT**")
        print("="*50)
        
        if not self.conflicts:
            print("✅ No target conflicts found!")
            return
            
        for conflict in self.conflicts:
            target = conflict['target']
            definitions = conflict['definitions']
            
            print(f"\n🔴 **CONFLICT: {target}**")
            print(f"   Defined in {len(definitions)} files:")
            
            for i, def_info in enumerate(definitions, 1):
                print(f"   {i}. {def_info['file']}:{def_info['line']}")
                print(f"      Definition: {def_info['definition']}")
                if def_info['dependencies']:
                    print(f"      Dependencies: {def_info['dependencies']}")
                    
            # Suggest resolution
            print(f"   💡 **Resolution needed**: Remove duplicates or rename targets")
            
    def generate_fix_recommendations(self) -> None:
        """Generate specific fix recommendations."""
        print(f"\n🔧 **FIX RECOMMENDATIONS**")
        print("="*50)
        
        if not self.conflicts:
            print("✅ No fixes needed!")
            return
            
        # Group conflicts by type
        internal_conflicts = []
        public_conflicts = []
        
        for conflict in self.conflicts:
            target = conflict['target']
            if target.startswith('_'):
                internal_conflicts.append(conflict)
            else:
                public_conflicts.append(conflict)
                
        if internal_conflicts:
            print(f"\n### 🔧 Internal Target Conflicts ({len(internal_conflicts)} targets)")
            print("These are likely dependency check functions that should be centralized:")
            
            for conflict in internal_conflicts:
                target = conflict['target']
                files = [d['file'] for d in conflict['definitions']]
                print(f"  • {target} → Keep in Makefile.common, remove from: {', '.join(files[1:])}")
                
        if public_conflicts:
            print(f"\n### ⚠️ Public Target Conflicts ({len(public_conflicts)} targets)")
            print("These need manual resolution:")
            
            for conflict in public_conflicts:
                target = conflict['target']
                files = [d['file'] for d in conflict['definitions']]
                print(f"  • {target} → Defined in: {', '.join(files)}")
                
    def test_all_help_commands(self) -> None:
        """Test all help commands to find additional issues."""
        print(f"\n🧪 **TESTING ALL HELP COMMANDS**")
        print("="*50)
        
        help_commands = [
            'help', 'help-platform', 'help-env', 'help-install', 
            'help-database', 'help-airflow', 'help-testing', 
            'help-quality', 'help-cleanup', 'help-common'
        ]
        
        for cmd in help_commands:
            try:
                result = subprocess.run(
                    ['make', '-n', cmd], 
                    cwd=pathlib.Path.cwd(),
                    capture_output=True, 
                    text=True,
                    timeout=10,
                    check=False
                )
                
                warnings = [line for line in result.stderr.split('\n') 
                           if 'warning:' in line and ('overriding' in line or 'ignoring' in line)]
                
                if warnings:
                    print(f"⚠️ {cmd}: {len(warnings)} warnings")
                else:
                    print(f"✅ {cmd}: clean")
                    
            except Exception as e:
                print(f"❌ {cmd}: error - {e}")
                
def main():
    """Main execution function."""
    print("🚀 **MAKEFILE CONFLICT DIAGNOSTIC TOOL**")
    print("=====================================")
    
    diagnostic = MakefileConflictDiagnostic()
    diagnostic.analyze_all_makefiles()
    diagnostic.generate_conflict_report()
    diagnostic.generate_fix_recommendations()
    diagnostic.test_all_help_commands()
    
    print(f"\n✅ **DIAGNOSTIC COMPLETE**")
    print("Use the recommendations above to fix conflicts")

if __name__ == "__main__":
    main()
