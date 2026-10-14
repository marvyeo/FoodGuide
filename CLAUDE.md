# Notes for Claude

Read `PROJECT_STATE.md` first. It has the architecture, data schemas, source-reliability notes and the refresh procedure.

- `data/places.json` is the source of truth for places. Change it through a pull request (the owner approves by merging). Never delete a place, because family logs reference place ids; set `"status": "closed"` instead.
- Keep `index.html` a single self-contained file (the same style as the owner's other Pages apps). Bump `CACHE` in `sw.js` when the shell changes.
- Before pushing, validate `places.json`: unique ids, valid `sources` keys, and hours slots matching `HH:MM-HH:MM` with days `0`–`6`.
- Update `PROJECT_STATE.md` (coverage table, decisions, next up) at the end of any working session.
