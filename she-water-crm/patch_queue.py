"""
SHE Water CRM — Patch: Add staff, queue, and case activity endpoints
Run from inside she-water-crm: python patch_queue.py
"""

import os, shutil
from datetime import datetime

os.makedirs('backups', exist_ok=True)
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2('server.js', f'backups/server.js.{ts}.bak')
print(f"  ✓ Backup: backups/server.js.{ts}.bak")

content = open('server.js', encoding='utf-8').read()

# Check what's already there
has_staff    = "app.get('/api/staff'" in content
has_queue    = "app.get('/api/queue/" in content
has_case_act = "app.get('/api/case/:case_id/activities'" in content

print(f"  Staff endpoint:           {'✓ exists' if has_staff else '✗ missing'}")
print(f"  Queue endpoint:           {'✓ exists' if has_queue else '✗ missing'}")
print(f"  Case activities endpoint: {'✓ exists' if has_case_act else '✗ missing'}")

NEW_ENDPOINTS = """
// ── STAFF ────────────────────────────────────────────────────

app.get('/api/staff', async (req, res) => {
  try {
    const r = await pool.query(`
      SELECT staff_id, first_name, last_name, role, region_id, email
      FROM staff WHERE active_flag = TRUE
      ORDER BY role, last_name
    `);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

// ── MY QUEUE ─────────────────────────────────────────────────

app.get('/api/queue/:staff_id', async (req, res) => {
  const { staff_id } = req.params;
  try {
    const staffRes = await pool.query(
      `SELECT role, region_id FROM staff WHERE staff_id = $1`, [staff_id]
    );
    if (!staffRes.rows.length) return res.json([]);
    const { role } = staffRes.rows[0];

    // Map role to the status_steps they own
    const stepMap = {
      caseworker:     ['results_received', 'closeout_scheduled', 'maintenance_monitoring', 'open', 'awaiting_lab_results'],
      field_staff:    ['field_visit_scheduled', 'sample_collected'],
      region_manager: ['pending_approval'],
      vendor:         ['vendor_scheduled'],
    };
    const mySteps = stepMap[role] || ['open'];
    const placeholders = mySteps.map((_, i) => `$${i + 1}`).join(', ');

    const r = await pool.query(`
      SELECT
        cr.case_id,
        pe.pid,
        p.first_name,
        p.last_name,
        c.county_name,
        pr.program_code,
        pe.wq_phase,
        pe.status_secondary,
        pe.status_step,
        cr.case_status,
        cr.opened_date,
        EXTRACT(DAY FROM NOW() - cr.opened_date)::INT AS days_open,
        es.status_name,
        st2.first_name || ' ' || st2.last_name AS assigned_to
      FROM case_record cr
      JOIN program_enrollment pe ON pe.enrollment_id = cr.enrollment_id
      JOIN program pr ON pr.program_id = pe.program_id
      JOIN person p ON p.pid = pe.pid
      JOIN structure s ON s.structure_id = pe.structure_id
      JOIN apn a ON a.apn_id = s.apn_id
      JOIN county c ON c.county_id = a.county_id
      JOIN enrollment_status es ON es.status_id = pe.status_id
      LEFT JOIN staff st2 ON st2.staff_id = cr.assigned_staff_id
      WHERE cr.case_status NOT IN ('closed')
        AND pe.status_step IN (${placeholders})
        AND pe.exit_date IS NULL
      ORDER BY cr.opened_date ASC
      LIMIT 100
    `, mySteps);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

// ── CASE ACTIVITIES ──────────────────────────────────────────

app.get('/api/case/:case_id/activities', async (req, res) => {
  const { case_id } = req.params;
  try {
    const r = await pool.query(`
      SELECT
        a.activity_id,
        a.activity_date,
        a.notes,
        a.next_step_triggered,
        at.activity_name,
        at.activity_category,
        pr.program_code,
        s.first_name || ' ' || s.last_name AS performed_by_name,
        s.role AS staff_role
      FROM activity a
      JOIN activity_type at ON at.activity_type_id = a.activity_type_id
      JOIN case_record cr ON cr.case_id = a.case_id
      JOIN program_enrollment pe ON pe.enrollment_id = cr.enrollment_id
      JOIN program pr ON pr.program_id = pe.program_id
      LEFT JOIN staff s ON s.staff_id = a.performed_by
      WHERE a.case_id = $1
      ORDER BY a.activity_date DESC, a.activity_id DESC
    `, [case_id]);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});
"""

added = []

if not has_staff or not has_queue or not has_case_act:
    # Find a good place to insert — before the last line (app.listen or similar)
    # Insert before the TW endpoints
    insert_marker = "// ── TANK WATER ENDPOINTS"
    if insert_marker in content:
        content = content.replace(insert_marker, NEW_ENDPOINTS + "\n" + insert_marker)
        added.append("staff, queue, case activities")
    else:
        # Append before end of file
        content = content.rstrip() + "\n" + NEW_ENDPOINTS + "\n"
        added.append("staff, queue, case activities (appended)")

open('server.js', 'w', encoding='utf-8').write(content)

# Verify
verify = open('server.js', encoding='utf-8').read()
print()
print(f"  Staff endpoint:           {'✓' if 'app.get(\"/api/staff\"' in verify else '✗'}")
print(f"  Queue endpoint:           {'✓' if 'app.get(\"/api/queue/' in verify else '✗'}")
print(f"  Case activities endpoint: {'✓' if 'app.get(\"/api/case/:case_id/activities\"' in verify else '✗'}")
print(f"  server.js size:           {os.path.getsize('server.js'):,} bytes")

if added:
    print(f"\n  ✓ Added: {', '.join(added)}")
else:
    print(f"\n  ~ All endpoints already present")

print()
print("Restart: npx kill-port 3000 && npm start")
print()
print("Then open http://localhost:3000/activity.html")
print("Select a staff member — queue should populate")
print()
print("Commit:")
print('  git add .')
print('  git commit -m "add staff, queue, case activity endpoints"')
print('  git push')
