# Makan Map — project state

_Last updated: 15 Oct 2026, ~09:30 SGT (v1.3: malls + mall directories, cuisine/venue filters, data pipeline in `tools/`)_

> **New chat? Start here.**
> 1. Read this file. Then `CLAUDE.md`. Then run `python3 tools/coverage.py` for live coverage.
> 2. The repo is `marvyeo/FoodGuide`: attach it with push access and clone it. GitHub's REST API works via `gh api` (unset `GH_TOKEN` first; GraphQL is blocked).
> 3. Data changes go on a branch and into a PR. App changes (`index.html`, `sw.js`; bump `CACHE` in `sw.js`) can go straight to `main`.
> 4. The owner's next likely asks are in section 7.

A family food map of Singapore. You filter by when, how far, budget, dine-in/tapau and craving, then spin for a stall or a food centre. You log and rate meals, and you collect stamps and badges. The app is installable from GitHub Pages and works offline. Day-to-day use costs no AI tokens. Claude is only involved to build or refresh the places data.

- **Repo:** `marvyeo/FoodGuide`
- **App URL:** https://marvyeo.github.io/FoodGuide/ (GitHub Pages, live)
- **Status:** v1.3 live.
  - The owner signs in with Google on PC and phone. The family sheet exists.
  - Photos are tested only against mocked Google APIs.
- **Data:** PRs #1–#4 merged on 15 Oct. Live: **1,268 places** (19 hawker centres, 15 malls, 61 standalones), Home ground and East zones only.

---

## 1. Architecture

| Layer | Where | Notes |
|---|---|---|
| App | `index.html` (single file), `sw.js`, `manifest.json`, `icons/` | Vanilla JS, Leaflet map (cdnjs), **OneMap** tiles (SLA; free, no key, attribution with logo required). CARTO was dropped on 15 Oct 2026 because it began requiring an API key. Same patterns as TVWorld: Google Identity Services token client, redirect-sign-in fallback, network-first service worker. |
| Places data | `data/places.json` | Curated in the repo and versioned. Every change goes in through a pull request, and **merging the PR is the approval step**. The service worker fetches it network-first, so a merged PR shows up the next time the app opens online. |
| Family data | One Google Sheet in the family owner's Drive (title "Makan Map — family data") | Tabs: `members`, `logs`, `wants`, `places_added`, `photos`. Missing tabs are added automatically on sync, so older family sheets upgrade themselves. **Rows are only ever appended; the newest row per key wins**, so concurrent edits from several phones never conflict. Edits and deletes append a new row with the same id. |
| Offline | `localStorage` (`mm.*` keys) + IndexedDB (`makanmap`) | Cached copy of the sheet plus an **outbox** of unsent rows. Photos taken offline wait in IndexedDB. Everything flushes when you're back online and signed in. |
| Photos | Each person's own Drive, folder "Makan Map photos" | Uploaded with the `drive.file` scope, which only covers files the app creates, never the rest of anyone's Drive. Photos are shrunk to 1600px JPEG on the phone first. Each is shared **view-by-link** so other family members can see it without extra setup. The `photos` tab records the place, kind (food/menu) and an optional log. Thumbnails load from `drive.google.com/thumbnail?id=…`, falling back to `lh3.googleusercontent.com/d/…`. |

**Why a Sheet and not Drive JSON like TVWorld:** a file the app creates under the `drive.file` scope can't be opened by *other* family members' accounts without adding the Google Picker (and an API key). A shared Sheet plus the `spreadsheets` scope needs one extra API switched on and nothing else. Append-only rows also remove the need for TVWorld-style version merging.

