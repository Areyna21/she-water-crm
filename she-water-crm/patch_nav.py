"""
Patch Nav.jsx to use correct port for dashboard and program links
Run from inside she-water-crm folder: python patch_nav.py
"""
import os, shutil
from datetime import datetime

def backup(f):
    os.makedirs('backups', exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(f, f'backups/{os.path.basename(f)}.{ts}.bak')
    print(f"  ✓ Backup created")

NAV_FILE = os.path.join('public','app','components','Nav.jsx')

OLD = '''            <a href="/" style={{...btn, textDecoration:'none'}}>Dashboard</a>
            <a href="/bw.html" style={{...btn, textDecoration:'none', color:'var(--bw)'}}>BW</a>
            <a href="/tw.html" style={{...btn, textDecoration:'none', color:'var(--tw)'}}>TW</a>
            <a href="/wq.html" style={{...btn, textDecoration:'none', color:'var(--wq)'}}>WQ</a>
            <a href="/ww.html" style={{...btn, textDecoration:'none', color:'var(--ww)'}}>WW</a>'''

NEW = '''            <a href="http://localhost:3000" style={{...btn, textDecoration:'none'}}>Dashboard</a>
            <a href="http://localhost:3000/bw.html" style={{...btn, textDecoration:'none', color:'var(--bw)'}}>BW</a>
            <a href="http://localhost:3000/tw.html" style={{...btn, textDecoration:'none', color:'var(--tw)'}}>TW</a>
            <a href="http://localhost:3000/wq.html" style={{...btn, textDecoration:'none', color:'var(--wq)'}}>WQ</a>
            <a href="http://localhost:3000/ww.html" style={{...btn, textDecoration:'none', color:'var(--ww)'}}>WW</a>'''

if not os.path.exists(NAV_FILE):
    print(f"ERROR: {NAV_FILE} not found. Run from inside she-water-crm folder.")
    exit()

backup(NAV_FILE)
content = open(NAV_FILE, encoding='utf-8').read()

if OLD in content:
    content = content.replace(OLD, NEW)
    open(NAV_FILE, 'w', encoding='utf-8').write(content)
    print("  ✓ Nav links updated to use correct ports")
else:
    print("  ~ Pattern not found — may already be patched")

print()
print("Done. Vite will hot reload automatically.")
print("No restart needed.")
