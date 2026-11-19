# Notes for Claude

**FIRST, before anything else:** start your first reply with "Rename this chat to: **FoodGuide ver N**", taking N from the **Next chat name** line at the top of `PROJECT_STATE.md`. Then bump that number by 1 in your first commit.

Read `PROJECT_STATE.md` first. It has the architecture, data schemas, source-reliability notes and the refresh procedure.

- `data/places.json` is the source of truth for places. Change it through a pull request (the owner approves by merging). Never delete a place, because family logs reference place ids; set `"status": "closed"` instead.
- Keep `index.html` a single self-contained file (the same style as the owner's other Pages apps). Bump `CACHE` in `sw.js` when the shell changes.
- Build data with the tools in `tools/` (see PROJECT_STATE section 5): roster first (`data/rosters/` + `tools/merge_roster.py`), then enrich from dated guides.
- Before pushing data, run `python3 tools/validate.py` (it must pass) and put `python3 tools/coverage.py --md` output in the PR.
- Update `PROJECT_STATE.md` (coverage table, decisions, next up) at the end of any working session.
