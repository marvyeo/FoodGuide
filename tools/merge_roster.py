"""Merge a complete roster (every stall/outlet at a centre or mall) into data/places.json.

Roster files live in data/rosters/<cluster-id>.txt:
    # source: <key-suffix> | <url> | <snapshot description> | fetched YYYY-MM-DD
    Name|#unit
    Name|#unit
    ...
Usage:  python3 tools/merge_roster.py data/rosters/m-bedok-mall.txt [more files...]   (or --all)

Rows may carry an optional third field, a directory note: "Opening Soon" / "New Store" (tagged "new"),
"Temporarily Closed" (kept open, noted in status_note), and an optional fourth field: the directory's opening
hours as free text ("Monday to Sunday ; 11am to 10pm"). Hours are parsed with speclib.free_hours (ambiguous text
is skipped) and fill places with no hours; an official live directory also refreshes non-"detailed" places.

Official live directories (snapshot field starts with "live", e.g. CapitaLand's own store list) are
authoritative: every row is added (no superseding), and mapped places in that cluster that the directory
no longer lists are set to status "closed" (never deleted) with a closed_note. Pass --dry-run to preview.

Rules for other rosters (completeness first, freshness wins):
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
from speclib import load, save, norm, unit_key, slug, guess_cuisine, free_hours
from validate import validate

def parse(path):
    head, rows = None, []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("#"):
            if head is None: head = [x.strip() for x in line[1:].split("|")]
            continue
        if not line.strip(): continue
        parts = [x.strip() for x in line.split("|")] + ["", "", ""]
        rows.append((parts[0], parts[1], parts[2], parts[3]))
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
    official = bool(head and len(head) > 2 and head[2].lower().startswith("live"))
    fetched = c["roster"]["fetched"]
    stats = {"matched": 0, "added": 0, "superseded": [], "closed": [], "reopened": [], "hours": 0}
    seen = set()
    def note_it(p, note):
        nl = note.lower()
        if nl in ("opening soon", "new store") and "new" not in p.setdefault("tags", []): p["tags"].append("new")
        if nl == "temporarily closed": p["status_note"] = f"Temporarily closed (directory, {fetched})"
        elif p.get("status_note", "").startswith("Temporarily closed"): p.pop("status_note")
    def hours_it(p, text):
        h = free_hours(text)
        if h and (not p.get("hours") or (official and p.get("confidence") != "detailed")):
            if p.get("hours") != h: stats["hours"] += 1
            p["hours"] = h
    for name, unit, note, hrs in rows:
        n = norm(name)
        hit = next((p for p in places if n and (n == norm(p["name"]) or (len(n) >= 5 and (n in norm(p["name"]) or norm(p["name"]) in n)))), None)
        if not hit and unit_key(unit):   # same unit, same first letters: a respelling ("Gwanjang Gaon" / "Gwangjang GAON")
            hit = next((p for p in places if p["id"] not in seen and unit_key(p.get("unit")) == unit_key(unit) and len(n) >= 4 and norm(p["name"])[:4] == n[:4]), None)
        if hit:
            stats["matched"] += 1; seen.add(hit["id"])
            if unit and (not hit.get("unit") or official): hit["unit"] = unit
            if official and hit.get("status") == "closed":
                hit["status"] = "open"; hit.pop("closed_note", None); stats["reopened"].append(hit["name"])
            note_it(hit, note); hours_it(hit, hrs)
            continue
        uk = unit_key(unit)
        clash = None if official else next((p for p in places if uk and unit_key(p.get("unit")) == uk and p.get("confidence") != "listed"), None)
        if clash:
            stats["superseded"].append(f"{name} ({unit}) → now {clash['name']}"); continue
        display = f"{name} ({short})"
        pid = ("p-" + slug(cid + " " + name))[:62].rstrip("-")
        if pid in ids: continue
        p = {"cluster": cid, "name": display, "unit": unit, "cuisine": guess_cuisine(name), "dishes": [], "hours": [],
             "modes": ["dine", "takeaway"], "diet": [], "tags": [], "must_try": False, "status": "open", "price_band": 1,
             "sources": [key], "verified": "unconfirmed", "confidence": "listed", "id": pid}
        note_it(p, note); hours_it(p, hrs)
        D["places"].append(p); places.append(p); ids.add(pid); seen.add(pid); stats["added"] += 1
    if official:
        for p in places:
            if p["id"] not in seen and p.get("status") != "closed":
                p["status"] = "closed"; p["closed_note"] = f"Not in the official {c['name']} directory on {fetched}"
                stats["closed"].append(f"{p['name']} ({p.get('unit') or 'no unit'}, {p['confidence']})")
    return cid, len(rows), stats

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--dry-run"]; dry = "--dry-run" in sys.argv
    files = sorted(glob.glob("data/rosters/*.txt")) if args == ["--all"] else args
    D = load()
    for f in files:
        cid, total, s = merge(D, f)
        print(f"{cid}: roster {total} | already mapped {s['matched']} | added {s['added']} | superseded {len(s['superseded'])} | closed {len(s['closed'])} | hours set {s['hours']}")
        for x in s["superseded"]: print("   superseded:", x)
        for x in s["closed"]: print("   closed (not in official directory):", x)
        for x in s["reopened"]: print("   reopened:", x)
    errs = validate(D)
    if errs: raise SystemExit("validation failed: " + "; ".join(errs[:5]))
    if dry: print("dry run — nothing saved")
    else: save(D); print("saved")
