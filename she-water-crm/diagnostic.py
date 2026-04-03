"""
SHE Water CRM — Full System Diagnostic
Tests project structure, git, AND live API endpoints + database
Run from inside she-water-crm: python diagnostic.py
"""

import os, json, re, subprocess
from datetime import datetime

GREEN  = '\033[92m'
YELLOW = '\033[93m'
RED    = '\033[91m'
CYAN   = '\033[96m'
BOLD   = '\033[1m'
RESET  = '\033[0m'

def ok(msg):   print(f"  {GREEN}✓{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}~{RESET} {msg}")
def fail(msg): print(f"  {RED}✗{RESET} {msg}")
def info(msg): print(f"  {CYAN}→{RESET} {msg}")
def head(msg): print(f"\n{BOLD}{msg}{RESET}")
def line():    print("─" * 60)

print()
print(f"{BOLD}{'=' * 60}{RESET}")
print(f"{BOLD}  SHE Water CRM — Full System Diagnostic{RESET}")
print(f"{BOLD}  {datetime.now().strftime('%Y-%m-%d %H:%M')}{RESET}")
print(f"{BOLD}{'=' * 60}{RESET}")

if not os.path.exists('server.js'):
    print(f"\n{RED}ERROR: Run from inside the she-water-crm folder{RESET}")
    exit()

# 1. FILES
head("1. PROJECT FILES")
line()
files = {
    'server.js':'API server','package.json':'Node config','vite.config.js':'Vite config',
    '.env':'DB connection','public/index.html':'Dashboard','public/intake.html':'Intake',
    'public/bw.html':'BW screen','public/tw.html':'TW screen','public/wq.html':'WQ screen',
    'public/ww.html':'WW screen','public/activity.html':'Activity log',
    'public/app/App.jsx':'React App','public/app/components/ParticipantSearch.jsx':'React search',
    'public/app/components/ParticipantProfile.jsx':'React profile',
    'sql/schema.sql':'Schema','sql/mock_data.sql':'Mock data',
}
present = missing = 0
for path, desc in files.items():
    if os.path.exists(path):
        ok(f"{path:<52} {desc} ({os.path.getsize(path):,}b)")
        present += 1
    else:
        fail(f"{path:<52} {desc} — MISSING")
        missing += 1
print(f"\n  {GREEN}{present} present{RESET}" + (f", {RED}{missing} missing{RESET}" if missing else ""))

# 2. GIT
head("2. GIT STATUS")
line()
try:
    log = subprocess.run(['git','log','--oneline','-5'],capture_output=True,text=True)
    ok("Git initialized")
    for l in log.stdout.strip().split('\n'): info(l)
    status = subprocess.run(['git','status','--short'],capture_output=True,text=True)
    u = [l for l in status.stdout.strip().split('\n') if l.strip()]
    if u:
        warn(f"{len(u)} uncommitted change(s):")
        for x in u[:8]: print(f"    {x}")
    else:
        ok("Working tree clean")
except: warn("Git check failed")

# 3. DATABASE
head("3. DATABASE — TABLE COUNTS")
line()
db_url = None
if os.path.exists('.env'):
    for enc in ['utf-8','utf-16','utf-8-sig']:
        try:
            for l in open('.env',encoding=enc):
                if 'DATABASE_URL' in l and '=' in l:
                    db_url = l.split('=',1)[1].strip()
                    break
            if db_url: break
        except: continue

if not db_url:
    fail("DATABASE_URL not found in .env")
