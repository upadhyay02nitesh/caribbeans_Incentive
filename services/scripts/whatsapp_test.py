"""Check the WhatsApp Cloud API setup, and optionally send one test alert.

    python scripts/whatsapp_test.py            # read-only: config, number, templates
    python scripts/whatsapp_test.py --send     # also sends one alert to WHATSAPP_TO

The read-only run touches nothing outside Meta's Graph API GET endpoints.
--send delivers a real WhatsApp message, so it asks for nothing else: make sure
WHATSAPP_TO is a recipient registered in Meta -> WhatsApp -> API Setup while the
sender is still the test number.
"""

import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from services.whatsapp import send_inquiry_alert  # noqa: E402

SAMPLE = [
    ("Company", "Lumen Health"),
    ("Contact name", "Marie Duvall"),
    ("E-mail", "marie.duvall@lumenhealth.com"),
    ("Phone", "+1 646 555 0142"),
    ("Group size", "60"),
]


def get(path, token, params=""):
    url = f"https://graph.facebook.com/v23.0/{path}{params}"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        return {"error": exc.read().decode()[:300]}


def main():
    app = create_app()
    cfg = app.config
    token = cfg.get("WHATSAPP_TOKEN", "")
    phone_id = cfg.get("WHATSAPP_PHONE_ID", "")
    waba = os.environ.get("WHATSAPP_WABA_ID", "")

    print("Configured:")
    for key in ("WHATSAPP_PHONE_ID", "WHATSAPP_TO", "WHATSAPP_TEMPLATE", "WHATSAPP_TEMPLATE_LANG"):
        print(f"  {key:26} {cfg.get(key) or '(blank)'}")
    print(f"  {'WHATSAPP_WABA_ID':26} {waba or '(blank)'}")
    print(f"  {'WHATSAPP_TOKEN':26} {'set' if token else '(blank)'}")

    if not token:
        print("\nNo token — alerts archive to instance/whatsapp_outbox.jsonl.")
        return

    if phone_id:
        info = get(phone_id, token, "?fields=display_phone_number,verified_name,quality_rating,code_verification_status")
        print(f"\nSender: {info.get('display_phone_number', '?')} "
              f"({info.get('verified_name', '?')}, quality {info.get('quality_rating', '?')}, "
              f"{info.get('code_verification_status', '?')})")

    if waba:
        templates = get(waba, token, "/message_templates?fields=name,status,language&limit=20").get("data", [])
        print("Templates:")
        for t in templates:
            print(f"  {t['name']:22} {t['status']:10} {t['language']}")

    if "--send" not in sys.argv:
        print("\nRead-only run. Add --send to deliver one test alert.")
        return

    if not cfg.get("WHATSAPP_TO"):
        print("\nWHATSAPP_TO is blank — nothing to send to.")
        return

    with app.test_request_context():
        sent = send_inquiry_alert("brief", SAMPLE, "BRF-TEST-0001")
    print(f"\nSend reported: {sent}. See the log above, or instance/whatsapp_outbox.jsonl for the archived payload.")


if __name__ == "__main__":
    main()
