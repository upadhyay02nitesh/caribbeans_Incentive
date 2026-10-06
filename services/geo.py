"""Visitor location lookups (server-side only; no key ever reaches the browser).

Two kinds of location, never mixed up:
  browser_gps     coordinates the visitor's browser shared after they allowed it
                  (POST /t/location), named via reverse geocoding
  ip_approximate  derived from the request IP: Vercel's edge geo headers first
                  (free, no extra call), else an IP provider

IP-derived coordinates are approximate by nature and are stored without an
accuracy figure. Every function here returns None on any failure; callers fall
back, and visitor tracking never depends on a lookup succeeding.
"""

import json
import logging
import urllib.parse
import urllib.request
from ipaddress import ip_address

from flask import current_app

logger = logging.getLogger(__name__)

TIMEOUT = 4  # seconds, for every outbound lookup

# ISO 3166-1 alpha-2 -> English short name (Vercel's headers carry only the code).
_COUNTRIES = (
    "AD:Andorra|AE:United Arab Emirates|AF:Afghanistan|AG:Antigua and Barbuda|AI:Anguilla|AL:Albania|AM:Armenia|"
    "AO:Angola|AR:Argentina|AS:American Samoa|AT:Austria|AU:Australia|AW:Aruba|AX:Åland Islands|AZ:Azerbaijan|"
    "BA:Bosnia and Herzegovina|BB:Barbados|BD:Bangladesh|BE:Belgium|BF:Burkina Faso|BG:Bulgaria|BH:Bahrain|"
    "BI:Burundi|BJ:Benin|BL:Saint Barthélemy|BM:Bermuda|BN:Brunei|BO:Bolivia|BQ:Caribbean Netherlands|BR:Brazil|"
    "BS:Bahamas|BT:Bhutan|BW:Botswana|BY:Belarus|BZ:Belize|CA:Canada|CD:DR Congo|CF:Central African Republic|"
    "CG:Congo|CH:Switzerland|CI:Côte d'Ivoire|CL:Chile|CM:Cameroon|CN:China|CO:Colombia|CR:Costa Rica|CU:Cuba|"
    "CV:Cabo Verde|CW:Curaçao|CY:Cyprus|CZ:Czechia|DE:Germany|DJ:Djibouti|DK:Denmark|DM:Dominica|"
    "DO:Dominican Republic|DZ:Algeria|EC:Ecuador|EE:Estonia|EG:Egypt|ER:Eritrea|ES:Spain|ET:Ethiopia|FI:Finland|"
    "FJ:Fiji|FR:France|GA:Gabon|GB:United Kingdom|GD:Grenada|GE:Georgia|GF:French Guiana|GG:Guernsey|GH:Ghana|"
    "GI:Gibraltar|GL:Greenland|GM:Gambia|GN:Guinea|GP:Guadeloupe|GQ:Equatorial Guinea|GR:Greece|GT:Guatemala|"
    "GU:Guam|GW:Guinea-Bissau|GY:Guyana|HK:Hong Kong|HN:Honduras|HR:Croatia|HT:Haiti|HU:Hungary|ID:Indonesia|"
    "IE:Ireland|IL:Israel|IM:Isle of Man|IN:India|IQ:Iraq|IR:Iran|IS:Iceland|IT:Italy|JE:Jersey|JM:Jamaica|"
    "JO:Jordan|JP:Japan|KE:Kenya|KG:Kyrgyzstan|KH:Cambodia|KN:Saint Kitts and Nevis|KR:South Korea|KW:Kuwait|"
    "KY:Cayman Islands|KZ:Kazakhstan|LA:Laos|LB:Lebanon|LC:Saint Lucia|LI:Liechtenstein|LK:Sri Lanka|LR:Liberia|"
    "LS:Lesotho|LT:Lithuania|LU:Luxembourg|LV:Latvia|LY:Libya|MA:Morocco|MC:Monaco|MD:Moldova|ME:Montenegro|"
    "MF:Saint Martin|MG:Madagascar|MK:North Macedonia|ML:Mali|MM:Myanmar|MN:Mongolia|MO:Macao|MQ:Martinique|"
    "MR:Mauritania|MS:Montserrat|MT:Malta|MU:Mauritius|MV:Maldives|MW:Malawi|MX:Mexico|MY:Malaysia|"
    "MZ:Mozambique|NA:Namibia|NC:New Caledonia|NE:Niger|NG:Nigeria|NI:Nicaragua|NL:Netherlands|NO:Norway|"
    "NP:Nepal|NZ:New Zealand|OM:Oman|PA:Panama|PE:Peru|PF:French Polynesia|PG:Papua New Guinea|PH:Philippines|"
    "PK:Pakistan|PL:Poland|PM:Saint Pierre and Miquelon|PR:Puerto Rico|PS:Palestine|PT:Portugal|PY:Paraguay|"
    "QA:Qatar|RE:Réunion|RO:Romania|RS:Serbia|RU:Russia|RW:Rwanda|SA:Saudi Arabia|SC:Seychelles|SD:Sudan|"
    "SE:Sweden|SG:Singapore|SI:Slovenia|SK:Slovakia|SL:Sierra Leone|SM:San Marino|SN:Senegal|SO:Somalia|"
    "SR:Suriname|SV:El Salvador|SX:Sint Maarten|SY:Syria|TC:Turks and Caicos Islands|TG:Togo|TH:Thailand|"
    "TN:Tunisia|TR:Türkiye|TT:Trinidad and Tobago|TW:Taiwan|TZ:Tanzania|UA:Ukraine|UG:Uganda|US:United States|"
    "UY:Uruguay|UZ:Uzbekistan|VC:Saint Vincent and the Grenadines|VE:Venezuela|VG:British Virgin Islands|"
    "VI:U.S. Virgin Islands|VN:Vietnam|YT:Mayotte|ZA:South Africa|ZM:Zambia|ZW:Zimbabwe"
)
COUNTRY_NAMES: dict[str, str] = {code: name for code, _, name in (p.partition(":") for p in _COUNTRIES.split("|"))}


