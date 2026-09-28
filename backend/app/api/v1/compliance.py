from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import (
    ApplicantCreate, ApplicantUpdate, ApplicantResponse,
    ConsistencyCheckResponse, ScreeningResultResponse,
    WatchlistCreate, WatchlistUpdate, WatchlistResponse,
    ImpactAnalysisResponse, ImpactAnalysisDetailResponse,
    AlertResponse, AlertResolveRequest,
    CaseCreateRequest, CaseResponse, CaseResolveRequest,
    DashboardSummaryResponse, AuditLogResponse
)
from app.repositories import (
    ApplicantRepository, IDRecordRepository, WatchlistRepository,
    ScreeningRepository, AlertRepository, CaseRepository, AuditRepository
)
from app.services.consistency_service import ConsistencyService
from app.services.screening_service import ScreeningService
from app.services.impact_service import ImpactService
from app.services.case_service import CaseService
from app.services.llm_service import LLMService
from app.services.matching_service import MatchingService

# --- APPLICANTS ROUTER ---
applicants_router = APIRouter(prefix="/applicants", tags=["Applicants"])

@applicants_router.post("", response_model=ApplicantResponse, status_code=status.HTTP_201_CREATED)
def create_applicant(applicant_in: ApplicantCreate, db: Session = Depends(get_db)):
    repo = ApplicantRepository(db)
    if applicant_in.application_id and repo.get_by_id(applicant_in.application_id):
        raise HTTPException(status_code=400, detail=f"Applicant {applicant_in.application_id} already exists")
    
    applicant = repo.create(applicant_in)
    
    # Log Audit
    audit_repo = AuditRepository(db)
    audit_repo.create({
        "application_id": applicant.application_id,
        "action": "APPLICANT_CREATED",
        "entity_type": "APPLICATION",
        "entity_id": applicant.application_id,
        "old_value": "NONE",
        "new_value": applicant.status,
        "performed_by": "SYSTEM_ONBOARDING",
        "reason": f"Created new applicant profile for {applicant.full_name}"
    })

    # Auto-screen
    screening_service = ScreeningService(db)
    screening_service.screen_applicant(applicant.application_id)

    return repo.get_by_id(applicant.application_id)

@applicants_router.get("", response_model=List[ApplicantResponse])
def list_applicants(
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=5000),
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    repo = ApplicantRepository(db)
    return repo.get_all(skip=skip, limit=limit, status=status, risk_level=risk_level)

@applicants_router.get("/{application_id}", response_model=ApplicantResponse)
def get_applicant(application_id: str, db: Session = Depends(get_db)):
    repo = ApplicantRepository(db)
    applicant = repo.get_by_id(application_id)
    if not applicant:
        raise HTTPException(status_code=404, detail=f"Applicant {application_id} not found")
    return applicant

@applicants_router.put("/{application_id}", response_model=ApplicantResponse)
def update_applicant(application_id: str, update_in: ApplicantUpdate, db: Session = Depends(get_db)):
    repo = ApplicantRepository(db)
    audit_repo = AuditRepository(db)
    old_app = repo.get_by_id(application_id)
    if not old_app:
        raise HTTPException(status_code=404, detail=f"Applicant {application_id} not found")
    
    old_status = old_app.status
    old_risk = old_app.risk_level
    updated = repo.update(application_id, update_in)
    
    audit_repo.create({
        "application_id": application_id,
        "action": "APPLICANT_UPDATED",
        "entity_type": "APPLICATION",
        "entity_id": application_id,
        "old_value": f"Status: {old_status}, Risk: {old_risk}",
        "new_value": f"Status: {updated.status}, Risk: {updated.risk_level}",
        "performed_by": "COMPLIANCE_OFFICER",
        "reason": f"Updated profile for {updated.full_name}"
    })
    return updated

@applicants_router.post("/{application_id}/verify", response_model=ApplicantResponse)
def verify_applicant(application_id: str, db: Session = Depends(get_db)):
    repo = ApplicantRepository(db)
    audit_repo = AuditRepository(db)
    applicant = repo.get_by_id(application_id)
    if not applicant:
        raise HTTPException(status_code=404, detail=f"Applicant {application_id} not found")
    
    old_status = applicant.status
    updated = repo.update(application_id, ApplicantUpdate(status="APPROVED"))
    
    audit_repo.create({
        "application_id": application_id,
        "action": "APPLICANT_MARKED_VERIFIED",
        "entity_type": "APPLICATION",
        "entity_id": application_id,
        "old_value": old_status,
        "new_value": "VERIFIED",
        "performed_by": "COMPLIANCE_OFFICER",
        "reason": f"Manually verified KYC applicant {applicant.full_name} ({application_id})"
    })
    return updated