### Sign-in and family flow
1. Sign in with Google (popup, or a redirect fallback for iOS home-screen apps).
2. No family yet → **Start a new family** (the app creates the Sheet) or **Join** (paste an invite link `…/FoodGuide/?family=<sheetId>`).
3. On first join, each person picks a display name and emoji (stored in `members`, keyed by Google `sub`).
4. Owner: Passport → Settings → **Copy family invite link**, then share the Sheet with each member as **Editor**.
5. Without signing in you can still browse and spin as a guest; logging requires sign-in.
6. **New device, same Google account (fixed 15 Oct):** the family id used to live only in the device's localStorage, so a second device was asked to start a new family. Now, when signed in with no family on the device, the app searches Drive (`drive.file`) for sheets it created named "Makan Map — family data":
   - One found: it opens automatically.
   - Several found: you pick one, usually the oldest.
   - None found: start or join a family as before.

   Limitation: `drive.file` only sees sheets the app created *for that account*, so **members who joined someone else's family still need the invite link on each new device**.

### Sheet schema
| Tab | Columns | Key |
|---|---|---|
| members | member_id, email, name, emoji, at | member_id |
| logs | log_id, at, member_id, place_id, dish, stars (1–5), again (Y/M/N), mode (dine/takeaway), note, deleted (0/1) | log_id |
| wants | member_id, place_id, at, active (1/0) | member_id + place_id |
| places_added | id, at, member_id, json (a full place object) | id |
| photos | photo_id, at, member_id, place_id, file_id (Drive), kind (food/menu), caption, deleted (0/1), log_id | photo_id |

### places.json schema
- `home`: the default origin for distances (Bedok Reservoir Park). Each phone can override it via *Set home here*.
- `zones[]`: `home`, `east`, `northeast`, `north`, `central`, `west`, each with a colour and description.
- `mrt[]`: stations used for the "nearest MRT" line. Home ground and East stations so far (21); add each new zone's stations.
- `sources{}`: key → {name, url, date}. Places cite these keys.
- `clusters[]`: food centres and malls. Fields: `id, name, type` (`hawker` / `mall` / `coffeeshop`), `address, lat, lng, zone, stalls_total` (roster count: NEA for hawker centres, directory count for malls; the coverage-bar denominator; null = unknown), `roster?` ({source, count, snapshot, fetched}, set by `merge_roster.py`), `notes, sources`.
- Places in malls are named `Brand (Mall)`, e.g. "Genki Sushi (Tampines Mall)".
- `places[]`: fields are
  - `id, cluster?, name, name_zh?, unit, cuisine` (see `CUISINES` in index.html), `dishes[{name, price?, price_note?}]`, `price_band` 1–4
  - `hours`: `[[days, ["HH:MM-HH:MM", …]], …]` with days as a string of `0`–`6` (0 = Sunday); an end time before the start time means the slot runs past midnight
  - `modes` (`dine`/`takeaway`), `travels_well?, diet[], tags[]` (breakfast, supper, group, dessert, 24h, occasion), `must_try, status` (`open`/`closed`), `verified` (YYYY-MM, or `unconfirmed`), `sources[]`, `note?`
  - `confidence`:
    - `detailed`: dishes plus hours from a dated guide.
    - `partial`: dishes and prices but no hours.
    - `listed`: name and unit from a roster only. The app shows a "Listed only, snap the menu" prompt and gives these a lower spin weight.
  - When **Only open** is on, stalls with unknown hours are assumed open 7am–8pm.
  - `lat/lng/zone/address` are inherited from the cluster when omitted

Price bands: 1 = under $8, 2 = $8–20, 3 = $20–50, 4 = $50+.

---

## 2. What's built (v1.3)

- **Spin:**
  - Weighted random pick: your family's ratings + a novelty bonus for untried places + must-try + bookmarks − distance. Anyone who rated a place 2★ or less with "not again" vetoes it.
  - Slot-reel animation.
  - **Centre mode** for groups: ranks food centres by how many matching stalls and kinds of food are open, then lists them by cuisine.
- **Filters:**
  - Who's eating (multi-select family members), and when (now / breakfast / lunch / dinner / supper, checked against real opening hours).
  - How far: walkable ≤1.3 km, short ride ≤4 km, anywhere.
  - Budget, dine-in/tapau, cravings.
  - Toggles for open-only, untried-only, must-try only.
