from typing import Optional, List
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
    application_id: Optional[str] = None # Optional custom ID, e.g. APP0001

class ApplicantUpdate(BaseModel):
    full_name: Optional[str] = None
    dob: Optional[str] = None
    address: Optional[str] = None
    id_number: Optional[str] = None
    occupation: Optional[str] = None
    annual_income: Optional[float] = None
    country: Optional[str] = None
    status: Optional[str] = None
    risk_level: Optional[str] = None

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
    status: str # MATCH, MISMATCH, FORMAT_INVALID, MISSING
    reason: str

class ConsistencyCheckResponse(BaseModel):
    passed: bool
    checks: List[FieldCheckResult]

# --- WATCHLIST SCHEMAS ---
class WatchlistBase(BaseModel):
    name: str
    country: Optional[str] = None
    reason: str

class WatchlistCreate(WatchlistBase):
    watchlist_id: Optional[str] = None

class WatchlistResponse(WatchlistBase):
    watchlist_id: str
    created_at: datetime
    updated_at: datetime

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
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- ALERT SCHEMAS ---
class AlertResponse(BaseModel):
    alert_id: str
    application_id: str
    screening_id: Optional[str] = None
    alert_type: str
    status: str
    created_at: datetime
    screening_result: Optional[ScreeningResultResponse] = None

    class Config:
        from_attributes = True

class AlertReviewRequest(BaseModel):
    action: str # APPROVE_APPLICANT, REJECT_APPLICANT, DISMISS_ALERT
    reviewed_by: str
    reason: str

# --- AUDIT LOG SCHEMAS ---
class AuditLogResponse(BaseModel):
    audit_id: str
    application_id: str
    action: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
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
    in_review_applications: int
    open_alerts: int
    risk_breakdown: dict
