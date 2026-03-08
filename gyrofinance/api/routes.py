"""All API route handlers."""

import tempfile
import os
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .deps import get_db
from .schemas import (
    UploadResponse, KPIResponse, MonthlyKPIResponse,
    ReportResponse, ComparativeResponse,
    ClassifyRequest, ClassifyResponse,
    OverrideRequest, OverrideResponse,
    TransactionOut,
)

from core.parser import parse_extract
from core.categorizer import categorize
from core.kpi import compute_kpis, compute_monthly_kpis, compute_mom_delta
from memory.ledger import (
    get_mapping, save_mapping, bulk_save_transactions,
    get_transactions, override_category,
)
from llm.classifier import classify_unknown
from llm.reporter import generate_monthly_report, generate_comparative_analysis

router = APIRouter()


# ---------------------------------------------------------------------------
# Upload & ingest
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a CSV bank extract, categorize, and store transactions."""
    suffix = os.path.splitext(file.filename or "")[-1] or ".csv"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        df = parse_extract(tmp_path)
    finally:
        os.unlink(tmp_path)

    imported = 0
    skipped = 0
    ambiguous = 0
    rows = []

    for _, row in df.iterrows():
        vendor = str(row.get("vendor", ""))
        description = str(row.get("description", ""))

        # 1. Check memory first
        saved_cat = get_mapping(db, vendor)
        if saved_cat:
            category, source = saved_cat, "rule"
            certain = True
        else:
            category, certain = categorize(vendor, description)
            source = "rule"

        if not certain:
            # 2. Ask LLM only when rule-based fails
            category = classify_unknown(vendor, description)
            source = "llm"
            save_mapping(db, vendor, category)
            ambiguous += 1

        rows.append({**row.to_dict(), "category": category, "category_source": source})

    result_df = pd.DataFrame(rows)
    prev_count = db.execute(__import__("sqlalchemy").text("SELECT COUNT(*) FROM transactions")).scalar()
    bulk_save_transactions(db, result_df)
    new_count = db.execute(__import__("sqlalchemy").text("SELECT COUNT(*) FROM transactions")).scalar()

    imported = new_count - prev_count
    skipped = len(df) - imported - ambiguous

    return UploadResponse(
        imported=imported,
        skipped_duplicates=max(0, skipped),
        ambiguous=ambiguous,
        message=f"Importate {imported} transazioni, {ambiguous} classificate via LLM.",
    )


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
    month: str | None = Query(None, description="YYYY-MM"),
    category: str | None = Query(None),
    db: Session = Depends(get_db),
):
    df = get_transactions(db, month=month, category=category)
    if df.empty:
        return []
    records = df.to_dict(orient="records")
    for r in records:
        if pd.notna(r.get("date")):
            r["date"] = str(r["date"])
        else:
            r["date"] = None
    return records


# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------

@router.get("/kpis", response_model=KPIResponse)
def get_kpis(
    month: str | None = Query(None, description="YYYY-MM"),
    db: Session = Depends(get_db),
):
    df = get_transactions(db, month=month)
    if df.empty:
        raise HTTPException(status_code=404, detail="Nessuna transazione trovata.")
    kpis = compute_kpis(df)
    return KPIResponse(month=month, kpis=kpis)


@router.get("/kpis/monthly", response_model=MonthlyKPIResponse)
def get_monthly_kpis(db: Session = Depends(get_db)):
    df = get_transactions(db)
    if df.empty:
        raise HTTPException(status_code=404, detail="Nessuna transazione trovata.")
    monthly = compute_monthly_kpis(df)
    deltas = compute_mom_delta(monthly)
    return MonthlyKPIResponse(monthly=monthly, deltas=deltas)


# ---------------------------------------------------------------------------
# LLM endpoints
# ---------------------------------------------------------------------------

@router.get("/generate-report", response_model=ReportResponse)
def generate_report(
    month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
):
    df = get_transactions(db, month=month)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Nessun dato per {month}.")
    kpis = compute_kpis(df)
    narrative = generate_monthly_report(kpis, month)
    return ReportResponse(month=month, narrative=narrative)


@router.get("/generate-report/comparative", response_model=ComparativeResponse)
def comparative_report(db: Session = Depends(get_db)):
    df = get_transactions(db)
    if df.empty:
        raise HTTPException(status_code=404, detail="Nessuna transazione trovata.")
    monthly = compute_monthly_kpis(df)
    deltas = compute_mom_delta(monthly)
    narrative = generate_comparative_analysis(monthly, deltas)
    return ComparativeResponse(narrative=narrative)


@router.post("/classify-unknown", response_model=ClassifyResponse)
def classify_endpoint(req: ClassifyRequest, db: Session = Depends(get_db)):
    """Manually classify a single ambiguous transaction via LLM."""
    _, certain = __import__("core.categorizer", fromlist=["categorize"]).categorize(
        req.vendor, req.description
    )
    if certain:
        from core.categorizer import categorize as cat_fn
        category, _ = cat_fn(req.vendor, req.description)
        return ClassifyResponse(category=category, source="rule")

    category = classify_unknown(req.vendor, req.description)
    save_mapping(db, req.vendor, category)
    return ClassifyResponse(category=category, source="llm")


# ---------------------------------------------------------------------------
# Manual override
# ---------------------------------------------------------------------------

@router.post("/override-category", response_model=OverrideResponse)
def override(req: OverrideRequest, db: Session = Depends(get_db)):
    """Manually override the category of a transaction."""
    success = override_category(db, req.tx_hash, req.category)
    if not success:
        raise HTTPException(status_code=404, detail="Transazione non trovata.")
    return OverrideResponse(success=True, message="Categoria aggiornata e mapping salvato.")