- **Explore and Map filters (v1.3):**
  - Venue type: Hawker, Malls or Restaurants.
  - Multi-select cuisine chips.
  - Both are shared between Explore and Map, and remembered on the device in `prefs.browseKind` and `prefs.browseCuisines`.
  - Centre cards show which stalls match. Malls are 🛍️ in lists and square pins on the map.
- **Place sheet links:** 🧾 *Menu (Google)* opens a Google search for "<name> <centre> menu". Google offers no stable deep link to its Menu tab, so the search is the closest; it usually shows the Menu tab in the results panel.
- **Explore:** centres and malls sorted by distance, zone filter, each with a coverage bar ("14 of ~72 stalls mapped"); all places; bookmarks; search by name, dish or cuisine.
- **Place sheet:**
  - Dishes and prices, hours table, open-now status, walk/drive time, nearest MRT.
  - Family ratings, directions (Google Maps), bookmark, sources with dates.
- **Centre sheet:** stall roster, coverage, and **Add a stall** (family mapping of stalls with no online presence → `places_added`).
- **Map:** OneMap basemap limited to Singapore, markers coloured by zone, hollow = not tried, ⭐ = has a must-try. Filters: untried, must-try, open now. Tiles are cached (600 max) for offline.
- **Photos (v1.1):**
  - Each place sheet has a photo strip with **📷 Food photo** and **🧾 Menu / signboard** buttons. On a phone these open the camera or the photo library.
  - Photos can also be attached while logging a meal.
  - Tapping a photo opens a viewer, where you can delete your own.
  - The first food photo becomes the place's cover image and its thumbnail in lists.
  - **See photos online** links open Google Maps, Google Images and Burpple searches. Photos from the web are linked out to, not copied into the app, because they're copyrighted.
  - Badges: 📸 Food snapper (5 food photos) and 🧾 Menu hunter (3 menus).
  - The first upload after this update asks each person to allow Drive access to the app's own files. The sync chip shows "Tap to allow photos".
- **Log:** stars, "would you queue again", dine-in/tapau, dish, note. Edit and delete your own logs. Family feed.
- **Passport:**
  - Places tried, centres stamped, week streak, progress by zone, 16-square cuisine bingo, 16 badges.
  - Family leaderboard and "hot takes" (where ratings differ by 2 or more stars).
  - Settings.

---

## 3. Data coverage

**Live (15 Oct 2026, 09:30):** 1,268 places: 19 hawker centres, 15 malls and 61 standalone restaurants/cafés, in the **Home ground** and **East** zones. North East, North, Central and West aren't built yet.

Regenerate this table with `python3 tools/coverage.py --md`. "Roster" is the known total: the NEA cooked-food stall count for hawker centres, the directory count for malls. `?` means no roster yet, i.e. a completeness gap.

