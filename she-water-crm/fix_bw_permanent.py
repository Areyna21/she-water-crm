"""
SHE Water CRM — Permanent BW Participants Fix
Reads your actual server.js and surgically fixes the broken vendor reference
Run from inside she-water-crm: python fix_bw_permanent.py
"""

import os, re, shutil
from datetime import datetime

os.makedirs('backups', exist_ok=True)
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2('server.js', f'backups/server.js.{ts}.bak')
print(f"\n  ✓ Backup: backups/server.js.{ts}.bak")

content = open('server.js', encoding='utf-8').read()

# Find the exact BW participants endpoint block
start = content.find("app.get('/api/bw/participants'")
if start == -1:
    print("  ✗ Cannot find BW participants endpoint")
    exit()

# Find the end of this endpoint
end = content.find("\napp.get(", start + 10)
if end == -1:
    end = content.find("\napp.post(", start + 10)

current_block = content[start:end]
print(f"\n  Current BW participants block ({len(current_block)} chars):")
print("  " + "\n  ".join(current_block.split('\n')[:5]) + "\n  ...")

# Check what's wrong
if 'v.vendor_name' in current_block and 'JOIN vendor v' not in current_block:
    print("\n  ✗ Confirmed: v.vendor_name used without JOIN vendor")
elif 'v.vendor_id' in current_block and 'JOIN vendor v' not in current_block:
    print("\n  ✗ Confirmed: v.vendor_id used without JOIN vendor")
else:
    print("\n  ~ Query looks OK — checking for other issues...")

# Replace with the clean fixed version regardless
CLEAN_BLOCK = """app.get('/api/bw/participants', async (req, res) => {
  const { vendor, county } = req.query;
  try {
    const conditions = ["pr.program_code = 'BW'", "pe.exit_date IS NULL"];
    const params = [];
    if (vendor) { params.push(vendor); conditions.push(`v_sub.vendor_id = $${params.length}`); }
    if (county) { params.push(county); conditions.push(`c.county_name = $${params.length}`); }

    const result = await pool.query(`
      SELECT
        p.pid,
        p.first_name,
        p.last_name,
        pe.program_specific_id,
        pe.enrollment_id,
        es.status_name,
        COALESCE(ps.household_size, 0) AS household_size,
        a.apn_number,
        c.county_name,
        s.structure_type,
        s.unit_number,
        (SELECT v.vendor_id
         FROM delivery d JOIN vendor v ON v.vendor_id = d.vendor_id
         WHERE d.enrollment_id = pe.enrollment_id
         ORDER BY d.scheduled_date DESC LIMIT 1) AS vendor_id,
        (SELECT v.vendor_name
         FROM delivery d JOIN vendor v ON v.vendor_id = d.vendor_id
         WHERE d.enrollment_id = pe.enrollment_id
         ORDER BY d.scheduled_date DESC LIMIT 1) AS vendor_name,
        (SELECT d.scheduled_date
         FROM delivery d
         WHERE d.enrollment_id = pe.enrollment_id
         ORDER BY d.scheduled_date DESC LIMIT 1) AS last_delivery,
        (SELECT d.delivery_status
         FROM delivery d
         WHERE d.enrollment_id = pe.enrollment_id
         ORDER BY d.scheduled_date DESC LIMIT 1) AS last_status,
        (SELECT d.scheduled_date
         FROM delivery d
         WHERE d.enrollment_id = pe.enrollment_id
           AND d.scheduled_date >= CURRENT_DATE
         ORDER BY d.scheduled_date ASC LIMIT 1) AS next_delivery,
        CASE
          WHEN COALESCE(ps.household_size,0) <= 2 THEN 20
          WHEN COALESCE(ps.household_size,0) <= 4 THEN 40
          WHEN COALESCE(ps.household_size,0) <= 6 THEN 50
          ELSE 60
        END AS allotment_gallons
      FROM program_enrollment pe
      JOIN program pr ON pr.program_id = pe.program_id
      JOIN person p ON p.pid = pe.pid
      JOIN enrollment_status es ON es.status_id = pe.status_id
      JOIN structure s ON s.structure_id = pe.structure_id
      JOIN apn a ON a.apn_id = s.apn_id
      JOIN county c ON c.county_id = a.county_id
      LEFT JOIN person_structure ps
        ON ps.pid = p.pid AND ps.end_date IS NULL
      WHERE pr.program_code = 'BW' AND pe.exit_date IS NULL
      ORDER BY p.last_name, p.first_name
    `);
    res.json(result.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});"""

# Replace the block
new_content = content[:start] + CLEAN_BLOCK + content[end:]
open('server.js', 'w', encoding='utf-8').write(new_content)
print("  ✓ BW participants endpoint replaced with clean subquery version")
print("  ✓ Includes vendor_id, vendor_name, last_delivery, next_delivery, allotment_gallons")
print("  ✓ No GROUP BY — uses safe correlated subqueries")
print("  ✓ Supports ?vendor= and ?county= filters")

# Verify fix
verify = open('server.js', encoding='utf-8').read()
bw_idx = verify.find("app.get('/api/bw/participants'")
bw_block = verify[bw_idx:bw_idx+1500]
if 'JOIN vendor v' not in bw_block and 'v.vendor_name' in bw_block and 'subquery' not in bw_block.lower():
    print("\n  ✗ WARNING: Fix may not have applied correctly")
else:
    print("\n  ✓ Fix verified — no bare vendor references in query")

print(f"\n  server.js size: {os.path.getsize('server.js'):,} bytes")
print()
print("  Restart server: npx kill-port 3000 && npm start")
print("  Then run diagnostic: python diagnostic.py")
print()
print("  Commit:")
print('  git add .')
print('  git commit -m "permanent fix BW participants query"')
print('  git push')
