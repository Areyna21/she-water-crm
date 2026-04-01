"""
SHE Water CRM — Patch: Fix TW/WQ/WW participant queries
Run from inside the she-water-crm folder: python patch_program_queries.py
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
print("SHE Water CRM — Fix TW/WQ/WW Participant Queries")
print("=" * 55)
print()

if not os.path.exists('server.js'):
    print("ERROR: Run from inside the she-water-crm folder.")
    exit()

backup('server.js')
content = open('server.js', encoding='utf-8').read()
applied = 0

# ── FIX 1: TW participants — remove bad person_structure join ─
old_tw = """      JOIN person_structure ps ON ps.pid = p.pid AND ps.end_date IS NULL
      LEFT JOIN tank_service_area tsa ON tsa.structure_id=s.structure_id
      LEFT JOIN tank t ON t.tank_id=tsa.tank_id
      LEFT JOIN vendor v ON v.vendor_id=t.vendor_id
      WHERE pr.program_code='TW' AND pe.exit_date IS NULL
      GROUP BY p.pid,p.first_name,p.last_name,pe.program_specific_id,es.status_name,
               ps.household_size,a.apn_number,c.county_name,s.structure_type,
               t.capacity_gallons,v.vendor_name,pe.enrollment_id"""

new_tw = """      LEFT JOIN person_structure ps ON ps.pid = p.pid AND ps.end_date IS NULL
      LEFT JOIN tank_service_area tsa ON tsa.structure_id=s.structure_id
      LEFT JOIN tank t ON t.tank_id=tsa.tank_id
      LEFT JOIN vendor v ON v.vendor_id=t.vendor_id
      WHERE pr.program_code='TW' AND pe.exit_date IS NULL
      GROUP BY p.pid,p.first_name,p.last_name,pe.program_specific_id,es.status_name,
               ps.household_size,a.apn_number,c.county_name,s.structure_type,
               t.capacity_gallons,v.vendor_name,pe.enrollment_id"""

if old_tw in content:
    content = content.replace(old_tw, new_tw)
    print("  ✓ Fixed TW participants query")
    applied += 1
else:
    print("  ~ TW query — pattern not found, may already be fixed")

# ── FIX 2: WQ participants — fix ambiguous join ───────────────
old_wq = """      WHERE pr.program_code='WQ' AND pe.exit_date IS NULL
      ORDER BY wqr.exceeds_mcl_flag DESC NULLS LAST, p.last_name"""

new_wq = """      WHERE pr.program_code='WQ' AND pe.exit_date IS NULL
      GROUP BY p.pid, p.first_name, p.last_name, a.apn_number, c.county_name,
               spt.point_type_name, wqr.contaminant, wqr.value, wqr.unit,
               wqr.mcl_value, wqr.exceeds_mcl_flag, e.equipment_type
      ORDER BY wqr.exceeds_mcl_flag DESC NULLS LAST, p.last_name"""

if old_wq in content:
    content = content.replace(old_wq, new_wq)
    print("  ✓ Fixed WQ participants query")
    applied += 1
else:
    print("  ~ WQ query — pattern not found, may already be fixed")

# ── FIX 3: WW cases — ensure clean join ──────────────────────
old_ww = """      WHERE pr.program_code='WW'
      ORDER BY cr.opened_date DESC"""

new_ww = """      WHERE pr.program_code='WW'
      GROUP BY cr.case_id, cr.opened_date, cr.closed_date, cr.case_status, cr.notes,
               p.pid, p.first_name, p.last_name, a.apn_number, c.county_name,
               st.first_name, st.last_name
      ORDER BY cr.opened_date DESC"""

if old_ww in content:
    content = content.replace(old_ww, new_ww)
    print("  ✓ Fixed WW cases query")
    applied += 1
else:
    print("  ~ WW query — pattern not found, may already be fixed")

# ── FIX 4: Add activity log endpoint ─────────────────────────
activity_endpoint = """
// ── ACTIVITY LOG ────────────────────────────────────────────