| Zone | Type | Name | Mapped | Roster | Detailed | Partial | Listed | Roster source |
|---|---|---|---|---|---|---|---|---|
| east | hawker | Bedok Corner Food Centre | 10 | 32 (31%) | 10 | 0 | 0 | NEA count |
| east | hawker | Changi Village Hawker Centre | 28 | 87 (32%) | 11 | 0 | 17 | NEA count |
| east | hawker | Dunman Food Centre | 25 | 30 (83%) | 10 | 2 | 13 | NEA count |
| east | hawker | East Coast Lagoon Food Village | 26 | 63 (41%) | 14 | 0 | 12 | NEA count |
| east | hawker | Eunos Crescent Market & Food Centre (4A) | 28 | 42 (67%) | 0 | 10 | 18 | NEA count |
| east | hawker | Geylang Serai Market & Food Centre | 38 | 63 (60%) | 0 | 10 | 28 | NEA count |
| east | hawker | Haig Road Market & Food Centre | 15 | 72 (21%) | 0 | 13 | 2 | NEA count |
| east | hawker | Hawker Centre @ Our Tampines Hub | 11 | ? (?) | 7 | 4 | 0 | — |
| east | hawker | Marine Parade Central Market & Food Centre | 19 | 55 (35%) | 0 | 10 | 9 | NEA count |
| east | hawker | Old Airport Road Food Centre | 41 | 168 (24%) | 32 | 4 | 5 | NEA count |
| east | hawker | Pasar 16 @ Bedok South (Blk 16) | 26 | 64 (41%) | 11 | 0 | 15 | NEA count |
| east | hawker | Pasir Ris Central Hawker Centre | 11 | ? (?) | 11 | 0 | 0 | — |
| east | hawker | Tampines Round Market & Food Centre (Blk 137) | 30 | 45 (67%) | 16 | 0 | 14 | NEA count |
| east | mall | Century Square | 48 | 50 (96%) | 10 | 0 | 38 | singmalls-m-century-square |
| east | mall | Changi City Point | 63 | 61 (100%) | 24 | 0 | 39 | singmalls-m-changi-city-point |
| east | mall | Downtown East (E!Hub & E!Avenue) | 9 | ? (?) | 0 | 0 | 9 | — |
| east | mall | Eastpoint Mall | 5 | ? (?) | 5 | 0 | 0 | — |
| east | mall | Jewel Changi Airport | 129 | 134 (96%) | 25 | 0 | 104 | singmalls-m-jewel |
| east | mall | Parkway Parade | 52 | 49 (100%) | 10 | 0 | 42 | singmalls-m-parkway-parade |
| east | mall | Pasir Ris Mall | 12 | ? (?) | 12 | 0 | 0 | — |
| east | mall | Paya Lebar Quarter (PLQ) | 76 | 78 (97%) | 18 | 0 | 58 | singmalls-m-plq |
| east | mall | Paya Lebar Square | 53 | 53 (100%) | 9 | 0 | 44 | singmalls-m-paya-lebar-square |
| east | mall | SingPost Centre | 18 | ? (?) | 0 | 17 | 1 | — |
| east | mall | Tampines 1 | 11 | ? (?) | 11 | 0 | 0 | — |
| east | mall | Tampines Mall | 56 | 56 (100%) | 17 | 0 | 39 | singmalls-m-tampines-mall |
| east | mall | White Sands | 53 | 53 (100%) | 9 | 0 | 44 | singmalls-m-white-sands |
| east | mall | i12 Katong | 44 | 39 (100%) | 0 | 13 | 31 | singmalls-m-i12-katong |
| home | hawker | Bedok 216 Food Centre & Market | 48 | 82 (59%) | 17 | 8 | 23 | NEA count |
| home | hawker | Bedok 85 Fengshan Centre | 26 | 72 (36%) | 24 | 1 | 1 | NEA count |
| home | hawker | Bedok Interchange Hawker Centre (208B) | 19 | 70 (27%) | 9 | 1 | 9 | NEA count |
| home | hawker | Blk 538 Bedok North St 3 Market & Food Centre | 40 | 40 (100%) | 13 | 0 | 27 | NEA count |
| home | hawker | Kaki Bukit 511 Market & Food Centre | 34 | 42 (81%) | 16 | 0 | 18 | NEA count |
| home | hawker | Pasar Makan @ Reservoir (Blk 630) | 31 | 36 (86%) | 11 | 5 | 15 | NEA count |
| home | mall | Bedok Mall | 72 | 69 (100%) | 8 | 8 | 56 | singmalls-m-bedok-mall |

Standalone restaurants/cafés: 61 | Total places: 1268 | Gaps (no roster): 7

