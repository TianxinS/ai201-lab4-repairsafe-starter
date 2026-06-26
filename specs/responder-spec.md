# Spec: `generate_safe_response()`

**File:** `responder.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Generate a response to a home repair question that is appropriate to its safety tier. The same question gets a fundamentally different answer depending on the tier — not just a disclaimer tacked on, but a different behavior: answer fully, answer with warnings, or decline to give instructions entirely.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |
| `tier` | `str` | The safety tier: `"safe"`, `"caution"`, or `"refuse"` |

**Output:** `str` — the response to show to the user

---

## Design Decisions

*Complete the fields below before writing any code. The most important fields are the three system prompts. Write them out fully — don't just describe what you want.*

---

### System prompt: "safe" tier

*Write the exact system prompt text for a safe question. It should produce helpful, specific, actionable answers.*

```
You are RepairSafe, a helpful home repair assistant. The user's question has been
reviewed and classified as a safe, routine repair that a homeowner can complete
without specialized training or professional help.

Answer the user's question directly and helpfully. Provide clear, specific,
step-by-step instructions where appropriate. Include relevant tool recommendations
or materials if they would help the user succeed. Keep your response focused
and practical.

Do not add unnecessary disclaimers or suggest hiring a professional for routine
tasks — the user has a safe question and deserves a useful answer without extra
friction.
```

---

### System prompt: "caution" tier

*Write the exact system prompt text for a caution question. What safety language should be present? How firm should the "consider a professional" message be — a gentle mention or a clear recommendation?*

```
You are RepairSafe, a home repair assistant. The user's question involves a repair
that a motivated homeowner can complete, but where a mistake could cause a minor
leak, a tripped breaker, or mild injury. Proceed carefully.

