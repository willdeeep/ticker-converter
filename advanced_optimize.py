#!/usr/bin/env python3
"""
Advanced Makefile Optimization: Phase 2 Implementation
=====================================================

Implements the final recommendations from the deduplication analysis:
1. Legacy Alias Cleanup (✅ Complete)
2. Functional Consolidation 
3. Common Pattern Extraction (✅ Complete)
4. Documentation Standardization
5. Module Organization

This script performs advanced optimizations including:
- Command consolidation based on functional similarity
- Documentation standardization across modules
- Module redistribution for better logical grouping
- Performance optimization through pattern extraction
"""

import re
import pathlib
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass

@dataclass
class CommandInfo:
    name: str
    description: str
    module: str
    dependencies: List[str]
    implementation: str
    category: str

class AdvancedMakefileOptimizer:
    def __init__(self, make_dir: str = "make"):
        self.make_dir = pathlib.Path(make_dir)
        self.commands: Dict[str, CommandInfo] = {}
        self.optimization_results = {
            "consolidations": [],
            "redistributions": [],
            "standardizations": [],
            "pattern_extractions": []
        }
        
    def analyze_commands(self) -> None:
        """Extract and analyze all commands from Makefile modules."""
        print("🔍 **PHASE 2 OPTIMIZATION ANALYSIS**")
        print("="*50)
        
        for makefile_path in self.make_dir.glob("Makefile.*"):
            self._analyze_makefile(makefile_path)
            
        self._analyze_main_makefile()
        
        print(f"📊 Total commands analyzed: {len(self.commands)}")
        
    def _analyze_makefile(self, path: pathlib.Path) -> None:
        """Analyze individual Makefile module."""
        module_name = path.name.replace("Makefile.", "")
        
        try:
            content = path.read_text()
            # Extract command definitions
            command_pattern = r'^([a-zA-Z][a-zA-Z0-9_-]*):.*?##\s*(.+?)$'
            matches = re.findall(command_pattern, content, re.MULTILINE)
            
            for name, description in matches:
                # Skip internal targets
                if name.startswith('_'):
                    continue
                    
                self.commands[name] = CommandInfo(
                    name=name,
                    description=description.strip(),
                    module=module_name,
                    dependencies=self._extract_dependencies(content, name),
                    implementation=self._extract_implementation(content, name),
                    category=self._categorize_command(name, description)
                )
                
        except Exception as e:
            print(f"⚠ Warning: Could not analyze {path}: {e}")
            
    def _analyze_main_makefile(self) -> None:
        """Analyze main Makefile."""
        main_path = pathlib.Path("Makefile")
        if main_path.exists():
            self._analyze_makefile_content(main_path, "main")
            
    def _analyze_makefile_content(self, path: pathlib.Path, module: str) -> None:
        """Helper to analyze Makefile content."""
        try:
            content = path.read_text()
            command_pattern = r'^([a-zA-Z][a-zA-Z0-9_-]*):.*?##\s*(.+?)$'
            matches = re.findall(command_pattern, content, re.MULTILINE)
            
            for name, description in matches:
                if name.startswith('_'):
                    continue
                    
                if name not in self.commands:  # Avoid duplicates
                    self.commands[name] = CommandInfo(
                        name=name,
                        description=description.strip(),
                        module=module,
                        dependencies=self._extract_dependencies(content, name),
                        implementation=self._extract_implementation(content, name),
                        category=self._categorize_command(name, description)
                    )
        except Exception as e:
            print(f"⚠ Warning: Could not analyze {path}: {e}")
            
    def _extract_dependencies(self, content: str, command: str) -> List[str]:
        """Extract command dependencies."""
        # Look for command definition line
        pattern = f'^{re.escape(command)}:\\s*([^#\\n]+)'
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            deps_line = match.group(1).strip()
            # Extract dependency names (simple heuristic)
            deps = [dep.strip() for dep in deps_line.split() if not dep.startswith('$')]
            return [dep for dep in deps if dep and not dep.startswith('-')]
        return []
        
    def _extract_implementation(self, content: str, command: str) -> str:
        """Extract command implementation (first few lines)."""
        lines = content.split('\n')
        in_command = False
        impl_lines = []
        
        for line in lines:
            if line.startswith(f"{command}:"):
                in_command = True
                continue
            elif in_command:
                if line.startswith('\t') or line.startswith(' '):
                    impl_lines.append(line.strip())
                    if len(impl_lines) >= 3:  # Get first 3 lines
                        break
                elif line.strip() and not line.startswith('#'):
                    break  # End of command
                    
        return ' '.join(impl_lines)[:100] + '...' if impl_lines else ''
        
    def _categorize_command(self, name: str, description: str) -> str:
        """Categorize command based on name and description."""
        test_keywords = ['test', 'coverage', 'benchmark', 'pytest']
        quality_keywords = ['lint', 'format', 'black', 'pylint', 'mypy', 'quality']
        database_keywords = ['db', 'database', 'postgres', 'sql']
        airflow_keywords = ['airflow', 'dag', 'scheduler', 'webserver']
        install_keywords = ['install', 'deps', 'dependencies', 'pip', 'setup']
        clean_keywords = ['clean', 'remove', 'delete', 'teardown']
        env_keywords = ['env', 'environment', 'venv', 'virtual']
        info_keywords = ['info', 'show', 'debug', 'status', 'list']
        
        name_lower = name.lower()
        desc_lower = description.lower()
        text = f"{name_lower} {desc_lower}"
        
        if any(keyword in text for keyword in test_keywords):
            return "testing"
        elif any(keyword in text for keyword in quality_keywords):
            return "quality"
        elif any(keyword in text for keyword in database_keywords):
            return "database"
        elif any(keyword in text for keyword in airflow_keywords):
            return "airflow"
        elif any(keyword in text for keyword in install_keywords):
            return "install"
        elif any(keyword in text for keyword in clean_keywords):
            return "cleanup"
        elif any(keyword in text for keyword in env_keywords):
            return "env"
        elif any(keyword in text for keyword in info_keywords):
            return "info"
        else:
            return "general"
            
    def identify_consolidation_opportunities(self) -> None:
        """Identify commands that can be consolidated."""
        print("\n🔧 **FUNCTIONAL CONSOLIDATION OPPORTUNITIES**")
        print("="*50)
        
        # Group by similar functionality
        functional_groups = {}
        for cmd in self.commands.values():
            base_name = self._get_base_command_name(cmd.name)
            if base_name not in functional_groups:
                functional_groups[base_name] = []
            functional_groups[base_name].append(cmd)
            
        # Find consolidation opportunities
        for base_name, commands in functional_groups.items():
            if len(commands) > 1:
                # Check if commands are similar enough to consolidate
                if self._should_consolidate(commands):
                    self.optimization_results["consolidations"].append({
                        "base_name": base_name,
                        "commands": [cmd.name for cmd in commands],
                        "recommendation": self._generate_consolidation_recommendation(commands)
                    })
                    
    def _get_base_command_name(self, name: str) -> str:
        """Extract base command name (e.g., 'test-unit' -> 'test')."""
        return name.split('-')[0]
        
    def _should_consolidate(self, commands: List[CommandInfo]) -> bool:
        """Determine if commands should be consolidated."""
        # Simple heuristic: consolidate if >2 commands with similar descriptions
        if len(commands) < 2:
            return False
            
        # Check for similar implementation patterns
        implementations = [cmd.implementation for cmd in commands]
        similar_count = 0
        
        for i, impl1 in enumerate(implementations):
            for impl2 in implementations[i+1:]:
                if self._implementation_similarity(impl1, impl2) > 0.6:
                    similar_count += 1
                    
        return similar_count >= len(commands) // 2
        
    def _implementation_similarity(self, impl1: str, impl2: str) -> float:
        """Calculate similarity between implementations."""
        if not impl1 or not impl2:
            return 0.0
            
        # Simple word-based similarity
        words1 = set(impl1.lower().split())
        words2 = set(impl2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
        
    def _generate_consolidation_recommendation(self, commands: List[CommandInfo]) -> str:
        """Generate consolidation recommendation."""
        cmd_names = [cmd.name for cmd in commands]
        base_name = self._get_base_command_name(commands[0].name)
        
        return f"Consolidate {cmd_names} into flexible '{base_name}' command with options"
        
    def identify_redistribution_opportunities(self) -> None:
        """Identify commands that should be moved to different modules."""
        print("\n📁 **MODULE REDISTRIBUTION OPPORTUNITIES**")
        print("="*50)
        
        misplaced_commands = []
        
        for cmd in self.commands.values():
            expected_module = cmd.category
            current_module = cmd.module
            
            if expected_module != current_module and expected_module != "general":
                misplaced_commands.append({
                    "command": cmd.name,
                    "current_module": current_module,
                    "recommended_module": expected_module,
                    "reason": f"Command functionality aligns better with {expected_module} module"
                })
                
        self.optimization_results["redistributions"] = misplaced_commands
        
        for cmd in misplaced_commands:
            print(f"• Move '{cmd['command']}' from {cmd['current_module']} → {cmd['recommended_module']}")
            
    def standardize_documentation(self) -> None:
        """Standardize command descriptions."""
        print("\n📝 **DOCUMENTATION STANDARDIZATION**")
        print("="*50)
        
        # Define standardization patterns
        patterns = {
            "run": "Execute",
            "show": "Display",
            "start": "Start",
            "stop": "Stop",
            "restart": "Restart",
            "create": "Create",
            "delete": "Remove",
            "remove": "Remove",
            "clean": "Clean",
            "install": "Install",
            "update": "Update",
            "check": "Validate",
            "validate": "Validate",
            "test": "Run tests",
            "coverage": "Generate coverage",
            "profile": "Profile performance",
            "debug": "Debug and troubleshoot"
        }
        
        standardizations = []
        
        for cmd in self.commands.values():
            old_desc = cmd.description
            new_desc = self._standardize_description(old_desc, patterns)
            
            if old_desc != new_desc:
                standardizations.append({
                    "command": cmd.name,
                    "module": cmd.module,
                    "old_description": old_desc,
                    "new_description": new_desc
                })
                
        self.optimization_results["standardizations"] = standardizations
        
        if standardizations:
            print(f"📊 Found {len(standardizations)} descriptions to standardize")
            for std in standardizations[:5]:  # Show first 5 examples
                print(f"• {std['command']}: '{std['old_description']}' → '{std['new_description']}'")
        else:
            print("✅ All descriptions already follow standard patterns")
            
    def _standardize_description(self, description: str, patterns: Dict[str, str]) -> str:
        """Standardize a command description."""
        desc_lower = description.lower()
        
        for old_pattern, new_pattern in patterns.items():
            if desc_lower.startswith(old_pattern):
                # Replace the starting word
                rest = description[len(old_pattern):].strip()
                return f"{new_pattern} {rest}" if rest else new_pattern
                
        # Ensure proper capitalization
        if description and description[0].islower():
            return description[0].upper() + description[1:]
            
        return description
        
    def generate_optimization_report(self) -> None:
        """Generate comprehensive optimization report."""
        print("\n📊 **ADVANCED OPTIMIZATION REPORT**")
        print("="*50)
        
        # Module distribution analysis
        module_distribution = {}
        for cmd in self.commands.values():
            module_distribution[cmd.module] = module_distribution.get(cmd.module, 0) + 1
            
        print("\n### Current Module Distribution:")
        for module, count in sorted(module_distribution.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.commands)) * 100
            print(f"  {module:20}: {count:3} commands ({percentage:5.1f}%)")
            
        # Category analysis
        category_distribution = {}
        for cmd in self.commands.values():
            category_distribution[cmd.category] = category_distribution.get(cmd.category, 0) + 1
            
        print("\n### Command Categories:")
        for category, count in sorted(category_distribution.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.commands)) * 100
            print(f"  {category:20}: {count:3} commands ({percentage:5.1f}%)")
            
        # Optimization opportunities summary
        print("\n### Optimization Opportunities:")
        print(f"  Consolidations:     {len(self.optimization_results['consolidations']):3} opportunities")
        print(f"  Redistributions:    {len(self.optimization_results['redistributions']):3} commands")
        print(f"  Standardizations:   {len(self.optimization_results['standardizations']):3} descriptions")
        
    def generate_implementation_recommendations(self) -> None:
        """Generate specific implementation recommendations."""
        print("\n🎯 **IMPLEMENTATION RECOMMENDATIONS**")
        print("="*50)
        
        print("\n### Priority 1: High-Impact Optimizations")
        
        # Consolidation recommendations
        if self.optimization_results["consolidations"]:
            print("\n#### Command Consolidations:")
            for cons in self.optimization_results["consolidations"][:3]:  # Top 3
                print(f"• {cons['recommendation']}")
                print(f"  Commands: {', '.join(cons['commands'])}")
                
        # Module redistribution recommendations
        if self.optimization_results["redistributions"]:
            print("\n#### Module Redistributions:")
            for redis in self.optimization_results["redistributions"][:5]:  # Top 5
                print(f"• Move '{redis['command']}' to {redis['recommended_module']} module")
                
        print("\n### Priority 2: Quality Improvements")
        
        # Documentation standardization
        std_count = len(self.optimization_results["standardizations"])
        if std_count > 0:
            print(f"\n#### Documentation: {std_count} descriptions to standardize")
            print("  • Implement consistent verb patterns (Execute, Display, Validate, etc.)")
            print("  • Ensure proper capitalization")
            print("  • Add emojis for better visual organization")
            
        print("\n### Priority 3: Performance Optimizations")
        print("• Extract common PostgreSQL operation patterns")
        print("• Implement parallel execution for independent operations")
        print("• Add conditional execution based on file changes")
        print("• Optimize dependency checking with caching")
        
def main():
    """Main execution function."""
    print("🚀 **ADVANCED MAKEFILE OPTIMIZATION**")
    print("====================================")
    print("Implementing final recommendations from deduplication analysis")
    print()
    
    optimizer = AdvancedMakefileOptimizer()
    
    # Perform analysis
    optimizer.analyze_commands()
    
    # Identify optimization opportunities
    optimizer.identify_consolidation_opportunities()
    optimizer.identify_redistribution_opportunities()
    optimizer.standardize_documentation()
    
    # Generate reports
    optimizer.generate_optimization_report()
    optimizer.generate_implementation_recommendations()
    
    print("\n✅ **ADVANCED OPTIMIZATION ANALYSIS COMPLETE**")
    print("Run specific optimization phases to implement recommendations")

if __name__ == "__main__":
    main()
