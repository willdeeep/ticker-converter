#!/usr/bin/env python3
"""
Comprehensive Makefile Command Deduplication Analysis Tool
Analyzes all commands                for alias in aliases:
                    alias_type = "legacy" if alias in legacy_aliases else "alias"
                    print(f"  - `{alias}` ({alias_type})")ross the modular Makefile system to identify:
1. Synonyms and functional duplicates
2. Unnecessary redundancy 
3. Refactoring opportunities
4. Command consolidation recommendations
"""

import re
import subprocess
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple
import difflib

class MakefileAnalyzer:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.commands = {}  # command_name -> {file, line, description, dependencies, implementation}
        self.synonyms = defaultdict(list)  # primary_command -> [aliases]
        self.functional_groups = defaultdict(list)  # function_type -> [commands]
        
    def extract_all_commands(self):
        """Extract all commands from all Makefile sources"""
        makefile_paths = [
            self.workspace_root / "Makefile",
            self.workspace_root / "make" / "Makefile.platform",
            self.workspace_root / "make" / "Makefile.env", 
            self.workspace_root / "make" / "Makefile.install",
            self.workspace_root / "make" / "Makefile.database",
            self.workspace_root / "make" / "Makefile.airflow",
            self.workspace_root / "make" / "Makefile.testing",
            self.workspace_root / "make" / "Makefile.quality",
            self.workspace_root / "make" / "Makefile.cleanup"
        ]
        
        for makefile_path in makefile_paths:
            if makefile_path.exists():
                self._parse_makefile(makefile_path)
                
    def _parse_makefile(self, makefile_path: Path):
        """Parse individual Makefile and extract command details"""
        with open(makefile_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        current_command = None
        for i, line in enumerate(lines, 1):
            # Match command definitions: command_name: [dependencies] ## description
            cmd_match = re.match(r'^([a-zA-Z][a-zA-Z0-9_-]*)\s*:\s*([^#]*?)(?:\s*##\s*(.*))?$', line.strip())
            if cmd_match:
                cmd_name = cmd_match.group(1)
                dependencies = cmd_match.group(2).strip() if cmd_match.group(2) else ""
                description = cmd_match.group(3).strip() if cmd_match.group(3) else ""
                
                # Extract implementation (next few lines)
                implementation_lines = []
                for j in range(i, min(i + 10, len(lines))):
                    if j < len(lines) and lines[j].startswith('\t'):
                        implementation_lines.append(lines[j].strip())
                    elif j > i and lines[j].strip() and not lines[j].startswith('\t'):
                        break
                        
                self.commands[cmd_name] = {
                    'file': makefile_path.name,
                    'line': i,
                    'description': description,
                    'dependencies': dependencies,
                    'implementation': implementation_lines,
                    'full_line': line.strip()
                }
                
    def identify_synonyms(self):
        """Identify command synonyms and aliases"""
        print("🔍 **SYNONYM AND ALIAS ANALYSIS**\n")
        
        # Direct aliases (command: other_command format)
        direct_aliases = {}
        legacy_aliases = {}
        
        for cmd_name, cmd_info in self.commands.items():
            deps = cmd_info['dependencies']
            desc = cmd_info['description']
            
            # Check for direct aliases (single dependency, no implementation)
            if deps and not cmd_info['implementation']:
                # Split dependencies and check if it's a single command
                dep_parts = [d.strip() for d in deps.split() if not d.startswith('_')]
                if len(dep_parts) == 1 and dep_parts[0] in self.commands:
                    if 'legacy' in desc.lower() or 'alias' in desc.lower():
                        legacy_aliases[cmd_name] = dep_parts[0]
                    else:
                        direct_aliases[cmd_name] = dep_parts[0]
        
        # Group by target command
        alias_groups = defaultdict(list)
        for alias, target in {**direct_aliases, **legacy_aliases}.items():
            alias_groups[target].append(alias)
            
        # Report aliases
        if alias_groups:
            print("### 📋 **Direct Command Aliases**")
            for target, aliases in sorted(alias_groups.items()):
                legacy_count = sum(1 for a in aliases if a in legacy_aliases)
                modern_count = len(aliases) - legacy_count
                print(f"- **`{target}`** ← {modern_count} modern aliases, {legacy_count} legacy aliases")
                for alias in aliases:
                    alias_type = "🏷️ legacy" if alias in legacy_aliases else "🔗 alias"
                    print(f"  - `{alias}` ({alias_type})")
            print()
        
        return direct_aliases, legacy_aliases
        
    def identify_functional_duplicates(self):
        """Identify commands with similar functionality"""
        print("🎯 **FUNCTIONAL DUPLICATE ANALYSIS**\n")
        
        # Group by functional patterns
        function_patterns = {
            'test': r'test|spec|check',
            'install': r'install|setup|deps',
            'clean': r'clean|remove|delete|teardown', 
            'lint': r'lint|format|quality|style',
            'database': r'db|database|postgres',
            'airflow': r'airflow|dag|workflow',
            'coverage': r'coverage|cov',
            'help': r'help|info|show',
            'debug': r'debug|diagnose|doctor',
            'validate': r'validate|verify|check',
            'config': r'config|settings|env'
        }
        
        functional_groups = defaultdict(list)
        
        for cmd_name, cmd_info in self.commands.items():
            desc = cmd_info['description'].lower()
            cmd_lower = cmd_name.lower()
            
            for func_type, pattern in function_patterns.items():
                if re.search(pattern, cmd_lower) or re.search(pattern, desc):
                    functional_groups[func_type].append((cmd_name, cmd_info))
        
        # Analyze each functional group for duplicates
        for func_type, commands in functional_groups.items():
            if len(commands) > 3:  # Only analyze groups with multiple commands
                print(f"### 🏗️ **{func_type.upper()} Commands** ({len(commands)} commands)")
                
                # Sub-categorize by more specific patterns
                subcategories = defaultdict(list)
                for cmd_name, cmd_info in commands:
                    # Extract more specific patterns
                    if 'coverage' in cmd_name or 'coverage' in cmd_info['description'].lower():
                        subcategories['coverage'].append(cmd_name)
                    elif 'report' in cmd_name or 'report' in cmd_info['description'].lower():
                        subcategories['reporting'].append(cmd_name)
                    elif 'check' in cmd_name or 'validate' in cmd_name:
                        subcategories['validation'].append(cmd_name)
                    elif 'fix' in cmd_name or 'auto' in cmd_info['description'].lower():
                        subcategories['auto-fix'].append(cmd_name)
                    elif 'debug' in cmd_name or 'info' in cmd_name:
                        subcategories['diagnostic'].append(cmd_name)
                    elif 'clean' in cmd_name:
                        subcategories['cleanup'].append(cmd_name)
                    else:
                        subcategories['general'].append(cmd_name)
                
                for subcat, cmd_list in subcategories.items():
                    if len(cmd_list) > 1:
                        print(f"  **{subcat.title()}**: {', '.join(f'`{cmd}`' for cmd in cmd_list)}")
                
                print()
        
        return functional_groups
        
    def analyze_description_similarity(self):
        """Find commands with very similar descriptions"""
        print("📝 **DESCRIPTION SIMILARITY ANALYSIS**\n")
        
        descriptions = {}
        for cmd_name, cmd_info in self.commands.items():
            desc = cmd_info['description']
            if desc and len(desc) > 10:  # Skip very short descriptions
                descriptions[cmd_name] = desc
        
        # Find similar descriptions
        similar_groups = []
        checked = set()
        
        for cmd1, desc1 in descriptions.items():
            if cmd1 in checked:
                continue
                
            similar_to_cmd1 = [cmd1]
            checked.add(cmd1)
            
            for cmd2, desc2 in descriptions.items():
                if cmd2 != cmd1 and cmd2 not in checked:
                    # Use difflib to find similarity
                    similarity = difflib.SequenceMatcher(None, desc1.lower(), desc2.lower()).ratio()
                    if similarity > 0.7:  # 70% similarity threshold
                        similar_to_cmd1.append(cmd2)
                        checked.add(cmd2)
            
            if len(similar_to_cmd1) > 1:
                similar_groups.append(similar_to_cmd1)
        
        if similar_groups:
            print("### 🔗 **Commands with Similar Descriptions**")
            for group in similar_groups:
                print(f"**Similar descriptions:**")
                for cmd in group:
                    print(f"  - `{cmd}`: {descriptions[cmd]}")
                print()
        else:
            print("✅ No commands found with significantly similar descriptions.\n")
            
    def analyze_implementation_overlap(self):
        """Find commands with overlapping implementations"""
        print("⚙️ **IMPLEMENTATION OVERLAP ANALYSIS**\n")
        
        # Look for commands that have identical or very similar implementation
        implementations = {}
        for cmd_name, cmd_info in self.commands.items():
            impl = ' '.join(cmd_info['implementation'])
            if impl and len(impl) > 10:
                implementations[cmd_name] = impl
        
        # Find similar implementations
        overlap_groups = []
        checked = set()
        
        for cmd1, impl1 in implementations.items():
            if cmd1 in checked:
                continue
                
            similar_to_cmd1 = [cmd1]
            checked.add(cmd1)
            
            for cmd2, impl2 in implementations.items():
                if cmd2 != cmd1 and cmd2 not in checked:
                    similarity = difflib.SequenceMatcher(None, impl1, impl2).ratio()
                    if similarity > 0.8:  # 80% similarity threshold
                        similar_to_cmd1.append(cmd2)
                        checked.add(cmd2)
            
            if len(similar_to_cmd1) > 1:
                overlap_groups.append(similar_to_cmd1)
        
        if overlap_groups:
            print("### 🔄 **Commands with Similar Implementations**")
            for group in overlap_groups:
                print(f"**Similar implementations:**")
                for cmd in group:
                    impl_preview = implementations[cmd][:100] + "..." if len(implementations[cmd]) > 100 else implementations[cmd]
                    print(f"  - `{cmd}`: {impl_preview}")
                print()
        else:
            print("✅ No commands found with significantly overlapping implementations.\n")
            
    def identify_redundant_commands(self):
        """Identify truly redundant commands that should be removed"""
        print("🗑️ **REDUNDANCY ELIMINATION RECOMMENDATIONS**\n")
        
        redundant_commands = []
        
        # Criteria for redundancy:
        # 1. Multiple aliases pointing to the same target
        # 2. Commands with identical functionality in different modules
        # 3. Legacy commands that duplicate modern equivalents
        
        direct_aliases, legacy_aliases = self.identify_synonyms()
        
        # Analyze legacy alias necessity
        print("### 🏷️ **Legacy Alias Analysis**")
        for alias, target in legacy_aliases.items():
            alias_info = self.commands.get(alias, {})
            target_info = self.commands.get(target, {})
            
            if alias_info and target_info:
                print(f"- **`{alias}`** → `{target}`")
                print(f"  - Legacy: {alias_info['description']}")
                print(f"  - Modern: {target_info['description']}")
                print(f"  - **Recommendation**: Consider deprecating `{alias}` in favor of `{target}`")
                print()
        
        return redundant_commands
        
    def suggest_refactoring_opportunities(self):
        """Suggest code refactoring opportunities"""
        print("🔧 **REFACTORING OPPORTUNITIES**\n")
        
        # Look for repeated patterns that could be functions
        common_patterns = defaultdict(list)
        
        for cmd_name, cmd_info in self.commands.items():
            impl = cmd_info['implementation']
            for line in impl:
                # Look for common patterns
                if 'echo' in line and 'printf' in line:
                    common_patterns['output_formatting'].append(cmd_name)
                elif '@echo' in line and '=====' in line:
                    common_patterns['section_headers'].append(cmd_name)
                elif 'find' in line and '-name' in line and '*.py' in line:
                    common_patterns['python_file_finding'].append(cmd_name)
                elif 'pip install' in line:
                    common_patterns['pip_operations'].append(cmd_name)
                elif 'psql' in line or 'pg_' in line:
                    common_patterns['postgres_operations'].append(cmd_name)
        
        if common_patterns:
            print("### 🔨 **Common Patterns for Function Extraction**")
            for pattern_type, commands in common_patterns.items():
                if len(commands) > 2:
                    print(f"**{pattern_type.replace('_', ' ').title()}** (used in {len(commands)} commands):")
                    print(f"  Commands: {', '.join(f'`{cmd}`' for cmd in commands[:5])}")
                    if len(commands) > 5:
                        print(f"  ... and {len(commands) - 5} more")
                    print(f"  **Recommendation**: Extract common logic into a shared function")
                    print()
        else:
            print("✅ No obvious common patterns found for function extraction.\n")
            
    def generate_optimization_report(self):
        """Generate comprehensive optimization recommendations"""
        print("📊 **OPTIMIZATION SUMMARY REPORT**\n")
        
        total_commands = len(self.commands)
        direct_aliases, legacy_aliases = self.identify_synonyms()
        
        stats = {
            'total_commands': total_commands,
            'direct_aliases': len(direct_aliases),
            'legacy_aliases': len(legacy_aliases),
            'unique_functional_commands': total_commands - len(direct_aliases) - len(legacy_aliases)
        }
        
        print(f"### 📈 **Command Statistics**")
        print(f"- **Total Commands**: {stats['total_commands']}")
        print(f"- **Direct Aliases**: {stats['direct_aliases']}")
        print(f"- **Legacy Aliases**: {stats['legacy_aliases']}")
        print(f"- **Unique Functional Commands**: {stats['unique_functional_commands']}")
        print(f"- **Alias Ratio**: {((stats['direct_aliases'] + stats['legacy_aliases']) / stats['total_commands'] * 100):.1f}%")
        print()
        
        # Distribution by module
        module_distribution = defaultdict(int)
        for cmd_info in self.commands.values():
            module_distribution[cmd_info['file']] += 1
            
        print(f"### 📂 **Command Distribution by Module**")
        for module, count in sorted(module_distribution.items(), key=lambda x: x[1], reverse=True):
            print(f"- **{module}**: {count} commands")
        print()
        
        return stats
        
    def run_full_analysis(self):
        """Run complete deduplication analysis"""
        print("# 🎯 **MAKEFILE COMMAND DEDUPLICATION ANALYSIS REPORT**")
        print("=" * 70)
        print()
        
        self.extract_all_commands()
        
        # Run all analysis components
        self.identify_synonyms()
        self.identify_functional_duplicates()
        self.analyze_description_similarity()
        self.analyze_implementation_overlap()
        self.identify_redundant_commands()
        self.suggest_refactoring_opportunities()
        
        # Generate final recommendations
        stats = self.generate_optimization_report()
        
        print("### 🎯 **FINAL RECOMMENDATIONS**")
        print("1. **Legacy Alias Cleanup**: Consider deprecating legacy aliases in favor of modern equivalents")
        print("2. **Functional Consolidation**: Review functional groups for potential command merging")
        print("3. **Common Pattern Extraction**: Extract repeated implementation patterns into shared functions")
        print("4. **Documentation Standardization**: Ensure consistent command descriptions and help messages")
        print("5. **Module Organization**: Consider redistribution of commands for better logical grouping")
        print()
        
        return stats

if __name__ == "__main__":
    analyzer = MakefileAnalyzer("/Users/willhuntleyclarke/repos/interests/ticker-converter")
    analyzer.run_full_analysis()
