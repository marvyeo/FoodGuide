# Makan Map — project state

_Last updated: 15 Oct 2026, ~01:40 SGT (v1.2: East zone build, clustered map, zone filter)_

A family food map of Singapore. You filter by when, how far, budget, dine-in/tapau and craving, then spin for a stall or a food centre. You log and rate meals, and you collect stamps and badges. The app is installable from GitHub Pages and works offline. Day-to-day use costs no AI tokens. Claude is only involved to build or refresh the places data.

- **Repo:** `marvyeo/FoodGuide`
- **App URL:** https://marvyeo.github.io/FoodGuide/ (GitHub Pages, live)
- **Status:** v1.1 live. Photos and the completeness data are tested in a headless browser with mocked Google APIs, but not yet with a real Google account.
- **Data:** PRs #1 (Home ground completeness), #2 (East zone) and #3 (East malls) merged 15 Oct. Live: 773 places, 19 food centres, 15 malls.

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
- `mrt[]`: stations used for the "nearest MRT" line. Currently only Home ground stations; add more with each zone.
- `sources{}`: key → {name, url, date}. Places cite these keys.
- `clusters[]`: food centres / coffeeshops. Fields: `id, name, type, address, lat, lng, zone, stalls_total` (NEA cooked-food stall count, used for the coverage bar), `notes, sources`.
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

## 2. What's built (v1.1)

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
- **Explore:** food centres sorted by distance, each with a coverage bar ("14 of ~72 stalls mapped"); all places; bookmarks; search by name, dish or cuisine.
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

