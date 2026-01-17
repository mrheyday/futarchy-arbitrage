#!/usr/bin/env python3
"""
Migrate print() statements to logging in bot files
"""

import re
import sys
from pathlib import Path

# Files to migrate
TARGET_FILES = [
    "src/arbitrage_commands/eip7702_bot.py",
    "src/arbitrage_commands/simple_bot.py",
    "src/arbitrage_commands/complex_bot.py",
    "src/arbitrage_commands/arbitrage_bot_v2.py",
    "src/arbitrage_commands/buy_cond.py",
]

# Replacement patterns
REPLACEMENTS = [
    # Error messages
    (r'print\("❌', 'logger.error("'),
    (r'print\(f"❌', 'logger.error(f"'),
    
    # Warnings
    (r'print\("⚠️', 'logger.warning("'),
    (r'print\(f"⚠️', 'logger.warning(f"'),
    (r'print\("Warning:', 'logger.warning("'),
    (r'print\(f"Warning:', 'logger.warning(f"'),
    
    # Success messages
    (r'print\("✅', 'logger.info("'),
    (r'print\(f"✅', 'logger.info(f"'),
    
    # Opportunity/Action messages
    (r'print\("🎯', 'logger.info("'),
    (r'print\(f"🎯', 'logger.info(f"'),
    (r'print\(f"Executing', 'logger.info(f"Executing'),
    
    # General info
    (r'print\(f"Starting', 'logger.info(f"Starting'),
    (r'print\(f"Account:', 'logger.info(f"Account:'),
    (r'print\(f"Amount:', 'logger.info(f"Amount:'),
    (r'print\(f"Interval:', 'logger.info(f"Interval:'),
    (r'print\(f"Tolerance:', 'logger.info(f"Tolerance:'),
    (r'print\(f"Mode:', 'logger.info(f"Mode:'),
    (r'print\(f"--- Iteration', 'logger.debug(f"--- Iteration'),
    
    # Price info
    (r'print\(f"YES  pool:', 'logger.debug(f"YES  pool:'),
    (r'print\(f"PRED pool:', 'logger.debug(f"PRED pool:'),
    (r'print\(f"NO   pool:', 'logger.debug(f"NO   pool:'),
    (r'print\(f"BAL  pool:', 'logger.debug(f"BAL  pool:'),
    (r'print\(f"Ideal price:', 'logger.debug(f"Ideal price:'),
    (r'print\(f"Balancer:', 'logger.debug(f"Balancer:'),
    (r'print\(f"Expected profit:', 'logger.debug(f"Expected profit:'),
    
    # Results
    (r'print\(f"  TX:', 'logger.info(f"  TX:'),
    (r'print\(f"  Gas used:', 'logger.info(f"  Gas used:'),
    (r'print\(f"  Final', 'logger.info(f"  Final'),
    (r'print\(f"  - ', 'logger.info(f"  - '),
    
    # Notes
    (r'print\(f"Note:', 'logger.info(f"Note:'),
    (r'print\("Note:', 'logger.info("Note:'),
    
    # Empty prints -> debug separator
    (r'print\(\)', 'logger.debug("")'),
]

def migrate_file(filepath: Path):
    """Migrate a single file"""
    print(f"\nMigrating {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    changes = 0
    
    # Apply replacements
    for pattern, replacement in REPLACEMENTS:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            count = len(re.findall(pattern, content))
            changes += count
            print(f"  ✓ Replaced {count}x: {pattern[:40]}...")
        content = new_content
    
    # Check if logger import exists
    if "from src.config.logging_config import" not in content:
        # Add after other imports
        import_pos = content.find("# Import")
        if import_pos == -1:
            import_pos = content.find("import ")
        
        if import_pos != -1:
            # Find end of imports section
            lines = content[:import_pos].split('\n')
            insert_line = len(lines)
            
            lines_all = content.split('\n')
            # Insert logging import
            lines_all.insert(insert_line, "")
            lines_all.insert(insert_line + 1, "# Import logging")
            lines_all.insert(insert_line + 2, "from src.config.logging_config import setup_logger, log_trade, log_price_check")
            lines_all.insert(insert_line + 3, "")
            lines_all.insert(insert_line + 4, "# Initialize logger")
            lines_all.insert(insert_line + 5, f"logger = setup_logger(\"{filepath.stem}\", level=10)  # DEBUG level")
            
            content = '\n'.join(lines_all)
            print(f"  ✓ Added logger import and initialization")
            changes += 1
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  ✅ Migrated {changes} changes")
        return changes
    else:
        print(f"  ℹ️  No changes needed")
        return 0

def main():
    root = Path(__file__).parent.parent
    total_changes = 0
    
    print("="*60)
    print("LOGGING MIGRATION TOOL")
    print("="*60)
    
    for file_path in TARGET_FILES:
        full_path = root / file_path
        if full_path.exists():
            changes = migrate_file(full_path)
            total_changes += changes
        else:
            print(f"\n⚠️  File not found: {file_path}")
    
    print("\n" + "="*60)
    print(f"COMPLETE: {total_changes} total changes across {len(TARGET_FILES)} files")
    print("="*60)

if __name__ == "__main__":
    main()
