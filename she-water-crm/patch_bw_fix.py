"""
SHE Water CRM — Safe Patch: Fix BW participants query
Uses exact string match instead of regex
Run from inside the she-water-crm folder: python patch_bw_safe.py
"""

import os, shutil
from datetime import datetime

def backup(filepath):
    os.makedirs('backups', exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = f"backups/{os.path.basename(filepath)}.{ts}.bak"
    shutil.copy2(filepath, dest)
    print(f"  ✓ Backup: {dest}")

print()
print("=" * 55)
print("SHE Water CRM — Safe BW Participants Fix")
print("=" * 55)
print()

if not os.path.exists('server.js'):
    print("ERROR: Run from inside the she-water-crm folder.")
    exit()

backup('server.js')
content = open('server.js', encoding='utf-8').read()

# Find the exact block to replace
OLD = """      LEFT JOIN delivery d2 ON d2.enrollment_id = pe.enrollment_id
      LEFT JOIN vendor v ON v.vendor_id = d2.vendor_id
      WHERE pr.program_code = 'BW' AND pe.exit_date IS NULL
      GROUP BY p.pid, p.first_name, p.last_name, pe.program_specific_id,
               pe.enrollment_id, es.status_name, ps.household_size,
               a.apn_number, c.county_name, s.structure_type, s.unit_number,
               v.vendor_id, v.vendor_name
      ORDER BY p.last_name, p.first_name"""

NEW = """      WHERE pr.program_code = 'BW' AND pe.exit_date IS NULL
      ORDER BY p.last_name, p.first_name"""

if OLD in content:
    content = content.replace(OLD, NEW)
    # Now also remove the vendor subquery select lines
    OLD2 = """        (SELECT d.scheduled_date FROM delivery d
         WHERE d.enrollment_id = pe.enrollment_id
         ORDER BY d.scheduled_date DESC LIMIT 1) AS last_delivery,
        (SELECT d.delivery_status FROM delivery d
         WHERE d.enrollment_id = pe.enrollment_id
         ORDER BY d.scheduled_date DESC LIMIT 1) AS last_status,
        (SELECT d.scheduled_date FROM delivery d
         WHERE d.enrollment_id = pe.enrollment_id
         AND d.scheduled_date >= CURRENT_DATE
         ORDER BY d.scheduled_date ASC LIMIT 1) AS next_delivery"""
    # Check if subqueries already exist
    if 'last_delivery' not in content:
        # Add subqueries to the SELECT — find the right place
        OLD3 = """        s.structure_type, s.unit_number
      FROM program_enrollment pe"""
        NEW3 = """        s.structure_type, s.unit_number,
        (SELECT v.vendor_name FROM delivery d
         JOIN vendor v ON v.vendor_id = d.vendor_id
         WHERE d.enrollment_id = pe.enrollment_id
         ORDER BY d.scheduled_date DESC LIMIT 1) AS vendor_name,
        (SELECT d.scheduled_date FROM delivery d
         WHERE d.enrollment_id = pe.enrollment_id
         ORDER BY d.scheduled_date DESC LIMIT 1) AS last_delivery,
        (SELECT d.delivery_status FROM delivery d
         WHERE d.enrollment_id = pe.enrollment_id
         ORDER BY d.scheduled_date DESC LIMIT 1) AS last_status,
        (SELECT d.scheduled_date FROM delivery d
         WHERE d.enrollment_id = pe.enrollment_id
         AND d.scheduled_date >= CURRENT_DATE
         ORDER BY d.scheduled_date ASC LIMIT 1) AS next_delivery
      FROM program_enrollment pe"""
        if OLD3 in content:
            content = content.replace(OLD3, NEW3)
            print("  ✓ Added delivery subqueries to SELECT")
    open('server.js', 'w', encoding='utf-8').write(content)
    print("  ✓ Removed broken GROUP BY — BW participants fixed")
    print()
    print("Done. Restart: npx kill-port 3000 && npm start")
    print()
    print("Commit:")
    print('  git add .')
    print('  git commit -m "fix BW participants GROUP BY error"')
    print('  git push')
else:
    print("  ~ Pattern not found in server.js")
    print()
    print("The BW participants endpoint may have already been modified.")
    print("Open server.js in VS Code and search for:")
    print("  GET /api/bw/participants")
    print("Find the GROUP BY block and remove the vendor join lines")
    print("leaving only: WHERE pr.program_code = 'BW' AND pe.exit_date IS NULL")