| Zone | Centres | Stalls/places | Notes |
|---|---|---|---|
| Home ground | 5 (630 Bedok Reservoir, 216 Bedok North, 85 Fengshan, 511 Kaki Bukit, 538 Bedok North) | 189 (91 detailed, 14 partial, 84 listed) | Built 15 Oct 2026; completeness pass same day (PR) |
| East malls | 15: Bedok Mall*, Tampines Mall, Tampines 1, Century Square, Jewel, White Sands, Pasir Ris Mall, Eastpoint, Changi City Point, Parkway Parade, i12 Katong, PLQ, Paya Lebar Square, SingPost Centre, Downtown East | 206 (158 detailed) | Built 15 Oct (PR #3). `clusters[].type = "mall"`, `stalls_total` null. Gaps: Eastpoint's Hawkers' Street food court; i12 and Downtown East have old or undated guides |
| East | 14 (Old Airport Rd, Bedok Interchange*, Bedok South, Bedok Corner, Tampines Round, Our Tampines Hub, Pasir Ris Central, Changi Village, Marine Parade, Haig Rd, Geylang Serai, Dunman, East Coast Lagoon, Eunos) | 378 incl. 61 restaurants/cafés (Tampines, Katong/Joo Chiat, Geylang) | Built 15 Oct 2026 (PR #2). *Within 2.5 km of home, so zoned Home ground |
| North East, North, Central, West | – | – | Later |

Per-centre coverage after the completeness PR (mapped / NEA cooked-food stalls):
- Blk 630: 31 / 36
- Bedok 216: 48 / 82
- Fengshan 85: 26 / 72. This is the weakest: there's no trustworthy online roster, so it relies on the family adding stalls.
- Kaki Bukit 511: 34 / 42
- Blk 538: 40 / 40. The NEA count is from 2024 and the roster lists 36 units; the extra entries come from guides.

The NEA counts include stalls that sell drinks, and some units sit vacant, so 100% isn't always reachable.

Standalones: 10 restaurants and cafés along Bedok Reservoir Rd and Bedok North.

Must-try flags so far: Seng Hiang BCM, Xing Ji BCM, Chai Chee Pork Porridge, Seng Kee Black Chicken Herbal Soup, Chin Lee Restaurant.

**East gaps:**
- No recent guide (newest is 2019–2023), so no confirmed hours: Marine Parade, Haig Road, Geylang Serai, Eunos.
- Biggest centre is the least covered: Old Airport Road, 41 of 168 stalls.
- Not built yet: Geylang-area centres (Sims Place, Circuit Road ×3, Aljunied, Geylang Bahru, Upper Boon Keng), Blk 58 New Upper Changi Rd, Marine Terrace 50A, and Kallang Estate.

### Source notes (read before refreshing)
- **Most current sources used:**
  - Daniel Food Diary (May 2026) for 216.
  - kopitiam.com.sg (Apr/May 2026) for 630 and 85. Prices in their articles are sparse.
  - Eatbook (Jul 2023, Sep 2024) for prices and for 511 and the standalones.
  - Completeness pass sources:
    - Seth Lui: 85 (updated Jul 2025) and 216 (updated Aug 2025).
    - HungryGoWhere 216 (Jul 2026).
    - kopitiam.com.sg: 511 (Sep 2026) and 538 (Jan 2026).
    - HawkerPedia 511 (Sep 2025), Singapore Verified 85 (Feb 2024), Burpple (undated).
  - Every place stores `verified` and `sources` with dates, and the app shows them.
- **Older data:** entries verified 2024-09 (the standalones and the 511 stalls) are the most likely to be stale. Check those first on the next refresh.
- **hawker.guide** (undated rosters with unit, name and cuisine) is **useful but must be cross-checked**:
  - Its 216, 511 and 538 rosters match 2025–26 guides closely, so they're used for `listed` entries.
  - Its "Blk 85 Bedok North St 4" page actually lists **Redhill** stalls, so it's not used for Fengshan.
  - Its Blk 630 unit numbers partly disagree with kopitiam.com.sg.
  - Where unit numbers conflict, the newer dated guide wins and the roster entry is kept without a unit.
- More hawker.guide roster pages, checked 15 Oct:
  - Usable: Blk 16 Bedok South, Blk 137 Tampines, Blk 84 Marine Parade (some odd 3-digit units, which were dropped), Blk 4A Eunos, Dunman, East Coast Lagoon, Changi Village, Geylang Serai.
  - Geylang Serai has generic "#02-01…#02-45 Geylang Serai <dish>" rows, which were skipped.
  - `bedok-food-centre` mixes Bedok Corner with Bedok Interchange, so it wasn't used.
  - Old Airport Road, 208B and Haig Road pages didn't load.
- **Data-entry tooling:** the East build used a small compact-spec helper (hours like `"Tue-Sun 10:00-18:00; Sat 11:00-21:00"`, dishes like `"Lor mee $4/$5 | ..."`). It isn't in the repo. Re-create a similar helper for the next zone, or edit `places.json` directly.
- **kopitiam.com.sg** articles are recent but sometimes contain obvious errors, such as two stalls sharing one unit. Cross-check their units against a roster.
- **There is no official stall-level dataset.** data.gov.sg has:
  - Centre-level counts: *List of Government Markets & Hawker Centres*, 107 centres, 6,121 cooked-food stalls, last updated Jun 2024.
  - *NEA Licensed Eating Establishments*: restaurants and shops, not hawker stalls, last updated Jun 2024.
- **Geocoding:** the OneMap search API (`onemap.gov.sg/api/common/elastic/search?searchVal=<postal>&returnGeom=Y`) works without a token.

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

## 5. Refresh runs (the only recurring token cost)

**Monthly refresh**, as a scheduled task or on request. Output is **one PR** against `data/places.json`.
1. Read `PROJECT_STATE.md` and `data/places.json`.
2. **Fold in family additions:** read the family Sheet's `places_added` tab and merge new stalls into `places.json`, keeping their `id`s so existing logs still point at them. This needs the Sheet ID, or the owner exports the tab.
3. **Closure check:** take the ~10% of places with the oldest `verified` dates, search each one, and update hours and prices or set `status: "closed"`. Never delete a place, because logs reference it.
4. **Read family photos:** for each new `menu` photo in the Sheet's `photos` tab, open the public image (`drive.google.com/thumbnail?id=<file_id>&sz=w1600`) and transcribe the dishes and prices into that place. Upgrade `listed` to `partial` or `detailed`, and add a `family-photo` source dated with the photo date.
5. **New openings:** search "new hawker stall / new restaurant <area> <month year>" for each mapped zone and add the confirmed ones.
6. Bump `updated`, and set `verified` on everything that was touched.
7. Validate: valid JSON, unique ids, every `sources` key exists, every hours slot matches `HH:MM-HH:MM`, days are `0`–`6`. Then open the PR with a summary.

Rough cost: about 15–30 searches/fetches per run (one short session).

**Zone build**, one session per zone, done the same way as Home ground:
1. Pull the NEA centre list for the zone (for `stalls_total`) and geocode with OneMap.
2. Find the 2025–26 food guide for each centre (DFD, Eatbook, Seth Lui, kopitiam.com.sg) and record stall, unit, dishes, prices and hours.
3. Add the area's notable restaurants and cafés, plus MRT stations.

Home ground took about 40 fetches for 5 centres and 50 places.

### Effort to map Singapore
- **Centres and well-known stalls:** about 107 NEA centres; at 4–8 fetches each, roughly 10–14 sessions. Expect ~15–25% of stalls per centre to come with good detail, because only the notable ones are written about.
- **Every stall** (~6,100 cooked-food stalls in NEA centres alone, plus coffeeshops): not achievable from online sources. The long tail comes from **family mapping**, using *Add a stall* during visits, which a refresh then folds into `places.json`. The coverage bars and the Mapper badge exist to drive this.

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
| 15 Oct | Roster-only stalls are included as `listed` | The owner wants to know what's at a centre even without details; family photos fill in the gaps |

## 7. Next up / ideas
- [ ] Owner setup (section 4) and a real sign-in test with two accounts.
- [ ] Build the East zone (Bedok Interchange, Bedok South, Chai Chee, Tampines, Simei, Pasir Ris, Changi Village, Marine Parade, Katong/Joo Chiat, Geylang).
- [ ] Monthly refresh as a scheduled task (needs a decision on how it reads `places_added`).
- [ ] "Worth the trip" island-wide must-try list (~20) ahead of full zone builds.
- [ ] Possibly: NEA cleaning/closure dates per centre (data.gov.sg dataset) to hide centres during cleaning weeks.
- [ ] Merge PR #1, then PR #2.
- [ ] Next session: "Worth the trip" list from the **Michelin Bib Gourmand 2026** hawker selection. The session ran out of usage while fetching it. Sources found:
  - Daniel Food Diary, 28 Jul 2026: https://danielfooddiary.com/2026/07/28/bibgourmand2026/
  - The official Michelin page: https://guide.michelin.com/sg/en/article/michelin-guide-ceremony/singapore-bib-gourmand-2026
- [ ] Then: the Geylang-area centres (see East gaps), and recent guides for Marine Parade, Haig Road, Geylang Serai and Eunos.
- [ ] Zones still to build: North East, North, Central, West.
- [ ] Fengshan 85: get a real roster, either by the family walking it with *Add a stall* plus signboard photos, or from a future source.
- [ ] Possibly: Google Places photos inside the app. This needs a Google Maps Platform API key with billing, restricted to `marvyeo.github.io`.
- [ ] Possibly: a "Still here ✓" quick confirm for `listed` stalls without a full log.
