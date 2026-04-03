require('dotenv').config();
const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

// ── PARTICIPANT SEARCH ──────────────────────────────────────
app.get('/api/participants', async (req, res) => {
  const { q } = req.query;
  const search = q ? `%${q}%` : '%';
  try {
    const result = await pool.query(`
      SELECT
        p.pid,
        p.first_name,
        p.last_name,
        p.phone_primary,
        p.preferred_language,
        p.interpreter_needed,
        a.apn_number,
        a.dmpid,
        c.county_name,
        r.region_name,
        s.structure_type,
        s.unit_number,
        ps.household_size,
        COALESCE(prog.programs, '—') AS programs,
        COALESCE(prog.statuses, '—') AS statuses
      FROM person p
      JOIN person_structure ps ON ps.pid = p.pid AND ps.end_date IS NULL
      JOIN structure s ON s.structure_id = ps.structure_id
      JOIN apn a ON a.apn_id = s.apn_id
      JOIN county c ON c.county_id = a.county_id
      LEFT JOIN region r ON r.region_id = a.region_id
      LEFT JOIN (
        SELECT
          pe.pid,
          string_agg(DISTINCT pr.program_code, ', ' ORDER BY pr.program_code) AS programs,
          string_agg(DISTINCT es.status_name, ', ') AS statuses
        FROM program_enrollment pe
        JOIN program pr ON pr.program_id = pe.program_id
        JOIN enrollment_status es ON es.status_id = pe.status_id
        WHERE pe.exit_date IS NULL
        GROUP BY pe.pid
      ) prog ON prog.pid = p.pid
      WHERE
        p.last_name ILIKE $1
        OR p.first_name ILIKE $1
        OR p.pid ILIKE $1
        OR p.phone_primary ILIKE $1
        OR a.apn_number ILIKE $1
      ORDER BY p.last_name, p.first_name
      LIMIT 100
    `, [search]);
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── PARTICIPANT PROFILE ─────────────────────────────────────
app.get('/api/participant/:pid', async (req, res) => {
  const { pid } = req.params;
  try {
    // Core person + current address
    const person = await pool.query(`
      SELECT
        p.pid, p.first_name, p.last_name, p.middle_name,
        p.phone_primary, p.phone_secondary, p.email,
        p.preferred_language, p.interpreter_needed,
        p.created_date,
        a.apn_number, a.dmpid, a.gsa_zone, a.floodplain_flag,
        a.mailing_address, a.management_zone,
        c.county_name,
        r.region_name,
        s.structure_type, s.unit_number,
        s.structure_lat, s.structure_long,
        ps.household_size, ps.start_date AS residence_start,
        rt.role_name,
        st.first_name || ' ' || st.last_name AS caseworker_name
      FROM person p
      JOIN person_structure ps ON ps.pid = p.pid AND ps.end_date IS NULL
      JOIN structure s ON s.structure_id = ps.structure_id
      JOIN apn a ON a.apn_id = s.apn_id
      JOIN county c ON c.county_id = a.county_id
      JOIN role_type rt ON rt.role_type_id = ps.role_type_id
      LEFT JOIN region r ON r.region_id = a.region_id
      LEFT JOIN program_enrollment pe ON pe.pid = p.pid AND pe.exit_date IS NULL
      LEFT JOIN staff st ON st.staff_id = pe.caseworker_id
      WHERE p.pid = $1
      LIMIT 1
    `, [pid]);

    // All enrollments
    const enrollments = await pool.query(`
      SELECT
        pe.enrollment_id,
        pe.program_specific_id,
        pr.program_name,
        pr.program_code,
        es.status_name,
        pe.enrollment_date,
        pe.exit_date,
        pe.exit_reason,
        st.first_name || ' ' || st.last_name AS caseworker,
        s.structure_type,
        s.unit_number,
        a.apn_number,
        c.county_name
      FROM program_enrollment pe
      JOIN program pr ON pr.program_id = pe.program_id
      JOIN enrollment_status es ON es.status_id = pe.status_id
      JOIN structure s ON s.structure_id = pe.structure_id
      JOIN apn a ON a.apn_id = s.apn_id
      JOIN county c ON c.county_id = a.county_id
      LEFT JOIN staff st ON st.staff_id = pe.caseworker_id
      WHERE pe.pid = $1
      ORDER BY pe.enrollment_date DESC
    `, [pid]);

    // Address history
    const history = await pool.query(`
      SELECT
        ps.start_date,
        ps.end_date,
        rt.role_name,
        ps.household_size,
        s.structure_type,
        s.unit_number,
        a.apn_number,
        c.county_name
      FROM person_structure ps
      JOIN structure s ON s.structure_id = ps.structure_id
      JOIN apn a ON a.apn_id = s.apn_id
      JOIN county c ON c.county_id = a.county_id
      JOIN role_type rt ON rt.role_type_id = ps.role_type_id
      WHERE ps.pid = $1
      ORDER BY ps.start_date DESC
    `, [pid]);

    // Cases
    const cases = await pool.query(`
      SELECT
        cr.case_id,
        cr.opened_date,
        cr.closed_date,
        cr.case_status,
        cr.notes,
        pr.program_name,
        pr.program_code,
        st.first_name || ' ' || st.last_name AS assigned_staff
      FROM case_record cr
      JOIN program_enrollment pe ON pe.enrollment_id = cr.enrollment_id
      JOIN program pr ON pr.program_id = pe.program_id
      LEFT JOIN staff st ON st.staff_id = cr.assigned_staff_id
      WHERE pe.pid = $1
      ORDER BY cr.opened_date DESC
    `, [pid]);

    if (!person.rows.length) {
      return res.status(404).json({ error: 'Participant not found' });
    }

    res.json({
      person: person.rows[0],
      enrollments: enrollments.rows,
      history: history.rows,
      cases: cases.rows
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── REGION LOOKUP ───────────────────────────────────────────
app.get('/api/region-lookup', async (req, res) => {
  const { apn, county } = req.query;
  try {
    const result = await pool.query(`
      SELECT
        a.apn_number,
        a.dmpid,
        a.gsa_zone,
        a.floodplain_flag,
        c.county_name,
        r.region_name,
        st.first_name || ' ' || st.last_name AS region_manager,
        st.phone AS manager_phone,
        array_agg(DISTINCT cw.first_name || ' ' || cw.last_name) AS caseworkers
      FROM apn a
      JOIN county c ON c.county_id = a.county_id
      LEFT JOIN region r ON r.region_id = a.region_id
      LEFT JOIN staff st ON st.staff_id = r.region_manager_id
      LEFT JOIN staff cw ON cw.region_id = r.region_id AND cw.role = 'caseworker'
      WHERE a.apn_number ILIKE $1
        AND ($2 = '' OR c.county_name ILIKE $3)
      GROUP BY a.apn_number, a.dmpid, a.gsa_zone, a.floodplain_flag,
               c.county_name, r.region_name, st.first_name, st.last_name, st.phone
      LIMIT 10
    `, [apn ? `%${apn}%` : '%', county || '', county ? `%${county}%` : '%']);
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── STATS FOR DASHBOARD ─────────────────────────────────────
app.get('/api/stats', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        (SELECT COUNT(*) FROM person) AS total_participants,
        (SELECT COUNT(*) FROM program_enrollment WHERE exit_date IS NULL) AS active_enrollments,
        (SELECT COUNT(*) FROM program_enrollment pe JOIN program pr ON pr.program_id = pe.program_id WHERE pr.program_code = 'BW' AND pe.exit_date IS NULL) AS active_bw,
        (SELECT COUNT(*) FROM program_enrollment pe JOIN program pr ON pr.program_id = pe.program_id WHERE pr.program_code = 'TW' AND pe.exit_date IS NULL) AS active_tw,
        (SELECT COUNT(*) FROM program_enrollment pe JOIN program pr ON pr.program_id = pe.program_id WHERE pr.program_code = 'WQ' AND pe.exit_date IS NULL) AS active_wq,
        (SELECT COUNT(*) FROM program_enrollment pe JOIN program pr ON pr.program_id = pe.program_id WHERE pr.program_code = 'WW' AND pe.exit_date IS NULL) AS active_ww,
        (SELECT COUNT(*) FROM case_record WHERE case_status = 'open') AS open_cases,
        (SELECT COUNT(*) FROM case_record WHERE case_status = 'pending_approval') AS pending_cases
    `);
    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`SHE Water CRM running at http://localhost:${PORT}`);
});

// ── APN LOOKUP ──────────────────────────────────────────────
app.get('/api/apn-lookup', async (req, res) => {
  const { apn, county_id } = req.query;
  try {
    const result = await pool.query(`
      SELECT a.apn_id, a.apn_number, a.dmpid, a.gsa_zone,
             a.floodplain_flag, a.mailing_address, a.region_id,
             c.county_name, r.region_name
      FROM apn a
      JOIN county c ON c.county_id = a.county_id
      LEFT JOIN region r ON r.region_id = a.region_id
      WHERE a.apn_number ILIKE $1 AND a.county_id = $2
      LIMIT 1
    `, [`%${apn}%`, county_id]);
    res.json(result.rows[0] || null);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// ── INTAKE ──────────────────────────────────────────────────
app.post('/api/intake', async (req, res) => {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const { person, household_size, monthly_income, income_verified,
            referral_source, referral_detail, location, programs,
            caseworker_id, notes } = req.body;

    // Generate PID
    const pidResult = await client.query(`SELECT pid FROM person ORDER BY pid DESC LIMIT 1`);
    let nextNum = 1;
    if (pidResult.rows.length) {
      const num = parseInt(pidResult.rows[0].pid.replace('PID-',''));
      nextNum = num + 1;
    }
    const pid = `PID-${String(nextNum).padStart(4,'0')}`;
    const cwId = caseworker_id || 2;

    await client.query(`
      INSERT INTO person (pid,first_name,middle_name,last_name,dob,phone_primary,
        phone_secondary,email,preferred_language,interpreter_needed,created_by)
      VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
    `,[pid,person.first_name,person.middle_name,person.last_name,person.dob,
       person.phone_primary,person.phone_secondary,person.email,
       person.preferred_language,person.interpreter_needed,cwId]);

    let apnId = location.existing_apn_id;
    if (!apnId) {
      const propResult = await client.query(`INSERT INTO property DEFAULT VALUES RETURNING property_id`);
      const apnResult = await client.query(`
        INSERT INTO apn (property_id,apn_number,county_id,gsa_zone,mailing_address,region_assignment_method)
        VALUES ($1,$2,$3,$4,$5,'manual_override') RETURNING apn_id
      `,[propResult.rows[0].property_id,location.apn_number,location.county_id,
         location.gsa_zone,location.mailing_address]);
      apnId = apnResult.rows[0].apn_id;
    }

    const structResult = await client.query(`
      INSERT INTO structure (apn_id,structure_type,unit_number) VALUES ($1,$2,$3) RETURNING structure_id
    `,[apnId,location.structure_type||'single_family',location.unit_number||null]);
    const structureId = structResult.rows[0].structure_id;

    await client.query(`
      INSERT INTO person_structure (pid,structure_id,role_type_id,household_size,start_date)
      VALUES ($1,$2,$3,$4,CURRENT_DATE)
    `,[pid,structureId,location.role_type_id,household_size]);

    await client.query(`
      INSERT INTO eligibility (pid,household_size,monthly_income,income_verified,effective_date)
      VALUES ($1,$2,$3,$4,CURRENT_DATE)
    `,[pid,household_size,monthly_income,income_verified]);

    if (referral_source) {
      await client.query(`
        INSERT INTO referral_source (pid,source_type,source_detail,referral_date)
        VALUES ($1,$2,$3,CURRENT_DATE)
      `,[pid,referral_source,referral_detail]);
    }

    const programMap = {'BW':1,'TW':2,'WQ':3,'WW':4};
    const programIds = {};

    for (const code of programs) {
      const programId = programMap[code];
      const seqResult = await client.query(
        `SELECT COUNT(*) as cnt FROM program_enrollment WHERE program_id=$1`,[programId]);
      const seq = parseInt(seqResult.rows[0].cnt)+1;
      const year = new Date().getFullYear();
      const progSpecificId = `${code}-${year}-${String(seq).padStart(4,'0')}`;
      programIds[code] = progSpecificId;

      const enrollResult = await client.query(`
        INSERT INTO program_enrollment
          (pid,program_id,structure_id,program_specific_id,caseworker_id,status_id,enrollment_date)
        VALUES ($1,$2,$3,$4,$5,5,CURRENT_DATE) RETURNING enrollment_id
      `,[pid,programId,structureId,progSpecificId,cwId]);

      const caseResult = await client.query(`
        INSERT INTO case_record (enrollment_id,assigned_staff_id,opened_date,case_status,notes)
        VALUES ($1,$2,CURRENT_DATE,'pending_approval',$3) RETURNING case_id
      `,[enrollResult.rows[0].enrollment_id,cwId,notes||`Intake via CRM. Program: ${code}.`]);

      await client.query(`
        INSERT INTO activity (case_id,activity_type_id,performed_by,activity_date,notes)
        VALUES ($1,1,$2,NOW(),$3)
      `,[caseResult.rows[0].case_id,cwId,`Intake call. Enrolled in ${code}. ${notes||''}`]);
    }

    await client.query('COMMIT');
    res.json({ pid, program_ids: programIds });
  } catch (err) {
    await client.query('ROLLBACK');
    console.error('Intake error:', err);
    res.status(500).json({ error: err.message });
  } finally { client.release(); }
});

// ── BOTTLED WATER ENDPOINTS ─────────────────────────────────

app.get('/api/bw/stats', async (req, res) => {
  try {
    const now = new Date();
    const firstDay = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-01`;
    const lastDay  = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${new Date(now.getFullYear(), now.getMonth()+1, 0).getDate()}`;
    const result = await pool.query(`
      SELECT
        (SELECT COUNT(*) FROM program_enrollment pe
         JOIN program pr ON pr.program_id = pe.program_id
         WHERE pr.program_code = 'BW' AND pe.exit_date IS NULL) AS active,
        (SELECT COUNT(*) FROM delivery d
         JOIN program_enrollment pe ON pe.enrollment_id = d.enrollment_id
         JOIN program pr ON pr.program_id = pe.program_id
         WHERE pr.program_code = 'BW'
         AND d.scheduled_date BETWEEN $1 AND $2) AS scheduled,
        (SELECT COUNT(*) FROM delivery d
         JOIN program_enrollment pe ON pe.enrollment_id = d.enrollment_id
         JOIN program pr ON pr.program_id = pe.program_id
         WHERE pr.program_code = 'BW' AND d.delivery_status = 'delivered'
         AND d.scheduled_date BETWEEN $1 AND $2) AS delivered,
        (SELECT COUNT(*) FROM delivery d
         JOIN program_enrollment pe ON pe.enrollment_id = d.enrollment_id
         JOIN program pr ON pr.program_id = pe.program_id
         WHERE pr.program_code = 'BW' AND d.delivery_status = 'missed'
         AND d.scheduled_date BETWEEN $1 AND $2) AS missed,
        (SELECT COUNT(*) FROM delivery d
         JOIN program_enrollment pe ON pe.enrollment_id = d.enrollment_id
         JOIN program pr ON pr.program_id = pe.program_id
         WHERE pr.program_code = 'BW' AND d.delivery_status = 'disputed'
         AND d.scheduled_date BETWEEN $1 AND $2) AS disputed
    `, [firstDay, lastDay]);
    res.json(result.rows[0]);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/bw/vendors', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT v.vendor_id, v.vendor_name FROM vendor v
      JOIN vendor_type vt ON vt.vendor_type_id = v.vendor_type_id
      WHERE vt.type_name = 'Bottled Water Delivery' AND v.active_flag = TRUE
      ORDER BY v.vendor_name
    `);
    res.json(result.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/bw/participants', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        p.pid, p.first_name, p.last_name,
        pe.program_specific_id, pe.enrollment_id,
        es.status_name,
        COALESCE(ps.household_size, 0) AS household_size,
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
      LEFT JOIN person_structure ps ON ps.pid = p.pid AND ps.end_date IS NULL
      WHERE pr.program_code = 'BW' AND pe.exit_date IS NULL
      ORDER BY p.last_name, p.first_name
    `);
    res.json(result.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/bw/deliveries', async (req, res) => {
  const { year, month } = req.query;
  try {
    const firstDay = `${year}-${String(month).padStart(2,'0')}-01`;
    const lastDay  = `${year}-${String(month).padStart(2,'0')}-${new Date(year, month, 0).getDate()}`;
    const result = await pool.query(`
      SELECT d.delivery_id, d.scheduled_date, d.delivered_date,
             d.delivery_status, d.missed_reason, d.reported_by,
             d.allotment_units, d.vendor_id,
             p.pid, p.first_name, p.last_name,
             c.county_name, v.vendor_name
      FROM delivery d
      JOIN program_enrollment pe ON pe.enrollment_id = d.enrollment_id
      JOIN program pr ON pr.program_id = pe.program_id
      JOIN person p ON p.pid = pe.pid
      JOIN structure s ON s.structure_id = pe.structure_id
      JOIN apn a ON a.apn_id = s.apn_id
      JOIN county c ON c.county_id = a.county_id
      LEFT JOIN vendor v ON v.vendor_id = d.vendor_id
      WHERE pr.program_code = 'BW'
      AND d.scheduled_date BETWEEN $1 AND $2
      ORDER BY d.scheduled_date, p.last_name
    `, [firstDay, lastDay]);
    res.json(result.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/bw/missed', async (req, res) => {
  const { vendor, days } = req.query;
  try {
    const daysBack = parseInt(days) || 30;
    const vendorClause = vendor ? `AND d.vendor_id = ${parseInt(vendor)}` : '';
    const result = await pool.query(`
      SELECT d.delivery_id, d.scheduled_date, d.missed_reason, d.reported_by,
             p.pid, p.first_name, p.last_name,
             c.county_name, v.vendor_name, v.vendor_id
      FROM delivery d
      JOIN program_enrollment pe ON pe.enrollment_id = d.enrollment_id
      JOIN program pr ON pr.program_id = pe.program_id
      JOIN person p ON p.pid = pe.pid
      JOIN structure s ON s.structure_id = pe.structure_id
      JOIN apn a ON a.apn_id = s.apn_id
      JOIN county c ON c.county_id = a.county_id
      LEFT JOIN vendor v ON v.vendor_id = d.vendor_id
      WHERE pr.program_code = 'BW'
      AND d.delivery_status = 'missed'
      AND d.scheduled_date >= CURRENT_DATE - INTERVAL '${daysBack} days'
      ${vendorClause}
      ORDER BY d.scheduled_date DESC
    `);
    res.json(result.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/bw/vendor-performance', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        v.vendor_id, v.vendor_name,
        COUNT(*) AS total,
        SUM(CASE WHEN d.delivery_status = 'delivered' THEN 1 ELSE 0 END) AS delivered,
        SUM(CASE WHEN d.delivery_status = 'missed'    THEN 1 ELSE 0 END) AS missed,
        SUM(CASE WHEN d.delivery_status = 'disputed'  THEN 1 ELSE 0 END) AS disputed
      FROM delivery d
      JOIN program_enrollment pe ON pe.enrollment_id = d.enrollment_id
      JOIN program pr ON pr.program_id = pe.program_id
      JOIN vendor v ON v.vendor_id = d.vendor_id
      WHERE pr.program_code = 'BW'
      GROUP BY v.vendor_id, v.vendor_name
      ORDER BY total DESC
    `);
    res.json(result.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.post('/api/bw/log-miss', async (req, res) => {
  const { pid, scheduled_date, reported_by, vendor_id, missed_reason, notes } = req.body;
  try {
    const enroll = await pool.query(`
      SELECT pe.enrollment_id FROM program_enrollment pe
      JOIN program pr ON pr.program_id = pe.program_id
      WHERE pe.pid = $1 AND pr.program_code = 'BW' AND pe.exit_date IS NULL
      LIMIT 1
    `, [pid]);
    if (!enroll.rows.length) {
      return res.status(404).json({ error: 'No active BW enrollment found for this PID' });
    }
    const enrollId = enroll.rows[0].enrollment_id;
    await pool.query(`
      INSERT INTO delivery (enrollment_id, vendor_id, scheduled_date, delivery_status, missed_reason, reported_by)
      VALUES ($1, $2, $3, 'missed', $4, $5)
    `, [enrollId, vendor_id || null, scheduled_date, missed_reason, reported_by]);
    res.json({ success: true });
  } catch(err) { res.status(500).json({ error: err.message }); }
});

// ── TANK WATER ENDPOINTS ────────────────────────────────────

app.get('/api/tw/stats', async (req, res) => {
  try {
    const now = new Date();
    const firstDay = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-01`;
    const lastDay  = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${new Date(now.getFullYear(),now.getMonth()+1,0).getDate()}`;
    const r = await pool.query(`
      SELECT
        (SELECT COUNT(*) FROM program_enrollment pe JOIN program pr ON pr.program_id=pe.program_id WHERE pr.program_code='TW' AND pe.exit_date IS NULL) AS active,
        (SELECT COUNT(*) FROM tank WHERE active_flag=TRUE) AS active_tanks,
        (SELECT COUNT(*) FROM tank t JOIN tank_service_area tsa ON tsa.tank_id=t.tank_id GROUP BY t.tank_id HAVING COUNT(tsa.structure_id)>1 LIMIT 100) AS community_tanks,
        (SELECT COUNT(*) FROM tank_fill WHERE fill_date BETWEEN $1 AND $2) AS fills,
        (SELECT COUNT(*) FROM tank_fill WHERE fill_status='missed' AND scheduled_date BETWEEN $1 AND $2) AS missed_fills,
        (SELECT COALESCE(SUM(gallons_delivered),0) FROM tank_fill WHERE fill_date BETWEEN $1 AND $2) AS total_gallons
    `, [firstDay, lastDay]);
    res.json(r.rows[0]);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/tw/participants', async (req, res) => {
  try {
    const r = await pool.query(`
      SELECT p.pid, p.first_name, p.last_name, pe.program_specific_id,
             es.status_name, ps.household_size, a.apn_number, c.county_name,
             s.structure_type, t.capacity_gallons, v.vendor_name,
             (SELECT tf.fill_date FROM tank_fill tf WHERE tf.enrollment_id=pe.enrollment_id ORDER BY tf.fill_date DESC LIMIT 1) AS last_fill
      FROM program_enrollment pe
      JOIN program pr ON pr.program_id=pe.program_id
      JOIN person p ON p.pid=pe.pid
      JOIN enrollment_status es ON es.status_id=pe.status_id
      JOIN structure s ON s.structure_id=pe.structure_id
      JOIN apn a ON a.apn_id=s.apn_id
      JOIN county c ON c.county_id=a.county_id
      JOIN person_structure ps ON ps.pid=p.pid AND ps.end_date IS NULL
      LEFT JOIN tank_service_area tsa ON tsa.structure_id=s.structure_id
      LEFT JOIN tank t ON t.tank_id=tsa.tank_id
      LEFT JOIN vendor v ON v.vendor_id=t.vendor_id
      WHERE pr.program_code='TW' AND pe.exit_date IS NULL
      GROUP BY p.pid,p.first_name,p.last_name,pe.program_specific_id,es.status_name,
               ps.household_size,a.apn_number,c.county_name,s.structure_type,
               t.capacity_gallons,v.vendor_name,pe.enrollment_id
      ORDER BY p.last_name
    `);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/tw/tanks', async (req, res) => {
  try {
    const r = await pool.query(`
      SELECT t.tank_id, t.capacity_gallons, t.install_date,
             v.vendor_name, c.county_name,
             COUNT(DISTINCT tsa.structure_id) AS structures_served,
             COUNT(DISTINCT tsa.structure_id) > 1 AS is_community
      FROM tank t
      LEFT JOIN vendor v ON v.vendor_id=t.vendor_id
      LEFT JOIN tank_service_area tsa ON tsa.tank_id=t.tank_id
      LEFT JOIN apn a ON a.apn_id=tsa.apn_id
      LEFT JOIN county c ON c.county_id=a.county_id
      WHERE t.active_flag=TRUE
      GROUP BY t.tank_id,t.capacity_gallons,t.install_date,v.vendor_name,c.county_name
      ORDER BY t.tank_id
    `);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/tw/fills', async (req, res) => {
  const { vendor, status, from, to } = req.query;
  try {
    const conditions = [];
    const params = [];
    if (vendor) { params.push(vendor); conditions.push(`tf.vendor_id=$${params.length}`); }
    if (status) { params.push(status); conditions.push(`tf.fill_status=$${params.length}`); }
    if (from)   { params.push(from);   conditions.push(`tf.scheduled_date>=$${params.length}`); }
    if (to)     { params.push(to);     conditions.push(`tf.scheduled_date<=$${params.length}`); }
    const where = conditions.length ? 'WHERE ' + conditions.join(' AND ') : '';
    const r = await pool.query(`
      SELECT tf.fill_id, tf.scheduled_date, tf.fill_date, tf.fill_status,
             tf.gallons_delivered, tf.tank_id,
             p.first_name, p.last_name, c.county_name, v.vendor_name
      FROM tank_fill tf
      JOIN program_enrollment pe ON pe.enrollment_id=tf.enrollment_id
      JOIN person p ON p.pid=pe.pid
      JOIN structure s ON s.structure_id=pe.structure_id
      JOIN apn a ON a.apn_id=s.apn_id
      JOIN county c ON c.county_id=a.county_id
      LEFT JOIN vendor v ON v.vendor_id=tf.vendor_id
      ${where}
      ORDER BY tf.scheduled_date DESC
      LIMIT 200
    `, params);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/tw/vendor-performance', async (req, res) => {
  try {
    const r = await pool.query(`
      SELECT v.vendor_id, v.vendor_name,
             COUNT(*) AS total,
             SUM(CASE WHEN tf.fill_status='completed' THEN 1 ELSE 0 END) AS completed,
             SUM(CASE WHEN tf.fill_status='missed'    THEN 1 ELSE 0 END) AS missed,
             COALESCE(SUM(tf.gallons_delivered),0) AS total_gallons
      FROM tank_fill tf
      JOIN vendor v ON v.vendor_id=tf.vendor_id
      GROUP BY v.vendor_id,v.vendor_name ORDER BY total DESC
    `);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

// ── WATER QUALITY ENDPOINTS ─────────────────────────────────

app.get('/api/wq/stats', async (req, res) => {
  try {
    const r = await pool.query(`
      SELECT
        (SELECT COUNT(*) FROM program_enrollment pe JOIN program pr ON pr.program_id=pe.program_id WHERE pr.program_code='WQ' AND pe.exit_date IS NULL) AS active,
        (SELECT COUNT(*) FROM sample_point WHERE active_flag=TRUE) AS sample_points,
        (SELECT COUNT(*) FROM water_quality_result WHERE exceeds_mcl_flag=TRUE) AS exceeded,
        (SELECT COUNT(*) FROM equipment WHERE equipment_type='POE' AND active_flag=TRUE) AS poe,
        (SELECT COUNT(*) FROM equipment WHERE equipment_type='POU' AND active_flag=TRUE) AS pou,
        (SELECT COUNT(*) FROM water_quality_result WHERE result_date IS NULL) AS pending
    `);
    res.json(r.rows[0]);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/wq/participants', async (req, res) => {
  try {
    const r = await pool.query(`
      SELECT DISTINCT
        p.pid, p.first_name, p.last_name,
        a.apn_number, c.county_name,
        pe.program_specific_id,
        pe.wq_phase,
        pe.status_secondary,
        pe.status_step,
        es.status_name,
        cr.case_id,
        cr.opened_date,
        st.first_name || ' ' || st.last_name AS caseworker_name,
        spt.point_type_name,
        wqr.contaminant,
        wqr.value,
        wqr.unit,
        wqr.mcl_value,
        wqr.exceeds_mcl_flag,
        wqr.sample_date,
        e.equipment_type
      FROM program_enrollment pe
      JOIN program pr ON pr.program_id = pe.program_id
      JOIN person p ON p.pid = pe.pid
      JOIN enrollment_status es ON es.status_id = pe.status_id
      JOIN structure s ON s.structure_id = pe.structure_id
      JOIN apn a ON a.apn_id = s.apn_id
      JOIN county c ON c.county_id = a.county_id
      LEFT JOIN case_record cr ON cr.enrollment_id = pe.enrollment_id
      LEFT JOIN staff st ON st.staff_id = cr.assigned_staff_id
      LEFT JOIN sample_point sp ON sp.structure_id = s.structure_id
      LEFT JOIN sample_point_type spt ON spt.point_type_id = sp.point_type_id
      LEFT JOIN water_quality_result wqr ON wqr.sample_point_id = sp.sample_point_id
      LEFT JOIN equipment e ON e.sample_point_id = sp.sample_point_id
      WHERE pr.program_code = 'WQ' AND pe.exit_date IS NULL
      ORDER BY wqr.exceeds_mcl_flag DESC NULLS LAST, p.last_name
    `);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/wq/results', async (req, res) => {
  const { contaminant, exceeds, county } = req.query;
  try {
    const conditions = ['pr.program_code=\'WQ\''];
    const params = [];
    if (contaminant) { params.push(contaminant); conditions.push(`wqr.contaminant=$${params.length}`); }
    if (exceeds !== '') { params.push(exceeds === 'true'); conditions.push(`wqr.exceeds_mcl_flag=$${params.length}`); }
    if (county) { params.push(county); conditions.push(`c.county_name=$${params.length}`); }
    const r = await pool.query(`
      SELECT wqr.result_id, wqr.sample_date, wqr.result_date,
             wqr.contaminant, wqr.value, wqr.unit, wqr.mcl_value, wqr.exceeds_mcl_flag,
             p.pid, p.first_name, p.last_name,
             c.county_name, spt.point_type_name, v.vendor_name
      FROM water_quality_result wqr
      JOIN sample_point sp ON sp.sample_point_id=wqr.sample_point_id
      JOIN sample_point_type spt ON spt.point_type_id=sp.point_type_id
      LEFT JOIN structure s ON s.structure_id=sp.structure_id
      LEFT JOIN program_enrollment pe ON pe.structure_id=s.structure_id
      LEFT JOIN program pr ON pr.program_id=pe.program_id
      LEFT JOIN person p ON p.pid=pe.pid
      LEFT JOIN apn a ON a.apn_id=s.apn_id
      LEFT JOIN county c ON c.county_id=a.county_id
      LEFT JOIN vendor v ON v.vendor_id=wqr.vendor_id
      WHERE ${conditions.join(' AND ')}
      ORDER BY wqr.sample_date DESC LIMIT 200
    `, params);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/wq/contaminant-summary', async (req, res) => {
  try {
    const r = await pool.query(`
      SELECT contaminant, unit,
             AVG(value) AS avg_value, MAX(value) AS max_value,
             MIN(mcl_value) AS mcl_value,
             SUM(CASE WHEN exceeds_mcl_flag THEN 1 ELSE 0 END) AS exceed_count,
             COUNT(*) AS total_count
      FROM water_quality_result
      GROUP BY contaminant, unit
      ORDER BY exceed_count DESC, total_count DESC
    `);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/wq/equipment', async (req, res) => {
  try {
    const r = await pool.query(`
      SELECT e.equipment_id, e.equipment_type, e.make, e.model, e.serial_number,
             e.install_date, e.last_service_date, e.next_service_date,
             p.pid, c.county_name
      FROM equipment e
      JOIN sample_point sp ON sp.sample_point_id=e.sample_point_id
      LEFT JOIN structure s ON s.structure_id=sp.structure_id
      LEFT JOIN program_enrollment pe ON pe.structure_id=s.structure_id
      LEFT JOIN person p ON p.pid=pe.pid
      LEFT JOIN apn a ON a.apn_id=s.apn_id
      LEFT JOIN county c ON c.county_id=a.county_id
      WHERE e.active_flag=TRUE
      ORDER BY e.next_service_date ASC NULLS LAST
    `);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/wq/labs', async (req, res) => {
  try {
    const r = await pool.query(`
      SELECT v.vendor_name,
             COUNT(*) AS total,
             SUM(CASE WHEN exceeds_mcl_flag THEN 1 ELSE 0 END) AS exceeded
      FROM water_quality_result wqr
      JOIN vendor v ON v.vendor_id=wqr.vendor_id
      GROUP BY v.vendor_name ORDER BY total DESC
    `);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

// ── WATER WELL ENDPOINTS ────────────────────────────────────

app.get('/api/ww/stats', async (req, res) => {
  try {
    const r = await pool.query(`
      SELECT
        (SELECT COUNT(*) FROM case_record cr JOIN program_enrollment pe ON pe.enrollment_id=cr.enrollment_id JOIN program pr ON pr.program_id=pe.program_id WHERE pr.program_code='WW' AND cr.case_status='open') AS active,
        (SELECT COUNT(*) FROM case_record cr JOIN program_enrollment pe ON pe.enrollment_id=cr.enrollment_id JOIN program pr ON pr.program_id=pe.program_id WHERE pr.program_code='WW' AND cr.case_status='pending_approval') AS pending_approval,
        (SELECT COUNT(*) FROM case_record cr JOIN program_enrollment pe ON pe.enrollment_id=cr.enrollment_id JOIN program pr ON pr.program_id=pe.program_id WHERE pr.program_code='WW' AND cr.case_status='approved') AS drilling,
        (SELECT COUNT(*) FROM case_record cr JOIN program_enrollment pe ON pe.enrollment_id=cr.enrollment_id JOIN program pr ON pr.program_id=pe.program_id WHERE pr.program_code='WW' AND cr.case_status='closed' AND cr.closed_date >= date_trunc('year',CURRENT_DATE)) AS completed,
        (SELECT COUNT(*) FROM activity a JOIN activity_type at ON at.activity_type_id=a.activity_type_id WHERE at.activity_name='WQ Referral Triggered') AS wq_referrals,
        (SELECT COUNT(*) FROM well WHERE active_flag=TRUE) AS total_wells
    `);
    res.json(r.rows[0]);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/ww/cases', async (req, res) => {
  try {
    const r = await pool.query(`
      SELECT cr.case_id, cr.opened_date, cr.closed_date, cr.case_status, cr.notes,
             p.pid, p.first_name, p.last_name,
             a.apn_number, c.county_name,
             st.first_name || ' ' || st.last_name AS assigned_staff
      FROM case_record cr
      JOIN program_enrollment pe ON pe.enrollment_id=cr.enrollment_id
      JOIN program pr ON pr.program_id=pe.program_id
      JOIN person p ON p.pid=pe.pid
      JOIN structure s ON s.structure_id=pe.structure_id
      JOIN apn a ON a.apn_id=s.apn_id
      JOIN county c ON c.county_id=a.county_id
      LEFT JOIN staff st ON st.staff_id=cr.assigned_staff_id
      WHERE pr.program_code='WW'
      ORDER BY cr.opened_date DESC
    `);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/ww/wells', async (req, res) => {
  const { type, county } = req.query;
  try {
    const conditions = ['w.active_flag=TRUE'];
    const params = [];
    if (type)   { params.push(type);   conditions.push(`w.well_type=$${params.length}`); }
    if (county) { params.push(county); conditions.push(`c.county_name=$${params.length}`); }
    const r = await pool.query(`
      SELECT w.well_id, w.well_number, w.well_type, w.depth_ft,
             w.static_water_level, w.drill_date,
             a.apn_number, c.county_name,
             COUNT(DISTINCT ws.structure_id) AS structures_served,
             v.vendor_name AS driller_name
      FROM well w
      JOIN apn a ON a.apn_id=w.apn_id
      JOIN county c ON c.county_id=a.county_id
      LEFT JOIN well_structure ws ON ws.well_id=w.well_id
      LEFT JOIN vendor v ON v.vendor_id=w.driller_id
      WHERE ${conditions.join(' AND ')}
      GROUP BY w.well_id,w.well_number,w.well_type,w.depth_ft,w.static_water_level,
               w.drill_date,a.apn_number,c.county_name,v.vendor_name
      ORDER BY w.well_id
    `, params);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/ww/drillers', async (req, res) => {
  try {
    const r = await pool.query(`
      SELECT v.vendor_id, v.vendor_name,
             COUNT(w.well_id) AS total_wells,
             AVG(w.depth_ft) AS avg_depth,
             STRING_AGG(DISTINCT c.county_name, ', ') AS counties_served
      FROM vendor v
      JOIN vendor_type vt ON vt.vendor_type_id=v.vendor_type_id
      LEFT JOIN well w ON w.driller_id=v.vendor_id
      LEFT JOIN apn a ON a.apn_id=w.apn_id
      LEFT JOIN county c ON c.county_id=a.county_id
      WHERE vt.type_name='Well Driller'
      GROUP BY v.vendor_id,v.vendor_name ORDER BY total_wells DESC
    `);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/ww/approvals', async (req, res) => {
  try {
    const r = await pool.query(`
      SELECT ap.approval_id, ap.submitted_date, ap.decision, ap.decision_notes,
             cr.case_id, p.pid, p.first_name, p.last_name, c.county_name,
             sub.first_name || ' ' || sub.last_name AS submitted_by_name
      FROM approval ap
      JOIN case_record cr ON cr.case_id=ap.case_id
      JOIN program_enrollment pe ON pe.enrollment_id=cr.enrollment_id
      JOIN program pr ON pr.program_id=pe.program_id
      JOIN person p ON p.pid=pe.pid
      JOIN structure s ON s.structure_id=pe.structure_id
      JOIN apn a ON a.apn_id=s.apn_id
      JOIN county c ON c.county_id=a.county_id
      LEFT JOIN staff sub ON sub.staff_id=ap.submitted_by
      WHERE pr.program_code='WW'
      ORDER BY ap.submitted_date DESC
    `);
    res.json(r.rows);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

// ── STAFF ────────────────────────────────────────────────────

app.get('/api/staff', async (req, res) => {
  try {
    const r = await pool.query(`
      SELECT staff_id, first_name, last_name, role, region_id,
             email, phone
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
});

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

// ── CASE STATUS ──────────────────────────────────────────────

app.get('/api/case/:case_id/status', async (req, res) => {
  const { case_id } = req.params;
  try {
    const r = await pool.query(`
      SELECT
        cr.case_id, cr.case_status, cr.opened_date, cr.closed_date, cr.notes,
        pe.enrollment_id, pe.status_secondary, pe.status_step, pe.wq_phase,
        pe.program_specific_id,
        es.status_name,
        pr.program_name, pr.program_code,
        p.pid, p.first_name, p.last_name,
        st.first_name || ' ' || st.last_name AS caseworker_name
      FROM case_record cr
      JOIN program_enrollment pe ON pe.enrollment_id = cr.enrollment_id
      JOIN enrollment_status es ON es.status_id = pe.status_id
      JOIN program pr ON pr.program_id = pe.program_id
      JOIN person p ON p.pid = pe.pid
      LEFT JOIN staff st ON st.staff_id = cr.assigned_staff_id
      WHERE cr.case_id = $1
    `, [case_id]);
    res.json(r.rows[0] || null);
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.post('/api/case/:case_id/status', async (req, res) => {
  const { case_id } = req.params;
  const { case_status, status_secondary, status_step, notes, staff_id } = req.body;
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    await client.query(`
      UPDATE case_record
      SET case_status = $1,
          notes = COALESCE($2, notes),
          closed_date = CASE WHEN $1 = 'closed' THEN CURRENT_DATE ELSE closed_date END
      WHERE case_id = $3
    `, [case_status, notes, case_id]);
    if (status_secondary || status_step) {
      await client.query(`
        UPDATE program_enrollment pe
        SET status_secondary = COALESCE($1, status_secondary),
            status_step = COALESCE($2, status_step)
        FROM case_record cr
        WHERE cr.enrollment_id = pe.enrollment_id AND cr.case_id = $3
      `, [status_secondary, status_step, case_id]);
    }
    await client.query('COMMIT');
    res.json({ success: true });
  } catch(err) {
    await client.query('ROLLBACK');
    res.status(500).json({ error: err.message });
  } finally { client.release(); }
});
