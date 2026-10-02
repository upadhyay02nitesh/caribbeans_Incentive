# Knowledge folder

Drop the documents the assistant is allowed to answer from here:

- `.pdf` — brochures, fact sheets, proposals (text is extracted with pypdf)
- `.txt` / `.md` — FAQ exports, service descriptions, island notes

Everything in this folder is chunked and indexed at first use by
`services/knowledge.py`, alongside the site's own content (`content/*.py`).
"Ask Caraïbes" answers **only** from what is retrieved here — if a document
does not say it, the assistant says it does not know.

Restart the app after adding or changing files; the index is built once per
process. Point `KNOWLEDGE_DIR` at another folder to use one elsewhere.