Notes:
- **Hawker coverage %:** NEA counts include drinks stalls and vacant units, so 100% isn't always reachable.
- **Mall coverage %:**
  - It can read ≥100%: the directories are ~2024 snapshots and newer guides add tenants the directory doesn't know about.
  - 43 directory entries were dropped as superseded (see the PR #4 description).
- **Gaps, in priority order:**
  1. **No mall directory yet:** Tampines 1, Pasir Ris Mall, Eastpoint (plus its Hawkers' Street food court), SingPost Centre, Downtown East. Their SingMalls pages failed to fetch on 15 Oct. Retry them, or try the mall's own site, or Little Day Out.
  2. **Hawker centres under 40%:** Old Airport Rd (41/168), Haig Rd (15/72), Bedok Interchange (19/70), Changi Village (28/87), Bedok Corner (10/32), Marine Parade (19/55), Fengshan 85 (26/72). They need a stall roster; see the source notes.
  3. **No NEA count:** Our Tampines Hub and Pasir Ris Central (both new-generation centres not on the 2024 list).
  4. **East centres not built at all:** Sims Place, Circuit Road ×3, Aljunied Ave 2, Geylang Bahru, Upper Boon Keng, Blk 58 New Upper Changi Rd, Marine Terrace 50A, Kallang Estate. Plus coffeeshops, which have no official list.
  5. **No recent guide, so no hours:** Marine Parade, Haig Road, Geylang Serai, Eunos.
- **Must-try flags (27):** e.g. Seng Hiang & Xing Ji BCM, Chai Chee Pork Porridge, Chin Lee, Nam Sing Hokkien Mee, To-Ricos Kway Chap, Roast Paradise, 328 Katong Laksa, Lor 9 Beef Kway Teow, Lau Hong Ser Rojak, Changi Village nasi lemak, Haron Satay.

### Source notes (read before refreshing)
- **Freshness rule:**
  - Guides dated Sep 2023 or later: keep dishes, prices and hours.
  - Older guides: keep dishes, drop hours (`partial`).
  - Rosters and directories: name and unit only (`listed`).
- **Hawker rosters, hawker.guide** (undated):
  - Usable for 216, 511, 538, Bedok South, Tampines Round, Marine Parade, Eunos, Dunman, East Coast Lagoon, Changi Village and Geylang Serai, after cross-checking against dated guides.
  - **Wrong for Fengshan 85**: it lists Redhill stalls.
  - Its `bedok-food-centre` page mixes Bedok Corner with Bedok Interchange.
  - Skip Geylang Serai's generic "#02-01…#02-45 Geylang Serai <dish>" rows.
  - The Old Airport Road, 208B and Haig Road pages don't load.
- **Mall rosters, SingMalls** (`singmalls.app/en/malls/<slug>/directory`):
  - Complete food & beverage lists, but an undated ~2024 snapshot.
  - CapitaLand's own store pages load their content with JavaScript, so a plain page fetch gets nothing.
- **Dated guides:**
  - Eatbook, Seth Lui (check the "Updated" date), Daniel Food Diary, HungryGoWhere, kopitiam.com.sg (recent, but sometimes two stalls share one unit), Ordinary Patrons.
  - Women's Weekly and Miss Tam Chiak are often 2019–2023.
- **NEA:** data.gov.sg *List of Government Markets & Hawker Centres*, `d_68a42f09f350881996d83f9cd73ab02f`. It has 107 centres and stall counts (Jun 2024). Query it via WebFetch on `data.gov.sg/api/action/datastore_search?resource_id=…&limit=200`.
- **Geocoding:** OneMap search, `onemap.gov.sg/api/common/elastic/search?searchVal=<postal or address>&returnGeom=Y&getAddrDetails=Y`. No token needed, though it shows an "auth token missing" note.
- **Network:** the shell in Claude's workspace can't reach these sites. All fetching goes through WebFetch/WebSearch.

---

## 4. Setup still to do (owner)

1. ~~**GitHub Pages:** go to repo Settings → Pages → Deploy from branch → `main` / root.~~ Done 15 Oct.
2. **Google Cloud** (the project that owns the OAuth client in `CONFIG.CLIENT_ID`; it is currently the TVWorld client):
   - **Enable the Google Sheets API.** This is the one new thing needed.
   - Authorized JavaScript origin `https://marvyeo.github.io` should already be there from TVWorld.
   - Add `https://marvyeo.github.io/FoodGuide/` to **Authorized redirect URIs**. This is only needed for the "Try another way" sign-in.
   - Family members must be on the consent screen's **test users** list.
   - The consent screen will show TVWorld's app name and an "unverified app" warning. That's expected in testing mode.
   - Optional: create a separate project or client to brand it "Makan Map", then swap `CONFIG.CLIENT_ID`.
3. Open the app → Sign in → **Start a new family** → Passport → Settings → **Copy family invite link** → share the Sheet with each member as Editor and send them the link.

---

## 5. Data pipeline (completeness first)

The tools are in `tools/` (Python 3, standard library only). Run them from the repo root.

| Tool | What it does |
|---|---|
| `tools/speclib.py` | Helpers: `hours("Tue-Sun 10:00-18:00; Sat 11:00-14:00,17:00-21:00")`, `dishes("Lor mee $4/$5 \| Rojak from $3")`, `band()`, `guess_cuisine()` (keywords plus a `KNOWN` brand map; extend it), `norm()` brand matching, `unit_key()`, `km()`. |
| `tools/merge_roster.py` | Merges `data/rosters/<cluster-id>.txt` into `places.json` (see rules below). Use `--all` for every roster file. Safe to re-run. |
| `tools/validate.py` | Schema and integrity checks. **Run before every push**; it exits non-zero on problems. |
| `tools/coverage.py` | Coverage report per centre or mall (`--md` for markdown). |

**Roster file format** (`data/rosters/<cluster-id>.txt`):

```
# source: <kind> | <url> | <snapshot description> | fetched YYYY-MM-DD
Stall or outlet name|#unit
```

**Merge rules:**
- The roster count becomes the cluster's `stalls_total`.
- Names already in that cluster are matched and skipped.
- A roster entry whose unit is held by a different shop from a dated guide is dropped as **superseded** (an old tenant).
- Everything else is added as `listed`, with display name `Name (Mall)` and a guessed cuisine.

### Building a new area (do it in this order)
1. **Roster first, for completeness:**
   - **Hawker centres:** take the NEA count as `stalls_total`, plus a stall list (hawker.guide or another roster) saved to `data/rosters/c-<id>.txt`.
   - **Malls:** the SingMalls directory, saved to `data/rosters/m-<id>.txt`.
   - Note what you couldn't get as a gap in section 3.
2. **Enrich from dated guides:** dishes, prices and hours for the notable stalls. Write a small script with the `speclib` specs that appends places (see the East build in git history, PR #2 and #3). Apply the freshness rule.
3. **Geocode clusters and standalones** with OneMap. `zone`: ≤2.5 km from `home` means `home`, otherwise the zone of the area. Add the zone's MRT stations to `mrt[]`.
4. **Merge the roster** with `python3 tools/merge_roster.py data/rosters/<file>.txt`. Read the superseded list; it's a free freshness check.
5. **Run `python3 tools/validate.py`** and `python3 tools/coverage.py`.
6. **One PR per area.** Put the coverage table in the PR description. The owner merges, or asks Claude to merge.

Rough effort: about 1 session per zone of ~15 centres plus malls. The East took about 120 fetches.

### Monthly refresh (the only recurring token cost)
1. **Re-fetch rosters for changed centres and malls**, then diff against the `data/rosters/` file. New names are openings. Names that disappeared are likely closures: set `status: "closed"`, never delete (family logs reference ids). Update the roster file.
2. **Fold in family additions:** the family Sheet's `places_added` tab. Keep their ids. Needs the Sheet ID or an export.
3. **Read family menu photos** (`photos` tab, kind `menu`) and transcribe dishes and prices. Upgrade `listed` to `partial` or `detailed`.
4. **Closure/price check:** the oldest ~10% by `verified`.
5. **New openings:** search "new hawker stall / new restaurant <area> <month year>".
6. **Finish:** validate, run coverage, open a PR.

---

## 6. Decisions log

| Date | Decision | Why |
|---|---|---|
| 14 Oct | PWA on GitHub Pages, not a Google Sheet UI | Owner wants an app-like feel; family already uses Google logins on Pages apps |
| 14 Oct | Places in the repo, family data in a Google Sheet | Approving changes = merging a PR; data stays in the family's Drive; no server |
| 14 Oct | Zones: Home ground, East (+Pasir Ris, Changi, Marine Parade), North East, North, Central, West | Owner's layering; North added as its own zone |
| 14 Oct | Must-try is a flag, not a zone | Must-try places can be anywhere; the map shows them island-wide |
| 14 Oct | Diet info is only a minor tag (`diet[]`) | Not a household priority; shown as a badge when known |
| 15 Oct | Spreadsheets scope instead of drive.file + Picker | Sharing one file across accounts with drive.file needs the Picker plus an API key |
| 15 Oct | Reused TVWorld OAuth client for v1 | Origin and test users already set up; can swap later |
| 15 Oct | OneMap basemap instead of CARTO | CARTO started requiring an API key; OneMap is free and more detailed for Singapore |
| 15 Oct | Photos go in each uploader's Drive (`drive.file`), shared view-by-link | No API key, no Picker, and nobody grants access to their whole Drive; food photos are low-sensitivity |
| 15 Oct | Web photos are linked out to (Google Maps, Images, Burpple), not copied in | They're copyrighted. Embedding Google Places photos would need a paid API key, so it was deferred |
| 15 Oct | Zone by distance: ≤2.5 km from home = Home ground | Keeps 'home' meaning walkable or a short ride, whatever the planning area |
| 15 Oct | Guides older than Sep 2023: keep dishes, drop hours | Wrong hours are worse than none; the app assumes 7am–8pm for unknown hours when *Only open* is on |
| 15 Oct | 'Pick a centre' needs ≥2 stalls with confirmed hours open | Stops morning centres full of roster-only stalls winning at dinner |
| 15 Oct | Map groups restaurants into bubbles (Leaflet.markercluster via jsDelivr) | 61 Katong/Geylang restaurants were unreadable as separate pins |
| 15 Oct | Find the family sheet via a Drive search on new devices | localStorage-only family id made each device start a new family |
| 15 Oct | Malls as clusters with `type: "mall"` | Reuses centre UI (stall list, spin by centre, map pins) |
| 15 Oct | Chain outlets named "Brand (Mall)" | Ids must be unique and lists need to tell outlets apart; the app strips the brackets for web searches and match previews |
| 15 Oct | Completeness first: get a full roster (NEA count + stall list, or the mall directory) before enriching from guides | Guides only cover ~10–15 picks per place; the owner wants to know everything that's there |
| 15 Oct | Mall rosters from SingMalls; a dated guide's tenant beats the directory for the same unit | Directories are ~2024 snapshots; the clash is reported as superseded |
| 15 Oct | Data tooling committed in `tools/` | So any session (or a scheduled refresh) can build or refresh the same way |
| 15 Oct | Roster-only stalls are included as `listed` | The owner wants to know what's at a centre even without details; family photos fill in the gaps |

## 7. Next up / ideas
**Most likely next asks (in order):**
- [ ] **Close the East gaps** in section 3:
  - Mall directories for Tampines 1, Pasir Ris Mall, Eastpoint (+ Hawkers' Street), SingPost and Downtown East.
  - Stall rosters for Old Airport Rd, Haig Rd, Bedok Interchange, Changi Village and Fengshan.
  - The unbuilt Geylang-area centres.
- [ ] **"Worth the trip" island-wide list** from the **Michelin Bib Gourmand 2026** hawker selection. These would be `must_try` places in other zones, and the zone map already supports them. Sources:
  - https://danielfooddiary.com/2026/07/28/bibgourmand2026/
  - https://guide.michelin.com/sg/en/article/michelin-guide-ceremony/singapore-bib-gourmand-2026
- [ ] **Next zones:** North East, North, Central, West. Use the section 5 pipeline: roster first.
- [ ] **Monthly refresh as a scheduled task.** It needs a decision on how it reads the family Sheet's `places_added` and `photos` tabs.

**Later / ideas:**
- [ ] Coffeeshops: there's no official list. Map them per area from guides, plus the family's *Add a stall*.
- [ ] NEA cleaning/closure dates per centre (data.gov.sg) to hide centres during cleaning weeks.
- [ ] A "Still here ✓" quick confirm for `listed` stalls; it would feed the refresh.
- [ ] Google Places photos/menus in-app. This needs a paid Google Maps Platform key, so it's deferred.
- [ ] Owner: real two-account test of the family invite flow; photo upload on a phone.
