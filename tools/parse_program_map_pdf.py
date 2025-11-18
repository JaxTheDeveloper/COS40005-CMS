"""
Lightweight PDF parser to extract unit codes/names and student names from a program map PDF.

Usage:
  python tools/parse_program_map_pdf.py <pdf_path> [--out-dir data]

Notes:
- This is heuristic and may not extract perfectly from complex PDFs. Please review
  the generated JSON files before seeding the database.
- It tries to use pdfplumber or PyPDF2 (fallback). Install pdfplumber for best results:
    pip install pdfplumber
  or ensure PyPDF2 is available.
"""
from __future__ import annotations
import sys
import os
import re
import json
import unicodedata
from typing import List

try:
    import pdfplumber
    _HAS_PDFPLUMBER = True
except Exception:
    _HAS_PDFPLUMBER = False

try:
    import PyPDF2
    _HAS_PYPDF2 = True
except Exception:
    _HAS_PYPDF2 = False


UNIT_CODE_RE = re.compile(r"\b([A-Z]{2,4}\s?-?\d{3,4})\b")


def normalize_text(s: str) -> str:
    s = s.strip()
    # remove multiple spaces
    s = re.sub(r"\s+", " ", s)
    return s


def remove_diacritics(s: str) -> str:
    nkfd = unicodedata.normalize('NFKD', s)
    return ''.join([c for c in nkfd if not unicodedata.combining(c)])


def extract_text_from_pdf(path: str) -> str:
    if _HAS_PDFPLUMBER:
        texts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                texts.append(page.extract_text() or '')
        return '\n'.join(texts)
    elif _HAS_PYPDF2:
        reader = PyPDF2.PdfReader(path)
        texts = []
        for p in reader.pages:
            try:
                texts.append(p.extract_text() or '')
            except Exception:
                texts.append('')
        return '\n'.join(texts)
    else:
        raise RuntimeError('No PDF parser available. Install pdfplumber or PyPDF2.')


def find_units(text: str) -> List[dict]:
    units = {}
    lines = [normalize_text(l) for l in text.splitlines() if l.strip()]
    for i, line in enumerate(lines):
        for m in UNIT_CODE_RE.finditer(line):
            code = m.group(1).replace(' ', '').replace('-', '').upper()
            # try to get a name from the rest of the line after the code
            rest = line[m.end():].strip(' -:')
            name = rest
            if not name and i + 1 < len(lines):
                # maybe name on next line
                name = lines[i+1]
            name = normalize_text(name)
            if code not in units:
                units[code] = {'code': code, 'name': name, 'description': '', 'credit_points': 10, 'prerequisites': [], 'anti_requisites': [], 'offerings': []}
    return list(units.values())


def find_names(text: str) -> List[dict]:
    # Heuristic: names are lines with 2-4 words, no digits, and not all-caps unit codes
    names = []
    seen = set()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if any(char.isdigit() for char in line):
            continue
        words = line.split()
        if 2 <= len(words) <= 4:
            # exclude lines with punctuation or slashes
            if re.search(r'[\(\)\[\]/\\<>@,;:.]', line):
                continue
            # simple heuristic: treat as name
            candidate = ' '.join(words)
            # avoid unit names which may be longer but slip through; skip if long
            if len(candidate) > 60:
                continue
            if candidate.lower() in seen:
                continue
            seen.add(candidate.lower())
            # build email: given+middle+family@domain following user rule
            parts = [p for p in words if p]
            family = parts[0]
            given = parts[-1]
            middle = ''.join(parts[1:-1]) if len(parts) > 2 else ''
            local = (given + middle + family).lower()
            local = remove_diacritics(local)
            email = f"{local}@swin.edu.au"
            names.append({'full_name': candidate, 'username': local, 'email': email, 'password': 'password123', 'enrollments': []})
    return names


def write_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)


def main(argv):
    if len(argv) < 2:
        print('Usage: python tools/parse_program_map_pdf.py <pdf_path> [--out-dir data]')
        return 1
    pdf_path = argv[1]
    out_dir = 'data'
    if '--out-dir' in argv:
        idx = argv.index('--out-dir')
        if idx + 1 < len(argv):
            out_dir = argv[idx+1]

    text = extract_text_from_pdf(pdf_path)
    units = find_units(text)
    students = find_names(text)

    units_path = os.path.join(out_dir, 'units.json')
    students_path = os.path.join(out_dir, 'students.json')
    write_json(units, units_path)
    write_json(students, students_path)

    print(f'Wrote {len(units)} units to {units_path}')
    print(f'Wrote {len(students)} students to {students_path}')
    print('Please review the generated JSON files before running the seeder.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
