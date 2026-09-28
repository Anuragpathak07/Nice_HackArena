from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import ComplianceCase, ComplianceAlert, Applicant, AuditLog
from app.repositories import CaseRepository, AlertRepository, ApplicantRepository, AuditRepository
from app.schemas import CaseCreateRequest, CaseResolveRequest

class CaseService:
    def __init__(self, db: Session):
        self.db = db
        self.case_repo = CaseRepository(db)
        self.alert_repo = AlertRepository(db)
        self.applicant_repo = ApplicantRepository(db)
        self.audit_repo = AuditRepository(db)

    def create_case_from_alert(self, request: CaseCreateRequest) -> ComplianceCase:
        applicant = self.applicant_repo.get_by_id(request.application_id)
        if not applicant:
            raise ValueError(f"Applicant {request.application_id} not found")

        priority = "MEDIUM"
        recommended_action = "MANUAL_REVIEW"

        if request.alert_id:
            alert = self.alert_repo.get_by_id(request.alert_id)
            if alert:
                priority = alert.priority
                recommended_action = alert.recommended_action
                alert.status = "IN_REVIEW"

        case_data = {
            "application_id": applicant.application_id,
            "alert_id": request.alert_id,
            "priority": priority,
            "recommended_action": recommended_action,
            "status": "OPEN",
            "assigned_to": request.assigned_to or "Compliance Officer"
        }

        case = self.case_repo.create(case_data)

        # Log Audit Record
        self.audit_repo.create({
            "application_id": applicant.application_id,
            "action": "COMPLIANCE_CASE_CREATED",
            "entity_type": "CASE",
            "entity_id": case.case_id,
            "old_value": "NONE",
            "new_value": "OPEN",
            "performed_by": request.assigned_to or "SYSTEM",
            "reason": f"Created compliance case {case.case_id} for applicant {applicant.full_name}"
        })

        return case

    def resolve_case(self, case_id: str, request: CaseResolveRequest) -> ComplianceCase:
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise ValueError(f"Compliance Case {case_id} not found")

        applicant = self.applicant_repo.get_by_id(case.application_id)
        old_status = applicant.status if applicant else "UNKNOWN"

        case.final_action = request.final_action
        case.status = "RESOLVED"
        case.resolved_at = datetime.utcnow()
        case.resolution_reason = request.resolution_reason

        # Update Applicant Status
        if request.final_action == "APPROVED":
            new_applicant_status = "APPROVED"
        elif request.final_action == "REJECTED":
            new_applicant_status = "REJECTED"
        else:
            new_applicant_status = applicant.status if applicant else "PENDING"

        if applicant and new_applicant_status != old_status:
            self.applicant_repo.update(applicant.application_id, {"status": new_applicant_status})

        # Resolve associated alert if present
        if case.alert_id:
            alert = self.alert_repo.get_by_id(case.alert_id)
            if alert:
                alert.status = "RESOLVED"
                alert.resolved_at = datetime.utcnow()
                alert.resolved_by = request.resolved_by
                alert.resolution_reason = request.resolution_reason

        self.db.commit()
        self.db.refresh(case)

        # Log Audit Record
        self.audit_repo.create({
            "application_id": case.application_id,
            "action": f"COMPLIANCE_CASE_RESOLVED_{request.final_action}",
            "entity_type": "CASE",
            "entity_id": case.case_id,
            "old_value": f"Status: {old_status}, Case: OPEN",
            "new_value": f"Status: {new_applicant_status}, Case: RESOLVED",
            "performed_by": request.resolved_by,
            "reason": request.resolution_reason
        })

        return case
