"""Chat model access, through LangChain, in one place.

Both AI features (services/ask.py, services/project_assistant.py) get their
model from here so the key, model id, timeouts and retries are configured once.
The rest of the app never touches a provider directly — only this module knows
whether the model is reached via OpenRouter or a provider's own API, so a future
switch is a change here, not a rewrite of ask.py / project_assistant.py.

Provider: OpenRouter (https://openrouter.ai) — an OpenAI-compatible endpoint
that can route to any of its listed models by changing MODEL alone. Model
choice matters: OpenRouter also lists ":batch" variants (half price, but
asynchronous — minutes to 24h turnaround) which must never be used here, since
the chat widget needs a reply while the visitor is waiting. Always a plain,
non-batch model id.

``OPENROUTER_API_KEY`` is read from the environment on the server — it is
never sent to the browser. Without a key ``chat_model()`` returns None and
callers fall back to the existing assistant (services/chatbot.py — Claude,
then offline keywords), so the widget always works.
"""

import logging
import os
import threading

logger = logging.getLogger(__name__)

BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "google/gemini-3.6-flash"
TIMEOUT = 40
MAX_RETRIES = 2

_models = {}
_lock = threading.Lock()


def api_key():
    return os.environ.get("OPENROUTER_API_KEY", "").strip()


def model_name():
    model = (os.environ.get("OPENROUTER_MODEL") or DEFAULT_MODEL).strip()
    if model.endswith(":batch"):
        # A batch model would leave the visitor staring at a "typing…" indicator
        # for minutes to 24 hours — never actually use it here, just warn and
        # strip the suffix down to the normal synchronous model.
        logger.warning("OPENROUTER_MODEL=%s is a batch (asynchronous) model — "
                       "using the synchronous variant instead.", model)
        model = model[: -len(":batch")]
    return model


def available():
    return bool(api_key())


def chat_model(temperature=0.2):
    """A cached ChatOpenAI pointed at OpenRouter, or None when not configured."""
    if not available():
        return None
    key = (model_name(), temperature)
    if key in _models:
        return _models[key]
    with _lock:
        if key not in _models:
            try:
                from langchain_openai import ChatOpenAI

                _models[key] = ChatOpenAI(
                    model=model_name(),
                    api_key=api_key(),
                    base_url=BASE_URL,
                    temperature=temperature,
                    timeout=TIMEOUT,
                    max_retries=MAX_RETRIES,
                    # OpenRouter attributes usage to the calling app/site.
                    default_headers={
                        "HTTP-Referer": "https://caribbean-incentive.com",
                        "X-Title": "Caribbean Incentive",
                    },
                )
                logger.info("OpenRouter ready: %s (temperature %s)", model_name(), temperature)
            except Exception:
                logger.exception("Could not initialise OpenRouter.")
                return None
    return _models[key]


def response_text(response):
    """OpenAI-style responses return a plain string; handle a block-list
    shape too in case a routed model ever returns one (defensive only)."""
    content = response.content
    if isinstance(content, str):
        return content.strip()
    parts = []
    for block in content or []:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(p for p in parts if p).strip()


def to_messages(history):
    """Cleaned [{role, content}] turns -> LangChain message tuples."""
    return [("human" if m["role"] == "user" else "ai", m["content"]) for m in history]