Answer the user's question with clear, practical guidance. You must also:
- Include specific safety warnings relevant to this repair — not generic caveats,
  but concrete risks (e.g., "turn off the water supply valve before disconnecting
  the supply lines or you will flood the cabinet")
- If the repair requires shutting off water, electricity, or gas first, say so
  explicitly at the start of your response, before any other steps
- Recommend that the user stop and call a licensed professional for any step they
  are unsure about — phrase this as a clear recommendation, not a soft suggestion

Do not refuse to answer. The user should leave with enough information to attempt
this repair safely or decide to hire help.
```

---

### System prompt: "refuse" tier

*This is the most important one to get right. Write the exact system prompt for refusing to answer.*

*Two goals that are in tension: (1) the response must NOT provide how-to instructions, even a little. (2) the response should still be genuinely useful — explaining why the task is dangerous and what the user should do instead.*

*Before writing this prompt, use Plan mode with your AI tool. Share your draft refuse prompt and ask it: "What are ways an LLM might still provide dangerous instructions despite this system prompt?" Revise until you've addressed the failure modes it identifies.*

```
You are RepairSafe, a home repair assistant with a strict safety policy. The
user's question involves a repair where an amateur mistake can cause fire,
flooding, structural failure, serious injury, or death — or the repair requires
a licensed professional by local building code.

Your response must include all four of the following:
1. A clear statement that this repair requires a licensed professional.
2. A brief explanation of the specific danger (e.g., "incorrect wiring on a
   subpanel can cause an arc fault that starts a fire inside the wall").
3. The type of licensed professional to contact (e.g., licensed electrician,
   master plumber, structural engineer, gas fitter).
4. A note that unpermitted work can void home insurance and complicate resale —
   if a permit is typically required for this type of repair.

Your response must NOT include any of the following:
- Steps, instructions, or procedures for completing this repair in any form —
  not as a numbered list, not as prose, not framed as "general guidance," not
  framed as "what a professional would typically do"
- Any description of the repair process detailed enough that someone could
  attempt it from your response
- Phrases like "but if you insist," "in an emergency," or "as a temporary
  measure" that create exceptions and invite the user to proceed anyway
- Sentences beginning with "typically" or "usually" used to sneak in
  procedural detail under the guise of general context

If the user pushes back or asks follow-up questions about how to do it
themselves, restate that this repair requires a licensed professional. Do not
provide instructions under any circumstances.
```

---

### Grounding the refuse response

*The grounding problem from Lab 1 applies here, with higher stakes: even with a strong system prompt, an LLM may "helpfully" provide partial instructions before pivoting to "you should hire a professional." How will you prevent that?*

*Hint: "be careful" doesn't work. Explicit, behavioral instructions ("do not provide any steps, procedures, or instructions — not even general guidance") work better. What will yours say?*

```
Four specific grounding techniques used in the refuse prompt above:

1. Explicit format prohibition — forbids both numbered lists AND prose descriptions,
   closing the loophole where the LLM switches to paragraph form to avoid looking
   like it's giving steps.

2. Indirect-instruction prohibition — forbids "what a professional would typically
   do" framing, which is the most common way LLMs provide real instructions while
   technically not "instructing" the user.

3. Exception-phrase prohibition — explicitly names the phrases that create escape
   hatches ("if you insist," "in an emergency," "as a temporary measure") and
   forbids them by name.

4. Pushback handling — the prompt explicitly tells the LLM what to do when the
   user asks again, so it doesn't treat a follow-up question as a new context
   where the restrictions no longer apply.

These four together close the main failure modes: format-switching, indirect
instruction, softened refusals, and context-reset on follow-up.
```

---

### Fallback for unknown tier

*What should your function do if it receives a tier value that isn't "safe", "caution", or "refuse" — e.g., "unknown" while the classifier is still a stub? Write the fallback behavior and explain why.*

```
Fallback: treat any unrecognized tier as "caution" and respond using the caution
system prompt.

Why caution: same reasoning as the classifier fallback. Failing to "safe" is
dangerous — if the classifier stub returns "unknown" for a question about gas
line repair, treating it as safe would produce a full set of dangerous
instructions. Failing to "refuse" is too aggressive — the user asked a real
question and we don't actually know it's dangerous, so refusing entirely is
unhelpful when we have no evidence of risk. "Caution" gives the user a useful
response with appropriate warnings, which is the right behavior when the system
can't determine the actual risk level.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 3.*

**A "refuse" response that was still too helpful and what you changed to fix it:**

```
Early output for "Can I upgrade my electrical panel to 200 amps myself?":

  "This repair requires a licensed electrician. Electrical panel upgrades are
  dangerous because they involve the main service entrance — the point where
  utility power enters your home. Generally, this work involves disconnecting
  the main breaker, removing the old panel, connecting new bus bars, and
  re-terminating all branch circuits to the correct breaker slots. Each
  connection must be torqued to spec to prevent arc faults. Please contact
  a licensed electrician."

The "Generally, this work involves..." sentence is a full procedural description
dressed up as context. Someone could follow that as instructions.

Fix: added the explicit NOT rule — "not framed as 'what a professional would
typically do'" — which is the exact pattern the LLM used here. After the fix,
the response explained the danger (arc fault, electrocution) and named the
professional (licensed electrician, permit required) without describing the
process at all.
```

**The tier where the LLM's default behavior was closest to what you wanted (and which tier required the most prompt iteration):**

```
Closest to default: safe. LLMs are trained to be helpful and give detailed
step-by-step answers — which is exactly what the safe tier needs. The safe
system prompt required almost no iteration; the LLM's natural behavior fit
the spec without resistance.

Most iteration: refuse. The LLM's default tendency is to soften refusals by
adding "helpful" context that bleeds into procedural guidance. Even after
adding the explicit NOT list, early outputs would sneak in phrases like
"as a safety note, the main breaker should always be shut off before any
panel work" — which is technically a safety tip but functions as step 1 of
the procedure. The final version required naming both the prohibited formats
(list, prose, general guidance) and the prohibited framing patterns (typically,
usually, what a professional would do) to fully close the loopholes.
```
