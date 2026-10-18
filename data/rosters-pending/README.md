# Pending rosters (Central malls, work in progress, 18 Oct 2026)

Collected but **not merged yet**: the mall clusters don't exist in `places.json`, so `merge_roster.py` would refuse them.
To finish: add each cluster (geocode with OneMap, `zone: "central"`), move the file to `data/rosters/`, run `merge_roster.py`.

| File | Mall | Outlets | Source | Hours |
|---|---|---|---|---|
| m-plaza-singapura.txt | Plaza Singapura | 88 | CapitaLand API | no |
| m-raffles-city.txt | Raffles City | 95 | CapitaLand API (entity `rafflescitysingaporeshoppingcentre`) | no |
| m-funan.txt | Funan | 75 | CapitaLand API (entity `funan_1640709664`) | no |
| m-bugis-junction.txt | Bugis Junction | 81 | CapitaLand API | no |
| m-bugis-plus.txt | Bugis+ | 37 | CapitaLand API (entity `bugis`) | no |
| m-junction-8.txt | Junction 8 (Bishan) | 62 | CapitaLand API (entity `junction`) | no |
| m-clarke-quay.txt | Clarke Quay | 32 | CapitaLand API; nightclubs/bars-only removed | no |
| m-the-centrepoint.txt | The Centrepoint | 28 | Frasers store search | yes |
| m-tiong-bahru-plaza.txt | Tiong Bahru Plaza | 64 | Frasers store search | yes |
