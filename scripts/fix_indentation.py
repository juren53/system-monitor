#!/usr/bin/env python3

# Fix indentation issues in sysmon.py

import re

def fix_indentation():
    with open('src/sysmon.py', 'r') as f:
        content = f.read()
    
    # Fix the problematic show_users_guide method indentation
    # Replace the incorrectly placed method with nothing (temporarily)
    content = re.sub(
        r'\s*def show_users_guide\(self\):.*?',
        '',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    with open('src/sysmon.py', 'w') as f:
        f.write(content)

if __name__ == "__main__":
    fix_indentation()
    print("Removed problematic show_users_guide method")