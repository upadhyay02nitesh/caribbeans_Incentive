"""Knowledge corpus + retrieval for "Ask Caraïbes".

Two sources, both plain text by the time they reach the index:

* the site's own knowledge base (``services.chatbot.KNOWLEDGE``), rendered from
  ``content/*.py`` — always present, always current with the website;
* any .pdf / .txt / .md dropped into ``knowledge/`` (override with
  ``KNOWLEDGE_DIR``) — the client's brochures, fact sheets, FAQ exports.

Retrieval is a small in-process BM25 over ~1 kB chunks. No vector database and
no embedding calls: the corpus is a few hundred chunks, it is identical for
every visitor, and lexical scoring over accent-folded tokens handles English
and French alike. Swap in a vector store only if the corpus outgrows this.
"""

import logging
import math
import os
import re
import threading
import unicodedata
from collections import Counter

logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC_EXTENSIONS = (".pdf", ".txt", ".md")
CHUNK_CHARS = 1100
CHUNK_OVERLAP = 150
TOP_K = 8

# Words that carry no signal in either language the site answers in.
STOPWORDS = {
    "the", "and", "for", "you", "are", "our", "with", "that", "this", "from", "can", "what", "how",
    "does", "have", "has", "was", "were", "will", "would", "your", "about", "into", "they", "there",
    "les", "des", "une", "un", "est", "sont", "pour", "avec", "que", "qui", "dans", "vous", "nous",
    "sur", "par", "pas", "plus", "aux", "ses", "son", "ces", "cette", "comment", "quel", "quelle",
    "quels", "quelles", "combien", "est-ce", "de", "la", "le", "du", "en", "au", "il", "elle",
}

