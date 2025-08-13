#!/usr/bin/env python3
"""
Script to fix all imports in the models directory.
Changes absolute imports to relative imports.
"""

import os
import re

def fix_imports_in_file(filepath):
    """Fix imports in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace absolute imports with relative imports
    patterns = [
        (r'from apps\.backend_api\.models\.base import', 'from .base import'),
        (r'from apps\.backend_api\.models\.user import', 'from .user import'),
        (r'from apps\.backend_api\.models\.goals import', 'from .goals import'),
        (r'from apps\.backend_api\.models\.projects import', 'from .projects import'),
        (r'from apps\.backend_api\.models\.tasks import', 'from .tasks import'),
        (r'from apps\.backend_api\.models\.life_areas import', 'from .life_areas import'),
        (r'from apps\.backend_api\.models\.media import', 'from .media import'),
        (r'from apps\.backend_api\.models\.memory import', 'from .memory import'),
        (r'from apps\.backend_api\.models\.preferences import', 'from .preferences import'),
        (r'from apps\.backend_api\.models\.feedback import', 'from .feedback import'),
        (r'from apps\.backend_api\.models\.story import', 'from .story import'),
        (r'from apps\.backend_api\.models\.conversation import', 'from .conversation import'),
        (r'from apps\.backend_api\.models\.assistant import', 'from .assistant import'),
        (r'from apps\.backend_api\.models\.entities import', 'from .entities import'),
    ]
    
    changed = False
    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changed = True
    
    if changed:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Fixed imports in {filepath}")
        return True
    return False

def main():
    models_dir = 'models'
    fixed_count = 0
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            if fix_imports_in_file(filepath):
                fixed_count += 1
    
    print(f"\n📊 Fixed imports in {fixed_count} files")

if __name__ == '__main__':
    main()
