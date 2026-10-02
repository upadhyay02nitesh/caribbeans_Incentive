"""Download the three demo hero clips into static/video/.

Free Coverr stock, same spirit as scripts/fetch_curated_images.py: placeholder
footage for the demo, to be replaced with real Caribbean Incentive film. The hero
picks up any hero*.mp4 / hero*.webm in static/video/ automatically (see app.py).
"""

import os
import urllib.request

CLIPS = {
    "hero-1.mp4": "coverr-a-tropical-beach-681",
    "hero-2.mp4": "coverr-premium-a-yacht-sailing-on-the-blue-sea-3247",
    "hero-3.mp4": "coverr-a-small-island-4125",
}
QUALITY = "720p"  # 1080p is ~2x the bytes for little gain behind the overlay
DEST = os.path.join(os.path.dirname(__file__), "..", "static", "video")


def main():
    os.makedirs(DEST, exist_ok=True)
    for name, slug in CLIPS.items():
        url = f"https://cdn.coverr.co/videos/{slug}/{QUALITY}.mp4"
        path = os.path.join(DEST, name)
        print(f"{name} <- {slug}")
        urllib.request.urlretrieve(url, path)
    print(f"Done - {len(CLIPS)} clips in static/video/")


if __name__ == "__main__":
    main()