_index = None
_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Text handling
# ---------------------------------------------------------------------------
def _fold(text):
    """Lowercase and strip accents so 'séjour' and 'sejour' match."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c)
    )


def tokenize(text):
    return [t for t in re.findall(r"[a-z0-9]+", _fold(text)) if len(t) > 1 and t not in STOPWORDS]


# The corpus is written in English; visitors also write in French. Mapping the
# domain vocabulary keeps French questions hitting the right passages without
# an embedding model. Extend as the documents grow.
FR_EN = {
    "ile": "island", "iles": "islands", "destination": "destination", "sejour": "stay",
    "voyage": "travel", "vol": "flight", "vols": "flights", "avion": "flight",
    "aeroport": "airport", "acceder": "access", "acces": "access", "arriver": "arrive",
    "transfert": "transfers", "transferts": "transfers", "bateau": "boat", "yacht": "yacht",
    "hebergement": "accommodation", "hotel": "hotel", "hotels": "hotels", "villa": "villa",
    "restauration": "dining", "diner": "dinner", "gala": "gala", "soiree": "evening",
    "seminaire": "retreat", "evenement": "event", "evenements": "events",
    "reunion": "meeting", "congres": "conference", "incentive": "incentive",
    "equipe": "team", "cohesion": "team building", "activite": "experiences",
    "activites": "experiences", "experience": "experiences", "personnes": "guests",
    "participants": "guests", "groupe": "group", "budget": "budget", "prix": "cost",
    "tarif": "cost", "cout": "cost", "devis": "estimate", "nuits": "nights", "nuit": "night",
    "services": "services", "service": "services", "plage": "beach", "mer": "sea",
    "contact": "contact", "telephone": "phone", "adresse": "address", "bureau": "office",
    "entreprise": "corporate", "societe": "company", "durable": "sustainability",
    "ecologique": "sustainability", "securite": "safety", "meteo": "weather",
}


def expand(terms):
    """Query terms plus their English equivalents, so FR questions reach EN text."""
    out = list(terms)
    for term in terms:
        mapped = FR_EN.get(term)
        if mapped:
            out.extend(t for t in mapped.split() if t not in out)
    return out


def _chunks(text, source):
    """Line-aware chunking: break on headings, pack up to CHUNK_CHARS, and carry
    the current heading into every chunk so a fragment still says what it is about."""
    out, buf, heading = [], "", ""

    def flush():
        nonlocal buf
        body = buf.strip()
        if len(body) > 40:
            prefix = (heading + "\n") if heading and not body.startswith(heading) else ""
            out.append(prefix + body)
        buf = ""

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            flush()
            heading = line.lstrip("# ").strip()
            continue
        while len(line) > CHUNK_CHARS:          # one very long line — hard-split it
            flush()
            buf = line[:CHUNK_CHARS]
            line = line[CHUNK_CHARS - CHUNK_OVERLAP:]
            flush()
        if len(buf) + len(line) + 1 > CHUNK_CHARS:
            flush()
        buf += line + "\n"
    flush()
    return [{"source": source, "text": c} for c in out]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def _read_pdf(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.warning("pypdf is not installed — skipping %s", os.path.basename(path))
        return ""
    try:
        reader = PdfReader(path)
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception:
        logger.exception("Could not read %s", path)
        return ""


def document_dir():
    return os.environ.get("KNOWLEDGE_DIR") or os.path.join(ROOT, "knowledge")


def _documents():
    """Site knowledge first, then every supported file in the knowledge folder."""
    from services.chatbot import KNOWLEDGE  # rendered from content/ at import time

    docs = _chunks(KNOWLEDGE, "Caribbean Incentive website")

    folder = document_dir()
    if not os.path.isdir(folder):
        return docs
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not os.path.isfile(path) or not name.lower().endswith(DOC_EXTENSIONS):
            continue
        if name.lower().startswith("readme"):  # folder instructions, not client knowledge
            continue
        if name.lower().endswith(".pdf"):
            text = _read_pdf(path)
        else:
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                logger.exception("Could not read %s", path)
                continue
        chunks = _chunks(text, os.path.splitext(name)[0])
        logger.info("Knowledge: %s -> %d chunks", name, len(chunks))
        docs.extend(chunks)
    return docs


# ---------------------------------------------------------------------------
# BM25
# ---------------------------------------------------------------------------
K1, B = 1.5, 0.75


def _build():
    docs = _documents()
    postings, lengths = [], []
    df = Counter()
    for doc in docs:
        counts = Counter(tokenize(doc["text"]))
        postings.append(counts)
        lengths.append(sum(counts.values()) or 1)
        df.update(counts.keys())
    n = len(docs) or 1
    idf = {term: math.log(1 + (n - freq + 0.5) / (freq + 0.5)) for term, freq in df.items()}
    logger.info("Knowledge index: %d chunks from %d sources.", n, len({d["source"] for d in docs}))
    return {"docs": docs, "postings": postings, "lengths": lengths, "idf": idf,
            "avg_len": sum(lengths) / n if lengths else 1}


def index():
    global _index
    if _index is None:
        with _lock:
            if _index is None:
                _index = _build()
    return _index


def search(query, k=TOP_K):
    """Top-k chunks for a query, best first. Empty when nothing matches."""
    ix = index()
    terms = expand(tokenize(query))
    if not terms:
        return []
    scored = []
    for i, counts in enumerate(ix["postings"]):
        score = 0.0
        for term in terms:
            tf = counts.get(term)
            if not tf:
                continue
            norm = 1 - B + B * ix["lengths"][i] / ix["avg_len"]
            score += ix["idf"].get(term, 0) * tf * (K1 + 1) / (tf + K1 * norm)
        if score > 0:
            scored.append((score, i))
    scored.sort(reverse=True)
    return [dict(ix["docs"][i], score=round(score, 3)) for score, i in scored[:k]]


def context_for(query, k=TOP_K, budget=9000):
    """Retrieved chunks as one labelled block, capped so the prompt stays small."""
    parts, used = [], 0
    for hit in search(query, k):
        block = f"[{hit['source']}]\n{hit['text']}"
        if used + len(block) > budget:
            break
        parts.append(block)
        used += len(block)
    return "\n\n---\n\n".join(parts)


def stats():
    ix = index()
    sources = Counter(d["source"] for d in ix["docs"])
    return {"chunks": len(ix["docs"]), "sources": dict(sources), "dir": document_dir()}
