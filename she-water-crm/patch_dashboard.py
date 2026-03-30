"""
SHE Water CRM — Patch: Add program screen nav buttons to dashboard
Run from inside the she-water-crm folder: python patch_dashboard.py
"""

import os
import shutil
from datetime import datetime

def backup(filepath):
    os.makedirs('backups', exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join('backups', f"{os.path.basename(filepath)}.{ts}.bak")
    shutil.copy2(filepath, dest)
    print(f"  ✓ Backup: {dest}")

# ── PATCH 1: Add program buttons to dashboard ─────────────────
INDEX_FILE = os.path.join('public', 'index.html')

OLD_BTN = '<button class="btn btn-primary" onclick="showPage(\'search\')">View All Participants →</button>'

NEW_BTNS = '''<button class="btn btn-primary" onclick="showPage('search')">View All Participants →</button>
  <div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;">
    <button class="btn btn-primary" style="background:var(--bw);" onclick="window.location.href='/bw.html'">💧 Bottled Water →</button>
    <button class="btn btn-primary" style="background:var(--tw);" onclick="window.location.href='/tw.html'">🛢 Tank Water →</button>
    <button class="btn btn-primary" style="background:var(--wq);color:#000;" onclick="window.location.href='/wq.html'">🧪 Water Quality →</button>
    <button class="btn btn-primary" style="background:var(--ww);" onclick="window.location.href='/ww.html'">⛏ Water Well →</button>
  </div>'''

# ── RUN ──────────────────────────────────────────────────────
print()
print("=" * 50)
print("SHE Water CRM — Patch: Program Nav Buttons")
print("=" * 50)
print()

if not os.path.exists(INDEX_FILE):
    print(f"ERROR: {INDEX_FILE} not found.")
    print("Run this from inside the she-water-crm folder.")
    exit()

backup(INDEX_FILE)
content = open(INDEX_FILE, 'r', encoding='utf-8').read()

if OLD_BTN in content:
    content = content.replace(OLD_BTN, NEW_BTNS)
    open(INDEX_FILE, 'w', encoding='utf-8').write(content)
    print("  ✓ Added program nav buttons to dashboard")
else:
    print("  ~ Buttons may already be added or button text changed")
    print("    Check public/index.html manually if buttons don't appear")

print()
print("Done. Restart the server: npm start")
print()
print("Then commit:")
print('  git add .')
print('  git commit -m "add program nav buttons to dashboard"')
print('  git push')
print()