else:
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        ok("Connected to Neon")
        tables = [
            ('person','Participants'),('program_enrollment','Enrollments'),
            ('case_record','Cases'),('delivery','BW Deliveries'),
            ('tank_fill','TW Tank Fills'),('water_quality_result','WQ Results'),
            ('sample_point','Sample Points'),('equipment','Equipment'),
            ('approval','Approvals'),('activity','Activities'),
            ('well','Wells'),('staff','Staff'),('vendor','Vendors'),
            ('communication_log','Comm Log'),('contaminant_reference','Contaminants'),
        ]
        print()
        for table, label in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                c = GREEN if count > 0 else RED
                print(f"  {c}{'✓' if count>0 else '✗'}{RESET} {label:<28} {CYAN}{count:>6}{RESET} records")
            except Exception as e:
                fail(f"{label:<28} ERROR: {e}")

        print()
        cur.execute("""
            SELECT pe.wq_phase, pe.status_step, COUNT(*) n
            FROM program_enrollment pe JOIN program pr ON pr.program_id=pe.program_id
            WHERE pr.program_code='WQ' AND pe.exit_date IS NULL AND pe.wq_phase IS NOT NULL
            GROUP BY 1,2 ORDER BY n DESC
        """)
        rows = cur.fetchall()
        if rows:
            info("WQ phase distribution:")
            for r in rows: print(f"    {str(r[0]):<22} {str(r[1]):<28} n={r[2]}")

        cur.execute("SELECT MIN(scheduled_date),MAX(scheduled_date),COUNT(*) FROM delivery")
        r = cur.fetchone()
        if r and r[2]:
            print()
            info(f"BW deliveries: {r[2]} total | {r[0]} → {r[1]}")

        conn.close()
    except Exception as e:
        fail(f"DB error: {e}")

# 4. LIVE API
head("4. LIVE API ENDPOINT TESTS")
line()
try:
    import urllib.request, urllib.error
    BASE = 'http://127.0.0.1:3000'
    endpoints = [
        ('/api/stats','Dashboard stats'),
        ('/api/participants?q=','Participant search'),
        ('/api/participant/PID-0001','Participant profile'),
        ('/api/bw/stats','BW stats'),
        ('/api/bw/participants','BW participants'),
        ('/api/bw/deliveries?year=2026&month=4','BW April deliveries'),
        ('/api/bw/missed?days=30','BW missed'),
        ('/api/bw/vendor-performance','BW vendor perf'),
        ('/api/tw/stats','TW stats'),
        ('/api/tw/participants','TW participants'),
        ('/api/tw/tanks','TW tanks'),
        ('/api/tw/fills','TW fills'),
        ('/api/tw/vendor-performance','TW vendor perf'),
        ('/api/wq/stats','WQ stats'),
        ('/api/wq/participants','WQ participants'),
        ('/api/wq/results','WQ results'),
        ('/api/wq/contaminant-summary','WQ contaminants'),
        ('/api/wq/equipment','WQ equipment'),
        ('/api/wq/labs','WQ labs'),
        ('/api/ww/stats','WW stats'),
        ('/api/ww/cases','WW cases'),
        ('/api/ww/wells','WW wells'),
        ('/api/ww/drillers','WW drillers'),
        ('/api/ww/approvals','WW approvals'),
        ('/api/activity-types','Activity types'),
        ('/api/staff','Staff list'),
        ('/api/queue/1','Queue staff 1'),
        ('/api/case/1/status','Case 1 status'),
        ('/api/case/1/activities','Case 1 activities'),
    ]
    passed = failed = empty = 0
    for path, desc in endpoints:
        try:
            req = urllib.request.Request(BASE+path)
            with urllib.request.urlopen(req,timeout=5) as resp:
                data = json.loads(resp.read())
                count = len(data) if isinstance(data,list) else (1 if data else 0)
                if count == 0:
                    warn(f"{desc:<35} 200 OK — {YELLOW}EMPTY (no data){RESET}")
                    empty += 1
                else:
                    ok(f"{desc:<35} {GREEN}{count} record(s){RESET}")
                    passed += 1
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:80]
            fail(f"{desc:<35} HTTP {e.code} — {body}")
            failed += 1
        except urllib.error.URLError:
            fail(f"{desc:<35} {RED}Cannot connect to 127.0.0.1:3000{RESET}")
            failed += 1
        except Exception as e:
            fail(f"{desc:<35} {str(e)[:50]}")
            failed += 1

    print(f"\n  {GREEN}{passed} passed{RESET}  {YELLOW}{empty} empty{RESET}  {RED}{failed} failed{RESET}")
    if failed > 0:
        print(f"\n  {RED}Failed endpoints need fixing before building more features{RESET}")
    if empty > 0:
        print(f"\n  {YELLOW}Empty endpoints have working routes but missing/broken data joins{RESET}")

except Exception as e:
    warn(f"API test error: {e}")

# 5. SERVER ANALYSIS
head("5. SERVER.JS ANALYSIS")
line()
server = open('server.js',encoding='utf-8').read()
gets  = len(re.findall(r"app\.get\(",server))
posts = len(re.findall(r"app\.post\(",server))
ok(f"server.js: {os.path.getsize('server.js'):,} bytes  |  {gets} GET routes  |  {posts} POST routes")

