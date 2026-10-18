"""One-off build (19 Oct 2026): the four CBD food centres near the owner's office.
Lau Pa Sat, Amoy Street, Maxwell, Market Street. Owner's exception to the hawker scope.
Specs: Name | unit | dishes (; separated) | hours (free text) | cuisine | tags
Freshness rule: guides Sep 2023+ keep hours (detailed); older guides keep dishes only (partial).
Re-running is safe: existing ids are skipped.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from speclib import load, save, free_hours, dishes, band, slug

SOURCES = {
    "eb-maxwell": {"name": "Eatbook – Maxwell Food Centre guide", "url": "https://eatbook.sg/maxwell-food-centre/", "date": "2026-09"},
    "eb-amoy": {"name": "Eatbook – Amoy Street Food Centre guide", "url": "https://eatbook.sg/?p=28638", "date": "2026-07"},
    "eb-lps": {"name": "Eatbook – Lau Pa Sat food guide", "url": "https://eatbook.sg/lau-pa-sat/", "date": "2026-09"},
    "cn-lps": {"name": "City Nomads – Lau Pa Sat guide", "url": "https://citynomads.com/lau-pa-sat-hawker-centre-guide-8-stalls-for-authentic-hawker-fare-in-this-national-monument/", "date": "2020-02"},
    "sl-mkt": {"name": "Seth Lui – Market Street Hawker Centre guide", "url": "https://sethlui.com/market-street-hawker-centre-guide-singapore/", "date": "2022-05"},
}

CLUSTERS = [
    {"id": "c-lau-pa-sat", "name": "Lau Pa Sat", "type": "hawker", "address": "18 Raffles Quay, S048582", "lat": 1.280594, "lng": 103.850408,
     "zone": "central", "stalls_total": None, "sources": ["eb-lps", "cn-lps"],
     "notes": "Victorian cast-iron market (national monument), privately run, so not on NEA's list. Several stalls open 24 hours. Satay Street on Boon Tat Street opens in the evening."},
    {"id": "c-amoy-street", "name": "Amoy Street Food Centre", "type": "hawker", "address": "7 Maxwell Road (National Development Bldg Annex B), S069111", "lat": 1.279354, "lng": 103.846196,
     "zone": "central", "stalls_total": 134, "sources": ["nea", "eb-amoy"],
     "notes": "Two floors of CBD lunch favourites. Many stalls are weekday-lunch only and close by 2:30–3pm."},
    {"id": "c-maxwell", "name": "Maxwell Food Centre", "type": "hawker", "address": "1 Kadayanallur Street, S069184", "lat": 1.280331, "lng": 103.844747,
     "zone": "central", "stalls_total": 103, "sources": ["nea", "eb-maxwell"],
     "notes": "Chinatown's famous centre (Tian Tian chicken rice). Busy with tourists; open most of the day."},
    {"id": "c-market-street", "name": "Market Street Hawker Centre", "type": "hawker", "address": "86 Market Street (CapitaSpring), Levels 2–3", "lat": 1.284059, "lng": 103.849882,
     "zone": "central", "stalls_total": 56, "sources": ["nea", "sl-mkt"],
     "notes": "Reopened in CapitaSpring in 2022 (56 stalls, levels 2–3; NEA's 2024 list still shows 76 at the old Golden Shoe site). Mostly weekday breakfast and lunch."},
]

# Name | unit | dishes | hours | cuisine | tags
SPECS = {
 ("c-maxwell", "eb-maxwell"): """
