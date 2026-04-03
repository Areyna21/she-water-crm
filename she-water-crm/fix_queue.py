"""
SHE Water CRM — Fix queue endpoint 500 error
Run from inside she-water-crm: python fix_queue.py
"""

import os, shutil, re
from datetime import datetime

os.makedirs('backups', exist_ok=True)
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2('server.js', f'backups/server.js.{ts}.bak')
print(f"  ✓ Backup created")

content = open('server.js', encoding='utf-8').read()

# Find and replace the queue endpoint
old = """app.get('/api/queue/:staff_id', async (req, res) => {
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
});"""

new = """app.get('/api/queue/:staff_id', async (req, res) => {
  const { staff_id } = req.params;
  try {
    const staffRes = await pool.query(
      `SELECT role, region_id FROM staff WHERE staff_id = $1`, [staff_id]
    );
    if (!staffRes.rows.length) return res.json([]);
    const { role } = staffRes.rows[0];

    const stepMap = {
      caseworker:     ['results_received', 'closeout_scheduled', 'maintenance_monitoring', 'open', 'awaiting_lab_results'],
      field_staff:    ['field_visit_scheduled', 'sample_collected'],
      region_manager: ['pending_approval'],
      vendor:         ['vendor_scheduled'],
    };
    const mySteps = stepMap[role] || ['open'];

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
        AND pe.status_step = ANY($1::text[])
        AND pe.exit_date IS NULL
      ORDER BY cr.opened_date ASC
      LIMIT 100
    `, [mySteps]);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});"""

if old in content:
    content = content.replace(old, new)
    open('server.js', 'w', encoding='utf-8').write(content)
    print("  ✓ Queue endpoint fixed — now uses ANY($1::text[]) instead of dynamic IN")
else:
    print("  ~ Pattern not found — trying regex replacement")
    # Find queue endpoint by pattern and replace entire block
    pattern = r"app\.get\('/api/queue/:staff_id'.*?(?=\napp\.get|\napp\.post|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        content = content[:match.start()] + new + '\n' + content[match.end():]
        open('server.js', 'w', encoding='utf-8').write(content)
        print("  ✓ Queue endpoint replaced via regex")
    else:
        print("  ✗ Could not find queue endpoint — check server.js manually")
        exit()

print(f"  server.js: {os.path.getsize('server.js'):,} bytes")
print()
print("Restart: npx kill-port 3000 && npm start")
print()
print("Commit:")
print('  git add .')
print('  git commit -m "fix queue endpoint — use ANY array instead of dynamic IN"')
print('  git push')
