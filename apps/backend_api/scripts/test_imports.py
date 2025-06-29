#!/usr/bin/env python3
"""
Import Test Script

This script tests that all imports work correctly before starting the application.
"""

import sys
import os
import traceback

# Add parent directory to Python path to find app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import(module_name, import_statement):
    """Test a specific import and report results."""
    try:
        exec(import_statement)
        print(f"✅ {module_name}: OK")
        return True
    except Exception as e:
        print(f"❌ {module_name}: FAILED - {e}")
        traceback.print_exc()
        return False

def main():
    """Test all critical imports."""
    print("🔍 Testing Python imports...")
    print("=" * 40)
    
    imports_to_test = [
        ("Database", "from db import engine, Base, SessionLocal"),
        ("Dependencies", "from dependencies import get_db, get_current_user"),
        ("Models", "import models"),
        ("Event Bus", "from event_bus import EventType, publish, subscribe"),
        ("Services - Progress", "from services import progress"),
        ("Services - Storytelling", "from services import storytelling"),
        ("Services - Notifications", "from services import notifications"),
        ("Services - Memory", "from services import memory"),
        ("Event Consumers", "import event_consumers"),
        ("Health Router", "from routers.health import router"),
        ("Main Application", "import main"),
    ]
    
    failed_imports = []
    
    for module_name, import_statement in imports_to_test:
        if not test_import(module_name, import_statement):
            failed_imports.append(module_name)
    
    print("\n" + "=" * 40)
    if failed_imports:
        print(f"❌ {len(failed_imports)} imports failed:")
        for module in failed_imports:
            print(f"   - {module}")
        print("\n🔧 Fix these imports before starting the application.")
        sys.exit(1)
    else:
        print("🎉 All imports successful!")
        print("✅ Application should start without import errors.")
        sys.exit(0)

if __name__ == "__main__":
    main()