app.get('/api/activity/:pid', async (req, res) => {
  const { pid } = req.params;
  try {
    const result = await pool.query(`
      SELECT
        a.activity_id,
        a.activity_date,
        a.notes,
        a.next_step_triggered,
        a.survey123_ref,
        at.activity_name,
        at.activity_category,
        pr.program_name,
        pr.program_code,
        st.first_name || ' ' || st.last_name AS performed_by_name,
        cr.case_id
      FROM activity a
      JOIN activity_type at ON at.activity_type_id = a.activity_type_id
      JOIN case_record cr ON cr.case_id = a.case_id
      JOIN program_enrollment pe ON pe.enrollment_id = cr.enrollment_id
      JOIN program pr ON pr.program_id = pe.program_id
      LEFT JOIN staff st ON st.staff_id = a.performed_by
      WHERE pe.pid = $1
      ORDER BY a.activity_date DESC
      LIMIT 100
    `, [pid]);
    res.json(result.rows);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.post('/api/activity', async (req, res) => {
  const { case_id, activity_type_id, performed_by, notes, survey123_ref } = req.body;
  try {
    const result = await pool.query(`
      INSERT INTO activity (case_id, activity_type_id, performed_by, activity_date, notes, survey123_ref, next_step_triggered)
      VALUES ($1, $2, $3, NOW(), $4, $5,
        (SELECT triggers_next_step FROM activity_type WHERE activity_type_id = $2))
      RETURNING activity_id
    `, [case_id, activity_type_id, performed_by, notes, survey123_ref || null]);
    res.json({ activity_id: result.rows[0].activity_id });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/activity-types', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT at.activity_type_id, at.activity_name, at.activity_category,
             at.triggers_next_step, pr.program_code
      FROM activity_type at
      LEFT JOIN program pr ON pr.program_id = at.program_id
      WHERE at.active_flag = TRUE
      ORDER BY at.program_id NULLS FIRST, at.activity_name
    `);
    res.json(result.rows);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/case/:case_id/status', async (req, res) => {
  const { case_id } = req.params;
  try {
    const result = await pool.query(`
      SELECT cr.case_id, cr.case_status, cr.opened_date, cr.closed_date, cr.notes,
             pe.status_id, pe.status_secondary, pe.status_step,
             es.status_name, pr.program_name, pr.program_code,
             p.pid, p.first_name, p.last_name
      FROM case_record cr
      JOIN program_enrollment pe ON pe.enrollment_id = cr.enrollment_id
      JOIN enrollment_status es ON es.status_id = pe.status_id
      JOIN program pr ON pr.program_id = pe.program_id
      JOIN person p ON p.pid = pe.pid
      WHERE cr.case_id = $1
    `, [case_id]);
    res.json(result.rows[0] || null);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.post('/api/case/:case_id/status', async (req, res) => {
  const { case_id } = req.params;
  const { case_status, status_secondary, status_step, notes, staff_id } = req.body;
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    await client.query(`
      UPDATE case_record SET case_status = $1, notes = COALESCE($2, notes),
        closed_date = CASE WHEN $1 = 'closed' THEN CURRENT_DATE ELSE closed_date END
      WHERE case_id = $3
    `, [case_status, notes, case_id]);
    await client.query(`
      UPDATE program_enrollment pe SET
        status_secondary = $1, status_step = $2
      FROM case_record cr
      WHERE cr.enrollment_id = pe.enrollment_id AND cr.case_id = $3
    `, [status_secondary, status_step, case_id]);
    // Log the status change as an activity
    const at = await client.query(
      `SELECT activity_type_id FROM activity_type WHERE activity_name = $1 LIMIT 1`,
      [case_status === 'closed' ? 'Case Closed' : case_status === 'pending_approval' ? 'Submitted for Approval' : 'Approved']
    );
    if (at.rows.length) {
      await client.query(`
        INSERT INTO activity (case_id, activity_type_id, performed_by, activity_date, notes)
        VALUES ($1, $2, $3, NOW(), $4)
      `, [case_id, at.rows[0].activity_type_id, staff_id, `Status changed to: ${case_status}. ${notes || ''}`]);
    }
    await client.query('COMMIT');
    res.json({ success: true });
  } catch (err) {
    await client.query('ROLLBACK');
    res.status(500).json({ error: err.message });
  } finally { client.release(); }
});
"""

if "api/activity/:pid" not in content:
    # Insert before the last app.listen
    content = content.replace(
        "// ── BOTTLED WATER ENDPOINTS",
        activity_endpoint + "\n// ── BOTTLED WATER ENDPOINTS"
    )
    print("  ✓ Added activity log endpoints (GET/POST activity, status workflow)")
    applied += 1
else:
    print("  ~ Activity endpoints already present")

open('server.js', 'w', encoding='utf-8').write(content)

print()
print(f"Done. {applied} patch(es) applied.")
print()
print("Restart server: npx kill-port 3000 && npm start")
print()
print("New endpoints available:")
print("  GET  /api/activity/:pid       — all activities for a participant")
print("  POST /api/activity            — log a new activity")
print("  GET  /api/activity-types      — all activity type options")
print("  GET  /api/case/:id/status     — current case status")
print("  POST /api/case/:id/status     — update case status + log activity")
print()
print("Commit when ready:")
print('  git add .')
print('  git commit -m "fix TW/WQ/WW queries, add activity log and case status endpoints"')
print('  git push')