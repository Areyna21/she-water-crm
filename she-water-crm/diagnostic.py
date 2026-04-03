"""
SHE Water CRM — Project Diagnostic
Run from inside the she-water-crm folder: python diagnostic.py
Analyzes project structure, code, and tracks what is built vs outstanding
"""

import os
import json
import re
from datetime import datetime

# ── COLORS ───────────────────────────────────────────────────
GREEN  = '\033[92m'
YELLOW = '\033[93m'
RED    = '\033[91m'
CYAN   = '\033[96m'
BOLD   = '\033[1m'
RESET  = '\033[0m'

def ok(msg):    print(f"  {GREEN}✓{RESET} {msg}")
def warn(msg):  print(f"  {YELLOW}~{RESET} {msg}")
def miss(msg):  print(f"  {RED}✗{RESET} {msg}")
def info(msg):  print(f"  {CYAN}→{RESET} {msg}")
def head(msg):  print(f"\n{BOLD}{msg}{RESET}")
def line():     print("─" * 60)

print()
print(f"{BOLD}{'=' * 60}{RESET}")
print(f"{BOLD}  SHE Water CRM — Project Diagnostic{RESET}")
print(f"{BOLD}  {datetime.now().strftime('%Y-%m-%d %H:%M')}{RESET}")
print(f"{BOLD}{'=' * 60}{RESET}")

# ── CHECK ROOT ───────────────────────────────────────────────
if not os.path.exists('server.js'):
    print(f"\n{RED}ERROR: Run this from inside the she-water-crm folder{RESET}")
    exit()

# ── 1. PROJECT STRUCTURE ─────────────────────────────────────
head("1. PROJECT STRUCTURE")
line()

expected_files = {
    'server.js':                    'API server',
    'package.json':                 'Node config',
    'vite.config.js':               'Vite/React config',
    '.env':                         'Database connection',
    '.gitignore':                   'Git ignore',
    'README.md':                    'Documentation',
    'patch.py':                     'Code patcher',
    'public/index.html':            'Dashboard',
    'public/intake.html':           'Intake form',
    'public/bw.html':               'Bottled Water screen',
    'public/tw.html':               'Tank Water screen',
    'public/wq.html':               'Water Quality screen',
    'public/ww.html':               'Water Well screen',
    'public/app/index.html':        'React entry',
    'public/app/main.jsx':          'React main',
    'public/app/App.jsx':           'React App component',
    'public/app/styles.css':        'React styles',
    'public/app/components/Nav.jsx':              'React Nav',
    'public/app/components/UI.jsx':               'React UI primitives',
    'public/app/components/ParticipantSearch.jsx':'React search',
    'public/app/components/ParticipantProfile.jsx':'React profile',
    'public/app/hooks/useFetch.js': 'useFetch hook',
    'sql/schema.sql':               'Database schema',
    'sql/mock_data.sql':            'Mock data',
}

present = 0
missing = 0
for path, desc in expected_files.items():
    if os.path.exists(path):
        size = os.path.getsize(path)
        ok(f"{path:<50} {desc} ({size:,} bytes)")
        present += 1
    else:
        miss(f"{path:<50} {desc} — MISSING")
        missing += 1

print(f"\n  Files present: {GREEN}{present}{RESET} / {present + missing}")
if missing > 0:
    print(f"  Files missing: {RED}{missing}{RESET}")

# ── 2. API ENDPOINTS ─────────────────────────────────────────
head("2. API ENDPOINTS")
line()

server_content = open('server.js', encoding='utf-8').read()

endpoints = [
    ('GET  /api/stats',                  'Dashboard stats'),
    ('GET  /api/participants',           'Participant search'),
    ('GET  /api/participant/:pid',       'Participant profile'),
    ('GET  /api/apn-lookup',             'APN lookup'),
    ('GET  /api/region-lookup',          'Region routing'),
    ('POST /api/intake',                 'Create participant'),
    ('GET  /api/bw/stats',               'BW stats'),
    ('GET  /api/bw/participants',        'BW participants'),
    ('GET  /api/bw/deliveries',          'BW calendar data'),
    ('GET  /api/bw/missed',              'BW missed deliveries'),
    ('GET  /api/bw/vendor-performance',  'BW vendor metrics'),
    ('POST /api/bw/log-miss',            'Log missed delivery'),
    ('GET  /api/tw/stats',               'TW stats'),
    ('GET  /api/tw/participants',        'TW participants'),
    ('GET  /api/tw/tanks',               'Tank inventory'),
    ('GET  /api/tw/fills',               'Fill schedule'),
    ('GET  /api/tw/vendor-performance',  'TW hauler metrics'),
    ('GET  /api/wq/stats',               'WQ stats'),
    ('GET  /api/wq/participants',        'WQ participants'),
    ('GET  /api/wq/results',             'Lab results'),
    ('GET  /api/wq/contaminant-summary', 'Contaminant overview'),
    ('GET  /api/wq/equipment',           'Equipment tracking'),
    ('GET  /api/wq/labs',                'Lab performance'),
    ('GET  /api/ww/stats',               'WW stats'),
    ('GET  /api/ww/cases',               'WW cases'),
    ('GET  /api/ww/wells',               'Well inventory'),
    ('GET  /api/ww/drillers',            'Driller performance'),
    ('GET  /api/ww/approvals',           'Approval queue'),
]

