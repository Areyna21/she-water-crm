"""
SHE Water CRM — Q1 + April Delivery Data
Connects directly to Neon and inserts delivery records
Run from inside she-water-crm: python insert_q1_data.py
"""

import os, random, shutil
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
import psycopg2

random.seed(77)

# ── READ .env MANUALLY ───────────────────────────────────────
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
db_url = None
if os.path.exists(env_path):
    for enc in ['utf-8', 'utf-16', 'utf-8-sig']:
        try:
            for line in open(env_path, encoding=enc):
                line = line.strip()
                if 'DATABASE_URL' in line and '=' in line:
                    db_url = line.split('=', 1)[1].strip()
                    break
            if db_url:
                break
        except:
            continue

if not db_url:
    print("ERROR: DATABASE_URL not found in .env file")
    exit()

# ── CONNECT ──────────────────────────────────────────────────
print()
print("=" * 55)
print("SHE Water CRM — Q1 + April Delivery Data Insert")
print("=" * 55)
print()

conn = psycopg2.connect(db_url)
cur  = conn.cursor()
print("  ✓ Connected to Neon")

# ── ALSO PATCH server.js STATS TO ROLLING 30 DAYS ───────────
shutil.copy2('server.js', f'backups/server.js.{datetime.now().strftime("%Y%m%d_%H%M%S")}.bak')
content = open('server.js', encoding='utf-8').read()

OLD_STATS = """    const now = new Date();
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
    `, [firstDay, lastDay]);"""

NEW_STATS = """    const result = await pool.query(`
      SELECT
        (SELECT COUNT(*) FROM program_enrollment pe
         JOIN program pr ON pr.program_id = pe.program_id
         WHERE pr.program_code = 'BW' AND pe.exit_date IS NULL) AS active,
        (SELECT COUNT(*) FROM delivery d
         JOIN program_enrollment pe ON pe.enrollment_id = d.enrollment_id
         JOIN program pr ON pr.program_id = pe.program_id
         WHERE pr.program_code = 'BW'
         AND d.scheduled_date >= CURRENT_DATE - INTERVAL '30 days') AS scheduled,
        (SELECT COUNT(*) FROM delivery d
         JOIN program_enrollment pe ON pe.enrollment_id = d.enrollment_id
         JOIN program pr ON pr.program_id = pe.program_id
         WHERE pr.program_code = 'BW' AND d.delivery_status = 'delivered'
         AND d.scheduled_date >= CURRENT_DATE - INTERVAL '30 days') AS delivered,
        (SELECT COUNT(*) FROM delivery d
         JOIN program_enrollment pe ON pe.enrollment_id = d.enrollment_id
         JOIN program pr ON pr.program_id = pe.program_id
         WHERE pr.program_code = 'BW' AND d.delivery_status = 'missed'
         AND d.scheduled_date >= CURRENT_DATE - INTERVAL '30 days') AS missed,
        (SELECT COUNT(*) FROM delivery d
         JOIN program_enrollment pe ON pe.enrollment_id = d.enrollment_id
         JOIN program pr ON pr.program_id = pe.program_id
         WHERE pr.program_code = 'BW' AND d.delivery_status = 'disputed'
         AND d.scheduled_date >= CURRENT_DATE - INTERVAL '30 days') AS disputed
    `);"""

if OLD_STATS in content:
    content = content.replace(OLD_STATS, NEW_STATS)
    open('server.js', 'w', encoding='utf-8').write(content)
    print("  ✓ server.js stats updated to rolling 30 days")
else:
    print("  ~ Stats already updated or pattern changed")

# ── GET ACTIVE BW ENROLLMENTS ────────────────────────────────
cur.execute("""
    SELECT pe.enrollment_id
    FROM program_enrollment pe
    JOIN program pr ON pr.program_id = pe.program_id
    WHERE pr.program_code = 'BW' AND pe.exit_date IS NULL
    ORDER BY pe.enrollment_id
    LIMIT 50
""")
enrollments = [row[0] for row in cur.fetchall()]
print(f"  ✓ Found {len(enrollments)} active BW enrollments")

# ── GET BW VENDOR IDS ─────────────────────────────────────────
cur.execute("""
    SELECT v.vendor_id FROM vendor v
    JOIN vendor_type vt ON vt.vendor_type_id = v.vendor_type_id
    WHERE vt.type_name = 'Bottled Water Delivery'
""")
vendor_ids = [row[0] for row in cur.fetchall()]
print(f"  ✓ Found {len(vendor_ids)} BW vendors")

# ── CHECK EXISTING DATES ──────────────────────────────────────
cur.execute("SELECT MIN(scheduled_date), MAX(scheduled_date), COUNT(*) FROM delivery")
row = cur.fetchone()
print(f"  → Existing deliveries: {row[2]} records ({row[0]} to {row[1]})")

