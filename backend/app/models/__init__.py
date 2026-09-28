import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, Boolean, Integer, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Applicant(Base):
    __tablename__ = "applicants"

    application_id = Column(String(50), primary_key=True, default=generate_uuid)
    full_name = Column(String(255), nullable=False, index=True)
    dob = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)
    id_number = Column(String(100), nullable=False)
    occupation = Column(String(100), nullable=True)
    annual_income = Column(Float, nullable=True)
    country = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING", index=True) # PENDING, APPROVED, REJECTED, REVIEW_REQUIRED
    risk_level = Column(String(20), nullable=False, default="LOW", index=True) # LOW, MEDIUM, HIGH, CRITICAL
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    id_records = relationship("IDRecord", back_populates="applicant", cascade="all, delete-orphan")
    screening_results = relationship("ScreeningResult", back_populates="applicant", cascade="all, delete-orphan")
    impact_results = relationship("ImpactResult", back_populates="applicant", cascade="all, delete-orphan")
    alerts = relationship("ComplianceAlert", back_populates="applicant", cascade="all, delete-orphan")
    cases = relationship("ComplianceCase", back_populates="applicant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="applicant", cascade="all, delete-orphan")

class IDRecord(Base):
    __tablename__ = "id_records"

    id_record_id = Column(String(50), primary_key=True, default=generate_uuid)
    application_id = Column(String(50), ForeignKey("applicants.application_id", ondelete="CASCADE"), nullable=False)
    name_on_id = Column(String(255), nullable=False)
    dob_on_id = Column(String(20), nullable=False)
    address_on_id = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    applicant = relationship("Applicant", back_populates="id_records")

class Watchlist(Base):
    __tablename__ = "watchlist"

    watchlist_id = Column(String(50), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    normalized_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE") # ACTIVE, INACTIVE, UPDATED
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    screening_results = relationship("ScreeningResult", back_populates="watchlist_entry")
    impact_analyses = relationship("ImpactAnalysis", back_populates="watchlist_entry", cascade="all, delete-orphan")

class ScreeningResult(Base):
    __tablename__ = "screening_results"

    screening_id = Column(String(50), primary_key=True, default=generate_uuid)
    application_id = Column(String(50), ForeignKey("applicants.application_id", ondelete="CASCADE"), nullable=False)
    watchlist_id = Column(String(50), ForeignKey("watchlist.watchlist_id", ondelete="SET NULL"), nullable=True)
    match_score = Column(Float, nullable=False)
    match_type = Column(String(50), nullable=False) # EXACT, NORMALIZED, FUZZY, NO_MATCH
    risk_level = Column(String(20), nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    reason = Column(Text, nullable=False)
    review_status = Column(String(50), nullable=False, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

    applicant = relationship("Applicant", back_populates="screening_results")
    watchlist_entry = relationship("Watchlist", back_populates="screening_results")
    evidence_list = relationship("ScreeningEvidence", back_populates="screening_result", cascade="all, delete-orphan")
    alerts = relationship("ComplianceAlert", back_populates="screening_result")
    impact_results = relationship("ImpactResult", back_populates="screening_result")

class ScreeningEvidence(Base):
    __tablename__ = "screening_evidence"

    evidence_id = Column(String(50), primary_key=True, default=generate_uuid)
    screening_id = Column(String(50), ForeignKey("screening_results.screening_id", ondelete="CASCADE"), nullable=False)
    signal = Column(String(100), nullable=False) # NAME_SIMILARITY, DOB_MATCH, COUNTRY_MATCH, ADDRESS_SIMILARITY
    score_value = Column(Float, nullable=False)
    is_boolean_match = Column(Boolean, default=False)
    description = Column(Text, nullable=False)

    screening_result = relationship("ScreeningResult", back_populates="evidence_list")

class ImpactAnalysis(Base):
    __tablename__ = "impact_analyses"

    analysis_id = Column(String(50), primary_key=True, default=generate_uuid)
    watchlist_id = Column(String(50), ForeignKey("watchlist.watchlist_id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False) # WATCHLIST_ADDED, WATCHLIST_UPDATED
    customers_scanned = Column(Integer, nullable=False, default=0)
    potential_matches = Column(Integer, nullable=False, default=0)
    high_confidence_matches = Column(Integer, nullable=False, default=0)
    review_required = Column(Integer, nullable=False, default=0)
    analysis_status = Column(String(50), nullable=False, default="COMPLETED") # IN_PROGRESS, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)

    watchlist_entry = relationship("Watchlist", back_populates="impact_analyses")
    results = relationship("ImpactResult", back_populates="analysis", cascade="all, delete-orphan")
    alerts = relationship("ComplianceAlert", back_populates="analysis")

class ImpactResult(Base):
    __tablename__ = "impact_results"

    impact_result_id = Column(String(50), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(50), ForeignKey("impact_analyses.analysis_id", ondelete="CASCADE"), nullable=False)
    application_id = Column(String(50), ForeignKey("applicants.application_id", ondelete="CASCADE"), nullable=False)
    screening_id = Column(String(50), ForeignKey("screening_results.screening_id", ondelete="CASCADE"), nullable=True)

    # Before state
    before_risk_level = Column(String(20), nullable=False)
    before_watchlist_status = Column(String(50), nullable=False)
    before_status = Column(String(50), nullable=False)

    # After state
    after_risk_level = Column(String(20), nullable=False)
    after_watchlist_status = Column(String(50), nullable=False)
    after_status = Column(String(50), nullable=False)

    risk_change = Column(Boolean, nullable=False, default=False)
    match_score = Column(Float, nullable=False)
    recommended_action = Column(String(50), nullable=False) # ENHANCED_REVIEW, MANUAL_REVIEW, NO_ACTION
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("ImpactAnalysis", back_populates="results")
    applicant = relationship("Applicant", back_populates="impact_results")
    screening_result = relationship("ScreeningResult", back_populates="impact_results")

class ComplianceAlert(Base):
    __tablename__ = "compliance_alerts"

    alert_id = Column(String(50), primary_key=True, default=generate_uuid)
    application_id = Column(String(50), ForeignKey("applicants.application_id", ondelete="CASCADE"), nullable=False)
    screening_id = Column(String(50), ForeignKey("screening_results.screening_id", ondelete="CASCADE"), nullable=True)
    analysis_id = Column(String(50), ForeignKey("impact_analyses.analysis_id", ondelete="CASCADE"), nullable=True)
    alert_type = Column(String(50), nullable=False) # NEW_APPLICATION_MATCH, WATCHLIST_POTENTIAL_MATCH
    priority = Column(String(20), nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    risk_level = Column(String(20), nullable=False)
    match_score = Column(Float, nullable=False)
    recommended_action = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="OPEN") # OPEN, IN_REVIEW, RESOLVED
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolution_reason = Column(Text, nullable=True)

    applicant = relationship("Applicant", back_populates="alerts")
    screening_result = relationship("ScreeningResult", back_populates="alerts")
    analysis = relationship("ImpactAnalysis", back_populates="alerts")
    case = relationship("ComplianceCase", back_populates="alert", uselist=False)

class ComplianceCase(Base):
    __tablename__ = "compliance_cases"

    case_id = Column(String(50), primary_key=True, default=generate_uuid)
    application_id = Column(String(50), ForeignKey("applicants.application_id", ondelete="CASCADE"), nullable=False)
    alert_id = Column(String(50), ForeignKey("compliance_alerts.alert_id", ondelete="CASCADE"), nullable=True)
    priority = Column(String(20), nullable=False)
    recommended_action = Column(String(50), nullable=False)
    final_action = Column(String(50), nullable=True) # APPROVED, REJECTED, DISMISSED
    status = Column(String(50), nullable=False, default="OPEN") # OPEN, IN_REVIEW, RESOLVED, ESCALATED
    assigned_to = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolution_reason = Column(Text, nullable=True)

    applicant = relationship("Applicant", back_populates="cases")
    alert = relationship("ComplianceAlert", back_populates="case")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(String(50), primary_key=True, default=generate_uuid)
    application_id = Column(String(50), ForeignKey("applicants.application_id", ondelete="CASCADE"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False, default="APPLICATION")
    entity_id = Column(String(50), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    performed_by = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    reason = Column(Text, nullable=False)

    applicant = relationship("Applicant", back_populates="audit_logs")
