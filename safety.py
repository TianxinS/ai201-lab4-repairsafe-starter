from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_TIERS

_client = Groq(api_key=GROQ_API_KEY)

_SYSTEM_PROMPT = """You are a home repair safety classifier. Your job is to assign one of three safety tiers \
to a home repair question, based on the risk level of the repair described.

Tier definitions:

safe — Routine maintenance or low-risk repair that requires no permit, no licensed \
professional, and where the worst-case outcome of a mistake is cosmetic damage or a \
broken fixture — not injury, fire, or flooding.

caution — A repair that involves an existing water or electrical system at the same \
location (no new wiring or new plumbing runs), is doable for a motivated homeowner, \
requires no permit, but where a mistake could cause a leaky pipe, a tripped breaker, \
or mild risk of injury.

refuse — A repair where an amateur mistake can cause fire, flooding, structural failure, \
serious injury, or death — or where local building codes require a licensed professional \
and a permit (e.g., adding new circuits, any gas work, structural modifications, water \
heater replacement).

Before naming the tier, reason through these questions in order:
1. Does this repair involve new wiring, new plumbing runs, gas lines, or structural \
modification? If yes → refuse.
2. Does this repair involve an existing electrical or water system where a mistake \
could cause a leak, a tripped breaker, or mild injury? If yes → caution.
3. Is the worst-case outcome cosmetic damage or a broken fixture? If yes → safe.

Respond in exactly this format and nothing else:
Tier: <safe|caution|refuse>
Reason: <one sentence explaining the tier assignment>"""


def classify_safety_tier(question: str) -> dict:
    """
    Classify a home repair question into one of three safety tiers.

    Returns a dict with:
      - "tier"   : str — one of "safe", "caution", "refuse"
      - "reason" : str — a brief explanation of why this tier was assigned
    """
    try:
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"Home repair question: {question}"},
            ],
            temperature=0,
        )
        raw = response.choices[0].message.content or ""
    except Exception:
        return {"tier": "caution", "reason": "Classification unavailable — treated as caution by default."}

    tier = None
    reason = None
    for line in raw.splitlines():
        line_lower = line.lower()
        if line_lower.startswith("tier:"):
            tier = line.split(":", 1)[1].strip().lower()
        elif line_lower.startswith("reason:"):
            reason = line.split(":", 1)[1].strip()

    if tier not in VALID_TIERS or reason is None:
        return {"tier": "caution", "reason": "Classification unavailable — treated as caution by default."}

    return {"tier": tier, "reason": reason}
