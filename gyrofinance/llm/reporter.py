"""
LLM-based report and narrative generator.
Numbers are pre-computed by the Core Engine — LLM only narrates.
"""

from .client import get_client, MODEL
import json


REPORT_SYSTEM = (
    "Sei un CFO virtuale. Analizza i dati finanziari forniti e scrivi un report "
    "chiaro, diretto e professionale in italiano. "
    "Non inventare numeri. Usa solo i dati forniti. "
    "Evidenzia anomalie, trend, e suggerisci azioni concrete."
)

COMPARE_SYSTEM = (
    "Sei un analista finanziario. Confronta i dati mese su mese forniti e "
    "scrivi un'analisi comparativa in italiano. "
    "Sii conciso. Usa elenchi puntati quando utile."
)


def generate_monthly_report(kpis: dict, month: str) -> str:
    """Generate a narrative monthly report from KPI data."""
    client = get_client()
    prompt = (
        f"Report finanziario per il mese: {month}\n\n"
        f"Dati KPI:\n{json.dumps(kpis, indent=2, ensure_ascii=False)}\n\n"
        "Scrivi il report:"
    )
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=REPORT_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_comparative_analysis(monthly_kpis: dict, deltas: list) -> str:
    """Generate a month-over-month comparative narrative."""
    client = get_client()
    prompt = (
        f"KPI mensili:\n{json.dumps(monthly_kpis, indent=2, ensure_ascii=False)}\n\n"
        f"Delta mese su mese:\n{json.dumps(deltas, indent=2, ensure_ascii=False)}\n\n"
        "Analisi comparativa:"
    )
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=COMPARE_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
