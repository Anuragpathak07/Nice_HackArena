import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, Date, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Applicant(Base):
    __tablename__ = "applicants"

    application_id = Column(String(50), primary_key=True, default=generate_uuid)
    full_name = Column(String(255), nullable=False, index=True)
    dob = Column(String(20), nullable=False) # Store YYYY-MM-DD
    address = Column(Text, nullable=True)
    id_number = Column(String(100), nullable=False)
    occupation = Column(String(100), nullable=True)
    annual_income = Column(Float, nullable=True)
    country = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING", index=True) # PENDING, APPROVED, REJECTED, IN_REVIEW
    risk_level = Column(String(20), nullable=False, default="LOW", index=True) # LOW, MEDIUM, HIGH, CRITICAL
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    id_records = relationship("IDRecord", back_populates="applicant", cascade="all, delete-orphan")
    screening_results = relationship("ScreeningResult", back_populates="applicant", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="applicant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="applicant", cascade="all, delete-orphan")

class IDRecord(Base):
    __tablename__ = "id_records"

    id_record_id = Column(String(50), primary_key=True, default=generate_uuid)
    application_id = Column(String(50), ForeignKey("applicants.application_id", ondelete="CASCADE"), nullable=False)
    name_on_id = Column(String(255), nullable=False)
    dob_on_id = Column(String(20), nullable=False)
    address_on_id = Column(Text, nullable=False)

    applicant = relationship("Applicant", back_populates="id_records")

class Watchlist(Base):
    __tablename__ = "watchlist"

    watchlist_id = Column(String(50), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    screening_results = relationship("ScreeningResult", back_populates="watchlist_entry")

class ScreeningResult(Base):
    __tablename__ = "screening_results"

    screening_id = Column(String(50), primary_key=True, default=generate_uuid)
    application_id = Column(String(50), ForeignKey("applicants.application_id", ondelete="CASCADE"), nullable=False)
    watchlist_id = Column(String(50), ForeignKey("watchlist.watchlist_id", ondelete="SET NULL"), nullable=True)
    match_score = Column(Float, nullable=False)
    match_type = Column(String(50), nullable=False) # EXACT, NORMALIZED, FUZZY, NO_MATCH
    risk_level = Column(String(20), nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    reason = Column(Text, nullable=False)
    review_status = Column(String(50), nullable=False, default="PENDING_REVIEW") # PENDING_REVIEW, CONFIRMED_MATCH, FALSE_POSITIVE, DISMISSED
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    applicant = relationship("Applicant", back_populates="screening_results")
    watchlist_entry = relationship("Watchlist", back_populates="screening_results")
    alerts = relationship("Alert", back_populates="screening_result")

class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String(50), primary_key=True, default=generate_uuid)
    application_id = Column(String(50), ForeignKey("applicants.application_id", ondelete="CASCADE"), nullable=False)
    screening_id = Column(String(50), ForeignKey("screening_results.screening_id", ondelete="CASCADE"), nullable=True)
    alert_type = Column(String(50), nullable=False) # NEW_APPLICATION_MATCH, RE_SCREENING_MATCH
    status = Column(String(50), nullable=False, default="OPEN") # OPEN, IN_REVIEW, RESOLVED
    created_at = Column(DateTime, default=datetime.utcnow)

    applicant = relationship("Applicant", back_populates="alerts")
    screening_result = relationship("ScreeningResult", back_populates="alerts")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(String(50), primary_key=True, default=generate_uuid)
    application_id = Column(String(50), ForeignKey("applicants.application_id", ondelete="CASCADE"), nullable=False)
    action = Column(String(100), nullable=False)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    performed_by = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    reason = Column(Text, nullable=False)

    applicant = relationship("Applicant", back_populates="audit_logs")
