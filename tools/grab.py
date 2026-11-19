"""Pull text a browser javascript_tool call returned, from this session's transcript.
The JS must return a string starting with a unique marker, e.g. "@@ION@@" + rows.join("\\n").
Usage: python3 tools/grab.py @@ION@@ out.txt   (takes the LAST result containing the marker)"""
import sys, glob, json, os
marker, out = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl')), key=os.path.getmtime)
hit = None
def walk(o):
    global hit
    if isinstance(o, str):
        if ('"' + marker) in o: hit = o[o.index('"' + marker) + 1:]
    elif isinstance(o, dict): [walk(v) for v in o.values()]
    elif isinstance(o, list): [walk(v) for v in o]
for f in files:
    for line in open(f, encoding='utf-8'):
        if marker in line:
            try: walk(json.loads(line))
            except Exception: pass
if not hit: sys.exit('marker not found')
s = hit[hit.index(marker) + len(marker):]
end = s.find('"\n\n(captured at')
if end < 0: end = s.find('"\n\nTab Context')
if end >= 0: s = s[:end]
s = json.loads('"' + s + '"')
open(out, 'w', encoding='utf-8').write(s)
print(len(s.splitlines()), 'lines ->', out)