# ── BUILD DELIVERY DATES ──────────────────────────────────────
statuses_hist = (
    ['delivered'] * 72 +
    ['missed']    * 13 +
    ['disputed']  * 8  +
    ['delivered'] * 7   # extra delivered weight
)
reasons = [
    'Vendor out of stock',
    'No access to property',
    'Route skipped',
    'Vendor capacity issue',
    'Weather delay',
    'Driver shortage',
]
reporters = ['participant', 'staff', 'vendor']

# Build schedule dates
schedule_dates = []

# January 2026 — biweekly starting Jan 6
d = date(2026, 1, 6)
while d.month == 1:
    schedule_dates.append(('historical', d))
    d += timedelta(weeks=2)

# February 2026 — biweekly
d = date(2026, 2, 3)
while d.month == 2:
    schedule_dates.append(('historical', d))
    d += timedelta(weeks=2)

# March 2026 — biweekly
d = date(2026, 3, 3)
while d.month == 3:
    schedule_dates.append(('historical', d))
    d += timedelta(weeks=2)

# April 2026 — biweekly (future/scheduled)
for april_d in [date(2026, 4, 1), date(2026, 4, 15), date(2026, 4, 29)]:
    schedule_dates.append(('future', april_d))

print(f"\n  Building delivery records:")
print(f"    Jan dates:   {sum(1 for t,_ in schedule_dates if _.month==1)}")
print(f"    Feb dates:   {sum(1 for t,_ in schedule_dates if _.month==2)}")
print(f"    Mar dates:   {sum(1 for t,_ in schedule_dates if _.month==3)}")
print(f"    Apr dates:   {sum(1 for t,_ in schedule_dates if _.month==4)}")
print(f"    Enrollments: {len(enrollments)}")

# ── INSERT DELIVERIES ─────────────────────────────────────────
inserted = 0
skipped  = 0

# Get existing enrollment+date combos to avoid duplicates
cur.execute("SELECT enrollment_id, scheduled_date FROM delivery")
existing = set((r[0], r[1]) for r in cur.fetchall())

rows_to_insert = []
for enrollment_id in enrollments:
    vendor_id  = random.choice(vendor_ids)
    allotment  = random.choice([20, 40, 50, 60])

    for dtype, sched in schedule_dates:
        if (enrollment_id, sched) in existing:
            skipped += 1
            continue

        if dtype == 'future':
            status         = 'scheduled'
            delivered_date = None
            missed_reason  = None
            reported_by    = None
        else:
            status = random.choice(statuses_hist)
            delivered_date = sched + timedelta(days=random.randint(0,2)) if status == 'delivered' else None
            missed_reason  = random.choice(reasons) if status in ('missed','disputed') else None
            reported_by    = random.choice(reporters) if status in ('missed','disputed') else None

        rows_to_insert.append((
            enrollment_id, vendor_id, sched, delivered_date,
            allotment, status, missed_reason, reported_by
        ))

print(f"\n  Inserting {len(rows_to_insert)} records ({skipped} duplicates skipped)...")

cur.executemany("""
    INSERT INTO delivery
        (enrollment_id, vendor_id, scheduled_date, delivered_date,
         allotment_units, delivery_status, missed_reason, reported_by)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
""", rows_to_insert)

inserted = len(rows_to_insert)
conn.commit()

# Reset sequence
cur.execute("SELECT setval('delivery_delivery_id_seq', (SELECT MAX(delivery_id) FROM delivery))")
conn.commit()

# ── VERIFY ───────────────────────────────────────────────────
cur.execute("""
    SELECT
        EXTRACT(MONTH FROM scheduled_date) AS month,
        COUNT(*) AS total,
        SUM(CASE WHEN delivery_status='delivered' THEN 1 ELSE 0 END) AS delivered,
        SUM(CASE WHEN delivery_status='missed'    THEN 1 ELSE 0 END) AS missed,
        SUM(CASE WHEN delivery_status='disputed'  THEN 1 ELSE 0 END) AS disputed,
        SUM(CASE WHEN delivery_status='scheduled' THEN 1 ELSE 0 END) AS scheduled
    FROM delivery
    WHERE scheduled_date >= '2026-01-01'
    GROUP BY 1 ORDER BY 1
""")
rows = cur.fetchall()

months = {1:'January',2:'February',3:'March',4:'April'}
print(f"\n  Q1 + April summary:")
for row in rows:
    m = months.get(int(row[0]), str(row[0]))
    print(f"    {m:<10} total:{row[1]:>4}  delivered:{row[2]:>4}  missed:{row[3]:>3}  disputed:{row[4]:>3}  scheduled:{row[5]:>4}")

cur.execute("SELECT COUNT(*) FROM delivery")
total = cur.fetchone()[0]
print(f"\n  Total delivery records in database: {total}")

conn.close()

print()
print("=" * 55)
print(f"Done. {inserted} records inserted.")
print()
print("Restart server:  npx kill-port 3000 && npm start")
print()
print("Commit:")
print('  git add .')
print('  git commit -m "Q1+April delivery data, rolling 30d stats"')
print('  git push')