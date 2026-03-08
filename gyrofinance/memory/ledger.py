"""Memory Ledger — persistent storage for transactions, vendors, mappings."""

import pandas as pd
from sqlalchemy.orm import Session
from .models import Vendor, Transaction, CategoryMapping


# ---------------------------------------------------------------------------
# Category Mapping
# ---------------------------------------------------------------------------

def get_mapping(db: Session, vendor_pattern: str) -> str | None:
    """Return saved category for a vendor pattern, or None."""
    row = db.query(CategoryMapping).filter(
        CategoryMapping.vendor_pattern == vendor_pattern.lower()
    ).first()
    return row.category if row else None


def save_mapping(db: Session, vendor_pattern: str, category: str, is_manual: bool = False):
    """Upsert a vendor→category mapping."""
    row = db.query(CategoryMapping).filter(
        CategoryMapping.vendor_pattern == vendor_pattern.lower()
    ).first()
    if row:
        row.category = category
        row.is_manual = is_manual
        row.version += 1
    else:
        row = CategoryMapping(
            vendor_pattern=vendor_pattern.lower(),
            category=category,
            is_manual=is_manual,
        )
        db.add(row)
    db.commit()


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

def save_transaction(db: Session, row: dict) -> Transaction:
    """Insert a transaction if not already present (idempotent by tx_hash)."""
    existing = db.query(Transaction).filter(
        Transaction.tx_hash == row["tx_hash"]
    ).first()
    if existing:
        return existing

    tx = Transaction(
        tx_hash=row["tx_hash"],
        date=row.get("date"),
        vendor=row.get("vendor"),
        description=row.get("description"),
        amount=float(row["amount"]),
        category=row["category"],
        category_source=row.get("category_source", "rule"),
        is_fixed_cost=row.get("is_fixed_cost", False),
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def bulk_save_transactions(db: Session, df: pd.DataFrame):
    """Batch-insert categorized transactions."""
    for _, row in df.iterrows():
        save_transaction(db, row.to_dict())


def get_transactions(
    db: Session,
    month: str | None = None,
    category: str | None = None,
) -> pd.DataFrame:
    """Fetch transactions as DataFrame, optionally filtered."""
    q = db.query(Transaction)
    if category:
        q = q.filter(Transaction.category == category)
    rows = q.all()
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame([{
        "tx_hash": r.tx_hash,
        "date": r.date,
        "vendor": r.vendor,
        "description": r.description,
        "amount": r.amount,
        "category": r.category,
        "category_source": r.category_source,
        "is_fixed_cost": r.is_fixed_cost,
    } for r in rows])

    if month and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"].dt.to_period("M").astype(str) == month]

    return df


def override_category(db: Session, tx_hash: str, new_category: str) -> bool:
    """Manual override: update transaction category and save mapping."""
    tx = db.query(Transaction).filter(Transaction.tx_hash == tx_hash).first()
    if not tx:
        return False
    tx.category = new_category
    tx.category_source = "manual"
    if tx.vendor:
        save_mapping(db, tx.vendor, new_category, is_manual=True)
    db.commit()
    return True
