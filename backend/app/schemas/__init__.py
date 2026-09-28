from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field

# --- APPLICANT SCHEMAS ---
class ApplicantBase(BaseModel):
    full_name: str
    dob: str
    address: Optional[str] = None
    id_number: str
    occupation: Optional[str] = None
    annual_income: Optional[float] = None
    country: str

class ApplicantCreate(ApplicantBase):
    application_id: Optional[str] = None

class ApplicantUpdate(BaseModel):
    full_name: Optional[str] = None
    dob: Optional[str] = None
    address: Optional[str] = None
    id_number: Optional[str] = None
    occupation: Optional[str] = None
    annual_income: Optional[float] = None
    country: Optional[str] = None
    status: Optional[str] = None # PENDING, APPROVED, REJECTED, REVIEW_REQUIRED
    risk_level: Optional[str] = None # LOW, MEDIUM, HIGH, CRITICAL

class ApplicantResponse(ApplicantBase):
    application_id: str
    status: str
    risk_level: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- ID RECORD SCHEMAS ---
class IDRecordBase(BaseModel):
    name_on_id: str
    dob_on_id: str
    address_on_id: str

class IDRecordCreate(IDRecordBase):
    application_id: str

class IDRecordResponse(IDRecordBase):
    id_record_id: str
    application_id: str

    class Config:
        from_attributes = True

# --- CONSISTENCY CHECK SCHEMAS ---
class FieldCheckResult(BaseModel):
    field: str
    status: str # MATCH, PARTIAL_MATCH, MISMATCH, FORMAT_INVALID, MISSING
    application_value: Optional[str] = None
    id_value: Optional[str] = None
    reason: str

class ConsistencyCheckResponse(BaseModel):
    passed: bool
    mismatch_count: int = 0
    explanation: str
    checks: List[FieldCheckResult]

# --- WATCHLIST SCHEMAS ---
class WatchlistBase(BaseModel):
    name: str
    country: Optional[str] = None
    reason: str

class WatchlistCreate(WatchlistBase):
    watchlist_id: Optional[str] = None

class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = None

class WatchlistResponse(WatchlistBase):
    watchlist_id: str
    normalized_name: str
    status: str
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- SCREENING EVIDENCE SCHEMAS ---
class EvidenceItem(BaseModel):
    signal: str # NAME_SIMILARITY, DOB_MATCH, COUNTRY_MATCH, ADDRESS_SIMILARITY
    score_value: float
    is_boolean_match: bool
    description: str

    class Config:
        from_attributes = True

# --- SCREENING RESULTS SCHEMAS ---
class ScreeningResultResponse(BaseModel):
    screening_id: str
    application_id: str
    watchlist_id: Optional[str] = None
    match_score: float
    match_type: str
    risk_level: str
    reason: str
    review_status: str
    evidence_list: List[EvidenceItem] = []
    created_at: datetime

    class Config:
        from_attributes = True

# --- IMPACT RADAR SCHEMAS (FEATURE 5 CORE) ---
class ImpactStateDiff(BaseModel):
    risk_level: str
    watchlist_status: str
    status: str

class ImpactResultItem(BaseModel):
    impact_result_id: str
    application_id: str
    screening_id: Optional[str] = None
    before: ImpactStateDiff
    after: ImpactStateDiff
    risk_change: bool
    match_score: float
    recommended_action: str # ENHANCED_REVIEW, MANUAL_REVIEW, NO_ACTION
    reason: str

    class Config:
        from_attributes = True

class ImpactAnalysisResponse(BaseModel):
    analysis_id: str
    watchlist_id: str
    event_type: str
    customers_scanned: int
    potential_matches: int
    high_confidence_matches: int
    review_required: int
    analysis_status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ImpactAnalysisDetailResponse(ImpactAnalysisResponse):
    results: List[ImpactResultItem] = []

# --- COMPLIANCE ALERTS SCHEMAS ---
class AlertResponse(BaseModel):
    alert_id: str
    application_id: str
    screening_id: Optional[str] = None
    analysis_id: Optional[str] = None
    alert_type: str
    priority: str
    title: str
    description: str
    risk_level: str
    match_score: float
    recommended_action: str
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_reason: Optional[str] = None

    class Config:
        from_attributes = True

class AlertResolveRequest(BaseModel):
    action: str # APPROVE_APPLICANT, REJECT_APPLICANT, DISMISS_ALERT
    resolved_by: str
    reason: str

# --- COMPLIANCE CASE SCHEMAS ---
class CaseCreateRequest(BaseModel):
    application_id: str
    alert_id: Optional[str] = None
    assigned_to: Optional[str] = None

class CaseResponse(BaseModel):
    case_id: str
    application_id: str
    alert_id: Optional[str] = None
    priority: str
    recommended_action: str
    final_action: Optional[str] = None
    status: str
    assigned_to: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_reason: Optional[str] = None

    class Config:
        from_attributes = True

class CaseResolveRequest(BaseModel):
    final_action: str # APPROVED, REJECTED, DISMISSED
    resolved_by: str
    resolution_reason: str

# --- AUDIT LOG SCHEMAS ---
class AuditLogResponse(BaseModel):
    audit_id: str
    application_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    performed_by: str
    timestamp: datetime
    reason: str

    class Config:
        from_attributes = True

# --- DASHBOARD SUMMARY SCHEMAS ---
class DashboardSummaryResponse(BaseModel):
    total_applicants: int
    pending_applications: int
    approved_applications: int
    rejected_applications: int
    review_required_applications: int
    low_risk_applicants: int
    medium_risk_applicants: int
    high_risk_applicants: int
    critical_risk_applicants: int
    open_alerts: int
    open_cases: int
    recent_activity: List[AuditLogResponse] = []
