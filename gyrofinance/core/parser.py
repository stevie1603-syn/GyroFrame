"""CSV parser and normalizer for bank statement extracts."""

import pandas as pd
import hashlib
from pathlib import Path
from typing import Optional


REQUIRED_COLUMNS_ALIASES = {
    "date": ["data", "date", "data_valuta", "value_date", "data_operazione"],
    "description": ["descrizione", "description", "causale", "dettaglio", "memo"],
    "amount": ["importo", "amount", "valore", "dare/avere", "entrate/uscite"],
    "vendor": ["beneficiario", "vendor", "controparte", "fornitore", "merchant"],
}


def _detect_column(df: pd.DataFrame, aliases: list[str]) -> Optional[str]:
    for alias in aliases:
        for col in df.columns:
            if col.strip().lower() == alias.lower():
                return col
    return None


def load_csv(filepath: str | Path) -> pd.DataFrame:
    """Load a CSV file trying common separators and encodings."""
    for sep in [",", ";", "\t"]:
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(filepath, sep=sep, encoding=enc)
                if len(df.columns) > 1:
                    return df
            except Exception:
                continue
    raise ValueError(f"Cannot parse CSV: {filepath}")


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to canonical names and clean types."""
    col_map = {}
    for canonical, aliases in REQUIRED_COLUMNS_ALIASES.items():
        found = _detect_column(df, aliases)
        if found:
            col_map[found] = canonical

    df = df.rename(columns=col_map)

    # Amount: handle Italian decimal commas
    if "amount" in df.columns:
        df["amount"] = (
            df["amount"]
            .astype(str)
            .str.replace(r"\.", "", regex=True)   # remove thousands sep
            .str.replace(",", ".", regex=False)   # decimal sep
            .str.replace(r"[^\d\.\-]", "", regex=True)
        )
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    # Date
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")

    # Vendor fallback: use description
    if "vendor" not in df.columns and "description" in df.columns:
        df["vendor"] = df["description"].str.split().str[:3].str.join(" ")

    # Strip strings
    for col in ["description", "vendor"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicates and add a stable row hash."""
    df = df.drop_duplicates()

    def _row_hash(row: pd.Series) -> str:
        key = f"{row.get('date')}|{row.get('amount')}|{row.get('description', '')}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    df["tx_hash"] = df.apply(_row_hash, axis=1)
    df = df.drop_duplicates(subset=["tx_hash"])
    return df.reset_index(drop=True)


def parse_extract(filepath: str | Path) -> pd.DataFrame:
    """Full pipeline: load → normalize → deduplicate."""
    raw = load_csv(filepath)
    normalized = normalize(raw)
    clean = deduplicate(normalized)
    return clean
