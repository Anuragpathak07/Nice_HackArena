"""Frontend endpoints; writes use a single database transaction."""
from datetime import date, datetime
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlalchemy.orm import Session, selectinload
from app.core.database import get_db
from app.core.config import settings
from app.models import Applicant, IDRecord, ScreeningResult, Watchlist, AuditLog
from app.services.consistency_service import ConsistencyService
from app.services.screening_service import ScreeningService
from app.services.rescreening_service import ReScreeningService

router = APIRouter(prefix='/workspace', tags=['Workspace'])

class IdentityInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name_on_id: str = Field(min_length=2, max_length=255)
    dob_on_id: date
    address_on_id: str = Field(min_length=3, max_length=2000)

    @field_validator('dob_on_id')
    @classmethod
    def past_date(cls, value):
        if value > date.today():
            raise ValueError('Date of birth cannot be in the future')
        return value

class OnboardingInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    full_name: str = Field(min_length=2, max_length=255)
    dob: date
    address: str = Field(min_length=3, max_length=2000)
    id_number: str = Field(min_length=1, max_length=100)
    occupation: str = Field(min_length=2, max_length=100)
    annual_income: float = Field(ge=0, le=1e12, allow_inf_nan=False)
    country: str = Field(min_length=2, max_length=100)
    identity: Optional[IdentityInput] = None

    @field_validator('dob')
    @classmethod
    def past_date(cls, value):
        if value > date.today():
            raise ValueError('Date of birth cannot be in the future')
        return value

class DecisionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    decision: Literal['APPROVED', 'REJECTED']
    reviewed_by: str = Field(min_length=2, max_length=100)
    reason: str = Field(min_length=5, max_length=2000)

class DismissInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    reviewed_by: str = Field(min_length=2, max_length=100)
    reason: str = Field(min_length=5, max_length=2000)

class WatchlistInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=255)
    country: str = Field(min_length=2, max_length=100)
    reason: str = Field(min_length=5, max_length=2000)

def assessment(applicant):
    identity = applicant.id_records[0] if applicant.id_records else None
    consistency = ConsistencyService.verify_consistency(applicant, identity)
    active = [s for s in applicant.screening_results if s.review_status not in ('DISMISSED', 'FALSE_POSITIVE')]
    score = max((s.match_score for s in active), default=0)
    risk = 'HIGH' if score >= settings.FUZZY_HIGH_THRESHOLD else 'MEDIUM' if score >= settings.FUZZY_MEDIUM_THRESHOLD else 'LOW'
    return {'risk_level': risk, 'watchlist_matches': len(active), 'highest_match': score,
        'discrepancy_count': sum(c.status not in ('MATCH', 'NOT_VERIFIED') for c in consistency.checks),
        'unverified_count': sum(c.status == 'NOT_VERIFIED' for c in consistency.checks),
        'checks': [c.model_dump() for c in consistency.checks], 'passed': consistency.passed}

def applicant_json(applicant, detail=False):
    data = {c.name: getattr(applicant, c.name) for c in Applicant.__table__.columns}
    data.update(assessment(applicant))
    if detail:
        identity = applicant.id_records[0] if applicant.id_records else None
        data['identity'] = {c.name: getattr(identity, c.name) for c in IDRecord.__table__.columns} if identity else None
        data['matches'] = [{**{c.name: getattr(s, c.name) for c in ScreeningResult.__table__.columns},
            'name': s.watchlist_entry.name if s.watchlist_entry else 'Removed entry',
            'country': s.watchlist_entry.country if s.watchlist_entry else None,
            'watchlist_reason': s.watchlist_entry.reason if s.watchlist_entry else ''} for s in applicant.screening_results]
    return data

def get_applicant(db, application_id):
    applicant = db.query(Applicant).filter_by(application_id=application_id).with_for_update().first()
    if not applicant:
        raise HTTPException(404, 'Application not found')
    return applicant

