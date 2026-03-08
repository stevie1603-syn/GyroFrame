"""SQLAlchemy models for the Memory Ledger."""

from datetime import datetime
from sqlalchemy import (
    Column, String, Float, DateTime, Boolean, Integer,
    Text, UniqueConstraint, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    canonical_name = Column(String, nullable=False)
    default_category = Column(String, nullable=False)
    is_manual_override = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_hash = Column(String(16), unique=True, nullable=False, index=True)
    date = Column(DateTime, nullable=True)
    vendor = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    category_source = Column(String, default="rule")  # rule | llm | manual
    is_fixed_cost = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CategoryMapping(Base):
    __tablename__ = "category_mappings"
    __table_args__ = (UniqueConstraint("vendor_pattern", name="uq_vendor_pattern"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_pattern = Column(String, nullable=False)
    category = Column(String, nullable=False)
    version = Column(Integer, default=1)
    is_manual = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_engine(db_url: str = "sqlite:///./gyrofinance.db"):
    return create_engine(db_url, connect_args={"check_same_thread": False})


def get_session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(db_url: str = "sqlite:///./gyrofinance.db"):
    engine = get_engine(db_url)
    Base.metadata.create_all(bind=engine)
    return engine
