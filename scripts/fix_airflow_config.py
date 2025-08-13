#!/usr/bin/env python3
"""
Script to fix Airflow 3.0.4 configuration deprecation warnings.
Moves deprecated [webserver] settings to [api] section.
"""

import shutil
from pathlib import Path

# Airflow configuration file path
AIRFLOW_HOME = Path.home() / "airflow"
CONFIG_FILE = AIRFLOW_HOME / "airflow.cfg"
BACKUP_FILE = AIRFLOW_HOME / "airflow.cfg.backup"

def fix_airflow_config():
    """Fix Airflow configuration by moving deprecated settings."""
    
    if not CONFIG_FILE.exists():
        print(f"❌ Airflow config file not found: {CONFIG_FILE}")
        return False
    
    # Create backup
    shutil.copy2(CONFIG_FILE, BACKUP_FILE)
    print(f"✅ Backup created: {BACKUP_FILE}")
    
    # Read current config
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Settings to move from [webserver] to [api]
    webserver_to_api_mappings = {
        'web_server_port': 'port',
        'workers': 'workers', 
        'web_server_host': 'host',
        'access_logfile': 'access_logfile',
        'web_server_ssl_cert': 'ssl_cert',
        'web_server_ssl_key': 'ssl_key',
        'enable_swagger_ui': 'enable_swagger_ui'
    }
    
    new_lines = []
    in_webserver_section = False
    in_api_section = False
    api_additions = []
    
    for line in lines:
        stripped = line.strip()
        
        # Track which section we're in
        if stripped.startswith('[webserver]'):
            in_webserver_section = True
            in_api_section = False
            new_lines.append(line)
            continue
        elif stripped.startswith('[api]'):
            in_webserver_section = False
            in_api_section = True
            new_lines.append(line)
            continue
        elif stripped.startswith('[') and stripped.endswith(']'):
            # Entering a new section
            if in_api_section and api_additions:
                # Add moved settings to api section
                new_lines.extend(api_additions)
                api_additions = []
            in_webserver_section = False
            in_api_section = False
            new_lines.append(line)
            continue
        
        # Check if this line should be moved from webserver to api
        if in_webserver_section:
            setting_found = False
            for old_setting, new_setting in webserver_to_api_mappings.items():
                if stripped.startswith(f"{old_setting} ="):
                    # Comment out in webserver section
                    new_lines.append(f"# MOVED TO [api] SECTION: {line}")
                    # Add to api section
                    api_value = stripped.split('=', 1)[1].strip()
                    api_additions.append(f"{new_setting} = {api_value}\n")
                    setting_found = True
                    break
            
            if not setting_found:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # If we ended in api section, add any pending additions
    if api_additions:
        new_lines.extend(api_additions)
    
    # Write updated config
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ Airflow configuration updated successfully!")
    print("\n📝 Changes made:")
    for old, new in webserver_to_api_mappings.items():
        print(f"   • Moved {old} from [webserver] to {new} in [api]")
    
    print(f"\n🔄 To restore original config: cp {BACKUP_FILE} {CONFIG_FILE}")
    return True

if __name__ == "__main__":
    print("🔧 Fixing Airflow 3.0.4 configuration...")
    success = fix_airflow_config()
    if success:
        print("\n✅ Configuration fix completed!")
        print("\n🚀 You can now run 'make airflow' without deprecation warnings.")
    else:
        print("\n❌ Configuration fix failed!")
