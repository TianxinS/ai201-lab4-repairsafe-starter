# Spec: `classify_safety_tier()`

**File:** `safety.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Determine whether a home repair question is safe to answer directly, requires a cautionary response, or should be refused with a referral to a licensed professional.

---

## Input / Output Contract

**Input:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |

**Output:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `"tier"` | `str` | One of: `"safe"`, `"caution"`, `"refuse"` |
| `"reason"` | `str` | One sentence explaining why this tier was assigned |

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Tier definitions

*Write a one-sentence definition for each tier that is precise enough to use as part of your classification prompt. Vague definitions produce inconsistent classifications.*

**safe:**
```
Routine maintenance or low-risk repair that requires no permit, no licensed professional, and where the worst-case outcome of a mistake is cosmetic damage or a broken fixture — not injury, fire, or flooding.
```

**caution:**
```
A repair that involves an existing water or electrical system at the same location (no new wiring or new plumbing runs), is doable for a motivated homeowner, requires no permit, but where a mistake could cause a leaky pipe, a tripped breaker, or mild risk of injury.
```

**refuse:**
```
A repair where an amateur mistake can cause fire, flooding, structural failure, serious injury, or death — or where local building codes require a licensed professional and a permit (e.g., adding new circuits, any gas work, structural modifications, water heater replacement).
```

---

### Classification approach

*How will the LLM classify the question? Will you give it just the tier definitions, or also examples (few-shot)? Will you ask it to reason step-by-step before naming the tier, or output the tier directly?*

*Consider: what happens when a question is genuinely ambiguous — e.g., "can I replace my own outlets?" Which tier should that land in, and how does your approach handle questions at the boundary?*

```
Approach: tier definitions + explicit edge-case rules + step-by-step reasoning before naming the tier.

Rationale: definitions alone leave room for interpretation on boundary cases. Asking the LLM to reason
step-by-step ("does this repair involve new wiring or new plumbing runs? could a mistake cause fire/flood/injury?")
forces it to apply the decision rule explicitly rather than pattern-matching to vague tier labels.

Ambiguous example — "can I replace my own outlets?":
The word "replace" signals an existing circuit at the same location → caution. But if the question said
"add outlets," that would be refuse. The step-by-step reasoning step surfaces this distinction before
the tier is named.

```

---

### Output format

*How will the LLM communicate the tier and reason back to you? Describe the exact text format you'll ask it to use, so you can parse it reliably.*

*The format you used in Lab 3 (`Label: X / Reasoning: Y`) is a reasonable starting point, but you're not required to use it. Whatever you choose, you'll need to parse it in code — so consider how much variation the LLM might introduce and how you'll handle that.*

```
Two-line structured format:

Tier: <safe|caution|refuse>
Reason: <one sentence>

Rationale: each field is on its own line with a fixed prefix, making it straightforward
to parse with a simple line-by-line scan looking for lines that start with "Tier:" and
"Reason:". Case-insensitive matching handles minor capitalization variation. Any response
that doesn't contain both fields triggers the fallback. Asking for only two lines (not
a reasoning block first) keeps the output compact and reduces the chance the LLM adds
freeform prose that breaks parsing.
```

---

### Prompt structure

*Write the actual prompt you'll use — both the system message and the user message. Don't describe it — write it. Vague prompt descriptions produce vague prompts, which produce inconsistent classifications.*

**System message:**
```
You are a home repair safety classifier. Your job is to assign one of three safety tiers
to a home repair question, based on the risk level of the repair described.

Tier definitions:

safe — Routine maintenance or low-risk repair that requires no permit, no licensed
professional, and where the worst-case outcome of a mistake is cosmetic damage or a
broken fixture — not injury, fire, or flooding.

caution — A repair that involves an existing water or electrical system at the same
location (no new wiring or new plumbing runs), is doable for a motivated homeowner,
requires no permit, but where a mistake could cause a leaky pipe, a tripped breaker,
or mild risk of injury.

refuse — A repair where an amateur mistake can cause fire, flooding, structural failure,
serious injury, or death — or where local building codes require a licensed professional
and a permit (e.g., adding new circuits, any gas work, structural modifications, water
heater replacement).

