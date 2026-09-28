from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import (
    AlertResponse, AlertReviewRequest, AuditLogResponse, DashboardSummaryResponse
)
from app.repositories import AlertRepository, ApplicantRepository, AuditRepository, ScreeningRepository

# --- ALERTS ROUTER ---
alerts_router = APIRouter(prefix="/alerts", tags=["Compliance Alerts"])

@alerts_router.get("", response_model=List[AlertResponse])
def list_alerts(status: Optional[str] = Query(None), db: Session = Depends(get_db)):
    repo = AlertRepository(db)
    return repo.get_all(status=status)

@alerts_router.post("/{alert_id}/review")
def review_compliance_alert(alert_id: str, review_in: AlertReviewRequest, db: Session = Depends(get_db)):
    alert_repo = AlertRepository(db)
    app_repo = ApplicantRepository(db)
    audit_repo = AuditRepository(db)

    alert = alert_repo.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    applicant = app_repo.get_by_id(alert.application_id)
    if not applicant:
        raise HTTPException(status_code=404, detail=f"Applicant for alert not found")

    old_status = applicant.status

    if review_in.action == "APPROVE_APPLICANT":
        new_status = "APPROVED"
        alert.status = "RESOLVED"
    elif review_in.action == "REJECT_APPLICANT":
        new_status = "REJECTED"
        alert.status = "RESOLVED"
    elif review_in.action == "DISMISS_ALERT":
        new_status = applicant.status
        alert.status = "RESOLVED"
    else:
        raise HTTPException(status_code=400, detail="Invalid action type. Expected APPROVE_APPLICANT, REJECT_APPLICANT, or DISMISS_ALERT")

    if new_status != old_status:
        app_repo.update(applicant.application_id, {"status": new_status})

    db.commit()

    # Log Audit Record
    audit_repo.create({
        "application_id": applicant.application_id,
        "action": f"COMPLIANCE_ALERT_REVIEWED_{review_in.action}",
        "old_status": old_status,
        "new_status": new_status,
        "performed_by": review_in.reviewed_by,
        "reason": review_in.reason
    })

    return {
        "message": f"Alert {alert_id} reviewed successfully with action '{review_in.action}'.",
        "application_id": applicant.application_id,
        "new_status": new_status
    }

# --- DASHBOARD ROUTER ---
dashboard_router = APIRouter(prefix="/dashboard", tags=["Compliance Dashboard"])

@dashboard_router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    app_repo = ApplicantRepository(db)
    alert_repo = AlertRepository(db)

    total = app_repo.count()
    by_status = app_repo.count_by_status()
    by_risk = app_repo.count_by_risk()
    open_alerts = alert_repo.count_open()

    return DashboardSummaryResponse(
        total_applicants=total,
        pending_applications=by_status.get("PENDING", 0),
        approved_applications=by_status.get("APPROVED", 0),
        rejected_applications=by_status.get("REJECTED", 0),
        in_review_applications=by_status.get("IN_REVIEW", 0),
        open_alerts=open_alerts,
        risk_breakdown=by_risk
    )

# --- AUDIT ROUTER ---
audit_router = APIRouter(prefix="/audit-logs", tags=["Audit Trail"])

@audit_router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(application_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    repo = AuditRepository(db)
    return repo.get_all(application_id=application_id)
