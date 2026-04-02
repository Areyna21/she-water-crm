"""
SHE Water CRM — Water Quality Program Full Build
Generates complete WQ case data with ownership chain
Every step belongs to someone. Ball is always in one court.
Run from inside she-water-crm: python build_wq_program.py
"""

import os, random, json
from datetime import date, timedelta, datetime
import psycopg2

random.seed(42)

# ── CONNECT ──────────────────────────────────────────────────
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
db_url = None
for enc in ['utf-8', 'utf-16', 'utf-8-sig']:
    try:
        for line in open(env_path, encoding=enc):
            if 'DATABASE_URL' in line and '=' in line:
                db_url = line.split('=', 1)[1].strip()
                break
        if db_url: break
    except: continue

if not db_url:
    print("ERROR: DATABASE_URL not found in .env")
    exit()

conn = psycopg2.connect(db_url)
cur  = conn.cursor()
print()
print("=" * 60)
print("SHE Water CRM — WQ Program Full Build")
print("=" * 60)
print()
print("  ✓ Connected to Neon")

# ── STEP 1: ADD MISSING GAMA CONTAMINANTS ────────────────────
print("\nStep 1: Adding GAMA contaminants...")

contaminants_to_add = [
    ('DBCP',        0.2,    'ug/L',  'Agricultural pesticide legacy — SJV specific'),
    ('Manganese',   50.0,   'ug/L',  'Naturally occurring — secondary MCL'),
    ('Fluoride',    2.0,    'mg/L',  'Naturally occurring'),
    ('PFAS',        None,   'ng/L',  'Emerging contaminant — no current CA MCL'),
    ('TCP-123',     0.005,  'ug/L',  '1,2,3-Trichloropropane — industrial SJV'),
    ('Nitrite',     1.0,    'mg/L',  'Agricultural runoff'),
    ('Perchlorate', 6.0,    'ug/L',  'Industrial/agricultural'),
    ('Molybdenum',  None,   'ug/L',  'Naturally occurring — monitoring only'),
]

# Add reference table for contaminant MCLs
cur.execute("""
    CREATE TABLE IF NOT EXISTS contaminant_reference (
        contaminant_id   SERIAL PRIMARY KEY,
        name             VARCHAR(100) NOT NULL UNIQUE,
        mcl_value        DECIMAL(18,6),
        unit             VARCHAR(20),
        description      TEXT,
        gama_tracked     BOOLEAN DEFAULT TRUE,
        active_flag      BOOLEAN DEFAULT TRUE,
        created_date     TIMESTAMP DEFAULT NOW()
    )
""")

# Seed all contaminants including existing ones
all_contaminants = [
    ('Arsenic',              10.0,   'ug/L',  'Naturally occurring — widespread SJV'),
    ('Nitrate',              10.0,   'mg/L',  'Agricultural — most common SJV'),
    ('Hexavalent Chromium',  10.0,   'ug/L',  'New MCL October 2024'),
    ('Uranium',              20.0,   'ug/L',  'Naturally occurring'),
    ('Lead',                 15.0,   'ug/L',  'Infrastructure related'),
    ('Total Coliform',        0.0,   'MPN',   'Bacteriological'),
    ('1,2,3-TCP',             0.005, 'ug/L',  'Industrial — Fresno/Kern/Tulare'),
    ('DBCP',                  0.2,   'ug/L',  'Agricultural pesticide legacy — SJV'),
    ('Manganese',            50.0,   'ug/L',  'Naturally occurring — secondary MCL'),
    ('Fluoride',              2.0,   'mg/L',  'Naturally occurring'),
    ('PFAS',                 None,   'ng/L',  'Emerging — no current CA MCL'),
    ('Nitrite',               1.0,   'mg/L',  'Agricultural runoff'),
    ('Perchlorate',           6.0,   'ug/L',  'Industrial/agricultural'),
    ('Molybdenum',           None,   'ug/L',  'Naturally occurring — monitoring'),
]

for name, mcl, unit, desc in all_contaminants:
    cur.execute("""
        INSERT INTO contaminant_reference (name, mcl_value, unit, description)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (name) DO NOTHING
    """, (name, mcl, unit, desc))

conn.commit()
print(f"  ✓ {len(all_contaminants)} contaminants in reference table")

# ── STEP 2: ADD WQ ACTIVITY TYPES ────────────────────────────
print("\nStep 2: Adding WQ workflow activity types...")