bw_idx = server.find("'/api/bw/participants'")
if bw_idx > 0:
    bw_block = server[bw_idx:bw_idx+1200]
    if 'v.vendor_name' in bw_block and 'JOIN vendor v' not in bw_block:
        fail("BW participants: v.vendor_name used without JOIN vendor — will 500")
    elif 'v.vendor_id' in bw_block and 'JOIN vendor v' not in bw_block:
        fail("BW participants: v.vendor_id used without JOIN vendor — will 500")
    else:
        ok("BW participants query looks clean")
else:
    warn("BW participants endpoint not found in server.js")

# 6. BUILT
head("6. WHAT IS BUILT ✓")
line()
built = [
    "PostgreSQL schema — 39 tables, full relational model",
    "Migration v2 — GSA, ROE, demographics, site assessments, 31 new fields",
    "GAMA contaminant reference — 14 SJV contaminants with MCLs",
    "Neon database — 313 participants, 1150 BW deliveries, 754 TW fills, 98 WQ results",
    "Node/Express API — 30+ endpoints across all programs",
    "Dashboard — live stats, all program nav buttons including Activity Log",
    "Participant search — live filter, allotment, program badges",
    "Participant profile React — 5 tabs, APN, DMPID, GSA, enrollments",
    "New participant intake — 4-step form, creates PID + program IDs",
    "Bottled Water screen — calendar, Q1+April data, missed log, vendor perf",
    "Tank Water screen — participants, tanks, fills, haulers",
    "Water Quality screen — REFERENCE IMPLEMENTATION — all 5 tabs live",
    "WQ ownership chain — 848 activities, every step has an owner",
    "WQ phase tracking — investigation/mitigation/maintenance/closeout",
    "Water Well screen — cases, pipeline, wells, drillers, approvals",
    "Activity Log + My Queue screen — log activities, advance status_step",
    "Python direct Neon connection — data scripts bypass SQL editor",
    "Git version control — GitHub",
    "Python patch + diagnostic system",
]
for item in built: ok(item)

# 7. OUTSTANDING
head("7. OUTSTANDING ✗")
line()
outstanding = [
    ("HIGH",   "BW participants — query keeps breaking, needs permanent fix"),
    ("HIGH",   "Activity queue — needs data to show cases in queue"),
    ("HIGH",   "WQ screen — show wq_phase + status_step in participants tab"),
    ("HIGH",   "TW participants — confirm loading or fix join"),
    ("HIGH",   "Case workflow — advance button to move phase forward"),
    ("MEDIUM", "React profile — activity tab wired to live data"),
    ("MEDIUM", "React profile — programs/cases/history tabs fully wired"),
    ("MEDIUM", "TW/WW full program data — match WQ standard"),
    ("MEDIUM", "ArcGIS map — participant points on search screen"),
    ("MEDIUM", "BW calendar — vendor upload/paste delivery dates"),
    ("MEDIUM", "Power Automate webhooks — notify on status change"),
    ("MEDIUM", "Regrid API — APN auto-populate on intake"),
    ("MEDIUM", "Survey123 — site visit data to activity log"),
    ("MEDIUM", "Waitlist management screen"),
    ("LOW",    "Authentication — Microsoft SSO"),
    ("LOW",    "Power BI connection"),
    ("LOW",    "Export — CSV, PDF reports"),
    ("LOW",    "Document management — P drive paths"),
    ("LOW",    "Vendor/Staff management screens"),
    ("LOW",    "Deployment — Railway or Azure"),
]
colors = {'HIGH':RED,'MEDIUM':YELLOW,'LOW':CYAN}
for p, item in outstanding:
    print(f"  {colors[p]}[{p}]{RESET} {item}")

head("SUMMARY")
line()
high   = sum(1 for p,_ in outstanding if p=='HIGH')
medium = sum(1 for p,_ in outstanding if p=='MEDIUM')
low    = sum(1 for p,_ in outstanding if p=='LOW')
print(f"  Built:   {GREEN}{len(built)} items{RESET}")
print(f"  HIGH:    {RED}{high} — fix before building more{RESET}")
print(f"  MEDIUM:  {YELLOW}{medium} — next sprint{RESET}")
print(f"  LOW:     {CYAN}{low} — future{RESET}")
print()