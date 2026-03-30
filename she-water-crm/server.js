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