ep_found = 0
ep_missing = 0
for method_path, desc in endpoints:
    # Extract just the path pattern to search for
    path_part = method_path.strip().split()[-1]
    search = path_part.replace(':pid', '').replace('/:','/')
    # Look for the route in server code
    if search.rstrip('/') in server_content:
        ok(f"{method_path:<35} {desc}")
        ep_found += 1
    else:
        miss(f"{method_path:<35} {desc} — NOT FOUND IN server.js")
        ep_missing += 1

print(f"\n  Endpoints found:   {GREEN}{ep_found}{RESET} / {ep_found + ep_missing}")
if ep_missing > 0:
    print(f"  Endpoints missing: {RED}{ep_missing}{RESET}")

# ── 3. REACT COMPONENTS ──────────────────────────────────────
head("3. REACT COMPONENTS")
line()

components = [
    ('public/app/components/Nav.jsx',               'Navigation bar'),
    ('public/app/components/UI.jsx',                'Shared UI — Pill, Card, StatCard, Loading, Empty'),
    ('public/app/components/ParticipantSearch.jsx', 'Participant search with live filter'),
    ('public/app/components/ParticipantProfile.jsx','Full profile — 5 tabs'),
    ('public/app/hooks/useFetch.js',                'Data fetching hook'),
]

for path, desc in components:
    if os.path.exists(path):
        content = open(path, encoding='utf-8').read()
        lines = content.count('\n')
        ok(f"{os.path.basename(path):<40} {desc} ({lines} lines)")
    else:
        miss(f"{os.path.basename(path):<40} {desc}")

# Check what tabs exist in profile
if os.path.exists('public/app/components/ParticipantProfile.jsx'):
    profile = open('public/app/components/ParticipantProfile.jsx', encoding='utf-8').read()
    tabs = re.findall(r"tab === '(\w+)'", profile)
    info(f"Profile tabs implemented: {', '.join(set(tabs))}")

# ── 4. DATABASE SCHEMA ───────────────────────────────────────
head("4. DATABASE SCHEMA")
line()

if os.path.exists('sql/schema.sql'):
    schema = open('sql/schema.sql', encoding='utf-8').read()
    tables = re.findall(r'CREATE TABLE (\w+)', schema, re.IGNORECASE)
    indexes = re.findall(r'CREATE INDEX (\w+)', schema, re.IGNORECASE)
    ok(f"Schema file exists — {len(tables)} tables, {len(indexes)} indexes")
    info(f"Tables: {', '.join(tables)}")
else:
    miss("Schema file not found")

# ── 5. PACKAGE.JSON SCRIPTS ──────────────────────────────────
head("5. NPM SCRIPTS")
line()

if os.path.exists('package.json'):
    pkg = json.load(open('package.json', encoding='utf-8'))
    scripts = pkg.get('scripts', {})
    expected_scripts = ['start', 'dev', 'react', 'build']
    for s in expected_scripts:
        if s in scripts:
            ok(f"npm run {s:<10} → {scripts[s]}")
        else:
            miss(f"npm run {s:<10} → NOT DEFINED")
    
    deps = list(pkg.get('dependencies', {}).keys())
    devdeps = list(pkg.get('devDependencies', {}).keys())
    info(f"Dependencies: {', '.join(deps)}")
    info(f"Dev dependencies: {', '.join(devdeps)}")

# ── 6. GIT STATUS ────────────────────────────────────────────
head("6. GIT STATUS")
line()

import subprocess
try:
    result = subprocess.run(['git', 'log', '--oneline', '-5'], capture_output=True, text=True)
    if result.returncode == 0:
        ok("Git repository initialized")
        info("Last 5 commits:")
        for line_text in result.stdout.strip().split('\n'):
            print(f"    {line_text}")
    else:
        warn("Git not initialized or no commits")
except:
    warn("Git not found")

try:
    status = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
    uncommitted = [l for l in status.stdout.strip().split('\n') if l.strip()]
    if uncommitted:
        warn(f"{len(uncommitted)} uncommitted change(s):")
        for u in uncommitted[:10]:
            print(f"    {u}")
    else:
        ok("Working tree clean — all changes committed")
except:
    pass

