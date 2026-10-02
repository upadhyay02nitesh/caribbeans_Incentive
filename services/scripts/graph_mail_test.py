"""Check the Microsoft Graph mail setup, and optionally send one test message.

    python scripts/graph_mail_test.py                 # read-only: config + token + mailbox
    python scripts/graph_mail_test.py --send you@x.com  # also sends one real e-mail

The read-only run requests a token and reads the sender mailbox; it sends
nothing. Every failure prints the Azure error verbatim, because the AADSTS /
Graph codes say exactly which step of the setup is missing.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from services import graph_mail  # noqa: E402

HINTS = {
    "AADSTS7000215": "The client secret is wrong or missing — paste the secret VALUE, not its ID.",
    "AADSTS700016": "The app registration was not found in this tenant — check GRAPH_CLIENT_ID.",
    "AADSTS900023": "The tenant id is wrong — check GRAPH_TENANT_ID.",
    "AADSTS7000222": "The client secret has expired — create a new one in Certificates & secrets.",
    "ErrorAccessDenied": "Grant the APPLICATION permission Mail.Send and click 'Grant admin consent'.",
    "Authorization_RequestDenied": "Missing admin consent for Mail.Send (application permission).",
    "ResourceNotFound": "GRAPH_SENDER is not a mailbox in this tenant, or has no Exchange licence.",
    "MailboxNotEnabledForRESTAPI": "That mailbox cannot use Graph — it needs an Exchange Online licence.",
}


def main():
    app = create_app()
    with app.app_context():
        cfg = graph_mail.config()
        print("Configured:")
        print(f"  GRAPH_TENANT_ID      {cfg['tenant'] or '(blank)'}")
        print(f"  GRAPH_CLIENT_ID      {cfg['client'] or '(blank)'}")
        print(f"  GRAPH_CLIENT_SECRET  {'set' if cfg['secret'] else '(blank)'}")
        print(f"  GRAPH_SENDER         {cfg['sender'] or '(blank)'}")
        print(f"  INQUIRY_RECIPIENT    {app.config.get('INQUIRY_RECIPIENT') or '(blank)'}")

        ok, message = graph_mail.check()
        print(f"\n{'OK  ' if ok else 'FAIL'} {message}")
        if not ok:
            for code, hint in HINTS.items():
                if code in message:
                    print(f"     -> {hint}")
            return

        if "--send" not in sys.argv:
            print("\nRead-only run. Add --send <address> to deliver one test e-mail.")
            return

        to = sys.argv[sys.argv.index("--send") + 1]
        from services.mailer import _notification_html

        fields = [("Company", "Lumen Health"), ("Contact name", "Marie Duvall"),
                  ("E-mail", "marie.duvall@lumenhealth.com"), ("Phone", "+1 646 555 0142"),
                  ("Group size", "60"), ("Preferred dates", "March 2027")]
        sent = graph_mail.send(
            subject="Test — New event brief — BRF-GRAPH-TEST",
            html=_notification_html("brief", fields, "BRF-GRAPH-TEST"),
            to=to,
        )
        print(f"\nSent to {to}: {sent}")


if __name__ == "__main__":
    main()
