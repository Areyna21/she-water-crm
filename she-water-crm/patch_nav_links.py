"""
SHE Water CRM — Navigation Link Patch
Makes participant rows clickable across all screens
Run from inside she-water-crm: python patch_nav_links.py
"""

import os, shutil
from datetime import datetime

def backup(f):
    os.makedirs('backups', exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(f, f'backups/{os.path.basename(f)}.{ts}.bak')
    return f'backups/{os.path.basename(f)}.{ts}.bak'

def patch(filepath, replacements):
    if not os.path.exists(filepath):
        print(f"  ✗ {filepath} not found")
        return 0
    bak = backup(filepath)
    content = open(filepath, encoding='utf-8').read()
    applied = 0
    for old, new, label in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"  ✓ {label}")
            applied += 1
        else:
            print(f"  ~ {label} — pattern not found")
    open(filepath, 'w', encoding='utf-8').write(content)
    return applied

OPEN_PROFILE = """
  function openProfile(pid) {
    if (!pid || pid === '—') return;
    window.open('http://localhost:3001/?pid=' + pid, '_blank');
  }
"""

print()
print("=" * 55)
print("SHE Water CRM — Navigation Links")
print("=" * 55)

# ── BW.HTML ──────────────────────────────────────────────────
print("\nbw.html:")
patch('public/bw.html', [
    (
        "  function formatDate",
        OPEN_PROFILE + "  function formatDate",
        "Added openProfile function"
    ),
    (
        # Participants table row
        """            <tr class="clickable">
              <td class="pid-cell">${p.pid}</td>""",
        """            <tr class="clickable" onclick="openProfile('${p.pid}')">
              <td class="pid-cell">${p.pid}</td>""",
        "Participants row clickable"
    ),
    (
        # Missed deliveries row
        """              <td class="pid-cell">${e.pid || '—'}</td>""",
        """              <td class="pid-cell" onclick="openProfile('${e.pid}')" style="cursor:pointer;">${e.pid || '—'}</td>""",
        "Missed delivery PID clickable"
    ),
    (
        # Calendar day detail row
        """              <td class="pid-cell">${d.pid || '—'}</td>""",
        """              <td class="pid-cell" onclick="openProfile('${d.pid}')" style="cursor:pointer;">${d.pid || '—'}</td>""",
        "Calendar detail PID clickable"
    ),
])

# ── TW.HTML ──────────────────────────────────────────────────
print("\ntw.html:")
patch('public/tw.html', [
    (
        "  function formatDate",
        OPEN_PROFILE + "  function formatDate",
        "Added openProfile function"
    ),
    (
        """      <tbody>${data.map(p => `<tr class=\"clickable\">
        <td class=\"pid-cell\">${p.pid}</td>""",
        """      <tbody>${data.map(p => `<tr class=\"clickable\" onclick=\"openProfile('${p.pid}')\" >
        <td class=\"pid-cell\">${p.pid}</td>""",
        "Participants row clickable"
    ),
])

# ── WQ.HTML ──────────────────────────────────────────────────
print("\nwq.html:")
patch('public/wq.html', [
    (
        "  function filterParticipants",
        OPEN_PROFILE + "  function filterParticipants",
        "Added openProfile function"
    ),
    (
        # String concat version in wq.html
        "'<tr class=\"clickable\">' +",
        "'<tr class=\"clickable\" onclick=\"openProfile(\\'' + p.pid + '\\')\">' +",
        "Participants row clickable (string concat)"
    ),
    (
        # Lab results row
        """        <tbody>${data.map(r => `<tr>
          <td class="mono">${formatDate(r.sample_date)}</td>
          <td class="pid-cell">${r.pid||'—'}</td>""",
        """        <tbody>${data.map(r => `<tr class="clickable" onclick="openProfile('${r.pid}')">
          <td class="mono">${formatDate(r.sample_date)}</td>
          <td class="pid-cell">${r.pid||'—'}</td>""",
        "Lab results row clickable"
    ),
    (
        # Equipment row
        """          <td class="pid-cell">${e.pid||'—'}</td>""",
        """          <td class="pid-cell" onclick="openProfile('${e.pid}')" style="cursor:pointer;">${e.pid||'—'}</td>""",
        "Equipment PID clickable"
    ),
])

# ── WW.HTML ──────────────────────────────────────────────────
print("\nww.html:")
patch('public/ww.html', [
    (
        "  function formatDate",
        OPEN_PROFILE + "  function formatDate",
        "Added openProfile function"
    ),
    (
        # Cases table row
        """      <tbody>${data.map(c => `<tr class="clickable">
        <td class="mono">#${c.case_id}</td>
        <td class="pid-cell">${c.pid||'—'}</td>""",
        """      <tbody>${data.map(c => `<tr class="clickable" onclick="openProfile('${c.pid}')">
        <td class="mono">#${c.case_id}</td>
        <td class="pid-cell">${c.pid||'—'}</td>""",
        "Cases row clickable"
    ),
    (
        # Pipeline cards
        """          <span class="pid-cell">${c.pid}</span>""",
        """          <span class="pid-cell" onclick="openProfile('${c.pid}')" style="cursor:pointer;">${c.pid}</span>""",
        "Pipeline card PID clickable"
    ),
    (
        # Approvals row
        """          <td class="pid-cell">${a.pid||'—'}</td>""",
        """          <td class="pid-cell" onclick="openProfile('${a.pid}')" style="cursor:pointer;">${a.pid||'—'}</td>""",
        "Approvals PID clickable"
    ),
])

# ── ACTIVITY.HTML ─────────────────────────────────────────────
print("\nactivity.html:")
patch('public/activity.html', [
    (
        "  function showToast",
        OPEN_PROFILE + "  function showToast",
        "Added openProfile function"
    ),
    (
        # Queue item - add PID click
        """      <div class="queue-pid">${c.pid}</div>""",
        """      <div class="queue-pid" onclick="event.stopPropagation(); openProfile('${c.pid}')" style="cursor:pointer;text-decoration:underline;">${c.pid}</div>""",
        "Queue PID clickable"
    ),
])

# ── INDEX.HTML - Add React app link ──────────────────────────
print("\nindex.html:")
patch('public/index.html', [
    (
        "  function showPage",
        OPEN_PROFILE + "  function showPage",
        "Added openProfile function"
    ),
])

print()
print("=" * 55)
print("Done.")
print()
print("No server restart needed — just refresh the browser.")
print()
print("Test:")
print("  1. Open http://localhost:3000/wq.html")
print("  2. Click any row in the participants tab")
print("  3. React profile opens at localhost:3001 with that PID")
print()
print("Commit:")
print('  git add .')
print('  git commit -m "participant row navigation — all screens link to React profile"')
print('  git push')
