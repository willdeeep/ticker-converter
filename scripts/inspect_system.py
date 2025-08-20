#!/usr/bin/env python3
"""System inspection script for development diagnostics."""

import json
import os
import platform
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from ticker_converter.config.settings import get_settings
except ImportError:
    print("❌ Could not import settings - check your Python environment")
    sys.exit(1)


def inspect_system(detailed: bool = False) -> dict:
    """Inspect system components and return diagnostics."""
    diagnostics = {
        "timestamp": platform.node(),
        "detailed": detailed,
        "components": {}
    }
    
    print("🔍 Running system diagnostics...")
    
    # Check database configuration
    try:
        settings = get_settings()
        db_url = settings.database.get_url()
        if db_url:
            diagnostics["components"]["database"] = {
                "status": "✅ Configured",
                "details": "Database URL configured"
            }
        else:
            diagnostics["components"]["database"] = {
                "status": "❌ Missing", 
                "details": "Database URL not configured"
            }
    except Exception as e:
        diagnostics["components"]["database"] = {
            "status": "❌ Error",
            "details": f"Configuration error: {str(e)}"
        }
    
    # Check API configuration  
    try:
        api_key = getattr(settings, 'api_key', None)
        if api_key:
            diagnostics["components"]["api"] = {
                "status": "✅ Configured",
                "details": "API key configured"
            }
        else:
            diagnostics["components"]["api"] = {
                "status": "⚠️  Missing",
                "details": "API key not configured (may use dummy data)"
            }
    except Exception as e:
        diagnostics["components"]["api"] = {
            "status": "❌ Error", 
            "details": f"API configuration error: {str(e)}"
        }
    
    # Environment information
    env = os.getenv("ENVIRONMENT", "development")
    diagnostics["components"]["environment"] = {
        "status": "✅ Development" if env == "development" else "🚀 Production",
        "details": f"Environment: {env}"
    }
    
    if detailed:
        # Add detailed system information
        diagnostics["system_info"] = {
            "platform": f"{platform.system()} {platform.release()}",
            "python": platform.python_version(),
            "node": platform.node()
        }
    
    return diagnostics


def main():
    """Main inspection function.""" 
    detailed = "--detailed" in sys.argv
    
    try:
        diagnostics = inspect_system(detailed)
        
        # Print results
        print("\n📋 System Component Status:")
        print("=" * 50)
        
        for component, info in diagnostics["components"].items():
            print(f"{component.title():.<20} {info['status']}")
            if detailed:
                print(f"  └─ {info['details']}")
        
        if detailed and "system_info" in diagnostics:
            print("\n🖥️  System Information:")
            print("=" * 50)
            for key, value in diagnostics["system_info"].items():
                print(f"{key.title():.<20} {value}")
        
        print("\n✅ System diagnostics completed")
        print("💡 Use 'make help' for available operations")
        
        # Write JSON output if requested
        if "--json" in sys.argv:
            output_file = "system_diagnostics.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(diagnostics, f, indent=2)
            print(f"📄 JSON output written to {output_file}")
            
    except Exception as error:
        print(f"❌ Diagnostic error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
