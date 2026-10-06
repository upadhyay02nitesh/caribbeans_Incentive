import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-key-not-secure")
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

    INSTANCE_PATH = os.path.join(BASE_DIR, "instance")

    # Admin sign-in (/admin). Both required — blank disables sign-in.
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

    # Sellsy
    SELLSY_CLIENT_ID = os.environ.get("SELLSY_CLIENT_ID", "")
    SELLSY_CLIENT_SECRET = os.environ.get("SELLSY_CLIENT_SECRET", "")
    # Where website briefs land, in Sellsy account 207533 (SAS CARAIBES INCENTIVE TRAVEL):
    # pipeline "Enquiries pipeline", step "Incoming enquiry", source "Site Internet".
    # IDs are per account; switching accounts means changing all three.
    SELLSY_PIPELINE_ID = os.environ.get("SELLSY_PIPELINE_ID", "34")
    SELLSY_STEP_ID = os.environ.get("SELLSY_STEP_ID", "34")
    SELLSY_SOURCE_ID = os.environ.get("SELLSY_SOURCE_ID", "6")
    # Label on the tasks created for briefs and callbacks ("Aucun" in account 207533).
    SELLSY_TASK_LABEL_ID = os.environ.get("SELLSY_TASK_LABEL_ID", "11")
    # Sellsy staff id that owns (and is assigned) new website leads. Blank = the API key's user.
    SELLSY_OWNER_ID = os.environ.get("SELLSY_OWNER_ID", "")

    # Mail
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "1") == "1"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "")
    # Where every /lets-connect submission is delivered.
    INQUIRY_RECIPIENT = os.environ.get("INQUIRY_RECIPIENT", "niteshupa6@gmail.com")

    # Scheduling / messaging
    TEAMS_BOOKING_URL = os.environ.get("TEAMS_BOOKING_URL", "")
    WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "")

    # Microsoft Graph mail (Azure app registration) — primary mail transport.
    GRAPH_TENANT_ID = os.environ.get("GRAPH_TENANT_ID", "")
    GRAPH_CLIENT_ID = os.environ.get("GRAPH_CLIENT_ID", "")
    GRAPH_CLIENT_SECRET = os.environ.get("GRAPH_CLIENT_SECRET", "")
    GRAPH_SENDER = os.environ.get("GRAPH_SENDER", "")

    # WhatsApp Business (Cloud API) alerts for /lets-connect submissions
    WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID", "")
    WHATSAPP_TO = os.environ.get("WHATSAPP_TO", "")
    WHATSAPP_TEMPLATE = os.environ.get("WHATSAPP_TEMPLATE", "")
    WHATSAPP_TEMPLATE_LANG = os.environ.get("WHATSAPP_TEMPLATE_LANG", "en_US")
    WHATSAPP_API_VERSION = os.environ.get("WHATSAPP_API_VERSION", "v21.0")

    # Postgres (Supabase) — either DATABASE_URL, or the four parts below.
    # Stripped: a trailing space/newline from pasting into a dashboard ends up in
    # the database name ("postgres ") and the connection fails.
    DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
    if not DATABASE_URL and os.environ.get("PGHOST") and os.environ.get("PGPASSWORD"):
        DATABASE_URL = (
            f"postgresql://{os.environ.get('PGUSER', 'postgres')}:"
            f"{quote_plus(os.environ['PGPASSWORD'])}@{os.environ['PGHOST']}:"
            f"{os.environ.get('PGPORT', '5432')}/{os.environ.get('PGDATABASE', 'postgres')}"
        )

    # Supabase Storage (S3 protocol) for RFP documents
    SUPABASE_S3_ENDPOINT = os.environ.get("SUPABASE_S3_ENDPOINT", "")
    SUPABASE_S3_REGION = os.environ.get("SUPABASE_S3_REGION", "")
    SUPABASE_S3_ACCESS_KEY = os.environ.get("SUPABASE_S3_ACCESS_KEY", "")
    SUPABASE_S3_SECRET_KEY = os.environ.get("SUPABASE_S3_SECRET_KEY", "")
    SUPABASE_BUCKET = os.environ.get("SUPABASE_BUCKET", "rfp-uploads")

    # Visitor tracking: one IP -> city/country lookup per new visitor ({ip} is
    # substituted). ip-api.com's free tier is non-commercial; blank disables it.
    GEOIP_URL = os.environ.get("GEOIP_URL", "http://ip-api.com/json/{ip}?fields=status,country,countryCode,regionName,city,lat,lon,timezone,org,isp").strip()
    # Optional ipinfo.io token; when set it replaces GEOIP_URL as the IP provider (HTTPS, commercial use allowed).
    IP_GEOLOCATION_API_KEY = os.environ.get("IP_GEOLOCATION_API_KEY", "").strip()
    # Names browser-GPS coordinates (Nominatim/OpenStreetMap, no key). Blank disables naming, not GPS.
    REVERSE_GEOCODE_URL = os.environ.get(
        "REVERSE_GEOCODE_URL",
        "https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=10&lat={lat}&lon={lon}").strip()

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB, covers RFP upload cap
