"""
Fix vendor columns in BW participants query
Run from inside she-water-crm: python patch_bw_vendor.py
"""
import os, shutil
from datetime import datetime

os.makedirs('backups', exist_ok=True)
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2('server.js', f'backups/server.js.{ts}.bak')

content = open('server.js', encoding='utf-8').read()

OLD = """        p.pid, p.first_name, p.last_name,
        pe.program_specific_id, pe.enrollment_id,
        es.status_name, ps.household_size,
        a.apn_number, c.county_name,
        s.structure_type, s.unit_number,
        v.vendor_id, v.vendor_name,
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
      FROM program_enrollment pe
      JOIN program pr ON pr.program_id = pe.program_id
      JOIN person p ON p.pid = pe.pid
      JOIN enrollment_status es ON es.status_id = pe.status_id
      JOIN structure s ON s.structure_id = pe.structure_id
      JOIN apn a ON a.apn_id = s.apn_id
      JOIN county c ON c.county_id = a.county_id
      WHERE pr.program_code = 'BW' AND pe.exit_date IS NULL"""

NEW = """        p.pid, p.first_name, p.last_name,
        pe.program_specific_id, pe.enrollment_id,
        es.status_name, ps.household_size,
        a.apn_number, c.county_name,
        s.structure_type, s.unit_number,
        (SELECT v.vendor_id FROM delivery d
         JOIN vendor v ON v.vendor_id = d.vendor_id
         WHERE d.enrollment_id = pe.enrollment_id
         ORDER BY d.scheduled_date DESC LIMIT 1) AS vendor_id,
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
      FROM program_enrollment pe
      JOIN program pr ON pr.program_id = pe.program_id
      JOIN person p ON p.pid = pe.pid
      JOIN enrollment_status es ON es.status_id = pe.status_id
      JOIN structure s ON s.structure_id = pe.structure_id
      JOIN apn a ON a.apn_id = s.apn_id
      JOIN county c ON c.county_id = a.county_id
      LEFT JOIN person_structure ps ON ps.pid = p.pid AND ps.end_date IS NULL
      WHERE pr.program_code = 'BW' AND pe.exit_date IS NULL"""

if OLD in content:
    content = content.replace(OLD, NEW)
    open('server.js', 'w', encoding='utf-8').write(content)
    print("Fixed — vendor_id and vendor_name now use subqueries, person_structure LEFT JOIN added")
else:
    print("Pattern not found")
    # Show what we have around the BW participants area
    idx = content.find("api/bw/participants")
    if idx > 0:
        print("Current BW participants query:")
        print(content[idx:idx+800])