#!/usr/bin/env python3
"""
Documentation Standardization Script
===================================

Implements consistent command description patterns across all Makefile modules.
Applies standardization rules identified in the advanced optimization analysis.
"""

import re
import pathlib
from typing import Dict, List, Tuple

class DocumentationStandardizer:
    def __init__(self, make_dir: str = "make"):
        self.make_dir = pathlib.Path(make_dir)
        self.main_makefile = pathlib.Path("Makefile")
        
        # Standardization patterns
        self.patterns = {
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
            "test": "Execute tests",
            "coverage": "Generate coverage",
            "profile": "Profile performance",
            "debug": "Debug and troubleshoot",
            "open": "Open and display",
            "list": "List and display",
            "info": "Display information",
            "status": "Display status"
        }
        
        # Category emojis for better visual organization
        self.category_emojis = {
            "testing": "🧪",
            "quality": "✅", 
            "database": "🗄️",
            "airflow": "🌊",
            "install": "📦",
            "cleanup": "🧹",
            "env": "🔧",
            "info": "ℹ️",
            "general": "⚙️"
        }
        
    def standardize_all_files(self) -> None:
        """Standardize documentation in all Makefile modules."""
        print("📝 **DOCUMENTATION STANDARDIZATION**")
        print("="*50)
        
        total_changes = 0
        
        # Process all module files
        for makefile_path in self.make_dir.glob("Makefile.*"):
            changes = self._standardize_file(makefile_path)
            total_changes += changes
            
        # Process main Makefile
        if self.main_makefile.exists():
            changes = self._standardize_file(self.main_makefile)
            total_changes += changes
            
        print(f"\n✅ Documentation standardization complete!")
        print(f"📊 Total descriptions updated: {total_changes}")
        
    def _standardize_file(self, file_path: pathlib.Path) -> int:
        """Standardize documentation in a single file."""
        try:
            content = file_path.read_text()
            changes_count = 0
            
            # Find all command descriptions
            pattern = r'^([a-zA-Z][a-zA-Z0-9_-]*):.*?##\s*(.+?)$'
            matches = list(re.finditer(pattern, content, re.MULTILINE))
            
            # Process matches in reverse order to avoid offset issues
            for match in reversed(matches):
                command_name = match.group(1)
                old_description = match.group(2).strip()
                
                # Skip internal commands and already standardized ones
                if command_name.startswith('_') or self._is_already_standardized(old_description):
                    continue
                    
                new_description = self._standardize_description(old_description, command_name)
                
                if old_description != new_description:
                    # Replace the description in the content
                    start, end = match.span(2)
                    content = content[:start] + new_description + content[end:]
                    changes_count += 1
                    print(f"  {file_path.name}: '{command_name}' description updated")
                    
            # Write back if changes were made
            if changes_count > 0:
                file_path.write_text(content)
                print(f"✅ {file_path.name}: {changes_count} descriptions standardized")
            
            return changes_count
            
        except Exception as e:
            print(f"⚠️ Error processing {file_path}: {e}")
            return 0
            
    def _is_already_standardized(self, description: str) -> bool:
        """Check if description is already standardized."""
        # Check for emojis (indicates already standardized)
        if any(emoji in description for emoji in self.category_emojis.values()):
            return True
            
        # Check for deprecation warnings
        if "DEPRECATED" in description or "⚠️" in description:
            return True
            
        # Check for internal commands
        if description.startswith("Internal:"):
            return True
            
        return False
        
    def _standardize_description(self, description: str, command_name: str) -> str:
        """Standardize a single command description."""
        desc = description.strip()
        
        # Apply verb standardization
        desc_lower = desc.lower()
        for old_pattern, new_pattern in self.patterns.items():
            if desc_lower.startswith(old_pattern):
                rest = desc[len(old_pattern):].strip()
                desc = f"{new_pattern} {rest}" if rest else new_pattern
                break
                
        # Ensure proper capitalization
        if desc and desc[0].islower():
            desc = desc[0].upper() + desc[1:]
            
        # Add category emoji based on command name
        emoji = self._get_command_emoji(command_name)
        if emoji and not any(category_emoji in desc for category_emoji in self.category_emojis.values()):
            desc = f"{emoji} {desc}"
            
        return desc
        
    def _get_command_emoji(self, command_name: str) -> str:
        """Get appropriate emoji for command based on its name."""
        name_lower = command_name.lower()
        
        # Test-related commands
        if any(keyword in name_lower for keyword in ["test", "coverage", "benchmark", "pytest"]):
            return self.category_emojis["testing"]
            
        # Quality-related commands  
        elif any(keyword in name_lower for keyword in ["lint", "format", "black", "pylint", "mypy", "quality", "ruff", "isort"]):
            return self.category_emojis["quality"]
            
        # Database-related commands
        elif any(keyword in name_lower for keyword in ["db", "database", "postgres", "sql"]):
            return self.category_emojis["database"]
            
        # Airflow-related commands
        elif any(keyword in name_lower for keyword in ["airflow", "dag", "scheduler", "webserver"]):
            return self.category_emojis["airflow"]
            
        # Installation-related commands
        elif any(keyword in name_lower for keyword in ["install", "deps", "dependencies", "pip", "setup"]):
            return self.category_emojis["install"]
            
        # Cleanup-related commands
        elif any(keyword in name_lower for keyword in ["clean", "remove", "delete", "teardown"]):
            return self.category_emojis["cleanup"]
            
        # Environment-related commands
        elif any(keyword in name_lower for keyword in ["env", "environment", "venv", "virtual"]):
            return self.category_emojis["env"]
            
        # Info/help commands
        elif any(keyword in name_lower for keyword in ["info", "help", "show", "debug", "status", "list"]):
            return self.category_emojis["info"]
            
        # General commands
        else:
            return self.category_emojis["general"]
            
    def generate_standardization_report(self) -> None:
        """Generate a report of all standardization changes."""
        print("\n📊 **STANDARDIZATION PATTERNS APPLIED**")
        print("="*50)
        
        print("\n### Verb Standardization Patterns:")
        for old, new in self.patterns.items():
            print(f"  '{old}' → '{new}'")
            
        print("\n### Category Emojis Applied:")
        for category, emoji in self.category_emojis.items():
            print(f"  {emoji} {category}")
            
        print("\n### Quality Guidelines:")
        print("  • All descriptions start with standardized verbs")
        print("  • Proper capitalization enforced")
        print("  • Category emojis added for visual organization")
        print("  • Consistent formatting across all modules")

def main():
    """Main execution function."""
    print("🚀 **MAKEFILE DOCUMENTATION STANDARDIZATION**")
    print("============================================")
    
    standardizer = DocumentationStandardizer()
    standardizer.standardize_all_files()
    standardizer.generate_standardization_report()
    
    print("\n✅ **DOCUMENTATION STANDARDIZATION COMPLETE**")

if __name__ == "__main__":
    main()
