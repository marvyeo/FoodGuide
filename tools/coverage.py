"""Coverage report: how complete is each food centre / mall?   python3 tools/coverage.py [--md]
'roster' = known total (NEA count for hawker centres, directory count for malls). '?' = no roster yet (a gap)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from speclib import load
from collections import Counter
D = load()
rows = []
for c in D["clusters"]:
    ps = [p for p in D["places"] if p.get("cluster") == c["id"]]
    conf = Counter(p["confidence"] for p in ps)
    tot = c.get("stalls_total")
    rows.append((c["zone"], c.get("type", "hawker"), c["name"], len(ps), tot, conf["detailed"], conf["partial"], conf["listed"],
                 (c.get("roster") or {}).get("source", "NEA count" if c.get("type") == "hawker" and tot else "—")))
rows.sort()
md = "--md" in sys.argv
if md:
    print("| Zone | Type | Name | Mapped | Roster | Detailed | Partial | Listed | Roster source |\n|---|---|---|---|---|---|---|---|---|")
for z, t, n, m, tot, d, pa, l, src in rows:
    pct = f"{min(100, round(m / tot * 100))}%" if tot else "?"
    if md: print(f"| {z} | {t} | {n} | {m} | {tot or '?'} ({pct}) | {d} | {pa} | {l} | {src} |")
    else: print(f"{z:6} {t:6} {n[:42]:42} {m:4} / {str(tot or '?'):4} {pct:>5}  det {d:3} part {pa:3} list {l:3}  {src}")
solo = [p for p in D["places"] if not p.get("cluster")]
print(f"\nStandalone restaurants/cafés: {len(solo)} | Total places: {len(D['places'])} | Gaps (no roster): {sum(1 for r in rows if not r[4])}")