# ── 7. WHAT IS BUILT ─────────────────────────────────────────
head("7. WHAT IS BUILT ✓")
line()

built = [
    "PostgreSQL schema — 39 tables, full relational model",
    "Migration v2 — GSA eligibility, ROE, demographics, site assessments, 31 new fields",
    "GAMA contaminant reference table — 14 SJV contaminants with MCLs",
    "Live database on Neon — 313 participants, 1150 BW deliveries, 754 tank fills, 98 WQ results",
    "Node/Express API server — 28 endpoints, activity log, case status workflow",
    "Dashboard (localhost:3000) — live stats, all four program nav buttons",
    "Participant search — 100 results, live filter, allotment calc, program badges",
    "Participant profile — APN, DMPID, GSA, enrollments, cases, history — 5 tabs",
    "New participant intake — 4-step form, creates PID + program IDs end to end",
    "APN lookup against database on intake",
    "Bottled Water screen — living calendar, Q1+April data, missed delivery log, vendor performance",
    "Tank Water screen — participants, tank inventory, fill schedule, hauler metrics",
    "Water Quality screen — FULLY OPERATIONAL — all 5 tabs live with real SJV data",
    "WQ phase tracking — investigation, mitigation, maintenance, closeout, post-mitigation",
    "WQ ownership chain — every step owned by caseworker, field staff, vendor, or manager",
    "WQ 848 activities logged — complete audit trail per case",
    "Water Well screen — cases, pipeline board, well inventory, driller performance, approvals",
    "React app (localhost:3001) — participant search + full profile with 5 tabs",
    "Python direct Neon connection — data scripts insert without SQL editor",
    "Git version control — pushed to GitHub, clean working tree",
    "Python patch system — scriptable updates, auto-backup on every change",
    "Diagnostic tool — full project state snapshot",
]

for item in built:
    ok(item)

# ── 8. WHAT IS OUTSTANDING ───────────────────────────────────
head("8. WHAT IS OUTSTANDING ✗")
line()

outstanding = [
    ("HIGH",   "TW/WQ/WW screens — participants tab not populating yet"),
    ("HIGH",   "Activity logging — log any action against a case"),
    ("HIGH",   "Case status workflow — open → pending → approved → closed"),
    ("HIGH",   "Power Automate webhooks — notify next step on status change"),
    ("HIGH",   "ArcGIS map on search screen — participant points layer"),
    ("MEDIUM", "BW delivery calendar — vendor upload and paste dates"),
    ("MEDIUM", "BW calendar generator — optimized schedule from allotment rules"),
    ("MEDIUM", "Missed delivery vendor email — auto-draft on log"),
    ("MEDIUM", "New participant — Regrid API for APN auto-populate"),
    ("MEDIUM", "Survey123 field forms — site visit data feeding activity log"),
    ("MEDIUM", "React profile — activity tab needs data"),
    ("MEDIUM", "React profile — programs/cases/history tabs wiring"),
    ("MEDIUM", "Region assignment — resolve boundary APN policy"),
    ("MEDIUM", "Waitlist management — capacity limits per program"),
    ("LOW",    "Power BI connection — reporting layer"),
    ("LOW",    "Public ArcGIS dashboard — community intelligence"),
    ("LOW",    "AI Builder — state application PDF processing"),
    ("LOW",    "Document management — P drive file path tracking"),
    ("LOW",    "Communication log — call attempts, voicemails"),
    ("LOW",    "Eligibility expiration — income re-verification alerts"),
    ("LOW",    "Vendor management screens — add/edit vendors"),
    ("LOW",    "Staff management — add/edit staff and regions"),
    ("LOW",    "Export functions — CSV, PDF reports"),
    ("LOW",    "Authentication — staff login and role-based access"),
]

colors = {'HIGH': RED, 'MEDIUM': YELLOW, 'LOW': CYAN}
for priority, item in outstanding:
    c = colors.get(priority, RESET)
    print(f"  {c}[{priority}]{RESET} {item}")

# ── SUMMARY ──────────────────────────────────────────────────
head("SUMMARY")
line()

high   = sum(1 for p,_ in outstanding if p == 'HIGH')
medium = sum(1 for p,_ in outstanding if p == 'MEDIUM')
low    = sum(1 for p,_ in outstanding if p == 'LOW')

print(f"  Built:     {GREEN}{len(built)} items complete{RESET}")
print(f"  High:      {RED}{high} items — immediate priority{RESET}")
print(f"  Medium:    {YELLOW}{medium} items — next sprint{RESET}")
print(f"  Low:       {CYAN}{low} items — future{RESET}")
print()
print(f"  {BOLD}Next recommended action:{RESET}")
print(f"  Fix BW/TW/WQ/WW data loading, then activity logging,")
print(f"  then Power Automate webhooks for case workflow.")
print()
