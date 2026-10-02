"""Downloads free stock imagery + a short demo video loop for every slot in
content/media.py, so the demo never shows a broken <img> or a grey
picsum.photos square.

Run once from the project root:

    python scripts/fetch_placeholders.py

Swapping in real client photography later is a one-file change to
content/media.py + dropping matching files under static/ — this script
never needs to run again once real assets exist.
"""

import hashlib
import os
import sys
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

STATIC_DIR = os.path.join(ROOT, "static")

# A curated pool of confirmed-reachable Unsplash CDN photos (tropical beach,
# sailing, rainforest, dining, market, villa, gala). No API key required —
# these are direct, permanent asset URLs. Real client photography replaces
# these before launch (see README "Swapping in real photography").
PHOTO_IDS = [
    "1507525428034-b723cf961d3e",
    "1544551763-46a013bb70d5",
    "1580541631950-7282082b53ce",
    "1519046904884-53103b34b206",
    "1573843981267-be1999ff37cd",
    "1520250497591-112f2f40a3f4",
    "1546484475-7f7bd55792da",
    "1540202404-a2f29016b523",
    "1544644181-1484b3fdfc62",
    "1544198365-f5d60b6d8190",
    "1512100356356-de1b84283e18",
    "1544984243-ec57ea16fe25",
    "1583212292454-1fe6229603b7",
    "1601581875309-fafbf2d3ed3a",
    "1519861531473-9200262188bf",
    "1546587348-d12660c30c50",
    "1524492412937-b28074a5d7da",
    "1500375592092-40eb2168fd21",
    "1571902943202-507ec2618e8f",
]

def photo_url_for_key(key):
    idx = int(hashlib.md5(key.encode()).hexdigest(), 16) % len(PHOTO_IDS)
    return f"https://images.unsplash.com/photo-{PHOTO_IDS[idx]}?w=1400&q=80&auto=format&fit=crop"


def download(url, dest_path):
    if os.path.exists(dest_path):
        return "skip"
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp, open(dest_path, "wb") as f:
        f.write(resp.read())
    return "ok"


def main():
    from content.media import MEDIA

    ok, skipped, failed = 0, 0, 0

    for key, rel_path in MEDIA.items():
        dest = os.path.join(STATIC_DIR, rel_path)

        if rel_path.endswith((".mp4", ".webm")):
            # No reliable no-API-key HD Caribbean video CDN was found — the
            # hero uses a Ken Burns image crossfade instead (hero_scene_1..4).
            # Drop real footage at this path directly when the client supplies it.
            continue

        url = photo_url_for_key(key)

        try:
            result = download(url, dest)
            if result == "ok":
                ok += 1
                print(f"[ok]   {rel_path}")
            else:
                skipped += 1
        except Exception as exc:  # noqa: BLE001 - best-effort demo fetch
            failed += 1
            print(f"[fail] {rel_path} — {exc}")

    print(f"\nDone. {ok} downloaded, {skipped} already present, {failed} failed.")
    if failed:
        print("Failed slots will fall back to content/media.py's 'fallback' image at render time.")


if __name__ == "__main__":
    main()
