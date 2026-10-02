"""Write the three outbound emails to instance/email_preview/ as HTML.

    python scripts/preview_emails.py

Nothing is sent — this renders services/mailer.py's templates with sample data
so the design can be opened in a browser (or dragged into a mail client).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from services import mailer  # noqa: E402

BRIEF = [
    ("Company", "Lumen Health"),
    ("Contact name", "Marie Duvall"),
    ("E-mail", "marie.duvall@lumenhealth.com"),
    ("Phone", "+1 646 555 0142"),
    ("Country", "United States"),
    ("Type of request", "Incentive programme"),
    ("Group size", "60"),
    ("Preferred dates", "14 – 18 March 2027"),
    ("Average budget", "$150,000 – $250,000"),
    ("About the event", "Our top 60 performers.\nWe would like a day on the water and a closing gala on the beach."),
]

RFP = [
    ("Name", "Marie Duvall"),
    ("E-mail", "marie.duvall@lumenhealth.com"),
    ("Company", "Lumen Health"),
    ("Attached file", "Lumen-Health-RFP-2027.pdf"),
    ("File type", "application/pdf"),
    ("File size", 2483921),
    ("File URL", "https://example.supabase.co/storage/v1/object/public/rfps/RFP-1.pdf"),
    ("File path", "rfps/RFP-1.pdf"),
    ("Download (7 days)", "https://example.supabase.co/storage/v1/object/sign/rfps/RFP-1.pdf?X-Amz-Signature=demo"),
]

CALLBACK = [
    ("Name", "Marie Duvall"),
    ("E-mail", "marie.duvall@lumenhealth.com"),
    ("Company", "Lumen Health"),
    ("Phone", "+1 646 555 0142"),
]


def main():
    app = create_app()
    out = os.path.join(app.instance_path, "email_preview")
    os.makedirs(out, exist_ok=True)
    pages = {
        "notification-brief.html": lambda: mailer._notification_html("brief", BRIEF, "BRF-260920-4F1A"),
        "notification-rfp.html": lambda: mailer._notification_html("rfp", RFP, "RFP-260920-9C2B"),
        "notification-callback.html": lambda: mailer._notification_html("callback", CALLBACK, "CALL-260920-77D3"),
        "acknowledgement-brief.html": lambda: mailer._ack_html("Marie", "brief", "BRF-260920-4F1A"),
        "acknowledgement-rfp.html": lambda: mailer._ack_html("Marie", "rfp", "RFP-260920-9C2B"),
    }
    with app.app_context():
        for name, render in pages.items():
            with open(os.path.join(out, name), "w", encoding="utf-8") as fh:
                fh.write(render())
            print("wrote", os.path.join(out, name))
        print("\n--- plain-text twin (RFP notification) ---\n")
        print(mailer._plain(RFP, "RFP-260920-9C2B"))


if __name__ == "__main__":
    main()