@applicants_router.post("/{application_id}/reject", response_model=ApplicantResponse)
def reject_applicant(application_id: str, db: Session = Depends(get_db)):
    repo = ApplicantRepository(db)
    audit_repo = AuditRepository(db)
    applicant = repo.get_by_id(application_id)
    if not applicant:
        raise HTTPException(status_code=404, detail=f"Applicant {application_id} not found")
    
    old_status = applicant.status
    updated = repo.update(application_id, ApplicantUpdate(status="REJECTED"))
    
    audit_repo.create({
        "application_id": application_id,
        "action": "APPLICANT_MARKED_REJECTED",
        "entity_type": "APPLICATION",
        "entity_id": application_id,
        "old_value": old_status,
        "new_value": "REJECTED",
        "performed_by": "COMPLIANCE_OFFICER",
        "reason": f"Compliance officer rejected applicant {applicant.full_name} ({application_id})"
    })
    return updated

@applicants_router.post("/{application_id}/consistency-check", response_model=ConsistencyCheckResponse)
def run_consistency_check(application_id: str, db: Session = Depends(get_db)):
    app_repo = ApplicantRepository(db)
    id_repo = IDRecordRepository(db)
    audit_repo = AuditRepository(db)

    applicant = app_repo.get_by_id(application_id)
    if not applicant:
        raise HTTPException(status_code=404, detail=f"Applicant {application_id} not found")

    id_record = id_repo.get_by_applicant_id(application_id)
    result = ConsistencyService.verify_consistency(applicant, id_record)

    audit_repo.create({
        "application_id": applicant.application_id,
        "action": "CONSISTENCY_CHECK_COMPLETED",
        "entity_type": "APPLICATION",
        "entity_id": applicant.application_id,
        "old_value": "UNVERIFIED",
        "new_value": "VERIFIED" if result.passed else "DISCREPANCY",
        "performed_by": "CONSISTENCY_ENGINE",
        "reason": result.explanation
    })

    return result

@applicants_router.post("/{application_id}/screen", response_model=List[ScreeningResultResponse])
def trigger_applicant_screening(application_id: str, db: Session = Depends(get_db)):
    app_repo = ApplicantRepository(db)
    if not app_repo.get_by_id(application_id):
        raise HTTPException(status_code=404, detail=f"Applicant {application_id} not found")
    service = ScreeningService(db)
    return service.screen_applicant(application_id)

@applicants_router.get("/{application_id}/screening-results", response_model=List[ScreeningResultResponse])
def get_applicant_screening_results(application_id: str, db: Session = Depends(get_db)):
    repo = ScreeningRepository(db)
    return repo.get_by_applicant_id(application_id)

@applicants_router.post("/{application_id}/explain")
def generate_ai_case_summary(application_id: str, db: Session = Depends(get_db)):
    app_repo = ApplicantRepository(db)
    id_repo = IDRecordRepository(db)
    screening_repo = ScreeningRepository(db)

    applicant = app_repo.get_by_id(application_id)
    if not applicant:
        raise HTTPException(status_code=404, detail=f"Applicant {application_id} not found")

    id_record = id_repo.get_by_applicant_id(application_id)
    consistency = ConsistencyService.verify_consistency(applicant, id_record)
    screening_results = screening_repo.get_by_applicant_id(application_id)

    summary = LLMService.generate_case_summary(
        applicant=applicant,
        screening_results=screening_results,
        consistency_passed=consistency.passed
    )

    return {"application_id": application_id, "summary": summary}

# --- WATCHLIST ROUTER ---
watchlist_router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

