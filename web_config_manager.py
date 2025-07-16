#!/usr/bin/env python3

import re
import argparse
from pathlib import Path
from typing import Tuple


def comment_http_errors(content: str) -> Tuple[str, bool]:
    """Comment out the httpErrors element in Web.config content."""
    pattern = r'(\s*)(<httpErrors[^>]*>.*?</httpErrors>)'
    
    def replace_func(match):
        indent = match.group(1)
        element = match.group(2)
        return f'{indent}<!-- {element} -->'
    
    new_content, count = re.subn(pattern, replace_func, content, flags=re.DOTALL | re.IGNORECASE)
    return new_content, count > 0


def uncomment_http_errors(content: str) -> Tuple[str, bool]:
    """Uncomment the httpErrors element in Web.config content."""
    pattern = r'(\s*)<!--\s*(<httpErrors[^>]*>.*?</httpErrors>)\s*-->'
    
    def replace_func(match):
        indent = match.group(1)
        element = match.group(2)
        return f'{indent}{element}'
    
    new_content, count = re.subn(pattern, replace_func, content, flags=re.DOTALL | re.IGNORECASE)
    return new_content, count > 0


def process_web_config(file_path: Path, action: str) -> None:
    """Process the Web.config file to comment or uncomment httpErrors element."""
    if not file_path.exists():
        print(f"Error: File '{file_path}' not found.")
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    if action == 'comment':
        new_content, changed = comment_http_errors(content)
        action_desc = "commented out"
    else:
        new_content, changed = uncomment_http_errors(content)
        action_desc = "uncommented"
    
    if not changed:
        element_status = "commented" if action == "uncomment" else "uncommented"
        print(f"No httpErrors element found to {action} (already {element_status}?).")
        return
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Successfully {action_desc} httpErrors element in '{file_path}'.")
    except Exception as e:
        print(f"Error writing file: {e}")


def main():
    parser = argparse.ArgumentParser(description='Comment or uncomment httpErrors element in Web.config files')
    parser.add_argument('file', help='Path to Web.config file')
    
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--comment', action='store_true', 
                             help='Comment out the httpErrors element')
    action_group.add_argument('--uncomment', action='store_true', 
                             help='Uncomment the httpErrors element')
    
    args = parser.parse_args()
    
    file_path = Path(args.file)
    action = 'comment' if args.comment else 'uncomment'
    
    process_web_config(file_path, action)


if __name__ == '__main__':
    main()