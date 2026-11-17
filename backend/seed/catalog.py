"""Deterministic generator for the demo listing catalog.

No LLM is used: descriptions are assembled from templates with variation so
each one differs. Everything is driven by a seeded ``random.Random``, so the
same codes (GK-BAN-001 ...) always map to the same listing - the evals rely on it.

Each listing also carries ``tags`` (setting, audiences, nearby places) that are
*not* stored in the DB; they describe what the text says and let the eval
dataset compute acceptable matches for soft preferences like "quiet".
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass, field

CITY = "Pune"
SQFT_PER_GUNTHA = 1089


# --------------------------------------------------------------------------- localities
@dataclass(frozen=True)
class Locality:
    name: str
    code: str
    rate: tuple[int, int]  # apartment INR per sq ft (min, max)
    metro: float  # probability a listing here is near a metro station
    school: float  # probability a listing here is near a school
    settings: tuple[str, ...]  # surroundings, repeated to weight
    landmarks: tuple[str, ...]
    work_hub: str
    work_minutes: tuple[int, int]


LOCALITIES: tuple[Locality, ...] = (
    Locality("Baner", "BAN", (9500, 14000), 0.55, 0.7,
             ("quiet_lane", "park_facing", "green_hills", "main_road", "township"),
             ("Baner Hill", "the Balewadi High Street restaurants", "the Mumbai-Bengaluru highway"),
             "the Baner and Balewadi business parks", (5, 15)),
    Locality("Wakad", "WAK", (7000, 10500), 0.3, 0.7,
             ("quiet_lane", "main_road", "township", "lively_market", "park_facing"),
             ("Dange Chowk", "the Mumbai-Bengaluru highway", "Wakad bridge"),
             "Hinjewadi IT Park", (10, 20)),
    Locality("Kothrud", "KOT", (10500, 15500), 0.7, 0.85,
             ("quiet_lane", "quiet_lane", "park_facing", "green_hills", "lively_market", "main_road"),
             ("Karve Road", "Paud Road", "the old Kothrud market"),
             "the Deccan and Karve Road offices", (10, 25)),
    Locality("Hinjewadi", "HIN", (6500, 9500), 0.5, 0.5,
             ("township", "township", "main_road", "green_hills", "quiet_lane"),
             ("Hinjewadi Phase 1", "Hinjewadi Phase 3", "Maan Road"),
             "Hinjewadi IT Park", (5, 15)),
    Locality("Viman Nagar", "VIM", (10000, 15000), 0.45, 0.75,
             ("quiet_lane", "lively_market", "main_road", "park_facing"),
             ("Pune Airport", "Nagar Road", "the Viman Nagar cafe street"),
             "the Kharadi and Nagar Road IT offices", (10, 20)),
    Locality("Kharadi", "KHA", (8500, 13000), 0.2, 0.6,
             ("township", "main_road", "park_facing", "quiet_lane", "riverside"),
             ("Nagar Road", "the Mula-Mutha riverside", "the Kharadi bypass"),
             "the Kharadi IT parks", (5, 15)),
    Locality("Aundh", "AUN", (10000, 15000), 0.4, 0.85,
             ("quiet_lane", "quiet_lane", "park_facing", "lively_market", "leafy"),
             ("ITI Road", "Parihar Chowk", "Savitribai Phule Pune University"),
             "the Baner and Shivajinagar offices", (15, 25)),
    Locality("Hadapsar", "HAD", (6500, 9500), 0.1, 0.7,
             ("main_road", "lively_market", "township", "quiet_lane"),
             ("Solapur Road", "the Hadapsar industrial estate", "the Hadapsar gaon market"),
             "Magarpatta IT park", (10, 20)),
    Locality("Pimple Saudagar", "PIM", (7000, 10000), 0.35, 0.8,
             ("quiet_lane", "park_facing", "lively_market", "township"),
             ("Shivar Chowk", "the Aundh-Ravet BRTS road", "Rahatani"),
             "Hinjewadi IT Park", (20, 30)),
    Locality("Bavdhan", "BAV", (8000, 12000), 0.1, 0.6,
             ("green_hills", "green_hills", "quiet_lane", "riverside"),
             ("Chandni Chowk", "the Ram Nadi riverside", "the Mumbai-Bengaluru highway"),
             "Hinjewadi and Kothrud", (15, 25)),
    Locality("Magarpatta", "MAG", (9000, 13000), 0.1, 0.8,
             ("township", "township", "park_facing", "quiet_lane"),
             ("the central garden of the township", "Solapur Road", "Hadapsar"),
             "Magarpatta IT park", (2, 10)),
    Locality("Koregaon Park", "KOP", (14000, 22000), 0.3, 0.7,
             ("leafy", "leafy", "quiet_lane", "lively_market", "park_facing"),
             ("North Main Road", "Bund Garden", "Pune railway station"),
             "the Camp and Kalyani Nagar offices", (10, 20)),
)
LOCALITY_BY_NAME = {loc.name: loc for loc in LOCALITIES}

# Where the non-apartment types tend to be.
TYPE_AFFINITY: dict[str, dict[str, float]] = {
    "villa": {"Bavdhan": 3, "Koregaon Park": 3, "Aundh": 2, "Baner": 2, "Kharadi": 1,
              "Wakad": 1, "Hinjewadi": 1, "Kothrud": 1},
    "house": {"Kothrud": 2, "Aundh": 2, "Koregaon Park": 2, "Hadapsar": 2, "Bavdhan": 1.5,
              "Viman Nagar": 1, "Pimple Saudagar": 1},
    "plot_land": {"Hinjewadi": 3, "Bavdhan": 3, "Wakad": 2, "Hadapsar": 2, "Kharadi": 2,
                  "Baner": 1},
    "commercial": {"Koregaon Park": 2, "Viman Nagar": 2, "Kharadi": 2, "Magarpatta": 2,
                   "Hinjewadi": 2, "Baner": 2},
}

# 150 apartments + 12 houses + 10 villas + 20 plots + 8 commercial = 200
SLOTS: list[tuple[str, int | None]] = (
    [("apartment", 1)] * 25 + [("apartment", 2)] * 60 + [("apartment", 3)] * 50
    + [("apartment", 4)] * 15 + [("house", None)] * 12 + [("villa", None)] * 10
    + [("plot_land", None)] * 20 + [("commercial", None)] * 8
)


# --------------------------------------------------------------------------- phrase pools
SETTING_SENTENCES: dict[str, list[str]] = {
    "quiet_lane": [
        "It sits on a quiet, low-traffic lane, so the surroundings stay peaceful even on weekday evenings.",
        "Tucked into a calm residential pocket of {loc}, you hear birdsong more than traffic.",
        "The building is on a peaceful internal road away from main-road noise, ideal if you want a calm, serene home.",
        "A quiet lane with very little through traffic keeps things calm and safe for evening walks.",
    ],
    "park_facing": [
        "The living room and balcony look straight onto a landscaped public park with a jogging track.",
        "It is park facing, with open green views and fresh air from the garden across the road.",
        "A well-kept neighbourhood park with a children's play area is right opposite the gate.",
    ],
    "main_road": [
        "It is right on the main road, so buses, autos and shops are steps away, though the front side does get traffic noise.",
        "With direct main-road access commuting is easy, and the stretch stays busy and well lit late into the evening.",
        "Being on a busy main road, it has excellent visibility and connectivity, with some traffic noise during peak hours.",
    ],
    "green_hills": [
        "Surrounded by greenery with views of the nearby hills, the area feels open, calm and a little cooler than the city centre.",
        "The windows open to a green hill view, and mornings here are quiet and fresh.",
        "Set against the hills, the neighbourhood is green, peaceful and great for morning walks.",
    ],
    "township": [
        "It is part of a large gated township with wide internal roads, gardens, a clubhouse and round-the-clock security.",
        "The gated community has landscaped gardens and plenty of safe space for kids to cycle and play.",
        "It is inside a well-managed gated society with its own convenience shops, gardens and security.",
    ],
    "riverside": [
        "It is close to the riverside, with a pleasant breeze and a green, quiet promenade for evening walks.",
        "Being near the river, the surroundings are green and calm with open views.",
    ],
    "lively_market": [
        "It is in a lively neighbourhood with cafes, restaurants and a busy market within walking distance.",
        "Everything is walkable here: a bustling market, eateries and banks are just around the corner.",
        "The area is vibrant and well connected, with shops and cafes buzzing till late.",
    ],
    "leafy": [
        "It is on a leafy, tree-lined avenue known for its old trees and quiet, upscale feel.",
        "Old banyan and gulmohar trees line the lane, keeping it shaded, green and quiet.",
    ],
}
PLOT_SETTING_SENTENCES: dict[str, list[str]] = {
    "township": [
        "It is part of a gated plotted layout with internal tar roads, street lights and a security cabin.",
        "The plot is inside a gated layout with a common garden, wide internal roads and a guarded entrance.",
    ],
}
QUIET_SETTINGS = {"quiet_lane", "green_hills", "riverside", "leafy"}
SETTING_TITLE_PREFIX = {
    "park_facing": "Park-facing", "quiet_lane": "Quiet", "green_hills": "Hill-view",
    "township": "Gated-society", "riverside": "Riverside", "leafy": "Leafy-lane",
}

SCHOOL_PHRASES = [
    "a reputed CBSE school is a five-minute walk away",
    "two good schools are within a kilometre",
    "an international school is just down the road",
    "the school run is short, with several schools nearby",
]
METRO_PHRASES = [
    "the metro station is about {n} minutes on foot",
    "a metro station is within a kilometre",
    "the new metro line has a station close by",
]
HOSPITAL_PHRASES = [
    "a multispecialty hospital is a short drive away",
    "a 24x7 hospital is about {n} minutes away",
    "clinics and a large hospital are close by",
]
MARKET_PHRASES = [
    "supermarkets and a vegetable market are a short walk away",
    "daily needs like grocery stores, pharmacies and a weekly market are close",
    "a busy local market and supermarkets are around the corner",
]
NEARBY_PREFIXES = ["Nearby, ", "In terms of location, ", "For daily life, ", "", "Around it, "]

AMENITIES = [
    "a swimming pool", "a gym", "a clubhouse", "a children's play area", "a jogging track",
    "power backup", "24x7 security", "rainwater harvesting", "solar water heating",
    "a landscaped podium garden", "an indoor games room", "EV charging points",
]
OPENER_ADJ = ["bright", "spacious", "well-ventilated", "sunny", "airy", "well-maintained",
              "newly built", "east-facing", "ready-to-move", "thoughtfully planned"]

AUDIENCE_TEXT = {
    "working_professional": "working professionals",
    "working_couple": "a working couple",
    "first_time": "first-time buyers",
    "investor": "investors looking for steady rental income",
    "small_family": "a small family",
    "family_kids": "families with school-going kids",
    "growing_family": "a growing family",
    "large_family": "a large or joint family",
    "upgrade": "buyers upgrading to a premium home",
    "retiree": "retired couples who want a calm home",
    "garden_family": "families who want their own terrace and garden",
    "executive": "senior executives who want privacy",
    "build_own": "families planning to build their own bungalow",
    "land_investor": "long-term land investors",
    "business": "retail businesses and clinics",
    "office": "small offices and startups",
    "yield_investor": "investors seeking rental yield",
    "it_professional": "IT professionals who want a short commute",
}
SUITS_TEMPLATES = [
    "Ideal for {a} or {b}.",
    "A great fit for {a}, and it also suits {b}.",
    "Best suited to {a} and {b}.",
    "It works well for {a}; {b} will like it too.",
]


# --------------------------------------------------------------------------- spec
@dataclass
class ListingSpec:
    ref_code: str
    title: str
    city: str
    locality: str
    property_type: str
    bedrooms: int | None
    bathrooms: int | None
    area_value: float
    area_unit: str
    price_inr: int
    furnishing: str | None
    has_parking: bool
    near_school: bool
    near_metro: bool
    status: str
    description: str
    images: list[str]
    days_ago: int
    tags: set[str] = field(default_factory=set)


def _ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _round_price(p: float) -> int:
    step = 100_000 if p >= 10_000_000 else 50_000
    return max(step, int(round(p / step)) * step)


def _join(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def _a(word: str) -> str:
    """Indefinite article for ``word`` ("an airy", "an 8-storey", "a 12-storey")."""
    w = word.lower()
    vowel = w[:1] in "aeiou" or w.startswith(("8", "11-", "18-"))
    return f"{'an' if vowel else 'a'} {word}"


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


# --------------------------------------------------------------------------- builders
def _nearby_sentence(rng: random.Random, loc: Locality, school: bool, metro: bool,
                     setting: str, tags: set[str]) -> str:
    # School / metro must always be mentioned when the boolean column is true,
    # so they are never dropped. Optional extras fill up to 4 items, and their
    # tags are recorded only if the phrase actually makes it into the text.
    required: list[str] = []
    if school:
        required.append(rng.choice(SCHOOL_PHRASES))
    if metro:
        required.append(rng.choice(METRO_PHRASES).format(n=rng.randint(5, 12)))
    optional: list[tuple[str | None, str]] = []
    if rng.random() < 0.7:
        m = rng.randint(*loc.work_minutes)
        optional.append(("near_work_hub", rng.choice([
            f"it is about {m} minutes to {loc.work_hub}",
            f"{loc.work_hub} can be reached in about {m} minutes"])))
    if rng.random() < 0.55:
        optional.append(("near_hospital", rng.choice(HOSPITAL_PHRASES).format(n=rng.randint(5, 15))))
    if setting == "lively_market" or rng.random() < 0.5:
        optional.append(("near_market", rng.choice(MARKET_PHRASES)))
    if len(required) + len(optional) < 3 and rng.random() < 0.8:
        lm = rng.choice(loc.landmarks)
        optional.append((None, rng.choice([f"{lm} is a short drive away", f"it is close to {lm}"])))
    if len(required) + len(optional) < 2:
        optional.append(("near_market", rng.choice(MARKET_PHRASES)))
    rng.shuffle(optional)
    kept = optional[: max(0, 4 - len(required))]
    tags.update(tag for tag, _ in kept if tag)
    items = required + [phrase for _, phrase in kept]
    rng.shuffle(items)
    prefix = rng.choice(NEARBY_PREFIXES)
    body = _join(items)
    return (prefix + body if prefix else _cap(body)) + "."


def _setting_sentence(rng: random.Random, setting: str, loc: Locality, is_plot: bool) -> str:
    pool = PLOT_SETTING_SENTENCES.get(setting) if is_plot else None
    return rng.choice(pool or SETTING_SENTENCES[setting]).format(loc=loc.name)


def _furnishing_clause(furnishing: str | None) -> str:
    return {
        "fully_furnished": "comes fully furnished with a modular kitchen, wardrobes, ACs and lights",
        "semi_furnished": "is semi-furnished with a modular kitchen and wardrobes",
        "unfurnished": "is unfurnished, so you can do up the interiors your way",
    }.get(furnishing or "", "")


def _suits_sentence(rng: random.Random, audiences: list[str], tags: set[str]) -> str:
    picked = audiences[:2] if len(audiences) >= 2 else audiences + ["investors looking for steady rental income"]
    for a in picked:
        tags.add(f"suits:{a}")
    template = rng.choice(SUITS_TEMPLATES)
    return template.format(a=AUDIENCE_TEXT.get(picked[0], picked[0]),
                           b=AUDIENCE_TEXT.get(picked[1], picked[1]))


def _audiences(rng: random.Random, ptype: str, bhk: int | None, school: bool,
               setting: str, metro: bool) -> list[str]:
    if ptype == "apartment":
        base = {
            1: ["working_professional", "first_time", "investor", "working_couple"],
            2: ["working_couple", "small_family", "first_time", "investor"],
            3: ["growing_family", "small_family", "upgrade"],
            4: ["large_family", "upgrade"],
        }[bhk or 2]
    elif ptype == "house":
        base = ["large_family", "garden_family"]
    elif ptype == "villa":
        base = ["large_family", "executive", "upgrade"]
    elif ptype == "plot_land":
        base = ["build_own", "land_investor"]
    else:
        base = ["business", "office", "yield_investor"]
    base = list(base)
    rng.shuffle(base)
    if ptype in {"apartment", "house", "villa"}:
        if school and (bhk or 0) >= 2:
            base.insert(0, "family_kids")
        if setting in QUIET_SETTINGS and ptype != "apartment" or (setting in QUIET_SETTINGS and rng.random() < 0.3):
            base.insert(rng.randint(0, 1), "retiree")
        if metro and (bhk or 0) <= 2 and rng.random() < 0.6:
            base.insert(rng.randint(0, 1), "it_professional")
    # de-duplicate, keep order
    seen: set[str] = set()
    return [a for a in base if not (a in seen or seen.add(a))]


def _build(rng: random.Random, ref_code: str, loc: Locality, ptype: str, bhk: int | None,
           status: str, days_ago: int) -> ListingSpec:
    tags: set[str] = set()
    rate = rng.randint(*loc.rate)
    school = rng.random() < loc.school
    metro = rng.random() < loc.metro

    if ptype == "commercial":
        setting = rng.choice(["main_road", "main_road", "lively_market"])
    elif ptype == "plot_land":
        setting = rng.choice(["quiet_lane", "green_hills", "main_road", "township", "riverside"]
                             if loc.name in {"Bavdhan", "Kharadi"} else
                             ["quiet_lane", "green_hills", "main_road", "township"])
    else:
        setting = rng.choice(loc.settings)
    tags.add(f"setting:{setting}")
    if setting in QUIET_SETTINGS:
        tags.add("quiet")
    if setting in {"park_facing", "green_hills", "riverside", "leafy"}:
        tags.add("green")

    bedrooms: int | None = None
    bathrooms: int | None = None
    furnishing: str | None = None
    unit = "sqft"
    sentences: list[str] = []
    images: list[str] = []

    if ptype == "apartment":
        assert bhk is not None
        area = {1: (450, 650), 2: (680, 1050), 3: (1050, 1550), 4: (1650, 2500)}[bhk]
        area_value = float(rng.randrange(area[0], area[1], 5))
        bedrooms = bhk
        bathrooms = {1: 1, 2: 2, 3: rng.choice([2, 3, 3]), 4: rng.choice([3, 4, 4])}[bhk]
        has_parking = rng.random() < (0.75 if bhk == 1 else 0.92)
        furnishing = rng.choices(["unfurnished", "semi_furnished", "fully_furnished"], [35, 45, 20])[0]
        total = rng.randint(7, 24)
        floor = rng.randint(1, total)
        price = area_value * rate * rng.uniform(0.94, 1.06) * (1 + 0.004 * floor)
        adj = rng.choice(OPENER_ADJ)
        sentences.append(
            f"{_cap(_a(adj))} {bhk} BHK apartment of {int(area_value):,} sq ft carpet area on the "
            f"{_ordinal(floor)} floor of {_a(f'{total}-storey')} tower in {loc.name}."
        )
        sentences.append(_setting_sentence(rng, setting, loc, False))
        sentences.append(_nearby_sentence(rng, loc, school, metro, setting, tags))
        amen = rng.sample(AMENITIES, 3)
        tags.update(f"amenity:{a}" for a in amen)
        parking = ("one covered car parking slot" if has_parking
                   else "two-wheeler parking only (no allotted car parking)")
        sentences.append(
            f"The society has {_join(amen)}; the flat has {bathrooms} bathroom"
            f"{'s' if bathrooms > 1 else ''}, {parking}, and {_furnishing_clause(furnishing)}."
        )
        prefix = SETTING_TITLE_PREFIX.get(setting) if rng.random() < 0.6 else None
        prefix = prefix or _cap(adj)
        title = f"{prefix} {bhk} BHK Apartment in {loc.name}"
        images = [f"apartment_{rng.randint(1, 4)}"] + rng.sample(
            ["interior_1", "interior_2", "interior_3"], rng.randint(0, 2))

    elif ptype == "house":
        bhk = rng.choice([2, 3, 3, 4])
        kind = rng.choice(["independent bungalow", "row house", "independent house"])
        area_value = float(rng.randrange(1400, 3200, 50))
        bedrooms, bathrooms = bhk, max(2, bhk - rng.randint(0, 1))
        has_parking = rng.random() < 0.85
        furnishing = rng.choices(["unfurnished", "semi_furnished", "fully_furnished"], [40, 45, 15])[0]
        price = area_value * rate * rng.uniform(1.0, 1.2)
        extra = rng.choice(["a private terrace", "a front garden", "a terrace and a small garden",
                            "a pooja room and a backyard"])
        sentences.append(f"A {bhk} BHK {kind} with {int(area_value):,} sq ft built-up area in {loc.name}.")
        sentences.append(_setting_sentence(rng, setting, loc, False))
        sentences.append(_nearby_sentence(rng, loc, school, metro, setting, tags))
        parking = "a car porch for two cars" if has_parking else "street parking only"
        sentences.append(
            f"It has {bathrooms} bathrooms, {extra} and {parking}, and {_furnishing_clause(furnishing)}."
        )
        title = f"{bhk} BHK {kind.title()} in {loc.name}"
        images = [f"house_{rng.randint(1, 2)}"] + rng.sample(["interior_1", "interior_2", "interior_3"],
                                                            rng.randint(0, 2))

    elif ptype == "villa":
        bhk = rng.choice([3, 4, 4, 5])
        area_value = float(rng.randrange(2400, 5200, 50))
        bedrooms, bathrooms = bhk, bhk + rng.randint(0, 1)
        has_parking = True
        furnishing = rng.choices(["unfurnished", "semi_furnished", "fully_furnished"], [20, 50, 30])[0]
        price = area_value * rate * rng.uniform(1.2, 1.4)
        feats = rng.sample(["a private lawn", "a double-height living room", "a home theatre room",
                            "a servant room", "a private plunge pool", "a rooftop deck",
                            "an attached garden for every bedroom"], 2)
        tags.update(f"feature:{f}" for f in feats)
        sentences.append(
            f"A {bhk} BHK villa with {int(area_value):,} sq ft of built-up space in a gated villa "
            f"community in {loc.name}."
        )
        sentences.append(_setting_sentence(rng, setting, loc, False))
        sentences.append(_nearby_sentence(rng, loc, school, metro, setting, tags))
        sentences.append(
            f"It offers {_join(feats)}, {bathrooms} bathrooms and private parking for two cars, and "
            f"{_furnishing_clause(furnishing)}."
        )
        title = f"{bhk} BHK Villa in {loc.name}"
        images = [f"villa_{rng.randint(1, 2)}"] + rng.sample(["interior_1", "interior_2", "interior_3"],
                                                            rng.randint(1, 2))

    elif ptype == "plot_land":
        has_parking = False
        if rng.random() < 0.3:
            unit = "guntha"
            area_value = float(rng.choice([1, 1, 2, 2, 3, 4, 5]))
            sqft = area_value * SQFT_PER_GUNTHA
            area_text = f"{int(area_value)} guntha (about {int(sqft):,} sq ft)"
            title_area = f"{int(area_value)} Guntha"
        else:
            area_value = float(rng.randrange(1000, 5000, 100))
            sqft = area_value
            area_text = f"{int(area_value):,} sq ft"
            title_area = f"{int(area_value):,} sq ft"
        price = sqft * rate * rng.uniform(0.45, 0.65)
        corner = rng.random() < 0.3
        if corner:
            tags.add("corner_plot")
        road = rng.choice([20, 25, 30, 40])
        sentences.append(
            f"{_cap(_a('corner ' + area_text if corner else area_text))} NA residential plot in "
            f"{loc.name} with a clear title."
        )
        sentences.append(_setting_sentence(rng, setting, loc, True))
        sentences.append(_nearby_sentence(rng, loc, school, metro, setting, tags))
        sentences.append(
            f"It has a compound wall on {rng.choice([2, 3, 4])} sides, a {road} ft approach road and "
            f"water and electricity connections at the gate."
        )
        title = f"{title_area} Residential Plot in {loc.name}"
        images = [f"plot_{rng.randint(1, 2)}"]

    else:  # commercial
        kind, kind_title = rng.choice([
            ("ground-floor shop with wide frontage", "Ground-floor Shop"),
            ("office space in a commercial building", "Office Space"),
            ("showroom space on the main frontage", "Showroom"),
        ])
        area_value = float(rng.randrange(300, 2600, 25))
        bathrooms = rng.choice([1, 1, 2])
        has_parking = rng.random() < 0.6
        furnishing = rng.choice(["unfurnished", "fully_furnished"])
        price = area_value * rate * rng.uniform(1.25, 1.5)
        sentences.append(f"{_cap(_a(f'{int(area_value):,}'))} sq ft {kind} in {loc.name}.")
        sentences.append(_setting_sentence(rng, setting, loc, False))
        sentences.append(_nearby_sentence(rng, loc, school, metro, setting, tags))
        fitout = ("is fully fitted with workstations, a cabin and a pantry" if furnishing == "fully_furnished"
                  else "is a bare shell ready for your own fit-out")
        sentences.append(
            f"It has {bathrooms} washroom{'s' if bathrooms > 1 else ''}, power backup and "
            f"{'dedicated visitor parking' if has_parking else 'street parking only'}, and {fitout}."
        )
        title = f"{kind_title} in {loc.name}"
        images = [f"commercial_{rng.randint(1, 2)}"]

    audiences = _audiences(rng, ptype, bedrooms, school, setting, metro)
    sentences.append(_suits_sentence(rng, audiences, tags))

    if school:
        tags.add("near_school")
    if metro:
        tags.add("near_metro")

    return ListingSpec(
        ref_code=ref_code, title=title, city=CITY, locality=loc.name, property_type=ptype,
        bedrooms=bedrooms, bathrooms=bathrooms, area_value=area_value, area_unit=unit,
        price_inr=_round_price(price), furnishing=furnishing, has_parking=has_parking,
        near_school=school, near_metro=metro, status=status, description=" ".join(sentences),
        images=list(dict.fromkeys(images)), days_ago=days_ago, tags=tags,
    )


def _assign_localities(rng: random.Random) -> list[Locality]:
    """Non-apartments go by affinity; apartments then fill the least-used localities."""
    counts: Counter[str] = Counter()
    assigned: list[Locality | None] = [None] * len(SLOTS)
    for i, (ptype, _) in enumerate(SLOTS):
        if ptype == "apartment":
            continue
        weights = [TYPE_AFFINITY[ptype].get(loc.name, 0.2) for loc in LOCALITIES]
        loc = rng.choices(LOCALITIES, weights)[0]
        assigned[i] = loc
        counts[loc.name] += 1
    apt_idx = [i for i, (p, _) in enumerate(SLOTS) if p == "apartment"]
    rng.shuffle(apt_idx)
    for i in apt_idx:
        low = min(counts.get(loc.name, 0) for loc in LOCALITIES)
        options = [loc for loc in LOCALITIES if counts.get(loc.name, 0) == low]
        loc = rng.choice(options)
        assigned[i] = loc
        counts[loc.name] += 1
    return [a for a in assigned if a is not None]


def generate_catalog(seed: int = 42) -> list[ListingSpec]:
    """The 200 approved listings (about 10% sold), in a stable order."""
    rng = random.Random(seed)
    locs = _assign_localities(rng)
    order = list(range(len(SLOTS)))
    rng.shuffle(order)
    sold = set(rng.sample(order, len(SLOTS) // 10))

    per_loc: Counter[str] = Counter()
    specs: list[ListingSpec] = []
    for i in order:
        ptype, bhk = SLOTS[i]
        loc = locs[i]
        per_loc[loc.code] += 1
        code = f"GK-{loc.code}-{per_loc[loc.code]:03d}"
        specs.append(_build(rng, code, loc, ptype, bhk,
                            "sold" if i in sold else "available", rng.randint(1, 120)))
    specs.sort(key=lambda s: s.ref_code)
    return specs


PENDING_SHAPES: list[tuple[str, str, int | None]] = [
    ("Baner", "apartment", 2),
    ("Wakad", "apartment", 3),
    ("Kothrud", "house", None),
    ("Hinjewadi", "plot_land", None),
    ("Kharadi", "apartment", 1),
]


def generate_pending(seed: int = 7) -> list[ListingSpec]:
    """Five seller-submitted listings waiting in the admin approval queue."""
    rng = random.Random(seed)
    return [
        _build(rng, f"GK-PND-{i:03d}", LOCALITY_BY_NAME[loc], ptype, bhk, "available", rng.randint(0, 3))
        for i, (loc, ptype, bhk) in enumerate(PENDING_SHAPES, start=1)
    ]


if __name__ == "__main__":  # quick look: python -m seed.catalog
    cat = generate_catalog()
    print(Counter(s.locality for s in cat))
    print(Counter(s.property_type for s in cat))
    for s in cat[:5]:
        print(f"\n{s.ref_code} | {s.title} | Rs {s.price_inr:,} | {s.status}\n{s.description}\n{sorted(s.tags)}")
