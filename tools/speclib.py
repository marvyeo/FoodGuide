"""Shared helpers for building data/places.json. Python 3, standard library only.

Compact specs used by data-entry scripts:
  hours("Tue-Sun 10:00-18:00; Sat,Sun 11:00-14:00,17:00-21:00")  -> [["023456", ["10:00-18:00"]], ...]
      days: Mon..Sun, ranges wrap (Fri-Mon), "Daily". End before start = past midnight. "" -> [] (unknown).
  dishes("Lor mee $4/$5 | Rojak from $3 | Chendol")             -> [{"name","price","price_note"?}, ...]
  band(dishes) -> 1..4 price band from the lower-median price ($<8, <20, <50, 50+)
  guess_cuisine("Ajisen Ramen") -> "japanese"  (keyword heuristic for roster-only entries; default "other")
"""
import re, json, math, unicodedata

DAYS = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}
CUISINES = ["chicken-rice", "noodles", "carrot-cake", "yong-tau-foo", "rice", "vegetarian", "braised", "snacks", "drinks", "western",
            "dessert", "zi-char", "soup", "porridge", "dumplings", "bbq-seafood", "malay", "indian", "japanese", "korean", "thai", "cafe", "other"]

def _days(tok):
    tok = tok.lower().strip()
    if tok in ("daily", "everyday", "all"): return "0123456"
    out = []
    for part in tok.split(","):
        part = part.strip()
        if "-" in part:
            a, b = [DAYS[x.strip()[:3]] for x in part.split("-")]
            i = a
            while True:
                out.append(i)
                if i == b: break
                i = (i + 1) % 7
        else: out.append(DAYS[part[:3]])
    return "".join(str(x) for x in sorted(set(out)))

def hours(spec):
    if not spec: return []
    rules = []
    for rule in [r.strip() for r in spec.split(";") if r.strip()]:
        m = re.match(r"^([A-Za-z,\- ]+?)\s+(\d.*)$", rule)
        if not m: raise ValueError(f"bad hours rule: {rule!r}")
        sl = [s.strip() for s in m.group(2).split(",")]
        for s in sl:
            if not re.fullmatch(r"\d\d:\d\d-\d\d:\d\d", s): raise ValueError(f"bad slot {s!r} in {spec!r}")
        rules.append([_days(m.group(1)), sl])
    return rules

def dishes(spec):
    out = []
    for item in [x.strip() for x in (spec or "").split("|") if x.strip()]:
        m = re.search(r"\$(\d+(?:\.\d+)?)", item)
        if not m: out.append({"name": item}); continue
        name = re.sub(r"\s+(from|S)$", "", item[:m.start()].strip().rstrip("—-–:(").strip()).strip()
        d = {"name": name or item, "price": float(m.group(1))}
        note = item[m.start():].strip()
        if note != f"${m.group(1)}" or re.search(r"\bfrom\b", item):
            d["price_note"] = (("from " if re.search(r"\bfrom\b", item) else "") + note).strip()
        out.append(d)
    return out

