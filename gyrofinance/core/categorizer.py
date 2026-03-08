"""Rule-based categorizer. Deterministic, no LLM."""

import re
from typing import Optional

# ---------------------------------------------------------------------------
# Placeholder category rules — extend freely
# ---------------------------------------------------------------------------
CATEGORIES: dict[str, list[str]] = {
    "Marketing": [
        "meta", "facebook", "instagram", "google ads", "linkedin ads",
        "mailchimp", "hubspot", "advertising", "pubblicità",
    ],
    "Software & SaaS": [
        "aws", "amazon web services", "azure", "google cloud", "heroku",
        "github", "gitlab", "notion", "slack", "zoom", "figma", "canva",
        "stripe", "twilio",
    ],
    "Personale": [
        "stipendio", "salario", "salary", "busta paga", "cedolino",
        "inps", "enasarco", "f24", "irpef",
    ],
    "Affitto & Ufficio": [
        "affitto", "rent", "locazione", "coworking", "ufficio",
    ],
    "Utilities": [
        "enel", "eni", "a2a", "tim", "vodafone", "wind", "luce", "gas",
        "acqua", "internet", "telefono",
    ],
    "Banche & Finanza": [
        "commissione", "canone", "interessi", "bonifico", "spese bancarie",
        "rid", "sdd",
    ],
    "Fornitori": [
        "fattura", "invoice", "fornitore", "supplier", "vendor",
    ],
    "Entrate": [
        "accredito", "pagamento cliente", "incasso", "revenue", "ricavo",
    ],
    "Rimborsi & Crediti": [
        "rimborso", "refund", "nota credito", "credit note",
    ],
    "Altro": [],  # fallback
}


def _match_rules(text: str) -> Optional[str]:
    text_lower = text.lower()
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if re.search(re.escape(kw), text_lower):
                return category
    return None


def categorize(vendor: str, description: str = "") -> tuple[str, bool]:
    """
    Returns (category, is_certain).
    is_certain=False means the LLM should be consulted.
    """
    combined = f"{vendor} {description}"
    match = _match_rules(combined)
    if match:
        return match, True
    return "Altro", False


def list_categories() -> list[str]:
    return list(CATEGORIES.keys())
