"""Merge a complete roster (every stall/outlet at a centre or mall) into data/places.json.

Roster files live in data/rosters/<cluster-id>.txt:
    # source: <key-suffix> | <url> | <snapshot description> | fetched YYYY-MM-DD
    Name|#unit
    Name|#unit
    ...
Usage:  python3 tools/merge_roster.py data/rosters/m-bedok-mall.txt [more files...]   (or --all)

Rules (completeness first, freshness wins):
  * Sets the cluster's stalls_total to the roster count (the coverage-bar denominator) and records cluster.roster.
  * A roster name that matches an existing place in that cluster (brand match, ignoring "(Mall)" labels) is
    skipped; its unit fills in an empty unit.
  * A roster entry whose unit is held by a *different* shop from a dated guide is treated as an old tenant and
    dropped (reported as "superseded").
  * Everything else is added as confidence "listed", verified "unconfirmed", with a guessed cuisine.
Re-running is safe: already-merged names match and are skipped.
"""
import sys, os, re, glob
sys.path.insert(0, os.path.dirname(__file__))
from speclib import load, save, norm, unit_key, slug, guess_cuisine
from validate import validate

def parse(path):
    head, rows = None, []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("#"):
            if head is None: head = [x.strip() for x in line[1:].split("|")]
            continue
        if not line.strip(): continue
        name, _, unit = line.partition("|")
        rows.append((name.strip(), unit.strip()))
    return head, rows

def merge(D, path):
    cid = os.path.splitext(os.path.basename(path))[0]
    c = next((x for x in D["clusters"] if x["id"] == cid), None)
    if not c: raise SystemExit(f"{path}: no cluster with id {cid}")
    head, rows = parse(path)
    src_kind = head[0].replace("source:", "").strip() if head else "roster"
    key = f"{src_kind}-{cid}"
    D["sources"][key] = {"name": f"{src_kind} – {c['name']} directory", "url": head[1] if head and len(head) > 1 else "",
                         "date": head[2] if head and len(head) > 2 else "undated"}
    if key not in c.setdefault("sources", []): c["sources"].append(key)
    c["stalls_total"] = len(rows)
    c["roster"] = {"source": key, "count": len(rows), "snapshot": head[2] if head and len(head) > 2 else "", "fetched": (head[3].replace("fetched", "").strip() if head and len(head) > 3 else "")}
    short = c.get("short") or re.sub(r"\s*\(.*?\)", "", c["name"])
    places = [p for p in D["places"] if p.get("cluster") == cid]
    ids = {p["id"] for p in D["places"]}
    stats = {"matched": 0, "added": 0, "superseded": []}
    for name, unit in rows:
        n = norm(name)
        hit = next((p for p in places if n and (n == norm(p["name"]) or (len(n) >= 5 and (n in norm(p["name"]) or norm(p["name"]) in n)))), None)
        if hit:
            stats["matched"] += 1
            if not hit.get("unit") and unit: hit["unit"] = unit
            continue
        uk = unit_key(unit)
        clash = next((p for p in places if uk and unit_key(p.get("unit")) == uk and p.get("confidence") != "listed"), None)
        if clash:
            stats["superseded"].append(f"{name} ({unit}) → now {clash['name']}"); continue
        display = f"{name} ({short})"
        pid = ("p-" + slug(cid + " " + name))[:62].rstrip("-")
        if pid in ids: continue
        p = {"cluster": cid, "name": display, "unit": unit, "cuisine": guess_cuisine(name), "dishes": [], "hours": [],
             "modes": ["dine", "takeaway"], "diet": [], "tags": [], "must_try": False, "status": "open", "price_band": 1,
             "sources": [key], "verified": "unconfirmed", "confidence": "listed", "id": pid}
        D["places"].append(p); places.append(p); ids.add(pid); stats["added"] += 1
    return cid, len(rows), stats

if __name__ == "__main__":
    args = sys.argv[1:]
    files = sorted(glob.glob("data/rosters/*.txt")) if args == ["--all"] else args
    D = load()
    for f in files:
        cid, total, s = merge(D, f)
        print(f"{cid}: roster {total} | already mapped {s['matched']} | added {s['added']} | superseded {len(s['superseded'])}")
        for x in s["superseded"]: print("   superseded:", x)
    errs = validate(D)
    if errs: raise SystemExit("validation failed: " + "; ".join(errs[:5]))
    save(D); print("saved")