def band(ds):
    ps = sorted(d["price"] for d in ds if "price" in d)
    if not ps: return 1
    p = ps[(len(ps) - 1) // 2]
    return 1 if p < 8 else 2 if p < 20 else 3 if p < 50 else 4

_CUISINE_KEYWORDS = [  # first match wins; order matters
    ("vegetarian", r"vegan|vegetarian|greendot|elemen|\bveg\b"),
    ("dessert", r"dessert|gelat|ice cream|yogurt|yogost|yole|llaollao|smooy|swensen|baskin|cendol|chendol|durian|mochi|lady m|cheesecake|churros|apple strudel|tart|natural|kones|sweet hut|jin hor|nine fresh|ji de chi|xing fu|frozen|ice lab|pudding"),
    ("drinks", r"\btea\b|\bthe\b|\bthé\b|koi|liho|chicha|chagee|gong cha|playmade|sharetea|bober|r&b|alley|tuk tuk cha|chatramue|boost|juice|coconut|fruits|kopi|kaya|toast|coffee|starbucks|luckin|huggs|flash coffee|arabica|kopitime|chug|mr bean|xixiang|ya kun|wine connection|bottles|bean\b|hey long|tea pulse|herbal tea|oleh oleh"),
    ("japanese", r"ramen|sushi|\bdon\b|donburi|kaisendon|udon|soba|yakiniku|tonkatsu|katsu|tempura|izakaya|shokudo|teppan|pepper lunch|sukiya|yoshinoya|tenya|ippudo|kanada|keisuke|ajisen|itacho|sushiro|genki|tamago|aburi|ichiban|kajiken|menzo|maki-san|tori-q|toriten|osaka ohsho|gyudon|ichikokudo|tanuki|hoshino|tokyo"),
    ("korean", r"korean|seoul|bibimbap|nene|bonchon|jinjja|kko kko|ajumma|manna|chicken run|pizza maru|seorae|paik|coffeesarang|sarang|kimchi"),
    ("thai", r"thai|sanook|siam|boat noodle|yum yum"),
    ("malay", r"penyet|nasi|ayam|padang|malay|tiffin|indonesia|penang|peramakan|rempapa|violet oon|red ginger|tingkat|papparich|boleh|malaysia"),
    ("indian", r"briyani|biryani|prata|thosai|vadai|madura|rollgaadi|sankranti|kebab|pita"),
    ("dumplings", r"dim sum|tim sum|dian xin|xiao long|din tai fung|paradise dynasty|crystal jade|tim ho wan|canton|swee choon|pau\b|bao\b|dumpling|treasures|tsui wah|legendary hong kong"),
    ("snacks", r"bread|bakery|boulang|cake|cupcake|puff|curry puff|old chang kee|polar|donut|doughnut|krispy|j\.co|dunkin|auntie anne|pretzel|famous amos|cookie|bengawan|bee cheng|lim chee guan|thye moh|kee wah|croissant|beard papa|you tiao|chateraise|proofer|paul\b|delifrance|paris baguette|maison|pezzo|potato corner|mr you tiao|four leaves|breadtalk|primadeli|pancake|crolo|rice dumpling|tai chong kok|tai cheong|royce|chocolat|laderach|tong garden|irvins|snack|butter studio|duke|melvados|lavender|sourbombe|backyard bakers|eclair|nesuto|rich & good|kueh"),
    ("western", r"burger|pizza|pasta|steak|grill|western|kfc|mcdonald|jollibee|texas chicken|4fingers|wingstop|wing\.stop|nando|kenny rogers|long john|subway|stuff'd|crave|jack's place|hot tomato|fish & chips|shake shack|a&w|chicken|sub\b|cheese burger|salad|soup spoon|guzman|tacos|chimichanga|cantine|lobster|tapas|trattoria|mamma mia|saizeriya|pastamania|salvo|bistro|bar and grill|bar & grill|meathouse|fatburger|deli|eat\.|pita|monster planet|ps\.cafe|cafe|café"),
    ("zi-char", r"seafood|jumbo|tunglok|putien|dian xiao er|soup restaurant|zi char|kitchen|paradise classic|boon tong kee|house of teochew|tai er|suancai|tanyu|duck|roast|kam's|tun xiang|encik tan|wok hey|wok master|han's"),
    ("noodles", r"noodle|mee|mian|mixian|lanzhou|kolo|laksa|wanton|fishball|ban mian|mala tang|ma la tang|nuodle|mahua"),
    ("soup", r"bak kut teh|lao huo tang|soup|herbal"),
    ("rice", r"rice|bento|chicken rice|wee nam kee|delibowl|5 little bears|food court|kopitiam|food republic|food market|cookhouse|koufu"),
    ("other", r"hotpot|hot pot|haidilao|mala|grilled fish|steamboat|beauty in the pot|coucou|shabu|buffet"),
]
# Known brands the keyword rules get wrong or miss (extend as you go).
KNOWN = {
 "so pho": "other", "fei siong": "rice", "big fish small fish": "western", "bbq express": "rice", "blackball": "dessert", "chalk farm": "dessert",
 "choc spot": "dessert", "dough culture": "snacks", "fluff stack": "dessert", "fong sheng hao": "snacks", "gao peng": "zi-char", "gelare": "dessert",
 "juewei": "snacks", "janice wong": "dessert", "jiak zhey": "rice", "joe & dough": "cafe", "junshin": "japanese", "kazo": "snacks",
 "koong woh tong": "drinks", "kraftwich": "snacks", "lee wee": "snacks", "lu xiao xian": "snacks", "maccha house": "japanese", "mixue": "drinks",
 "ninja mama": "japanese", "onkei": "japanese", "poke theory": "western", "poulet bijou": "western", "prive": "cafe", "qi ji": "snacks",
 "rive gauche": "dessert", "rocky master": "snacks", "shang pin hot pot": "other", "shang social": "dumplings", "shi tang": "porridge",
 "suki-ya": "japanese", "swee heng": "snacks", "toss & turn": "dessert", "viva loca": "western", "ximenjie": "snacks", "yu ba fang": "rice",
 "yu kee": "braised", "yuba hut": "rice", "zing": "western", "ecreative": "dessert", "itea": "drinks", "myeureka": "snacks", "rroll": "dessert",
 "smol": "cafe", "aroma truffle": "snacks", "andersen's": "dessert", "attap house": "malay", "chinese tofu magician": "snacks", "dulcet": "dessert",
 "elfuego": "western", "fragrance": "snacks", "krate": "drinks", "mmmm!": "western", "oleole": "western", "re.juve": "drinks",
 "soul alife": "western", "xycd": "drinks", "fun toast": "drinks", "kaffe & toast": "drinks", "toast box": "drinks", "wine connection": "western",
 "the coffee bean": "cafe", "starbucks": "cafe", "huggs": "cafe", "flash coffee": "cafe", "luckin": "cafe", "another bean": "cafe", "arabica": "cafe",
 "hoshino coffee": "japanese", "o'coffee club": "cafe", "paul": "cafe", "delifrance": "cafe", "pazzion": "cafe", "tim hortons": "cafe",
 "tamjai": "noodles",
 # added 18 Oct 2026 with the official mall directories
 "ipot": "other", "haidilao": "other", "paradise hotpot": "other", "108 matcha": "dessert", "amacha": "drinks", "an acai": "dessert", "acai": "dessert",
 "brotherbird": "dessert", "churn": "dessert", "collin's": "western", "fieldnotes": "cafe", "grains & co": "rice", "hawkers' street": "rice",
 "i love taimei": "snacks", "keming": "dumplings", "kuriya": "japanese", "namu bulgogi": "korean", "nippon bite": "japanese", "plum village": "zi-char",
 "popeyes": "western", "rrooll": "dessert", "shiok pan": "snacks", "sinpopo": "cafe", "tsuzumi": "dessert", "yew kee": "braised",
 "50 years taste": "drinks", "50 taste": "drinks", "abundance": "zi-char", "auntie peng": "snacks", "butahage": "japanese", "chapanda": "drinks",
 "ministry of rojak": "snacks", "nan yang dao": "drinks", "57 mala": "other", "a hot hideout": "other", "andes by astons": "western",
 "butter & cream": "dessert", "koo kee": "noodles", "nandhana": "indian", "primadeli": "snacks", "sakura family": "japanese", "shi li fang": "other",
 "veggie house": "vegetarian", "xi men jie": "snacks", "baba nyonya": "malay", "cha mulan": "drinks", "creamie sippies": "dessert", "fish & co": "western",
 "heytea": "drinks", "lotteria": "korean", "monarchs & milkweed": "western", "mrs pho": "noodles", "nong geng ji": "zi-char", "queic": "snacks",
 "royal host": "western", "sugarbelly": "dessert", "tutto": "western", "wild coco": "drinks", "wu fang zhai": "snacks", "yes lemon": "drinks",
 "shan 山里有": "zi-char", "home's favourite": "snacks", "kele": "snacks", "dabba street": "indian", "food arena": "rice", "laaziiz": "western",
 "niu hong hong": "noodles", "roll gaadi": "indian", "saigon": "noodles", "supergreen": "western", "uncle john": "rice", "yangguofu": "noodles",
 "aroycado": "western", "cookboys": "western", "en seeds": "vegetarian", "nainai": "zi-char", "yo mama": "dessert", "barcook": "snacks",
 "first bowl": "noodles", "happy bites": "snacks", "khao hom": "thai", "o.bba": "korean", "redman": "snacks", "tsujiri": "dessert",
 "white restaurant": "noodles", "yayoi": "japanese", "empire chinese": "zi-char", "hakka yu": "zi-char", "honeyworld": "snacks", "lenu": "noodles",
 "madam ang": "snacks", "pat's oven": "snacks", "bites by scarlett": "snacks", "cedele": "cafe", "chao chao xiang": "zi-char", "chen's": "zi-char",
 "harrianns": "malay", "henri charpentier": "dessert", "nikutosake": "japanese", "pura brasa": "western", "rumel": "western", "carl's jr": "western",
 "chateraise": "dessert", "lau wang": "zi-char", "lickers": "dessert", "honeybee": "dessert", "sloppy shack": "western", "hahahotpot": "other",
 "ajiya": "japanese", "singapura heritage": "malay", "jyu yae": "japanese", "eminami": "japanese", "kin kao": "thai", "tiong bahru yong tao": "yong-tau-foo",
 "delifrance": "cafe", "crown prince": "zi-char", "wok": "zi-char", "cha yu fan hou": "rice", "each-a-cup": "drinks", "segar": "malay",
 "kopitiam": "rice", "kopi & tarts": "drinks", "kopifellas": "drinks", "pancake king": "snacks", "munchi": "snacks", "ottie": "snacks", "fragrance bak kwa": "snacks",
 "godiva": "dessert", "laderach": "dessert", "mdm ling": "snacks", "yu cookies": "snacks", "kang ji": "snacks", "eighteen plum": "snacks",
 "battercatch": "western", "eighteen plum": "snacks", "hainan second street": "rice", "ji xiang": "snacks", "little pond": "soup", "nespresso": "cafe", "shanghai tan": "dumplings", "xiang xiang hunan": "zi-char", "alchemist": "cafe", "im qalb": "korean", "kenangan": "cafe", "kuan zhai alley": "zi-char", "ygf malatang": "noodles", "delibowl": "rice", "toast & roll": "drinks", "cut butchery": "other", "sgfr": "other", "cellarbration": "other", "57°c mala": "other", "ipot mala": "other", "big fish": "western", "tai er": "zi-char",
}
def guess_cuisine(name):
    n = unicodedata.normalize("NFKD", re.sub(r"\s*\([^)]*\)$", "", name)).encode("ascii", "ignore").decode().lower().strip()
    for k, v in KNOWN.items():
        if n.startswith(k) or n == k: return v
    for c, pat in _CUISINE_KEYWORDS:
        if re.search(pat, n): return c
    return "other"

def norm(s):
    """Brand key for matching: lowercase, drop (...) labels, punctuation, 'the', common suffixes."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode() if s.isascii() is False else s
    s = re.sub(r"\([^)]*\)", "", s.lower())
    s = re.sub(r"[’'`]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\b(the|restaurant|cafe|express|singapore|sg|store|outlet|by koufu)\b", " ", s)
    return re.sub(r"\s+", "", s)

def unit_key(u):
    """'#B1-37/38' -> 'B1-37' (first unit) for clash checks."""
    m = re.search(r"#?\s*(B\d|\d\d)\s*-\s*(K?\d+[A-Z]?)", (u or "").upper())
    return f"{m.group(1)}-{m.group(2)}" if m else ""

def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def km(a, b):
    R = 6371; r = math.radians
    h = math.sin(r(b[0] - a[0]) / 2) ** 2 + math.cos(r(a[0])) * math.cos(r(b[0])) * math.sin(r(b[1] - a[1]) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

def load(path="data/places.json"): return json.load(open(path))
def save(D, path="data/places.json"): json.dump(D, open(path, "w"), ensure_ascii=False, indent=1)

# ---- free-text opening hours from mall directories -------------------------------------------
_DN = {"mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6, "sun": 0}
_DAYWORD = r"(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?"
_TIME = r"(\d{1,4})(?:[:.](\d{2}))?\s*(am|pm|noon|midnight)?"

def _t(h, m, ap, end=False):
    h, m = int(h), int(m or 0)
    if h > 24 and not m: h, m = h // 100, h % 100            # "930pm" without a separator
    ap = (ap or "").lower()
    if ap == "pm" and h < 12: h += 12
    if ap in ("am", "midnight") and h == 12: h = 0
    if ap == "noon": h = 12
    if h == 24: h = 0
    if not (0 <= h < 24 and 0 <= m < 60): raise ValueError
    return f"{h:02d}:{m:02d}"

def _dayset(txt):
    """'Monday to Thursday, Sunday' / 'Mon-Fri' / 'Daily' -> set of ints, or None if no day words."""
    t = txt.lower()
    if re.search(r"daily|everyday|every day|mon(day)?\s*(to|-|–)\s*sun(day)?", t) and not re.search(r"except", t): return set(range(7))
    out, found = set(), False
    for m in re.finditer(rf"({_DAYWORD})(?:\s*(?:to|-|–)\s*({_DAYWORD}))?", t):
        found = True
        a = _DN[m.group(1)[:3]]
        if m.group(2):
            b = _DN[m.group(2)[:3]]; i = a
            while True:
                out.add(i)
                if i == b: break
                i = (i + 1) % 7
        else: out.add(a)
    return out if found else None

def free_hours(text):
    """Best-effort parse of directory opening hours ('Monday to Sunday ; 11am to 10pm (last order 9.30pm)',
    '(Monday, Tuesday) 08:00 AM - 12:00 AM; (Friday, Saturday) 24 Hours', 'Mon-Fri: 8am-8pm; Sat & Sun: 9am-9pm').
    Returns the hours() list, or [] when the text is missing or ambiguous (wrong hours are worse than none)."""
    if not text: return []
    t = re.sub(r"\([^)]*last order[^)]*\)|last orders?[^;]*|kitchen[^;]*", " ", text, flags=re.I)
    t = re.sub(r"\(([^)]*)\)", r" \1 ", t)                      # '(Monday, Tuesday)' -> plain
    t = re.sub(r"\b(and|&)\s*(ph|public holidays?|eve of ph)\b|\bph\b|public holidays?|eve of ph|including", " ", t, flags=re.I)
    t = t.replace("–", "-").replace("—", "-")
    t = re.sub(r"24\s*h(ou)?rs?", "00:00 am - 12:00 midnight", t, flags=re.I)
    t = re.sub(r"12\s*midnight", "12:00 midnight", t, flags=re.I)
    rng = re.compile(rf"{_TIME}\s*(?:-|to)\s*{_TIME}", re.I)
    rules, cur, last_end, pending_slots = {}, None, 0, []
    try:
        for m in rng.finditer(t):
            between = t[last_end:m.start()]
            ds = _dayset(between)
            if ds is not None: cur = frozenset(ds)
            elif cur is None: cur = frozenset(range(7))
            elif rules and not re.fullmatch(r"[\s,;/&]*", between.replace("and", "")): return []
            elif rules and ";" in between and cur != frozenset(range(7)): return []   # 'Mon-Thu 7am-9pm; 7am-10pm' — which days?
            sap = m.group(3)
            if not sap and m.group(6) and m.group(6).lower() == "pm" and int(m.group(1)) < 12 and int(m.group(1)) <= int(m.group(4)): sap = "pm"
            elif not sap and m.group(6): sap = "am"
            a = _t(m.group(1), m.group(2), sap)
            b = _t(m.group(4), m.group(5), m.group(6), end=True)
            if a == "00:00" and b == "00:00": b = "24:00"
            rules.setdefault(cur, []).append(f"{a}-{b}")
            last_end = m.end()
    except (ValueError, KeyError):
        return []
    if not rules: return []
    seen = set()
    for ds in rules:
        if seen & ds: return []                                   # overlapping day sets — ambiguous
        seen |= ds
    return [["".join(str(d) for d in sorted(ds)), sl] for ds, sl in rules.items()]

def title_if_caps(name):
    """'CHICKEN HOTPOT & CO' -> 'Chicken Hotpot & Co' (only for ALL-CAPS directory names)."""
    letters = [c for c in name if c.isalpha() and c.isascii()]
    if not letters or not all(c.isupper() for c in letters): return name
    small = {"and", "of", "by", "the", "at", "x", "y", "&"}
    keep = {"BBQ", "KFC", "SF", "KOI", "BLVD", "R&B", "YGF", "HJH", "II", "III"}
    out = []
    for i, w in enumerate(name.split(" ")):
        if w in keep: out.append(w)
        elif i and w.lower() in small: out.append(w.lower())
        else: out.append(re.sub(r"[A-Za-z][A-Za-z’']*", lambda m: m.group(0)[0] + m.group(0)[1:].lower(), w))
    return " ".join(out)
