"""Ask Caraïbes — grounded Q&A over the knowledge corpus.

Retrieve (services/knowledge.py) -> prompt -> Gemini (LangChain). The model
answers *only* from the retrieved passages; anything outside them is answered
with an honest "I don't have that" plus a route to the team. Numbers are never
improvised: cost questions go through the existing website calculator
(content.pricing, via services.chatbot.run_estimate) as a bound tool.

Without a Gemini key this delegates to the previous assistant
(services/chatbot.py — Claude, then offline keywords), so the widget never
goes dark.
"""

import json
import logging

from services import gemini, knowledge
from services.chatbot import ESTIMATE_TOOL, clean_history, run_estimate
from services.chatbot import reply as legacy_reply

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 2

SYSTEM = """You are the assistant for Caribbean Incentive (Caraïbes Incentive), a boutique \
destination management company for corporate events, incentive travel and executive retreats \
in the Caribbean.

Ground rules — follow them exactly:
1. Answer ONLY from the CONTEXT passages below and the conversation so far. They are the whole \
truth you have about this company.
2. Never invent or estimate services, prices, availability, capacities, dates or partners. If the \
context does not answer the question, say plainly that you do not have that detail and offer to \
pass the question to the team through Let's Connect (or the Project Assistant tab for a brief).
3. For cost questions, call the estimate_trip tool — it runs the website's own calculator. Quote \
only the figures it returns, and say they are planning estimates that exclude airfare. Never \
quote a price without the tool.
4. Reply in the visitor's language: French if they write in French, otherwise English.
5. Keep it short and warm — two to four sentences, or a brief list when comparing. Plain text \
only: no markdown, no headings, no tables.
6. When a page helps, name it: Explore Our Islands, Your Caribbean Journey, Envision Your \
Experience (the estimator), Connected to the Caribbean (getting there), Let's Connect (enquiries).

CONTEXT
{context}
END CONTEXT"""


def _tool_spec():
    """The existing estimator tool, in the shape LangChain passes to Gemini."""
    schema = {k: v for k, v in ESTIMATE_TOOL["input_schema"].items() if k != "additionalProperties"}
    return {
        "name": ESTIMATE_TOOL["name"],
        "description": ESTIMATE_TOOL["description"],
        "parameters": schema,
    }


def _gemini_answer(history):
    llm = gemini.chat_model(temperature=0.2)
    if llm is None:
        return None

    from langchain_core.messages import SystemMessage, ToolMessage

    question = history[-1]["content"]
    # Retrieve on the question plus a little prior context, so follow-ups
    # ("and how do we get there?") still hit the right passages.
    recent = " ".join(m["content"] for m in history[-3:])
    context = knowledge.context_for(f"{question}\n{recent}")
    if not context:
        context = knowledge.context_for(question, k=3) or "(no matching passages)"

    messages = [SystemMessage(content=SYSTEM.format(context=context))]
    for role, content in gemini.to_messages(history):
        messages.append((role, content))

    model = llm.bind_tools([_tool_spec()])
    for _ in range(MAX_TOOL_ROUNDS):
        response = model.invoke(messages)
        calls = getattr(response, "tool_calls", None)
        if not calls:
            return gemini.response_text(response) or None

        messages.append(response)
        for call in calls:
            try:
                result = json.dumps(run_estimate(**call["args"]))
            except (TypeError, ValueError, KeyError) as exc:
                result = f"Error: {exc}"
            messages.append(ToolMessage(content=result, tool_call_id=call.get("id", "")))

    logger.warning("Ask: stopped after %d tool rounds.", MAX_TOOL_ROUNDS)
    return None


def reply(raw_history):
    """{'reply': str, 'mode': 'ask'} — falls back to the previous assistant."""
    history = clean_history(raw_history)
    if not history or history[-1]["role"] != "user":
        return {"reply": "Ask me anything about our islands, services or a planning estimate.",
                "mode": "none"}

    if gemini.available():
        try:
            text = _gemini_answer(history)
            if text:
                return {"reply": text, "mode": "ask"}
        except Exception:
            logger.exception("Gemini answer failed; falling back.")

    return legacy_reply(history)