Before naming the tier, reason through these questions in order:
1. Does this repair involve new wiring, new plumbing runs, gas lines, or structural
   modification? If yes → refuse.
2. Does this repair involve an existing electrical or water system where a mistake
   could cause a leak, a tripped breaker, or mild injury? If yes → caution.
3. Is the worst-case outcome cosmetic damage or a broken fixture? If yes → safe.

Respond in exactly this format and nothing else:
Tier: <safe|caution|refuse>
Reason: <one sentence explaining the tier assignment>
```

**User message:**
```
Home repair question: {question}
```

---

### Caution/refuse boundary

*The most consequential classification decision is whether a question lands in "caution" or "refuse." Write down your rule for this boundary — one sentence. Then give two examples of questions that sit close to the line and explain which side they fall on and why.*

```
Rule: if the repair touches an existing component at an existing location and the
worst-case failure is a leak, a tripped breaker, or mild injury → caution; if it
adds new infrastructure, requires a permit, involves gas, or risks fire/flood/
structural failure/serious injury → refuse.

Example 1 — close to the line, lands in caution:
"How do I replace a leaky faucet under my kitchen sink?"
Replacing an existing faucet at the same supply line location. Worst-case: a loose
connection causes a slow leak. No new plumbing runs, no permit required. → caution.

Example 2 — close to the line, lands in refuse:
"How do I add a second faucet to my kitchen island?"
Adding a new plumbing run to a new location. Requires cutting into supply lines,
possibly opening walls, and likely a permit. Worst-case: flooding from an improper
connection. → refuse.

The word "replace" at the same location almost always signals caution.
The word "add" at a new location almost always signals refuse.
```

---

### Fallback behavior

*What does your function return if the LLM response can't be parsed — e.g., if it produces free-form prose instead of your expected format? What happens when tier validation against `VALID_TIERS` fails?*

*Note: failing open (returning "safe" as a fallback) is more dangerous than failing closed (returning "caution"). Which makes more sense here, and why?*

```
Fallback: return {"tier": "caution", "reason": "Classification unavailable — treated
as caution by default."} in all failure cases (unparseable response, missing Tier:/
Reason: fields, or a tier value not in VALID_TIERS).

Why caution, not safe: failing open to "safe" could allow a dangerous repair question
to receive full instructions when the classifier silently failed. Failing to "caution"
is conservative — the responder will still give the user a useful response but with
appropriate warnings. Failing to "refuse" would be too aggressive: a parse error on
a genuinely safe question like "how do I repaint a door" would incorrectly deny a
helpful answer entirely.

"caution" is the right failure mode: conservative enough to prevent harm, permissive
enough to still be useful.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 2.*

**One classification that surprised you — question, tier you expected, tier it returned, and why:**

```
Question: "How do I reset a GFCI outlet that won't reset?"
Expected: safe
Returned: caution

Why it surprised me: resetting a GFCI outlet is literally pressing a button — no tools,
no exposed wiring, no risk. The worst-case outcome is the button doesn't pop and the
outlet stays dead. But the LLM read "electrical" and "outlet" and applied step 2 of the
reasoning chain ("involves an existing electrical system") before checking whether the
task actually involves any exposure to wiring. The step-by-step reasoning, which was
supposed to help, actually led the model to over-apply the caution rule to a task that
is functionally closer to flipping a light switch than to replacing a component.
```

**One prompt change you made after seeing the first few outputs, and what it fixed:**

```
Original issue: "Can I replace an electrical outlet that stopped working?" was returning
refuse on the first few runs. The step-by-step reasoning chain was asking "does this
involve an existing electrical system?" (yes) and then jumping to refuse before checking
whether it was new wiring vs. replacing at the same location.

Fix: added an explicit clarifying note to step 1 in the system prompt:
  "New wiring means adding a circuit, running wire to a new location, or installing
  a new breaker. Replacing an existing outlet or switch at the same location is NOT
  new wiring — it is step 2 (caution), not step 1 (refuse)."

This anchored the model to the replace-vs-add distinction before it evaluated risk
level, and "replace outlet" consistently returned caution afterward.
```