def country_name(code):
    code = (code or "").upper()
    return COUNTRY_NAMES.get(code, code)


def _float(value):
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if f == f and abs(f) != float("inf") else None  # reject NaN/inf


def valid_coords(lat, lon):
    lat, lon = _float(lat), _float(lon)
    if lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 180) or (lat == 0 and lon == 0):
        return None
    return round(lat, 6), round(lon, 6)


def _place(city="", region="", country_code="", country="", lat=None, lon=None, tz="", network=""):
    coords = valid_coords(lat, lon) if lat is not None else None
    code = (country_code or "").upper()[:2]
    place = {
        "city": (city or "")[:120], "region": (region or "")[:120],
        "country_code": code, "country": (country or country_name(code))[:120],
        "latitude": coords[0] if coords else None, "longitude": coords[1] if coords else None,
        "timezone": (tz or "")[:64], "network": (network or "")[:200],
    }
    return place if (place["city"] or place["country"]) else None


# ---------------------------------------------------------------- IP lookups
def from_vercel_headers(headers):
    """Vercel adds x-vercel-ip-* geo headers to every request; read them in-request."""
    code = headers.get("x-vercel-ip-country", "")
    if not code:
        return None
    return _place(
        city=urllib.parse.unquote(headers.get("x-vercel-ip-city", "")),
        region=headers.get("x-vercel-ip-country-region", ""),
        country_code=code,
        lat=headers.get("x-vercel-ip-latitude"), lon=headers.get("x-vercel-ip-longitude"),
        tz=headers.get("x-vercel-ip-timezone", ""),
    )


def _get_json(url, headers=None):
    req = urllib.request.Request(url, headers={"Accept": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def from_provider(ip):
    """IP provider lookup: ipinfo.io when IP_GEOLOCATION_API_KEY is set, else GEOIP_URL.

    A private or loopback address (local runs, LAN visitors) is looked up with a
    blank IP, so the provider answers for this server's public address.
    """
    try:
        addr = ip_address(ip)
    except ValueError:
        return None
    lookup_ip = "" if addr.is_private or addr.is_loopback else ip
    cfg = current_app.config
    try:
        key = cfg.get("IP_GEOLOCATION_API_KEY", "")
        if key:
            path = f"{lookup_ip}/json" if lookup_ip else "json"
            info = _get_json(f"https://ipinfo.io/{path}?token={urllib.parse.quote(key)}")
            if info.get("bogon"):
                return None
            lat, _, lon = (info.get("loc") or "").partition(",")
            return _place(city=info.get("city"), region=info.get("region"), country_code=info.get("country"),
                          lat=lat or None, lon=lon or None, tz=info.get("timezone"), network=info.get("org"))
        url = cfg.get("GEOIP_URL", "")
        if not url:
            return None
        info = _get_json(url.format(ip=lookup_ip))
        if info.get("status") not in (None, "success"):
            return None
        return _place(city=info.get("city"), region=info.get("regionName") or info.get("region"),
                      country_code=info.get("countryCode") or info.get("country_code"), country=info.get("country"),
                      lat=info.get("lat") or info.get("latitude"), lon=info.get("lon") or info.get("longitude"),
                      tz=info.get("timezone"), network=info.get("org") or info.get("isp"))
    except Exception:
        logger.warning("IP geolocation lookup failed.", exc_info=True)
        return None


# ------------------------------------------------------------ GPS naming
def reverse_geocode(lat, lon):
    """City/country for browser coordinates (REVERSE_GEOCODE_URL, Nominatim by default)."""
    url = current_app.config.get("REVERSE_GEOCODE_URL", "")
    if not url:
        return None
    contact = current_app.config.get("INQUIRY_RECIPIENT", "") or "website"
    try:
        info = _get_json(url.format(lat=lat, lon=lon),
                         headers={"User-Agent": f"CaribbeanIncentiveWebsite/1.0 ({contact})", "Accept-Language": "en"})
    except Exception:
        logger.warning("Reverse geocoding failed.", exc_info=True)
        return None
    a = info.get("address") or {}
    city = a.get("city") or a.get("town") or a.get("village") or a.get("municipality") or a.get("county") or ""
    return _place(city=city, region=a.get("state") or a.get("region") or "",
                  country_code=a.get("country_code", ""), country=a.get("country", ""))
