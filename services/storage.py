"""RFP document storage in Supabase Storage, through its S3-compatible endpoint.

Each uploaded RFP is written to a private bucket at

    rfps/<reference>/<original-file-name>

and the object's URL and path are saved on the row in
caribbean_incentive_rfp_uploads (services/store.py). The bucket stays private —
RFPs are confidential client documents — so the stored URL needs Supabase auth
to open. For people, `signed_url()` mints a time-limited link; the notification
email carries one valid for 7 days, the longest the S3 protocol allows.

Configure in .env (Supabase -> Storage -> S3 Configuration):
    SUPABASE_S3_ENDPOINT     https://<project>.storage.supabase.co/storage/v1/s3
    SUPABASE_S3_REGION       e.g. ap-southeast-2
    SUPABASE_S3_ACCESS_KEY   "New access key" -> Access key ID
    SUPABASE_S3_SECRET_KEY   ... -> Secret access key
    SUPABASE_BUCKET          optional, default "rfp-uploads" (created if missing)

Without the keys, upload_rfp() returns None and the file is kept in
instance/rfps/ exactly as before — the enquiry is never lost.
"""

import logging
import re
from urllib.parse import quote

from flask import current_app

logger = logging.getLogger(__name__)

SIGNED_URL_SECONDS = 7 * 24 * 3600  # S3 presigned URLs max out at 7 days

# Accepted RFP formats. The type is set from the extension because browsers
# often label Word / PowerPoint uploads as application/octet-stream.
CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


def content_type_for(filename, fallback="application/octet-stream"):
    import os

    return CONTENT_TYPES.get(os.path.splitext(filename or "")[1].lower(), fallback)

_client = None
_bucket_ready = False


def _config():
    cfg = current_app.config
    return {
        "endpoint": (cfg.get("SUPABASE_S3_ENDPOINT") or "").rstrip("/"),
        "region": cfg.get("SUPABASE_S3_REGION") or "",
        "access_key": cfg.get("SUPABASE_S3_ACCESS_KEY") or "",
        "secret_key": cfg.get("SUPABASE_S3_SECRET_KEY") or "",
        "bucket": cfg.get("SUPABASE_BUCKET") or "rfp-uploads",
    }


def configured():
    c = _config()
    return all((c["endpoint"], c["region"], c["access_key"], c["secret_key"]))


def _s3():
    global _client
    if _client is None:
        import boto3
        from botocore.config import Config

        c = _config()
        _client = boto3.client(
            "s3",
            endpoint_url=c["endpoint"],
            region_name=c["region"],
            aws_access_key_id=c["access_key"],
            aws_secret_access_key=c["secret_key"],
            # Supabase serves buckets as a path, not a subdomain.
            config=Config(s3={"addressing_style": "path"}, signature_version="s3v4",
                          retries={"max_attempts": 3}, connect_timeout=10, read_timeout=30),
        )
    return _client


def _ensure_bucket(bucket):
    global _bucket_ready
    if _bucket_ready:
        return
    s3 = _s3()
    try:
        s3.head_bucket(Bucket=bucket)
    except Exception:
        # Private by default; Supabase creates it via the S3 protocol.
        s3.create_bucket(Bucket=bucket)
        logger.info("Created Supabase storage bucket %s", bucket)
    _bucket_ready = True


def _safe_name(filename):
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", filename or "rfp.pdf").strip("-.")
    return name[:120] or "rfp.pdf"


def _object_url(bucket, path):
    """Supabase's canonical URL for a private object (opens with an auth token)."""
    base = _config()["endpoint"].rsplit("/storage/v1/s3", 1)[0].replace(".storage.supabase.co", ".supabase.co")
    return f"{base}/storage/v1/object/{bucket}/{quote(path)}"


def upload_rfp(reference, filename, payload, content_type="application/pdf"):
    """Store one RFP. Returns {'bucket','path','url','signed_url'} or None."""
    if not configured():
        return None
    c = _config()
    path = f"rfps/{reference}/{_safe_name(filename)}"
    content_type = content_type_for(filename, content_type)
    try:
        _ensure_bucket(c["bucket"])
        _s3().put_object(
            Bucket=c["bucket"], Key=path, Body=payload, ContentType=content_type,
            Metadata={"reference": reference, "original-name": quote(filename or "")},
        )
        logger.info("RFP %s stored at %s/%s", reference, c["bucket"], path)
        return {
            "bucket": c["bucket"],
            "path": path,
            "url": _object_url(c["bucket"], path),
            "signed_url": signed_url(path),
        }
    except Exception:
        logger.exception("Supabase upload failed for RFP %s — keeping it locally.", reference)
        return None


def signed_url(path, seconds=SIGNED_URL_SECONDS):
    """Time-limited download link for a stored RFP, or None if unavailable."""
    if not configured():
        return None
    try:
        return _s3().generate_presigned_url(
            "get_object", Params={"Bucket": _config()["bucket"], "Key": path}, ExpiresIn=seconds
        )
    except Exception:
        logger.exception("Could not sign URL for %s", path)
        return None
