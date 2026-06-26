import json
import os
from datetime import datetime, timezone
from config import LOG_FILE


def log_interaction(question: str, tier: str, response: str, tier_reason: str = "") -> None:
    """
    Append a structured record of this interaction to the audit log.

    Writes one JSON line to LOG_FILE (logs/audit.jsonl) and prints a
    one-line summary to the terminal.

    Fields logged:
      - timestamp       : ISO 8601 UTC datetime
      - tier            : safety tier assigned to this question
      - question        : user's question, truncated to 300 characters
      - response_preview: first 200 characters of the generated response
      - response_length : full character count of the response
      - tier_reason     : classifier's one-sentence explanation (optional, truncated to 200)
    """
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    entry = {
        "timestamp": timestamp,
        "tier": tier,
        "question": question[:300],
        "response_preview": response[:200],
        "response_length": len(response),
        "tier_reason": tier_reason[:200] if tier_reason else "",
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    question_preview = question[:60] + "..." if len(question) > 60 else question
    tier_padded = tier.ljust(7)
    print(f'[LOGGED] {timestamp} | tier={tier_padded} | "{question_preview}" → {len(response)} chars')