wq_activity_types = [
    # (name, category, triggers_next, owner_role)
    ('WQ Application Sent',             'intake',    False, 'caseworker'),
    ('WQ Application Received',         'intake',    True,  'caseworker'),
    ('WQ ID Created',                   'intake',    True,  'caseworker'),
    ('WQ Visit Scheduled',              'field',     True,  'caseworker'),
    ('WQ Initial Site Visit Completed', 'field',     True,  'field_staff'),
    ('Sample Collection Attempted',     'lab',       True,  'field_staff'),
    ('Unable to Collect Sample',        'lab',       True,  'field_staff'),
    ('Sampling Issue Resolved',         'lab',       True,  'caseworker'),
    ('Sample Delivered to Lab',         'lab',       True,  'field_staff'),
    ('Lab Results Received',            'lab',       True,  'caseworker'),
    ('Results Pass — First Sample',     'lab',       True,  'caseworker'),
    ('Results Pass — Retest',           'lab',       True,  'caseworker'),
    ('Results Fail',                    'lab',       True,  'caseworker'),
    ('Participant Notified — Pass',     'intake',    True,  'caseworker'),
    ('Participant Notified — Fail',     'intake',    True,  'caseworker'),
    ('Closeout Appointment Scheduled',  'intake',    True,  'caseworker'),
    ('Closeout Review Completed',       'approval',  True,  'caseworker'),
    ('WQ ID Closed',                    'intake',    False, 'region_manager'),
    ('Mitigation Planning Started',     'approval',  True,  'caseworker'),
    ('Mitigation Plan Approved',        'approval',  True,  'region_manager'),
    ('POU Installation Scheduled',      'field',     True,  'caseworker'),
    ('POU Installation Job Completed',  'field',     True,  'vendor'),
    ('POE Installation Scheduled',      'field',     True,  'caseworker'),
    ('POE Installation Job Completed',  'field',     True,  'vendor'),
    ('Sanitization Scheduled',          'field',     True,  'caseworker'),
    ('Sanitization Job Completed',      'field',     True,  'vendor'),
    ('Post-Mitigation Sample Scheduled','lab',       True,  'caseworker'),
    ('Post-Mitigation Sample Collected','lab',       True,  'field_staff'),
    ('Post-Mitigation Results Received','lab',       True,  'caseworker'),
    ('Active Maintenance Phase Entered','intake',    False, 'caseworker'),
    ('Annual Maintenance Retest Scheduled','lab',   True,  'caseworker'),
    ('Annual Maintenance Retest Completed','lab',   True,  'field_staff'),
    ('Maintenance Period Ended',        'intake',    True,  'caseworker'),
    ('Maintenance End Notification Sent','intake',  True,  'caseworker'),
    ('Program Closeout Review',         'approval',  True,  'caseworker'),
]

# Get WQ program ID
cur.execute("SELECT program_id FROM program WHERE program_code = 'WQ'")
wq_program_id = cur.fetchone()[0]

