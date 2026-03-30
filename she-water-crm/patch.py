"""
SHE Water CRM — Code Patcher
Run this script from inside the she-water-crm folder to apply fixes.
Usage: python patch.py
"""

import os
import re
import shutil
from datetime import datetime

# ── CONFIG ───────────────────────────────────────────────────
SERVER_FILE = 'server.js'
BACKUP_DIR  = 'backups'

def backup(filepath):
    """Create a timestamped backup before patching"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f"{os.path.basename(filepath)}.{ts}.bak")
    shutil.copy2(filepath, backup_path)
    print(f"  ✓ Backup created: {backup_path}")
    return backup_path

def patch_file(filepath, patches):
    """Apply a list of (old, new) string patches to a file"""
    if not os.path.exists(filepath):
        print(f"  ✗ File not found: {filepath}")
        return False

    backup(filepath)
    content = open(filepath, 'r', encoding='utf-8').read()
    applied = 0

    for old, new, description in patches:
        if old in content:
            content = content.replace(old, new, 1)
            print(f"  ✓ Applied: {description}")
            applied += 1
        else:
            print(f"  ~ Already applied or not found: {description}")

    open(filepath, 'w', encoding='utf-8').write(content)
    return applied

# ── PATCHES ──────────────────────────────────────────────────

SERVER_PATCHES = [

    # FIX 1: PID generation — use MAX instead of alphabetical sort
    (
        """const pidResult = await client.query(
      `SELECT pid FROM person ORDER BY pid DESC LIMIT 1`
    );
    let nextNum = 1;
    if (pidResult.rows.length) {
      const num = parseInt(pidResult.rows[0].pid.replace('PID-',''));
      nextNum = num + 1;
    }""",

        """const pidResult = await client.query(
      `SELECT MAX(CAST(REPLACE(pid, 'PID-', '') AS INTEGER)) as maxnum FROM person`
    );
    let nextNum = 1;
    if (pidResult.rows.length && pidResult.rows[0].maxnum) {
      nextNum = parseInt(pidResult.rows[0].maxnum) + 1;
    }""",

        "PID generation — MAX instead of alphabetical sort"
    ),

    # FIX 2: Property insert — use explicit columns instead of DEFAULT VALUES
    (
        """const propResult = await client.query(`INSERT INTO property DEFAULT VALUES RETURNING property_id`);""",

        """const propResult = await client.query(`INSERT INTO property (active_flag) VALUES (TRUE) RETURNING property_id`);""",

        "Property insert — explicit columns for compatibility"
    ),

]

# ── RUN ──────────────────────────────────────────────────────

def main():
    print()
    print("=" * 50)
    print("SHE Water CRM — Code Patcher")
    print("=" * 50)
    print()

    # Check we're in the right folder
    if not os.path.exists(SERVER_FILE):
        print(f"ERROR: {SERVER_FILE} not found.")
        print("Make sure you run this script from inside the she-water-crm folder.")
        print("Example: cd she-water-crm && python patch.py")
        return

    print(f"Patching {SERVER_FILE}...")
    count = patch_file(SERVER_FILE, SERVER_PATCHES)
    print()

    if count is not False:
        print(f"Done. {count} patch(es) applied.")
        print()
        print("Next steps:")
        print("  1. Restart the server: npm start")
        print("  2. Test new participant intake")
        print("  3. Commit the changes:")
        print('     git add .')
        print('     git commit -m "apply patches — PID fix and property insert fix"')
        print('     git push')
    else:
        print("Patching failed. Check the error above.")

    print()

if __name__ == '__main__':
    main()