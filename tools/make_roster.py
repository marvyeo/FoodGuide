"""Raw browser rows -> data/rosters/<id>.txt.
Input lines: name|unit|status|hours  (status: Opening Soon / New Store / Temporarily Closed / blank)
Usage: python3 tools/make_roster.py raw.txt m-ion-orchard "ion | https://www.ionorchard.com/en/dine.html | live directory (Dine)" [--drop "7-Eleven,Bluebird Travel"]"""
import sys, os, re, html, datetime
sys.path.insert(0, os.path.dirname(__file__))
from clean_directory import unit as cu, clean
DROP_ALWAYS = re.compile(r'^(7-eleven|cheers|bluebird travel|eu yan sang|watsons|guardian|fairprice|cold storage|don don donki|wine connection)$', re.I)
def main():
    raw, cid, src = sys.argv[1:4]
    drop = set(x.strip().lower() for x in (sys.argv[sys.argv.index('--drop') + 1].split(',') if '--drop' in sys.argv else []))
    out, seen = [], set()
    for line in open(raw, encoding='utf-8'):
        if not line.strip(): continue
        name, un, st, hrs = (line.rstrip('\n').split('|') + ['', '', ''])[:4]
        name = clean(html.unescape(name))
        name = re.sub(r'\s*\(([^)]*)\)$', lambda m: '' if m.group(1).lower().replace('è', 'e') in name.lower().replace('è', 'e') else m.group(0), name)
        if not name or DROP_ALWAYS.match(name) or name.lower() in drop: continue
        hrs = re.sub(r'<[^>]+>', ' ', html.unescape(hrs)); hrs = re.sub(r'\s+', ' ', hrs).strip().replace(';', ' ')
        st = {'opening soon': 'Opening Soon', 're-opening soon': 'Temporarily Closed', 'new store': 'New Store', 'new': 'New Store', 'temporarily closed': 'Temporarily Closed'}.get(st.strip().lower(), '')
        u = cu(un.strip()) if un.strip() else ''
        key = (name.lower(), u)
        if key in seen: continue
        seen.add(key); out.append(f'{name}|{u}|{st}|{hrs}'.rstrip('|'))
    path = f'data/rosters/{cid}.txt'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'# source: {src} | fetched {datetime.date.today()}\n' + '\n'.join(out) + '\n')
    print(len(out), 'rows ->', path)
main()