Ye Lai Xiang Tasty Barbecue|#01-94|Hainanese-Western set from $10.50|Mon-Fri 12pm to 2:30pm, 6pm to 9pm|western|
Danlao|#01-73|Tomato egg rice $5; Luncheon meat egg rice $5.50; Chicken cutlet egg rice $6.50; Char siew egg rice $6.50|Mon-Sat 11am to 8:30pm, Sun 11am to 4pm|rice|
Ah Tai Hainanese Chicken Rice|#01-07|Chicken rice from $5|Wed-Mon 11am to 7:30pm|chicken-rice|
Fish Village|#01-32|HK-style steamed red grouper $25; HK-style steamed prawns from $9; Thai sauce scallops $14; Stir-fry kai lan $6|Mon-Sat 11am to 8pm|bbq-seafood|group
The 1950s Coffee|#01-90|Iced milk coffee $1.90; Kopi C siew dai $1.40|Tue-Sun 8:30am to 4pm|drinks|breakfast
Mr Appam|#01-99|Original appam (two) $4; Princess appam $4.30; Butterfly pea gula melaka appam $3.20; Cempedak appam $5|Wed-Mon 9am to 8pm|indian|
75 China Street Peanuts Soup|#01-57|Peanut soup $1.40; Red bean soup $1.40; Tau suan $1.40|Mon-Sat 7:30am to 2pm|dessert|breakfast,dessert
Taste Of Jiang Nan|#01-62|Xiao long bao (six) $5; Pork wanton in chilli oil with noodles $5.50|Sun-Fri 11:30am to 8:30pm|dumplings|
Tong Xin Ju Special Shanghai Tim Sum|#01-92|Fried dumplings (eight) $5.60; Hot & sour soup $4/$5/$6; Peking noodles/hor fun $4/$5/$6|Tue, Thurs-Sun 11:30am to 8:30pm|dumplings|
Tian Tian Hainanese Chicken Rice|#01-10/11|Chicken rice from $5|Tue-Sun 10am to 8pm|chicken-rice|
Lakeview (Upper Thomson) Kim Goreng Pisang|#01-30|You tiao from $1; Butterfly bun from $1; Ham chim peng from $1; Goreng pisang from $1; Fried nian gao from $1|Tue-Sun 24 hours|snacks|supper,24h
Old Nyonya|#01-04|Rendang chicken rice/nasi lemak $7; Laksa $5/$7|Daily 10am to 9pm|malay|
Sisaket Thai Food|#01-85|Green curry chicken/beef rice $8; Phad Thai $6.50; Basil chicken/beef rice $7.50/$8.50|Mon 12am to 8:30am, Tue-Sat 10am to 8:30pm, Sun 10am to 12am|thai|
Zhen Zhen Porridge|#01-54|Sliced fish, shredded chicken and century egg porridge $4/$5|Wed, Fri-Sun 5:30am to 2pm|porridge|breakfast
Yi Jia Teochew Fish Porridge Fish Soup|#01-66|Batang fish soup/porridge from $4|Mon-Sat 10:30am to 2:30pm|soup|
Maxwell Fuzhou Oyster Cake|#01-05|Fuzhou oyster cake $2.50|Mon-Sat 9am to 8pm|snacks|
Taste Fusion Hainanese Chicken Chop|#01-24|Hainanese chicken chop set $8.80; Pork chop rice from $6.80|Mon-Fri 12pm to 10pm, Sat 12pm to 9:30pm|western|
Ri Xin Snack Delights|#01-55|Ang ku kueh $1; Wa kueh $2; Huat kueh from $2.50|Daily 6pm to 10pm|snacks|
Fu Shun Jin Ji Shao La Mian Jia|#01-71|Roast meat rice/noodles from $4|Mon-Fri 12pm to 5pm, Sat 11:30am to 8pm|chicken-rice|
Hup Kee Wu Xiang Guan Chang|#01-97|Ngoh hiang from $0.50 a piece|Thurs-Tue 12pm to 6pm|snacks|
Jin Hua Fish Head Bee Hoon|#01-77|Fish soup bee hoon from $5|Fri-Wed 11:30am to 7:30pm|soup|
Heng Heng Ondeh-Ondeh & Tapioca Cake|#01-31|Ondeh ondeh (five) $3.70; Tapioca cake $0.80; Kueh lapis $2.20|Mon-Sat 7am to 1pm|snacks|breakfast
Fu Ji Fuzhou Fish Ball Wanton Noodles|#01-06|Spinach mee $5/$6/$7; Fuzhou fishball rou yan soup $5/$6/$7; Fishball wanton mee $5/$6/$7|Sun-Fri 11:30am to 9pm|noodles|
Pakistani Dum Biryani|#01-69|Chicken biryani $8; Mutton biryani $9|Mon-Fri 10:30am to 8pm|indian|
Hock Lai Seng|#01-26|Fishball bak chor mee from $5|Mon-Sat 7am to 3pm|noodles|breakfast
Somerset Delicacies|#01-60|Belachan fried rice $4/$5; Mixed seafood hor fun $4/$5|Sun-Fri 11am to 9pm|zi-char|
Sichuan Cuisine|#01-87|Grilled fish on paper $22; La zi ji $11; Cumin beef/pork $11; Mapo tofu $6|Sun-Fri 11am to 9pm|zi-char|group
Welcome Ren Min|#01-33|Craft beer by the glass $11–15; by the pint $13–19|Mon 5:30pm to 10:30pm, Tue-Thurs 12pm to 10:30pm, Fri 12pm to 11pm, Sat 12pm to 10:30pm, Sun 12pm to 9:30pm|drinks|
Sultan Kebab|#01-86|Kebab wraps from $9; Tombik from $10; Kunefe $14|Sat-Thurs 10am to 9pm|other|
Ah Zhong Roasted Delights|#01-93|Two-meat rice/noodles $5; Three-combo set from $10|Thurs-Mon 11am to 9pm|chicken-rice|
""",
 ("c-amoy-street", "eb-amoy"): """