@watchlist_router.get("", response_model=List[WatchlistResponse])
def list_watchlist_entries(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    repo = WatchlistRepository(db)
    return repo.get_all(skip=skip, limit=limit)

@watchlist_router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
def create_watchlist_entry(entry_in: WatchlistCreate, db: Session = Depends(get_db)):
    repo = WatchlistRepository(db)
    audit_repo = AuditRepository(db)
    norm_name = MatchingService.normalize_name(entry_in.name)
    entry = repo.create(entry_in, normalized_name=norm_name)

    audit_repo.create({
        "action": "WATCHLIST_ENTRY_ADDED",
        "entity_type": "WATCHLIST",
        "entity_id": entry.watchlist_id,
        "old_value": "NONE",
        "new_value": entry.name,
        "performed_by": "COMPLIANCE_OFFICER",
        "reason": f"Added watchlist entry '{entry.name}' for {entry.reason}"
    })

    # Trigger KYC Impact Radar
    impact_service = ImpactService(db)
    impact_service.run_impact_analysis(entry.watchlist_id, event_type="WATCHLIST_ADDED")

    return entry

@watchlist_router.get("/{watchlist_id}", response_model=WatchlistResponse)
def get_watchlist_entry(watchlist_id: str, db: Session = Depends(get_db)):
    repo = WatchlistRepository(db)
    entry = repo.get_by_id(watchlist_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Watchlist entry {watchlist_id} not found")
    return entry

@watchlist_router.put("/{watchlist_id}", response_model=WatchlistResponse)
def update_watchlist_entry(watchlist_id: str, update_in: WatchlistUpdate, db: Session = Depends(get_db)):
    repo = WatchlistRepository(db)
    audit_repo = AuditRepository(db)
    norm_name = MatchingService.normalize_name(update_in.name) if update_in.name else None
    entry = repo.update(watchlist_id, update_in, normalized_name=norm_name)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Watchlist entry {watchlist_id} not found")

    audit_repo.create({
        "action": "WATCHLIST_ENTRY_UPDATED",
        "entity_type": "WATCHLIST",
        "entity_id": entry.watchlist_id,
        "old_value": f"Version {entry.version - 1}",
        "new_value": f"Version {entry.version}",
        "performed_by": "COMPLIANCE_OFFICER",
        "reason": f"Updated watchlist entry '{entry.name}'"
    })

    # Trigger KYC Impact Radar
    impact_service = ImpactService(db)
    impact_service.run_impact_analysis(entry.watchlist_id, event_type="WATCHLIST_UPDATED")

    return entry

# --- KYC IMPACT RADAR ROUTER (FEATURE 5 CORE) ---
impact_router = APIRouter(prefix="", tags=["KYC Impact Radar"])

@impact_router.post("/watchlist/{watchlist_id}/impact-analysis", response_model=ImpactAnalysisResponse)
def trigger_impact_analysis(watchlist_id: str, db: Session = Depends(get_db)):
    service = ImpactService(db)
    try:
        return service.run_impact_analysis(watchlist_id, event_type="WATCHLIST_MANUAL_TRIGGER")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@impact_router.get("/impact-analysis/{analysis_id}", response_model=ImpactAnalysisDetailResponse)
def get_impact_analysis_detail(analysis_id: str, db: Session = Depends(get_db)):
    from app.repositories import ImpactRepository
    repo = ImpactRepository(db)
    analysis = repo.get_analysis_by_id(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Impact Analysis {analysis_id} not found")
    
    results = repo.get_results_by_analysis_id(analysis_id)
    formatted_results = []
    for r in results:
        formatted_results.append({
            "impact_result_id": r.impact_result_id,
            "application_id": r.application_id,
            "screening_id": r.screening_id,
            "before": {
                "risk_level": r.before_risk_level,
                "watchlist_status": r.before_watchlist_status,
                "status": r.before_status
            },
            "after": {
                "risk_level": r.after_risk_level,
                "watchlist_status": r.after_watchlist_status,
                "status": r.after_status
            },
            "risk_change": r.risk_change,
            "match_score": r.match_score,
            "recommended_action": r.recommended_action,
            "reason": r.reason
        })

    return ImpactAnalysisDetailResponse(
        analysis_id=analysis.analysis_id,
        watchlist_id=analysis.watchlist_id,
        event_type=analysis.event_type,
        customers_scanned=analysis.customers_scanned,
        potential_matches=analysis.potential_matches,
        high_confidence_matches=analysis.high_confidence_matches,
        review_required=analysis.review_required,
        analysis_status=analysis.analysis_status,
        created_at=analysis.created_at,
        results=formatted_results
    )

# --- ALERTS & CASES ROUTER ---
alerts_router = APIRouter(prefix="/alerts", tags=["Compliance Alerts"])

@alerts_router.get("", response_model=List[AlertResponse])
def list_alerts(status: Optional[str] = Query(None), priority: Optional[str] = Query(None), db: Session = Depends(get_db)):
    repo = AlertRepository(db)
    return repo.get_all(status=status, priority=priority)

@alerts_router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: str, db: Session = Depends(get_db)):
    repo = AlertRepository(db)
    alert = repo.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return alert

@alerts_router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: str, resolve_in: AlertResolveRequest, db: Session = Depends(get_db)):
    alert_repo = AlertRepository(db)
    app_repo = ApplicantRepository(db)
    audit_repo = AuditRepository(db)

    alert = alert_repo.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    applicant = app_repo.get_by_id(alert.application_id)
    old_status = applicant.status if applicant else "UNKNOWN"

    if resolve_in.action == "APPROVE_APPLICANT":
        new_status = "APPROVED"
    elif resolve_in.action == "REJECT_APPLICANT":
        new_status = "REJECTED"
    else:
        new_status = applicant.status if applicant else "PENDING"

    alert.status = "RESOLVED"
    alert.resolved_by = resolve_in.resolved_by
    alert.resolution_reason = resolve_in.reason

    if applicant and new_status != old_status:
        app_repo.update(applicant.application_id, {"status": new_status})

    db.commit()

    audit_repo.create({
        "application_id": alert.application_id,
        "action": f"COMPLIANCE_ALERT_RESOLVED_{resolve_in.action}",
        "entity_type": "ALERT",
        "entity_id": alert.alert_id,
        "old_value": old_status,
        "new_value": new_status,
        "performed_by": resolve_in.resolved_by,
        "reason": resolve_in.reason
    })

    return {"message": "Alert resolved successfully", "new_status": new_status}

cases_router = APIRouter(prefix="/cases", tags=["Compliance Cases"])

@cases_router.get("", response_model=List[CaseResponse])
def list_cases(status: Optional[str] = Query(None), db: Session = Depends(get_db)):
    repo = CaseRepository(db)
    return repo.get_all(status=status)

@cases_router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(request: CaseCreateRequest, db: Session = Depends(get_db)):
    service = CaseService(db)
    try:
        return service.create_case_from_alert(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@cases_router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: str, db: Session = Depends(get_db)):
    repo = CaseRepository(db)
    case = repo.get_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Compliance case {case_id} not found")
    return case

@cases_router.post("/{case_id}/resolve", response_model=CaseResponse)
def resolve_case(case_id: str, request: CaseResolveRequest, db: Session = Depends(get_db)):
    service = CaseService(db)
    try:
        return service.resolve_case(case_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# --- DASHBOARD & AUDIT ROUTERS ---
dashboard_router = APIRouter(prefix="/dashboard", tags=["Compliance Dashboard"])

@dashboard_router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    app_repo = ApplicantRepository(db)
    alert_repo = AlertRepository(db)
    case_repo = CaseRepository(db)
    audit_repo = AuditRepository(db)

    total = app_repo.count()
    by_status = app_repo.count_by_status()
    by_risk = app_repo.count_by_risk()
    open_alerts = alert_repo.count_open()
    open_cases = case_repo.count_open()
    recent_audits = audit_repo.get_all(limit=10)

    return DashboardSummaryResponse(
        total_applicants=total,
        pending_applications=by_status.get("PENDING", 0),
        approved_applications=by_status.get("APPROVED", 0),
        rejected_applications=by_status.get("REJECTED", 0),
        review_required_applications=by_status.get("REVIEW_REQUIRED", 0) + by_status.get("IN_REVIEW", 0),
        low_risk_applicants=by_risk.get("LOW", 0),
        medium_risk_applicants=by_risk.get("MEDIUM", 0),
        high_risk_applicants=by_risk.get("HIGH", 0),
        critical_risk_applicants=by_risk.get("CRITICAL", 0),
        open_alerts=open_alerts,
        open_cases=open_cases,
        recent_activity=recent_audits
    )

audit_router = APIRouter(prefix="/audit-logs", tags=["Audit Trail"])

@audit_router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(application_id: Optional[str] = Query(None), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    repo = AuditRepository(db)
    return repo.get_all(application_id=application_id, limit=limit)
