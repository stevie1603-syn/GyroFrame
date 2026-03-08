"""
LLM-based classifier for ambiguous transactions.
Prompt is closed: LLM can only pick from predefined categories.
"""

from .client import get_client, MODEL, MAX_TOKENS
from core.categorizer import list_categories


CLASSIFY_SYSTEM = (
    "Sei un assistente contabile. Classifica la transazione nella categoria "
    "più appropriata tra quelle fornite. "
    "Rispondi SOLO con il nome esatto della categoria, nessun altro testo."
)


def classify_unknown(vendor: str, description: str) -> str:
    """
    Ask Claude to classify an ambiguous transaction.
    Returns one of the predefined categories.
    """
    categories = list_categories()
    categories_str = "\n".join(f"- {c}" for c in categories)

    prompt = (
        f"Transazione:\n"
        f"  Vendor: {vendor}\n"
        f"  Descrizione: {description}\n\n"
        f"Categorie disponibili:\n{categories_str}\n\n"
        f"Categoria:"
    )

    client = get_client()
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=CLASSIFY_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Validate: must be one of the known categories
    if raw in categories:
        return raw

    # Fuzzy fallback: case-insensitive match
    for cat in categories:
        if cat.lower() == raw.lower():
            return cat

    return "Altro"
