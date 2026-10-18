"""Fold an opening-hours list into a roster file's 4th field.

    python3 tools/roster_hours.py data/rosters/m-plq.txt hours.txt [--dry-run]

hours.txt lines: "Name|Daily 10:00-22:00" or "Name|Mon-Fri 11:00-21:30; Sat-Sun 10:00-21:30"
(anything speclib.free_hours understands). Names are matched to roster rows with speclib.norm
(exact, then containment for names of 5+ characters). Lines that don't parse, or don't match a
row, are reported and skipped. Re-run merge_roster.py on the roster afterwards to apply.
Use it when a landlord publishes hours on per-store pages rather than in the directory list.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from speclib import norm, free_hours

def main(roster, hours_file, dry=False):
    lines = open(roster, encoding="utf-8").read().splitlines()
    hrs = {}
    for l in open(hours_file, encoding="utf-8"):
        if "|" not in l: continue
        name, spec = [x.strip() for x in l.rstrip("\n").split("|", 1)]
        if not free_hours(spec): print("   unparsed:", name, "→", spec); continue
        hrs[norm(name)] = spec
    used, out, filled = set(), [], 0
    for l in lines:
        if l.startswith("#") or not l.strip(): out.append(l); continue
        parts = l.split("|") + ["", "", ""]
        n = norm(parts[0])
        key = n if n in hrs else next((k for k in hrs if len(n) >= 5 and len(k) >= 5 and (k in n or n in k)), None)
        if key:
            parts[3] = hrs[key]; used.add(key); filled += 1
        out.append("|".join(parts[:4]).rstrip("|"))
    for k in hrs:
        if k not in used: print("   no roster row for:", k)
    print(f"{roster}: hours for {filled} of {sum(1 for l in lines if l.strip() and not l.startswith('#'))} rows")
    if not dry: open(roster, "w", encoding="utf-8").write("\n".join(out) + "\n")

if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--dry-run"]
    main(a[0], a[1], "--dry-run" in sys.argv)