@router.get('/applications')
def applications(db: Session = Depends(get_db)):
    rows = db.query(Applicant).options(selectinload(Applicant.id_records), selectinload(Applicant.screening_results)).order_by(Applicant.created_at.desc(), Applicant.application_id).all()
    return [applicant_json(a) for a in rows]

@router.get('/applications/{application_id}')
def application_detail(application_id: str, db: Session = Depends(get_db)):
    return applicant_json(get_applicant(db, application_id), detail=True)

@router.post('/applications', status_code=201)
def onboard(payload: OnboardingInput, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude={'identity'})
    data['dob'] = payload.dob.isoformat()
    applicant = Applicant(**data, status='PENDING', risk_level='LOW')
    db.add(applicant)
    db.flush()
    if payload.identity:
        identity = payload.identity.model_dump()
        identity['dob_on_id'] = payload.identity.dob_on_id.isoformat()
        db.add(IDRecord(application_id=applicant.application_id, **identity))
    db.add(AuditLog(application_id=applicant.application_id, action='APPLICATION_CREATED', new_status='PENDING', performed_by='Onboarding', reason='Applicant details and available ID record submitted.'))
    db.flush()
    ScreeningService(db).screen_applicant(applicant.application_id, commit=False)
    db.flush()
    db.expire(applicant)
    return applicant_json(applicant, detail=True)

@router.post('/applications/{application_id}/screen')
def screen(application_id: str, db: Session = Depends(get_db)):
    applicant = get_applicant(db, application_id)
    ScreeningService(db).screen_applicant(application_id, commit=False)
    db.flush()
    db.expire(applicant)
    return applicant_json(applicant, detail=True)

@router.post('/applications/{application_id}/decision')
def decide(application_id: str, payload: DecisionInput, db: Session = Depends(get_db)):
    applicant = get_applicant(db, application_id)
    if applicant.status in ('APPROVED', 'REJECTED'):
        raise HTTPException(409, 'This application already has a decision. New watchlist evidence will reopen it for review.')
    old_status = applicant.status
    applicant.status = payload.decision
    for alert in applicant.alerts:
        alert.status = 'RESOLVED'
    for match in applicant.screening_results:
        if match.review_status == 'PENDING_REVIEW':
            match.review_status = 'REVIEWED'
            match.reviewed_by = payload.reviewed_by
            match.reviewed_at = datetime.utcnow()
    db.add(AuditLog(application_id=application_id, action='APPLICATION_' + payload.decision, old_status=old_status,
        new_status=payload.decision, performed_by=payload.reviewed_by, reason=payload.reason))
    db.flush()
    return applicant_json(applicant, detail=True)

@router.post('/matches/{screening_id}/dismiss')
def dismiss(screening_id: str, payload: DismissInput, db: Session = Depends(get_db)):
    match = db.get(ScreeningResult, screening_id)
    if not match:
        raise HTTPException(404, 'Match not found')
    applicant = get_applicant(db, match.application_id)
    if match.review_status in ('DISMISSED', 'FALSE_POSITIVE'):
        raise HTTPException(409, 'This match has already been dismissed')
    match.review_status = 'FALSE_POSITIVE'
    match.reviewed_by = payload.reviewed_by
    match.reviewed_at = datetime.utcnow()
    for alert in match.alerts:
        alert.status = 'RESOLVED'
    applicant.risk_level = assessment(applicant)['risk_level']
    db.add(AuditLog(application_id=applicant.application_id, action='WATCHLIST_MATCH_DISMISSED', old_status=applicant.status,
        new_status=applicant.status, performed_by=payload.reviewed_by, reason=payload.reason))
    db.flush()
    return applicant_json(applicant, detail=True)

@router.post('/watchlist', status_code=201)
def add_watchlist(payload: WatchlistInput, db: Session = Depends(get_db)):
    entry = Watchlist(**payload.model_dump())
    db.add(entry)
    db.flush()
    alerts = ReScreeningService(db).rescreen_watchlist_entry(entry, commit=False)
    return {'watchlist_id': entry.watchlist_id, 'alerts_generated': alerts}
