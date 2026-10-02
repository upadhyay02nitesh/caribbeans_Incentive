"""Overwrite every demo image slot in content/media.py with a hand-curated,
on-theme Unsplash photo (same file paths, so no template changes).

Supersedes the hashed pool in fetch_placeholders.py, which produced repeats and
off-brand shots. Run from the project root:

    python scripts/fetch_curated_images.py

Real client photography still replaces all of this before launch.
"""
import concurrent.futures as cf
import os
import urllib.request

STATIC = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "static")
P = {
    0: "1507525428034-b723cf961d3e", 1: "1519046904884-53103b34b206", 3: "1540202404-a2f29016b523",
    5: "1520250497591-112f2f40a3f4", 7: "1566073771259-6a8506099945", 8: "1582719508461-905c673771fd",
    9: "1551882547-ff40c63fe5fa", 10: "1414235077428-338989a2e8c0", 12: "1559339352-11d035aa65de",
    13: "1504674900247-0877df9cc836", 14: "1467003909585-2f8a72700288", 16: "1519671482749-fd09be7ccebf",
    17: "1511795409834-ef04bbd61622", 18: "1464366400600-7168b8af9bc3", 19: "1492684223066-81342ee5ff30",
    21: "1540575467063-178a50c2df87", 23: "1515187029135-18ee286d815b", 24: "1567899378494-47b22a2ae96a",
    25: "1605281317010-fe5ffe798166", 26: "1569263979104-865ab7cd8d13", 27: "1540946485063-a40da27545f8",
    28: "1506929562872-bb421503ef21", 29: "1510414842594-a61c69b5ae57", 32: "1468413253725-0d5181091126",
    33: "1437719417032-8595fd9e9dc6", 34: "1432405972618-c60b0225b8f9", 35: "1433086966358-54859d0ed716",
    40: "1551024709-8f23befc6f87", 41: "1470337458703-46ad1756a187", 42: "1544025162-d76694265947",
    44: "1519225421980-715cb0215aed", 47: "1544161515-4ab6ce6db874", 48: "1540555700478-4be289fbecef",
    49: "1506126613408-eca07ce68773", 50: "1545205597-3d9d02c29597", 51: "1552196563-55cd4e45efb3",
    52: "1602002418082-a4443e081dd1", 53: "1613490493576-7fde63acd811", 55: "1564013799919-ab600027ffc6",
    57: "1561501900-3701fa6a0864", 60: "1509233725247-49e657c54213", 62: "1596040033229-a9821ebd058d",
    63: "1488459716781-31db52582fe9", 65: "1511381939415-e44015466834", 68: "1513364776144-60967b0f800f",
    69: "1565193566173-7a0ee3dbe261", 70: "1511671782779-c97d3d27a1d4", 72: "1528605248644-14dd04022da1",
    73: "1529156069898-49953e39b3ac", 74: "1559494007-9f5847c49d94", 75: "1530053969600-caed2596d242",
    76: "1502933691298-84fc14542831", 77: "1437622368342-7a3d73a34c8f", 81: "1583212292454-1fe6229603b7",
    85: "1512100356356-de1b84283e18", 92: "1559128010-7c1ad6e1b6a5", 96: "1504681869696-d977211a5f4c",
    97: "1502680390469-be75c86b636f", 99: "1506953823976-52e1fdc0149a", 101: "1535262412227-85541e910204",
    102: "1517760444937-f6397edcbbcd", 104: "1484821582734-6c6c9f99a672", 105: "1439405326854-014607f694d7",
    106: "1471922694854-ff1b63b20054", 112: "1558642452-9d2a7deb7f62", 113: "1525596662741-e94ff9f26de1",
    114: "1519690889869-e705e59f72e1", 116: "1520483601560-389dff434fdf", 117: "1552733407-5d5c46c3bb3b",
    119: "1540541338287-41700207dee6",
}

SLOTS = {
    "img/hero/scene-1.jpg": 85, "img/hero/scene-2.jpg": 8, "img/hero/scene-3.jpg": 18, "img/hero/scene-4.jpg": 0,
    "img/hero-poster.jpg": 0, "img/fallback.jpg": 0,
    "img/itinerary/day1.jpg": 85, "img/itinerary/day2.jpg": 23, "img/itinerary/day3.jpg": 72,
    "img/itinerary/day4.jpg": 27, "img/itinerary/day5.jpg": 105,
}
ISLANDS = {  # hero, card, the-island, gastronomy, experiences
    "saint-martin": (28, 1, 29, 12, 27),
    "st-barth": (24, 53, 52, 10, 25),
    "anguilla": (104, 33, 101, 14, 51),
    "british-virgin-islands": (96, 26, 92, 40, 77),
    "dominica": (117, 35, 34, 63, 102),
    "grenada": (32, 116, 113, 62, 81),
    "barbados": (119, 60, 7, 42, 97),
}
for slug, ids in ISLANDS.items():
    for name, i in zip(("hero", "card", "the-island", "gastronomy", "experiences"), ids):
        SLOTS[f"img/islands/{slug}/{name}.jpg"] = i
EXPERIENCES = {
    "curated-experiences": (5, 8, 16, 53, 3, 57),
    "caribbean-legacy": (113, 55, 12, 29, 92, 57),
    "island-flavors": (13, 14, 10, 63, 40, 41),
    "across-sand-and-sea": (27, 28, 24, 76, 117, 104),
    "crafted-in-the-caribbean": (68, 69, 65, 62, 112, 114),
    "unique-team-building-experiences": (73, 72, 50, 97, 25, 23),
    "quiet-island-moments": (49, 47, 48, 51, 9, 74),
    "the-art-of-execution": (17, 18, 44, 21, 19, 114),
    "sustainability-and-authenticity": (77, 81, 75, 99, 106, 34),
}
for slug, ids in EXPERIENCES.items():
    for n, i in enumerate(ids, start=1):
        SLOTS[f"img/experiences/{slug}/{n}.jpg"] = i


def fetch(item):
    rel, idx = item
    width = 1920 if ("hero" in rel or "scene" in rel) else 1400
    height = "&h=2200" if rel.endswith("card.jpg") else ""
    url = f"https://images.unsplash.com/photo-{P[idx]}?w={width}{height}&q=78&auto=format&fit=crop"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = r.read()
    with open(os.path.join(STATIC, rel), "wb") as f:
        f.write(data)
    return rel


if __name__ == "__main__":
    with cf.ThreadPoolExecutor(10) as ex:
        done = list(ex.map(fetch, SLOTS.items()))
    print(len(done), "images written")
