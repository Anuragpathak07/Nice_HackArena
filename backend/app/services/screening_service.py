from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Applicant, Watchlist, ScreeningResult, ComplianceAlert, AuditLog
from app.repositories import (
    ApplicantRepository, WatchlistRepository, ScreeningRepository,
    AlertRepository, AuditRepository
)
from app.services.matching_service import MatchingService
from app.services.risk_service import RiskEngineService
from app.core.config import settings

class ScreeningService:
    def __init__(self, db: Session):
        self.db = db
        self.applicant_repo = ApplicantRepository(db)
        self.watchlist_repo = WatchlistRepository(db)
        self.screening_repo = ScreeningRepository(db)
        self.alert_repo = AlertRepository(db)
        self.audit_repo = AuditRepository(db)

    def screen_applicant(self, application_id: str) -> List[ScreeningResult]:
        applicant = self.applicant_repo.get_by_id(application_id)
        if not applicant:
            raise ValueError(f"Applicant {application_id} not found")

        watchlist_entries = self.watchlist_repo.get_all(limit=1000)
        screening_results = []
        highest_risk = "LOW"
        highest_score = 0.0

        for entry in watchlist_entries:
            score, match_type, reason, evidence_list = MatchingService.calculate_similarity_with_evidence(
                applicant_name=applicant.full_name,
                watchlist_name=entry.name,
                applicant_country=applicant.country,
                watchlist_country=entry.country,
                applicant_dob=applicant.dob,
                applicant_address=applicant.address
            )

            country_match = any(e["is_boolean_match"] for e in evidence_list if e["signal"] == "COUNTRY_MATCH")

            if score >= settings.FUZZY_MEDIUM_THRESHOLD:
                risk_level, recommended_action = RiskEngineService.calculate_risk(
                    match_score=score,
                    match_type=match_type,
                    country_match=country_match
                )

                full_reason = f"{reason}. Watchlist Reason: {entry.reason}"

                screening_data = {
                    "application_id": applicant.application_id,
                    "watchlist_id": entry.watchlist_id,
                    "match_score": score,
                    "match_type": match_type,
                    "risk_level": risk_level,
                    "reason": full_reason,
                    "review_status": "PENDING"
                }

                result = self.screening_repo.create(screening_data, evidence_items=evidence_list)
                screening_results.append(result)

                if risk_level == "CRITICAL" or (risk_level == "HIGH" and highest_risk != "CRITICAL"):
                    highest_risk = risk_level
                elif risk_level == "MEDIUM" and highest_risk not in ["HIGH", "CRITICAL"]:
                    highest_risk = "MEDIUM"

                if score > highest_score:
                    highest_score = score

                # Create Compliance Alert
                self.alert_repo.create({
                    "application_id": applicant.application_id,
                    "screening_id": result.screening_id,
                    "alert_type": "NEW_APPLICATION_MATCH",
                    "priority": "HIGH" if risk_level in ["HIGH", "CRITICAL"] else "MEDIUM",
                    "title": f"Initial Screening Match: {applicant.full_name}",
                    "description": f"Potential match with watchlist entry '{entry.name}' ({score:.1f}% similarity). Recommended Action: {recommended_action}",
                    "risk_level": risk_level,
                    "match_score": score,
                    "recommended_action": recommended_action,
                    "status": "OPEN"
                })

        # Update applicant risk level and status
        if screening_results:
            new_status = "REVIEW_REQUIRED"
            self.applicant_repo.update(applicant.application_id, {"status": new_status, "risk_level": highest_risk})
            
            # Log Audit Event
            self.audit_repo.create({
                "application_id": applicant.application_id,
                "action": "AUTOMATED_SCREENING_MATCH_DETECTED",
                "entity_type": "APPLICATION",
                "entity_id": applicant.application_id,
                "old_value": applicant.status,
                "new_value": new_status,
                "performed_by": "SYSTEM_SCREENING_ENGINE",
                "reason": f"Automated screening found {len(screening_results)} potential watchlist match(es). Highest Score: {highest_score:.1f}%"
            })
        else:
            self.audit_repo.create({
                "application_id": applicant.application_id,
                "action": "AUTOMATED_SCREENING_CLEARED",
                "entity_type": "APPLICATION",
                "entity_id": applicant.application_id,
                "old_value": applicant.status,
                "new_value": applicant.status,
                "performed_by": "SYSTEM_SCREENING_ENGINE",
                "reason": "Screened against active watchlist. No matches found."
            })

        return screening_results