Big Bowls Project|#02-90|Szechuan black bean salmon bowl $8; Mentaiko salmon bowl $9.50|Mon-Fri 11:30am to 2pm|rice|
Pepper Bowl|#02-102|Spring onion pork rice $6.30; Black pepper beef rice $6.80|Mon-Fri 10:30am to 2:30pm|rice|
Lagoon In A Bowl|#01-48|Mentaiko salmon bowl $11|Mon-Thurs 11am to 3pm, 6pm to 8pm, Fri 11am to 3pm|japanese|
Han Kee Fish Soup|#02-129|Sliced fish soup from $6|Mon-Fri 11am to 3pm|soup|
A Noodle Story|#01-39|Singapore-style ramen $10.80|Mon-Fri 10am to 8pm|noodles|
Piao Ji Fish Porridge|#02-100|Fish soup $8; Fish soup with prawns $10|Fri-Wed 10:30am to 3:30pm|soup|
Lian Hup Heng|#02-128|Orh nee tart $3.80; Almond financier $2.20; Lemon meringue tart $3.80|Mon-Fri 10:30am to 3pm|snacks|dessert
Hong Kee Beef Noodles|#01-42|Beef noodles soup from $6|Daily 9am to 2:30pm|noodles|
J2 Famous Crispy Curry Puff|#01-21|Curry puff from $2|Mon-Fri 8am to 3pm|snacks|breakfast
Coffee Break|#02-78|Kopi $1.90; Teh $1.90; Hazelnut mocha $4; Black sesame toast $3.50|Mon-Fri 7:30am to 2:30pm|drinks|breakfast
Ah Seng (Hai Nam) Coffee|#02-95|Kaya toast (two) $2.40; French toast $4; Kopi O $1|Sat-Mon 5:30am to 3pm, Tue 6am to 3pm, Wed 5:30am to 3pm|drinks|breakfast
Life Coffee|#02-134|Matcha latte $3.80; Egg cream hojicha $3.80; Vietnamese coffee|Mon-Fri 6:30am to 4pm, Sat 8am to 3:30pm, Sun 7:30am to 3:30pm|drinks|breakfast
Ah Ter Teochew Fishball Noodles|#01-14|Fishball noodles $4.50/$10; Fishball soup $6|Daily 7am to 2pm|noodles|breakfast
Amoy Street Fried Kway Teow|#01-01|Char kway teow from $4.50|Mon-Fri 7am to 2:30pm|noodles|
Rayyan's Waroeng Upnormal|#02-86|Ayam penyet $6; Balinese gyudon $7.50; Tempura prawn egg bowl $7.50|Mon-Fri 9am to 2:30pm|malay|
Mad Roaster|#02-107|Cold brew from $5.50; Honey butter latte $4.60; Kaya toast set $4.90|Mon-Fri 8am to 3pm, Sat 9am to 3pm|cafe|breakfast
Quan Ji|#01-56/57|Sweet and sour pork ribs from $13; Lala bee hoon $16; Prawn omelette from $13|Mon 11am to 1:30pm, Tue-Fri 11am to 9:30pm, Sat 3pm to 9:30pm|zi-char|group
Terry Katong Laksa|#01-28|Laksa from $5|Mon-Sat 8:30am to 5pm|noodles|
Swan City Noodle House|#02-105|Sarawak kampua noodles $5; Kolo mee $5|Mon-Fri 7:30am to 2:30pm, Sat 8am to 1:30pm|noodles|
Pho Hanoi|#02-104|Beef and brisket pho $7.20; Beef ball pho $6.50; Grilled pork vermicelli from $6.50|Mon-Fri 11am to 4pm|noodles|
Grandma Ban Mee|#01-07|Chilli ban mee $5.80|Mon-Fri 10am to 2:30pm|noodles|
Spicy Wife Nasi Lemak|#02-119|Aromatic chicken nasi lemak $6.50|Mon-Tue 10:45am to 2pm|malay|
Chun Feng Man Mian|#02-114|Truffle char siu noodles $9|Mon-Fri 9:30am to 3pm|noodles|
James Quesadillas & Brunch|#02-79|Pulled pork burrito $6.50/$8|Mon-Fri 7:30am to 2:30pm|western|
Good Day|#01-25|Beef hor fun $5; Sin chow hor fun $5; Sliced fish hor fun $5|Mon, Wed-Fri 7am to 4pm, Tue 7am to 2pm|noodles|
Gan Lao Zai|#02-123|Chilli crab noodles $8; Honey-glazed pork belly noodles $6.50|Mon-Sat 10:30am to 2:30pm|noodles|
Petit Krumbs|#02-133|Butter croissant $2.70; Taro mochi egg tart $2.50; Sourdough brownie $2|Mon-Fri 8:30am to 2:30pm|cafe|breakfast
Taco Liberation Co|#02-117|Veggie taco box from $5.90; Meat taco box from $8.50|Mon-Fri 8:30am to 2:30pm|western|
Pan's Kopi|#02-98|Taro butter toast $3.50; Iced matcha latte $3.50|Mon-Fri 7am to 3pm, Sat-Sun 8:30am to 3pm|drinks|breakfast
Wah Kee Noodle|#02-125|Wanton mee from $5; Mushroom noodles from $5|Mon-Fri 7am to 2:30pm|noodles|
""",
 ("c-lau-pa-sat", "eb-lps"): """
