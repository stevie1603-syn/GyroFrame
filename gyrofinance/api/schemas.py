"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel
from typing import Any, Optional


class UploadResponse(BaseModel):
    imported: int
    skipped_duplicates: int
    ambiguous: int
    message: str


class KPIResponse(BaseModel):
    month: Optional[str]
    kpis: dict[str, Any]


class MonthlyKPIResponse(BaseModel):
    monthly: dict[str, dict[str, Any]]
    deltas: list[dict[str, Any]]


class ReportResponse(BaseModel):
    month: str
    narrative: str


class ComparativeResponse(BaseModel):
    narrative: str


class ClassifyRequest(BaseModel):
    vendor: str
    description: str = ""


class ClassifyResponse(BaseModel):
    category: str
    source: str  # "rule" | "llm"


class OverrideRequest(BaseModel):
    tx_hash: str
    category: str


class OverrideResponse(BaseModel):
    success: bool
    message: str


class TransactionOut(BaseModel):
    tx_hash: str
    date: Optional[str]
    vendor: Optional[str]
    description: Optional[str]
    amount: float
    category: str
    category_source: str
