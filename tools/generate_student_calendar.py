"""Generate a simple weekly calendar HTML for a student's enrolled units.

Usage:
    python tools/generate_student_calendar.py <username> --out <path>

Reads `data/students.json` and `data/units.json` in the repo root. Expects SemesterOffering
information (meeting_day, meeting_time, class_hours) to be present in unit.offerings entries
and that the student enrollments reference unit codes and semester/year matching the offerings.

The script writes a static HTML file with a Monday-Friday hourly grid (08:00-18:00) and
plots each unit's weekly class as a block spanning the class_hours starting at meeting_time.
If the student has no enrollments the HTML will indicate this.
"""
import sys
import os
import json
from datetime import datetime, timedelta


def load_json(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def time_to_hour_min(tstr):
    # expects HH:MM
    try:
        h, m = map(int, tstr.split(':'))
        return h, m
    except Exception:
        return 9, 0


def generate_html(username, out_path):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    students_path = os.path.join(repo_root, 'data', 'students.json')
    units_path = os.path.join(repo_root, 'data', 'units.json')

    students = load_json(students_path)
    units = load_json(units_path)

    student = next((s for s in students if s.get('username') == username), None)
    if not student:
        print(f"User not found in {students_path}: {username}")
        return

    enrolls = student.get('enrollments', [])

    # Build offering lookup by unit_code -> offering with meeting info (prefer 2026 S1)
    offering_map = {}
    for u in units:
        code = u.get('code')
        for off in u.get('offerings', []):
            if off.get('year') == 2026 and off.get('semester') == 'S1':
                offering_map[code] = off
                break

    # Collect scheduled items for this student
    scheduled = []
    for e in enrolls:
        ucode = e.get('unit_code')
        off = offering_map.get(ucode)
        if not off:
            continue
        ch = off.get('class_hours', 3)
        day = off.get('meeting_day', 'Mon')
        t = off.get('meeting_time', '09:00')
        scheduled.append({'code': ucode, 'hours': ch, 'day': day, 'time': t})

    html_lines = []
    html_lines.append('<!doctype html>')
    html_lines.append('<html><head><meta charset="utf-8"><title>Student Calendar</title>')
    html_lines.append('<style>body{font-family:Arial,sans-serif}table.calendar{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:8px;text-align:center;height:60px}th{background:#f4f4f4} .slot{background:#cfe9ff;border-radius:4px;padding:4px}</style>')
    html_lines.append('</head><body>')
    html_lines.append(f'<h2>Weekly calendar for {student.get("full_name","")} ({username})</h2>')

    if not scheduled:
        html_lines.append('<p><em>No enrollments with schedule found for this student.</em></p>')
        html_lines.append('<p>If you want a preview timetable, enroll the student into offerings or ensure `enrollments` in `data/students.json` contains unit_code/year/semester entries.</p>')
        html_lines.append('</body></html>')
        with open(out_path, 'w', encoding='utf-8') as fo:
            fo.write('\n'.join(html_lines))
        print(f'Wrote calendar to {out_path}')
        return

    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    # hours from 8 to 18
    hours = list(range(8, 19))

    # build grid with empty cells
    cell_map = { (d,h): [] for d in days for h in hours }

    for item in scheduled:
        d = item['day']
        h,m = time_to_hour_min(item['time'])
        start = h
        for hr in range(start, start + int(item['hours'])):
            if (d, hr) in cell_map:
                cell_map[(d, hr)].append(item)

    # Write table header
    html_lines.append('<table class="calendar"><thead><tr><th>Time</th>')
    for d in days:
        html_lines.append(f'<th>{d}</th>')
    html_lines.append('</tr></thead><tbody>')

    for h in hours:
        html_lines.append(f'<tr><th>{h:02d}:00</th>')
        for d in days:
            items = cell_map.get((d,h), [])
            if items:
                cell_text = ''
                for it in items:
                    cell_text += f"<div class=\"slot\"><strong>{it['code']}</strong><br/>{it['hours']}h</div>"
                html_lines.append(f'<td>{cell_text}</td>')
            else:
                html_lines.append('<td></td>')
        html_lines.append('</tr>')

    html_lines.append('</tbody></table>')
    html_lines.append('</body></html>')

    with open(out_path, 'w', encoding='utf-8') as fo:
        fo.write('\n'.join(html_lines))

    print(f'Wrote calendar to {out_path}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python tools/generate_student_calendar.py <username> [--out out.html]')
        sys.exit(1)
    username = sys.argv[1]
    out = None
    if '--out' in sys.argv:
        idx = sys.argv.index('--out')
        if idx+1 < len(sys.argv):
            out = sys.argv[idx+1]
    if not out:
        out = os.path.join(os.path.dirname(__file__), f'../data/calendar_{username}.html')
        out = os.path.abspath(out)

    generate_html(username, out)