Chef Lup Roasted|Stall 4|Signature roast duck $59; Three-meat combo $20|Daily 24 hours|chicken-rice|24h,supper,group
Lao Fu Zi Fried Kway Teow|Stall 74-75|Char kway teow from $7.50; Laksa $7.50; Boiled cockles from $10|Sun-Fri 11:45am to 10pm, Sat 1pm to 10pm|noodles|
Thunder Tea Rice|Stall 25|Thunder tea rice $6.20; Thunder tea special $9.90|Daily 24 hours|vegetarian|24h,supper
Warong Pak Sapari|Stall 58|Mee soto $5.80|Daily 9am to 9pm|malay|
Nasi Lemak Ayam Taliwang|Stall 71|Nasi lemak ayam taliwang $9.20; Chicken fillet curry rice $7.50|Daily 9am to 12am|malay|supper
Delhi Express Indian Cuisine|Stall 11|Paneer butter masala from $6; Garlic naan $3; Butter chicken $8|Mon-Fri 11am to 10pm, Sat-Sun 12pm to 10pm|indian|
Seng Kee Local Delights|Stall 10|Fried kway teow $7.20; Laksa $7.50; Hokkien mee $7.50|Daily 8am to 10pm|noodles|
Qiu Lian Ban Mian|Stall 16|Ban mian $5.90; Tom yum ban mian $6.40; Dry noodles $7|Daily 10am to 8pm|noodles|
Rokus a.g.b.|Stall 24|Tteokbokki burger $13.90; Jumeokbap rice bowl $8.90; Folded kimbap $5.90|Daily 11am to 10:30pm|korean|
iEat Kitchen|Stall 56|Salted egg chicken rice $10; Chicken cutlet hor fun $6.80|Daily 10am to 10pm|rice|
Kallang Airport Wanton Noodle|Stall 57|Wanton noodles $6.20; Fried wantons $5/$7; Fried chicken wings $7.80|Daily 10am to 10pm|noodles|
Ri Ri Hong Mala Hot Pot|Stall 61-62|Mala hot pot||other|
Swatow Bai Le Braised Duck|Stall 9|Braised duck rice $5; Braised duck noodle set $5.50; Kway chap set $5.50|Daily 9am to 12:30am|braised|supper
Maya's Veggie Delight|Stall 47|Vegetarian butter chicken $8; Garlic naan $3|Daily 8am to 10:30pm|vegetarian|
Creme & Cone|Stall 79-87|Ice cream single $5.30 / double $6.30; Lemon mango tart $7.90|Sat-Thurs 12pm to 10pm, Fri 9am to 10pm|dessert|dessert
Butter & Cream Bakery|Stall 5-6|Choco explosion doffin $3.60; Classic cheese tart $2.90|Mon-Thurs 10am to 9pm, Fri 10am to 10pm, Sat 10:30am to 10pm, Sun 10:30am to 9pm|dessert|dessert
Nakoko|C-01|Acai bowl medium $6.50 / large $8.20; Yoghurt bowl from $6.20; Sundae $9.50|Daily 12pm to 10pm|dessert|dessert
Yuen Kee Dumpling|Stall 9A|Shrimp and pork dumplings (10) $9.80; Chilli oil la mian $11.80|Daily 10am to 9:30pm|dumplings|
Sing HK Kitchen|Stall 12|Scrambled egg garlic pork chop rice $7.30; Baked chicken dry noodles $6.80|Daily 10am to 11pm|rice|supper
Lion City Dim Sum|Stall 18|Large pork bao $2.30; Otah siew mai $2.80|Daily 24 hours|dumplings|24h,supper,breakfast
""",
 ("c-lau-pa-sat", "cn-lps"): """
