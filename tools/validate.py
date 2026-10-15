"""Validate data/places.json. Run before every push:  python3 tools/validate.py
Exits non-zero on any problem."""
import re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from speclib import load, CUISINES

def validate(D):
    errs = []
    ids = [p["id"] for p in D["places"]]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup: errs.append(f"duplicate place ids: {sorted(dup)[:10]}")
    cids = [c["id"] for c in D["clusters"]]
    if len(cids) != len(set(cids)): errs.append("duplicate cluster ids")
    zones = {z["id"] for z in D["zones"]}
    inside = lambda lat, lng: isinstance(lat, (int, float)) and 1.15 < lat < 1.48 and 103.6 < lng < 104.1
    for c in D["clusters"]:
        if c.get("type") not in ("hawker", "mall", "coffeeshop"): errs.append(f"{c['id']}: bad type {c.get('type')}")
        if c["zone"] not in zones: errs.append(f"{c['id']}: bad zone")
        if not inside(c["lat"], c["lng"]): errs.append(f"{c['id']}: coords outside Singapore")
        for s in c.get("sources", []):
            if s not in D["sources"]: errs.append(f"{c['id']}: unknown source {s}")
    cset = set(cids)
    for p in D["places"]:
        n = p.get("name", "?")
        if p["cuisine"] not in CUISINES: errs.append(f"{n}: bad cuisine {p['cuisine']}")
        if p.get("cluster") and p["cluster"] not in cset: errs.append(f"{n}: unknown cluster")
        if not p.get("cluster"):
            if not inside(p.get("lat"), p.get("lng")): errs.append(f"{n}: standalone without valid coords")
            if p.get("zone") not in zones: errs.append(f"{n}: bad zone")
        if p.get("confidence") not in ("detailed", "partial", "listed"): errs.append(f"{n}: bad confidence")
        if p.get("status") not in ("open", "closed"): errs.append(f"{n}: bad status")
        if p.get("price_band") not in (1, 2, 3, 4): errs.append(f"{n}: bad price_band")
        for s in p.get("sources", []):
            if s not in D["sources"]: errs.append(f"{n}: unknown source {s}")
        for days, slots in p.get("hours", []):
            if not re.fullmatch("[0-6]+", days): errs.append(f"{n}: bad days {days}")
            for s in slots:
                if not re.fullmatch(r"\d\d:\d\d-\d\d:\d\d", s): errs.append(f"{n}: bad slot {s}")
        for d in p.get("dishes", []):
            if not d.get("name"): errs.append(f"{n}: dish without name")
    return errs

if __name__ == "__main__":
    D = load(sys.argv[1] if len(sys.argv) > 1 else "data/places.json")
    errs = validate(D)
    for e in errs[:50]: print("ERROR", e)
    print(f"{len(D['places'])} places, {len(D['clusters'])} clusters — {'OK' if not errs else f'{len(errs)} problems'}")
    sys.exit(1 if errs else 0)
