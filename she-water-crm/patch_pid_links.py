"""
SHE Water CRM — Patch: Add PID click navigation to all screens
Clicking any PID opens the participant profile in React
Run from inside she-water-crm: python patch_pid_links.py
"""

import os, shutil
from datetime import datetime

def backup(f):
    os.makedirs('backups', exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(f, f'backups/{os.path.basename(f)}.{ts}.bak')

print()
print("=" * 55)
print("SHE Water CRM — PID Navigation Links")
print("=" * 55)
print()

# The JS helper function to add to each screen
# Opens React profile at localhost:3001/?pid=PID-XXXX
NAV_FUNCTION = """
  function openProfile(pid) {
    window.open('http://localhost:3001/?pid=' + pid, '_blank');
  }
"""

# Files to patch and what to add the function near
screens = [
    'public/bw.html',
    'public/tw.html',
    'public/wq.html',
    'public/ww.html',
    'public/activity.html',
]

for filepath in screens:
    if not os.path.exists(filepath):
        print(f"  ~ Skipping {filepath} — not found")
        continue

    backup(filepath)
    content = open(filepath, encoding='utf-8').read()

    # Add openProfile function if not already there
    if 'function openProfile' not in content:
        content = content.replace(
            '  function formatDate',
            NAV_FUNCTION + '  function formatDate'
        )
        if 'function openProfile' not in content:
            # Try alternate insertion point
            content = content.replace(
                '  const API = \'\';',
                '  const API = \'\';\n' + NAV_FUNCTION
            )

    # Make pid-cell tds clickable by adding onclick
    # Replace <td class="pid-cell">${p.pid}</td> with clickable version
    content = content.replace(
        '<td class="pid-cell">${p.pid}</td>',
        '<td class="pid-cell" style="cursor:pointer;text-decoration:underline;" onclick="openProfile(\'${p.pid}\')">${p.pid}</td>'
    )
    content = content.replace(
        "<td class=\"pid-cell\">${p.pid}</td>",
        '<td class="pid-cell" style="cursor:pointer;text-decoration:underline;" onclick="openProfile(\'${p.pid}\')">${p.pid}</td>'
    )
    # Also handle cases table PIDs
    content = content.replace(
        '<td class="pid-cell">${c.pid||\'—\'}</td>',
        '<td class="pid-cell" style="cursor:pointer;text-decoration:underline;" onclick="openProfile(\'${c.pid}\')">${c.pid||\'—\'}</td>'
    )

    open(filepath, 'w', encoding='utf-8').write(content)
    print(f"  ✓ {filepath}")

print()
print("Done. Restart server and refresh screens.")
print("Clicking any PID opens the React participant profile.")
print()
print("Commit:")
print('  git add .')
print('  git commit -m "PID navigation links across all screens"')
print('  git push')