Satay Club (Satay Street)|Stalls 7 & 8, Boon Tat St|Chicken, mutton, beef satay $0.70 a stick (min 10); Rice cake $1||bbq-seafood|supper,group
""",
 ("c-market-street", "sl-mkt"): """
Golden Nur|#03-11/12|Crispy chicken briyani $6.50; Curry chicken briyani $6.50; Soto ayam $3.50/$4||indian|
Hock Gooi Hainanese Curry Rice|#02-03|Pork chop set $3.50; Braised pork set $3.50; Curry chicken wing set $3.50||rice|breakfast
Sunrise Traditional Coffee & Toast|#02-15|Kopi O $1.10; Kaya toast set $3.50; Soft bun set $3.50||drinks|breakfast
Tiong Bahru Wanton Mee|#02-19|Wanton noodles $4.50/$5.50; Shredded chicken hor fun $4.50/$5.50||noodles|
Wei Nan Wang Hock Kian Lor Mee|#02-05|Lor mee $3.50/$4||noodles|
Ah Liang Ipoh Hor Fun|#02-04|Seafood hor fun $5/$6; Crab meat hor fun $4/$5; Shredded chicken hor fun $4/$5||noodles|
Tian Ci Traditional Prawn Noodle|#03-18|Prawn noodles from $4||noodles|
Yummy Nyonya Peranakan|#02-22|Beef rendang, chap chye and chye sim plate $5||malay|
Heng's Authentic Teochew Mee Pok|#02-20|Mee pok $4/$5/$6||noodles|
Market Street Nasi Lemak|#03-22|Nasi lemak sets $3.50–$4.30||malay|
""",
}

def main():
    D = load()
    D["sources"].update({k: v for k, v in SOURCES.items() if k not in D["sources"]})
    have = {c["id"] for c in D["clusters"]}
    for c in CLUSTERS:
        if c["id"] not in have: D["clusters"].append(c)
    cl = {c["id"]: c for c in D["clusters"]}
    ids = {p["id"] for p in D["places"]}
    added = 0
    for (cid, src), block in SPECS.items():
        c = cl[cid]; date = SOURCES[src]["date"]; fresh = date >= "2023-09"
        for line in block.strip().splitlines():
            name, unit, ds, hrs, cuisine, tags = [x.strip() for x in line.split("|")]
            pid = f"p-{cid}-{slug(name)}"
            if pid in ids: continue
            dl = dishes(ds.replace(";", " |"))
            h = free_hours(hrs) if (fresh and hrs) else []
            D["places"].append({
                "cluster": cid, "name": name, "unit": unit, "cuisine": cuisine, "dishes": dl,
                "hours": h or [], "sources": [src], "verified": date if fresh else "unconfirmed",
                "modes": ["dine", "takeaway"], "diet": ["vegetarian"] if cuisine == "vegetarian" else [],
                "tags": [t for t in tags.split(",") if t], "must_try": False, "status": "open",
                "price_band": band(dl) if dl else 1, "id": pid, "lat": c["lat"], "lng": c["lng"],
                "zone": c["zone"], "address": c["address"],
                "confidence": "detailed" if h else ("partial" if dl else "listed"),
            })
            ids.add(pid); added += 1
    save(D)
    print("added", added)

if __name__ == "__main__":
    main()