# Add activity types
added = 0
for name, category, triggers, owner in wq_activity_types:
    cur.execute("""
        SELECT activity_type_id FROM activity_type WHERE activity_name = %s
    """, (name,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO activity_type (program_id, activity_name, activity_category, triggers_next_step)
            VALUES (%s, %s, %s, %s)
        """, (wq_program_id, name, category, triggers))
        added += 1

conn.commit()
print(f"  ✓ Added {added} WQ activity types")

# Get all WQ activity type IDs
cur.execute("""
    SELECT activity_type_id, activity_name
    FROM activity_type WHERE program_id = %s OR program_id IS NULL
""", (wq_program_id,))
at_map = {row[1]: row[0] for row in cur.fetchall()}

# ── STEP 3: ADD WQ PHASE TO ENROLLMENT ───────────────────────
print("\nStep 3: Ensuring wq_phase column exists...")
cur.execute("""
    ALTER TABLE program_enrollment
    ADD COLUMN IF NOT EXISTS wq_phase VARCHAR(50)
""")
conn.commit()
print("  ✓ wq_phase column ready")

# ── STEP 4: LOAD STAFF BY REGION AND ROLE ────────────────────
print("\nStep 4: Loading staff roster...")

cur.execute("""
    SELECT staff_id, first_name, last_name, role, region_id
    FROM staff WHERE active_flag = TRUE
""")
all_staff = cur.fetchall()

def get_staff(role, region_id):
    matches = [s for s in all_staff if s[3] == role and s[4] == region_id]
    if matches: return random.choice(matches)[0]
    matches = [s for s in all_staff if s[3] == role]
    return random.choice(matches)[0] if matches else all_staff[0][0]

def get_caseworker(region_id):  return get_staff('caseworker', region_id)
def get_field_staff(region_id): return get_staff('field_staff', region_id)
def get_manager(region_id):     return get_staff('region_manager', region_id)

print(f"  ✓ {len(all_staff)} staff loaded")

# ── STEP 5: LOAD WQ ENROLLMENTS ──────────────────────────────
print("\nStep 5: Loading WQ enrollments...")

cur.execute("""
    SELECT pe.enrollment_id, pe.pid, pe.structure_id, pe.caseworker_id,
           a.region_id, pe.program_specific_id,
           pe.enrollment_date
    FROM program_enrollment pe
    JOIN program pr ON pr.program_id = pe.program_id
    JOIN structure s ON s.structure_id = pe.structure_id
    JOIN apn a ON a.apn_id = s.apn_id
    WHERE pr.program_code = 'WQ' AND pe.exit_date IS NULL
    ORDER BY pe.enrollment_id
""")
wq_enrollments = cur.fetchall()
print(f"  ✓ {len(wq_enrollments)} active WQ enrollments")

# Get sample points
cur.execute("SELECT sample_point_id, point_type_id FROM sample_point")
sample_points = cur.fetchall()

# Get labs
cur.execute("""
    SELECT v.vendor_id FROM vendor v
    JOIN vendor_type vt ON vt.vendor_type_id = v.vendor_type_id
    WHERE vt.type_name = 'Water Quality Lab'
""")
labs = [r[0] for r in cur.fetchall()]

# Get WQ equipment vendors (labs do installations too in some cases)
cur.execute("SELECT vendor_id FROM vendor WHERE vendor_type_id IN (1,2,3,4)")
all_vendors = [r[0] for r in cur.fetchall()]

# ── STEP 6: CONTAMINANT WEIGHTS FOR SJV ──────────────────────
sjv_contaminants = [
    ('Nitrate',              10.0,  'mg/L',  0.35),
    ('Arsenic',              10.0,  'ug/L',  0.25),
    ('Hexavalent Chromium',  10.0,  'ug/L',  0.15),
    ('1,2,3-TCP',             0.005,'ug/L',  0.08),
    ('DBCP',                  0.2,  'ug/L',  0.05),
    ('Uranium',              20.0,  'ug/L',  0.05),
    ('Manganese',            50.0,  'ug/L',  0.04),
    ('Fluoride',              2.0,  'mg/L',  0.02),
    ('PFAS',                 None,  'ng/L',  0.01),
]

def pick_contaminant():
    weights = [c[3] for c in sjv_contaminants]
    total   = sum(weights)
    r = random.random() * total
    cumulative = 0
    for cont in sjv_contaminants:
        cumulative += cont[3]
        if r <= cumulative:
            return cont[0], cont[1], cont[2]
    return sjv_contaminants[0][:3]

# ── STEP 7: PHASE ASSIGNMENT ──────────────────────────────────
# Assign phases to enrollments
phases = (
    ['investigation_scheduled']  * 8 +
    ['investigation_sampling']   * 6 +
    ['first_pass_closeout']      * 5 +
    ['maintenance_active']       * 10 +
    ['mitigation_pou']           * 5 +
    ['mitigation_poe']           * 4 +
    ['mitigation_sanitization']  * 2 +
    ['post_mitigation_sampling'] * 4
)

# Pad or trim to match enrollment count
while len(phases) < len(wq_enrollments):
    phases.append(random.choice(['maintenance_active', 'investigation_scheduled', 'mitigation_pou']))
phases = phases[:len(wq_enrollments)]
random.shuffle(phases)

# ── STEP 8: BUILD ACTIVITY TRAILS ────────────────────────────
print("\nStep 6: Building activity trails and case records...")

def days_ago(n): return date.today() - timedelta(days=n)
def days_from(d, n): return d + timedelta(days=n)

def log_activity(case_id, activity_name, performed_by, activity_date, notes, next_step=False):
    if activity_name not in at_map:
        return
    cur.execute("""
        INSERT INTO activity (case_id, activity_type_id, performed_by, activity_date, notes, next_step_triggered)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (case_id, at_map[activity_name], performed_by, activity_date, notes, next_step))

def insert_wq_result(sample_point_id, contaminant, mcl, unit, exceeds, lab_id, sample_date):
    if exceeds:
        if mcl:
            value = round(mcl * random.uniform(1.1, 3.0), 4)
        else:
            value = round(random.uniform(10, 50), 4)
    else:
        if mcl:
            value = round(mcl * random.uniform(0.05, 0.85), 4)
        else:
            value = round(random.uniform(0.1, 5.0), 4)

    result_date = sample_date + timedelta(days=random.randint(7, 21))
    cur.execute("""
        INSERT INTO water_quality_result
            (sample_point_id, vendor_id, contaminant, value, unit,
             mcl_value, exceeds_mcl_flag, sample_date, result_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING result_id
    """, (sample_point_id, lab_id, contaminant, value, unit,
          mcl, exceeds, sample_date, result_date))
    return cur.fetchone()[0], value, result_date

def get_or_create_sample_point(structure_id, point_type_id, well_id=None):
    cur.execute("""
        SELECT sample_point_id FROM sample_point
        WHERE structure_id = %s AND point_type_id = %s
        LIMIT 1
    """, (structure_id, point_type_id))
    row = cur.fetchone()
    if row: return row[0]
    cur.execute("""
        INSERT INTO sample_point (point_type_id, well_id, structure_id, location_description)
        VALUES (%s, %s, %s, %s) RETURNING sample_point_id
    """, (point_type_id, well_id, structure_id,
          'Point of entry at meter' if point_type_id == 1 else 'Kitchen sink fixture'))
    return cur.fetchone()[0]

cases_built = 0
activities_built = 0

for i, enrollment in enumerate(wq_enrollments):
    enroll_id, pid, structure_id, caseworker_id, region_id, prog_id, enroll_date = enrollment
    phase = phases[i]

    cw  = caseworker_id or get_caseworker(region_id)
    fs  = get_field_staff(region_id)
    mgr = get_manager(region_id)
    lab = random.choice(labs) if labs else 1

    # Get case record
    cur.execute("""
        SELECT case_id FROM case_record WHERE enrollment_id = %s LIMIT 1
    """, (enroll_id,))
    case_row = cur.fetchone()
    if not case_row:
        continue
    case_id = case_row[0]

    contaminant, mcl, unit = pick_contaminant()

    # ── Base intake activities (all phases) ──────────────────
    intake_date = days_ago(random.randint(30, 180))

    log_activity(case_id, 'WQ Application Sent',     cw, intake_date,
                 f"Application mailed to participant {pid}.", True)
    log_activity(case_id, 'WQ Application Received', cw, days_from(intake_date, random.randint(3,10)),
                 "Application received with proof of income and address.", True)
    log_activity(case_id, 'WQ ID Created',           cw, days_from(intake_date, random.randint(1,3)),
                 f"WQ ID assigned: {prog_id}.", True)

    visit_date = days_from(intake_date, random.randint(7, 21))
    log_activity(case_id, 'WQ Visit Scheduled',      cw, days_from(intake_date, 5),
                 f"Initial WQ site visit scheduled for {visit_date}.", True)

    activities_built += 4

    # ── PHASE: INVESTIGATION SCHEDULED ───────────────────────
    if phase == 'investigation_scheduled':
        cur.execute("""
            UPDATE program_enrollment SET wq_phase = %s, status_secondary = %s, status_step = %s
            WHERE enrollment_id = %s
        """, ('investigation', 'Initial Visit Scheduled', 'field_visit_scheduled', enroll_id))
        cur.execute("""
            UPDATE case_record SET case_status = 'open', notes = %s WHERE case_id = %s
        """, (f"WQ visit scheduled. Awaiting field staff completion. Ball: Field Staff.", case_id))

    # ── PHASE: INVESTIGATION — SAMPLING ──────────────────────
    elif phase == 'investigation_sampling':
        log_activity(case_id, 'WQ Initial Site Visit Completed', fs, visit_date,
                     f"Site visit completed. Well assessed. Sample collection attempted.", True)
        sample_date = days_from(visit_date, 1)

        # 15% chance unable to collect on first attempt
        if random.random() < 0.15:
            log_activity(case_id, 'Unable to Collect Sample', fs, visit_date,
                         "Unable to access well. Gate locked. Left notice.", True)
            log_activity(case_id, 'Sampling Issue Resolved',  cw, days_from(visit_date, 3),
                         "Contacted participant. Access arranged for reschedule.", True)
            activities_built += 2

        log_activity(case_id, 'Sample Collection Attempted', fs, sample_date,
                     f"Sample collected from well head. Contaminant of concern: {contaminant}.", True)
        log_activity(case_id, 'Sample Delivered to Lab',     fs, days_from(sample_date, 1),
                     f"Sample delivered to lab. Lab ID: {lab}.", True)

        cur.execute("""
            UPDATE program_enrollment SET wq_phase = %s, status_secondary = %s, status_step = %s
            WHERE enrollment_id = %s
        """, ('investigation', 'Sample at Lab', 'awaiting_lab_results', enroll_id))
        cur.execute("""
            UPDATE case_record SET case_status = 'open', notes = %s WHERE case_id = %s
        """, ("Sample collected and at lab. Awaiting results. Ball: Lab.", case_id))
        activities_built += 2

    # ── PHASE: FIRST PASS → CLOSEOUT ─────────────────────────
    elif phase == 'first_pass_closeout':
        log_activity(case_id, 'WQ Initial Site Visit Completed', fs, visit_date,
                     "Site visit completed. Sample collected.", True)
        log_activity(case_id, 'Sample Collection Attempted',     fs, visit_date,
                     f"Sample collected. Contaminant tested: {contaminant}.", True)
        log_activity(case_id, 'Sample Delivered to Lab',         fs, days_from(visit_date, 1),
                     "Sample delivered to lab.", True)

        sample_date   = visit_date
        sp_id         = get_or_create_sample_point(structure_id, 3)
        result_id, value, result_date = insert_wq_result(sp_id, contaminant, mcl, unit, False, lab, sample_date)

        log_activity(case_id, 'Lab Results Received',            cw, result_date,
                     f"{contaminant} result: {value} {unit}. Below MCL. Results PASS.", True)
        log_activity(case_id, 'Results Pass — First Sample',     cw, days_from(result_date, 1),
                     f"First sample passed. No maintenance phase required per protocol.", True)
        log_activity(case_id, 'Participant Notified — Pass',     cw, days_from(result_date, 2),
                     "Participant notified of passing results by phone.", True)
        log_activity(case_id, 'Closeout Appointment Scheduled',  cw, days_from(result_date, 3),
                     "Closeout appointment scheduled to review results with participant.", True)

        cur.execute("""
            UPDATE program_enrollment SET wq_phase = %s, status_secondary = %s, status_step = %s
            WHERE enrollment_id = %s
        """, ('closeout', 'First Pass — Closeout Pending', 'closeout_scheduled', enroll_id))
        cur.execute("""
            UPDATE case_record SET case_status = 'open', notes = %s WHERE case_id = %s
        """, ("Results passed on first sample. Closeout appointment scheduled. Ball: Caseworker.", case_id))
        activities_built += 7

    # ── PHASE: MAINTENANCE ACTIVE ─────────────────────────────
    elif phase == 'maintenance_active':
        log_activity(case_id, 'WQ Initial Site Visit Completed', fs, visit_date,
                     "Site visit completed. Initial sample collected.", True)
        log_activity(case_id, 'Sample Delivered to Lab',         fs, days_from(visit_date, 1),
                     "Sample delivered to lab.", True)

        # Initial result — passed
        sp_id = get_or_create_sample_point(structure_id, 3)
        result_id, value, result_date = insert_wq_result(sp_id, contaminant, mcl, unit, False, lab, visit_date)

        log_activity(case_id, 'Lab Results Received',            cw, result_date,
                     f"Initial results: {contaminant} {value} {unit}. PASS.", True)
        log_activity(case_id, 'Results Pass — First Sample',     cw, days_from(result_date, 1),
                     "Results passed. Entering active maintenance phase.", True)
        log_activity(case_id, 'Active Maintenance Phase Entered',cw, days_from(result_date, 2),
                     "Participant enrolled in 3-year annual maintenance monitoring.", False)

        # One annual retest already done
        retest_date = days_from(result_date, random.randint(300, 400))
        if retest_date < date.today():
            log_activity(case_id, 'Annual Maintenance Retest Scheduled', cw, days_from(retest_date, -14),
                         "Annual retest scheduled.", True)
            log_activity(case_id, 'Annual Maintenance Retest Completed', fs, retest_date,
                         f"Annual retest sample collected. Contaminant: {contaminant}.", True)
            retest_result_id, retest_value, retest_result_date = insert_wq_result(
                sp_id, contaminant, mcl, unit, False, lab, retest_date)
            log_activity(case_id, 'Results Pass — Retest', cw, retest_result_date,
                         f"Annual retest: {contaminant} {retest_value} {unit}. PASS. Maintenance continues.", True)
            activities_built += 3

        cur.execute("""
            UPDATE program_enrollment SET wq_phase = %s, status_secondary = %s, status_step = %s
            WHERE enrollment_id = %s
        """, ('maintenance', 'Active Maintenance', 'maintenance_monitoring', enroll_id))
        cur.execute("""
            UPDATE case_record SET case_status = 'open', notes = %s WHERE case_id = %s
        """, ("In active maintenance phase. Annual retesting required. Ball: Caseworker.", case_id))
        activities_built += 6

    # ── PHASE: MITIGATION — POU ───────────────────────────────
    elif phase == 'mitigation_pou':
        log_activity(case_id, 'WQ Initial Site Visit Completed', fs, visit_date, "Site visit completed.", True)
        log_activity(case_id, 'Sample Delivered to Lab',         fs, days_from(visit_date, 1), "Sample delivered.", True)

        sp_id = get_or_create_sample_point(structure_id, 2)  # POU
        result_id, value, result_date = insert_wq_result(sp_id, contaminant, mcl, unit, True, lab, visit_date)

        log_activity(case_id, 'Lab Results Received',        cw, result_date,
                     f"{contaminant} EXCEEDS MCL: {value} {unit} (MCL: {mcl}). Action required.", True)
        log_activity(case_id, 'Results Fail',                cw, days_from(result_date, 1),
                     f"Results failed. {contaminant} at {value} {unit}. Mitigation required.", True)
        log_activity(case_id, 'Participant Notified — Fail', cw, days_from(result_date, 2),
                     "Participant notified of failing results. Mitigation options explained.", True)
        log_activity(case_id, 'Mitigation Planning Started', cw, days_from(result_date, 3),
                     "Mitigation plan initiated. POU treatment recommended for kitchen/drinking water.", True)
        log_activity(case_id, 'Mitigation Plan Approved',    mgr, days_from(result_date, 7),
                     "POU mitigation plan approved by region manager.", True)
        log_activity(case_id, 'POU Installation Scheduled',  cw, days_from(result_date, 10),
                     "POU unit installation scheduled with vendor.", True)

        cur.execute("""
            UPDATE program_enrollment SET wq_phase = %s, status_secondary = %s, status_step = %s
            WHERE enrollment_id = %s
        """, ('mitigation', 'POU Mitigation', 'vendor_scheduled', enroll_id))
        cur.execute("""
            UPDATE case_record SET case_status = 'open', notes = %s WHERE case_id = %s
        """, (f"POU mitigation scheduled. {contaminant} exceeded MCL at {value} {unit}. Ball: Vendor.", case_id))
        activities_built += 8

    # ── PHASE: MITIGATION — POE ───────────────────────────────
    elif phase == 'mitigation_poe':
        log_activity(case_id, 'WQ Initial Site Visit Completed', fs, visit_date, "Site visit completed.", True)
        log_activity(case_id, 'Sample Delivered to Lab',         fs, days_from(visit_date, 1), "Sample delivered.", True)

        sp_id = get_or_create_sample_point(structure_id, 1)  # POE
        result_id, value, result_date = insert_wq_result(sp_id, contaminant, mcl, unit, True, lab, visit_date)

        log_activity(case_id, 'Lab Results Received',        cw, result_date,
                     f"{contaminant} EXCEEDS MCL: {value} {unit}. Whole-house treatment needed.", True)
        log_activity(case_id, 'Results Fail',                cw, days_from(result_date, 1),
                     "Results failed. POE whole-house treatment recommended.", True)
        log_activity(case_id, 'Participant Notified — Fail', cw, days_from(result_date, 2),
                     "Participant notified. POE treatment explained.", True)
        log_activity(case_id, 'Mitigation Planning Started', cw, days_from(result_date, 3),
                     "POE mitigation plan initiated.", True)
        log_activity(case_id, 'Mitigation Plan Approved',    mgr, days_from(result_date, 7),
                     "POE mitigation approved.", True)
        log_activity(case_id, 'POE Installation Scheduled',  cw, days_from(result_date, 10),
                     "POE unit installation scheduled.", True)

        cur.execute("""
            UPDATE program_enrollment SET wq_phase = %s, status_secondary = %s, status_step = %s
            WHERE enrollment_id = %s
        """, ('mitigation', 'POE Mitigation', 'vendor_scheduled', enroll_id))
        cur.execute("""
            UPDATE case_record SET case_status = 'open', notes = %s WHERE case_id = %s
        """, (f"POE mitigation scheduled. {contaminant} at {value} {unit}. Ball: Vendor.", case_id))
        activities_built += 7

    # ── PHASE: MITIGATION — SANITIZATION ─────────────────────
    elif phase == 'mitigation_sanitization':
        log_activity(case_id, 'WQ Initial Site Visit Completed', fs, visit_date, "Site visit completed.", True)
        log_activity(case_id, 'Sample Delivered to Lab',         fs, days_from(visit_date, 1), "Sample delivered.", True)

        sp_id = get_or_create_sample_point(structure_id, 3)  # Well
        result_id, value, result_date = insert_wq_result(
            sp_id, 'Total Coliform', 0.0, 'MPN', True, lab, visit_date)

        log_activity(case_id, 'Lab Results Received',        cw, result_date,
                     "Total Coliform detected. Bacteriological contamination. Sanitization required.", True)
        log_activity(case_id, 'Results Fail',                cw, days_from(result_date, 1),
                     "Coliform positive. Sanitization mitigation initiated.", True)
        log_activity(case_id, 'Participant Notified — Fail', cw, days_from(result_date, 1),
                     "Participant notified. Bottled water provided immediately as bridge.", True)
        log_activity(case_id, 'Mitigation Planning Started', cw, days_from(result_date, 2),
                     "Sanitization plan initiated. Vendor to shock well.", True)
        log_activity(case_id, 'Mitigation Plan Approved',    mgr, days_from(result_date, 4),
                     "Sanitization approved. Emergency protocol.", True)
        log_activity(case_id, 'Sanitization Scheduled',      cw, days_from(result_date, 5),
                     "Sanitization job scheduled with vendor.", True)

        cur.execute("""
            UPDATE program_enrollment SET wq_phase = %s, status_secondary = %s, status_step = %s
            WHERE enrollment_id = %s
        """, ('mitigation', 'Sanitization', 'vendor_scheduled', enroll_id))
        cur.execute("""
            UPDATE case_record SET case_status = 'open', notes = %s WHERE case_id = %s
        """, ("Sanitization job scheduled. Coliform detected. Ball: Vendor.", case_id))
        activities_built += 7

    # ── PHASE: POST-MITIGATION SAMPLING ──────────────────────
    elif phase == 'post_mitigation_sampling':
        log_activity(case_id, 'WQ Initial Site Visit Completed', fs, visit_date, "Initial site visit done.", True)
        log_activity(case_id, 'Sample Delivered to Lab',         fs, days_from(visit_date, 1), "Initial sample delivered.", True)

        sp_type = random.choice([1, 2])  # POE or POU
        sp_id   = get_or_create_sample_point(structure_id, sp_type)
        result_id, value, result_date = insert_wq_result(sp_id, contaminant, mcl, unit, True, lab, visit_date)

        log_activity(case_id, 'Lab Results Received',             cw, result_date,
                     f"{contaminant} exceeded MCL at {value} {unit}. Mitigation completed.", True)
        log_activity(case_id, 'Results Fail',                     cw, days_from(result_date, 1),
                     "Initial results failed. Treatment installed.", True)
        log_activity(case_id, 'Mitigation Plan Approved',         mgr, days_from(result_date, 7),
                     "Mitigation approved.", True)

        install_date = days_from(result_date, random.randint(10, 21))
        etype = 'POE' if sp_type == 1 else 'POU'
        log_activity(case_id, f'{etype} Installation Job Completed', random.choice(all_vendors) if all_vendors else cw,
                     install_date, f"{etype} unit installed. Post-mitigation sample to follow.", True)

        # Insert equipment record
        makes = [('Watts','OneFlow OF-1'),('Pentair','WS48-56SXT'),('Everpure','H-300 ROM')]
        make, model = random.choice(makes)
        next_svc = install_date + timedelta(days=365)
        cur.execute("""
            INSERT INTO equipment (sample_point_id, equipment_type, make, model, install_date, next_service_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (sp_id, etype, make, model, install_date, next_svc))

        post_sample_date = days_from(install_date, random.randint(7, 21))
        log_activity(case_id, 'Post-Mitigation Sample Scheduled',  cw, days_from(install_date, 2),
                     "Post-mitigation sample scheduled to verify treatment effectiveness.", True)
        log_activity(case_id, 'Post-Mitigation Sample Collected',   fs, post_sample_date,
                     f"Post-mitigation sample collected. {etype} treatment in place.", True)

        # Post-mitigation result — should pass now
        pm_result_id, pm_value, pm_result_date = insert_wq_result(
            sp_id, contaminant, mcl, unit, False, lab, post_sample_date)

        log_activity(case_id, 'Post-Mitigation Results Received',   cw, pm_result_date,
                     f"Post-mitigation: {contaminant} at {pm_value} {unit}. PASS. Treatment effective.", True)

        cur.execute("""
            UPDATE program_enrollment SET wq_phase = %s, status_secondary = %s, status_step = %s
            WHERE enrollment_id = %s
        """, ('post_mitigation', 'Post-Mitigation Verification', 'results_received', enroll_id))
        cur.execute("""
            UPDATE case_record SET case_status = 'open', notes = %s WHERE case_id = %s
        """, (f"Post-mitigation results received. Treatment verified effective. Ball: Caseworker.", case_id))
        activities_built += 9

    cases_built += 1

conn.commit()
print(f"  ✓ {cases_built} cases built with activity trails")
print(f"  ✓ {activities_built} activities logged")

# ── STEP 9: VERIFY ───────────────────────────────────────────
print("\nStep 7: Verifying...")

cur.execute("""
    SELECT pe.wq_phase, pe.status_secondary, pe.status_step, COUNT(*) as count
    FROM program_enrollment pe
    JOIN program pr ON pr.program_id = pe.program_id
    WHERE pr.program_code = 'WQ' AND pe.exit_date IS NULL
    GROUP BY pe.wq_phase, pe.status_secondary, pe.status_step
    ORDER BY pe.wq_phase, count DESC
""")
rows = cur.fetchall()
print(f"\n  WQ Phase Distribution:")
for row in rows:
    print(f"    {str(row[0]):<25} {str(row[1]):<35} {str(row[2]):<30} n={row[3]}")

cur.execute("SELECT COUNT(*) FROM water_quality_result")
wqr_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM equipment")
equip_count = cur.fetchone()[0]

cur.execute("""
    SELECT COUNT(*) FROM activity a
    JOIN case_record cr ON cr.case_id = a.case_id
    JOIN program_enrollment pe ON pe.enrollment_id = cr.enrollment_id
    JOIN program pr ON pr.program_id = pe.program_id
    WHERE pr.program_code = 'WQ'
""")
wq_activity_count = cur.fetchone()[0]

cur.execute("""
    SELECT contaminant, COUNT(*) as tests,
           SUM(CASE WHEN exceeds_mcl_flag THEN 1 ELSE 0 END) as failed
    FROM water_quality_result
    GROUP BY contaminant ORDER BY tests DESC
""")
cont_rows = cur.fetchall()

print(f"\n  WQ Results:    {wqr_count}")
print(f"  Equipment:     {equip_count}")
print(f"  WQ Activities: {wq_activity_count}")
print(f"\n  Contaminant breakdown:")
for row in cont_rows:
    rate = round((row[2]/row[1])*100) if row[1] > 0 else 0
    print(f"    {str(row[0]):<25} tests:{row[1]:>3}  failed:{row[2]:>3}  fail rate:{rate}%")

cur.execute("""
    SELECT pe.status_step, COUNT(*) as cases,
           STRING_AGG(DISTINCT st.role, ', ') as ball_with
    FROM program_enrollment pe
    JOIN program pr ON pr.program_id = pe.program_id
    LEFT JOIN case_record cr ON cr.enrollment_id = pe.enrollment_id
    LEFT JOIN staff st ON st.staff_id = cr.assigned_staff_id
    WHERE pr.program_code = 'WQ' AND pe.exit_date IS NULL
    GROUP BY pe.status_step ORDER BY cases DESC
""")
queue_rows = cur.fetchall()
print(f"\n  Case queue by status_step:")
for row in queue_rows:
    print(f"    {str(row[0]):<35} cases:{row[1]:>3}")

conn.commit()
conn.close()

print()
print("=" * 60)
print("WQ Program build complete.")
print()
print("Restart server: npx kill-port 3000 && npm start")
print()
print("Commit:")
print('  git add .')
print('  git commit -m "WQ full program build — phases, ownership chain, GAMA contaminants"')
print('  git push')
