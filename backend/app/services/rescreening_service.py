from typing import List
from sqlalchemy.orm import Session
from app.models import Watchlist, Applicant
from app.repositories import ApplicantRepository, ScreeningRepository, AlertRepository, AuditRepository
from app.services.matching_service import MatchingService
from app.core.config import settings

class ReScreeningService:
    def __init__(self, db: Session):
        self.db = db
        self.applicant_repo = ApplicantRepository(db)
        self.screening_repo = ScreeningRepository(db)
        self.alert_repo = AlertRepository(db)
        self.audit_repo = AuditRepository(db)

    def rescreen_watchlist_entry(self, watchlist_entry: Watchlist) -> int:
        """
        Runs continuous re-screening for a new or updated watchlist entry against all active applicants.
        Returns count of new alerts generated.
        """
        all_applicants = self.applicant_repo.get_all(limit=5000)
        alerts_generated = 0

        for applicant in all_applicants:
            score, match_type, reason = MatchingService.calculate_similarity(
                applicant_name=applicant.full_name,
                watchlist_name=watchlist_entry.name,
                applicant_country=applicant.country,
                watchlist_country=watchlist_entry.country
            )

            if score >= settings.FUZZY_MEDIUM_THRESHOLD:
                if score >= settings.FUZZY_HIGH_THRESHOLD or match_type in ["EXACT", "NORMALIZED"]:
                    risk_level = "HIGH" if not (watchlist_entry.country and watchlist_entry.country.lower() == applicant.country.lower()) else "CRITICAL"
                else:
                    risk_level = "MEDIUM"

                full_reason = f"Re-screening Match: {reason}. Watchlist Reason: {watchlist_entry.reason}"

                # 1. Save screening result
                screening_result = self.screening_repo.create({
                    "application_id": applicant.application_id,
                    "watchlist_id": watchlist_entry.watchlist_id,
                    "match_score": score,
                    "match_type": match_type,
                    "risk_level": risk_level,
                    "reason": full_reason,
                    "review_status": "PENDING_REVIEW"
                })

                # 2. Create Compliance Alert
                self.alert_repo.create({
                    "application_id": applicant.application_id,
                    "screening_id": screening_result.screening_id,
                    "alert_type": "RE_SCREENING_MATCH",
                    "status": "OPEN"
                })

                # 3. Update applicant status to IN_REVIEW
                old_status = applicant.status
                self.applicant_repo.update(applicant.application_id, {
                    "status": "IN_REVIEW",
                    "risk_level": risk_level if risk_level in ["HIGH", "CRITICAL"] else applicant.risk_level
                })

                # 4. Record Audit Log
                self.audit_repo.create({
                    "application_id": applicant.application_id,
                    "action": "CONTINUOUS_RESCREENING_ALERT",
                    "old_status": old_status,
                    "new_status": "IN_REVIEW",
                    "performed_by": "CONTINUOUS_RESCREENING_ENGINE",
                    "reason": f"New watchlist entry '{watchlist_entry.name}' produced a {score:.1f}% fuzzy match."
                })

                alerts_generated += 1

        return alerts_generated
