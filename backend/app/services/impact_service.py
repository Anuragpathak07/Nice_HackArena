from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import Watchlist, Applicant, ImpactAnalysis, ImpactResult, ComplianceAlert, AuditLog
from app.repositories import (
    ApplicantRepository, WatchlistRepository, ScreeningRepository,
    ImpactRepository, AlertRepository, AuditRepository
)
from app.services.matching_service import MatchingService
from app.services.risk_service import RiskEngineService
from app.core.config import settings

class ImpactService:
    def __init__(self, db: Session):
        self.db = db
        self.applicant_repo = ApplicantRepository(db)
        self.watchlist_repo = WatchlistRepository(db)
        self.screening_repo = ScreeningRepository(db)
        self.impact_repo = ImpactRepository(db)
        self.alert_repo = AlertRepository(db)
        self.audit_repo = AuditRepository(db)

    def run_impact_analysis(self, watchlist_id: str, event_type: str = "WATCHLIST_ADDED") -> ImpactAnalysis:
        """
        Executes the 9-stage KYC Impact Radar pipeline:
        Watchlist Change -> Candidate Filtering -> Matching -> Evidence -> Risk Recalculation ->
        Before/After Comparison -> Recommended Action -> Alert Generation -> Audit Log.
        """
        watchlist_entry = self.watchlist_repo.get_by_id(watchlist_id)
        if not watchlist_entry:
            raise ValueError(f"Watchlist entry {watchlist_id} not found")

        # Check idempotency: If analysis already exists for this watchlist & event, return existing record
        existing_analysis = self.impact_repo.get_analysis_by_watchlist_and_event(watchlist_id, event_type)
        if existing_analysis and existing_analysis.analysis_status == "COMPLETED":
            return existing_analysis

        # 1. Create Impact Analysis Master Record
        analysis = self.impact_repo.create_analysis({
            "watchlist_id": watchlist_entry.watchlist_id,
            "event_type": event_type,
            "analysis_status": "IN_PROGRESS"
        })

        all_applicants = self.applicant_repo.get_all(limit=10000)
        potential_matches_count = 0
        high_confidence_count = 0
        review_required_count = 0

        for applicant in all_applicants:
            # 2. Candidate Pre-filtering & Matching
            score, match_type, reason, evidence_list = MatchingService.calculate_similarity_with_evidence(
                applicant_name=applicant.full_name,
                watchlist_name=watchlist_entry.name,
                applicant_country=applicant.country,
                watchlist_country=watchlist_entry.country,
                applicant_dob=applicant.dob,
                applicant_address=applicant.address
            )

            # Check if country matches
            country_match = any(e["is_boolean_match"] for e in evidence_list if e["signal"] == "COUNTRY_MATCH")

            # 3. Recalculate Risk & Action
            after_risk_level, recommended_action = RiskEngineService.calculate_risk(
                match_score=score,
                match_type=match_type,
                country_match=country_match
            )

            # Preserve Before State
            before_state = {
                "risk_level": applicant.risk_level,
                "watchlist_status": "CLEAR" if applicant.status in ["PENDING", "APPROVED"] else "POTENTIAL_MATCH",
                "status": applicant.status
            }

            if score >= settings.FUZZY_MEDIUM_THRESHOLD:
                potential_matches_count += 1
                if score >= settings.FUZZY_HIGH_THRESHOLD or match_type in ["EXACT", "NORMALIZED"]:
                    high_confidence_count += 1
                review_required_count += 1

                after_status = "REVIEW_REQUIRED"
                after_watchlist_status = "POTENTIAL_MATCH"
                risk_changed = (before_state["risk_level"] != after_risk_level) or (before_state["status"] != after_status)

                # Save Screening Result & Evidence
                screening_result = self.screening_repo.create({
                    "application_id": applicant.application_id,
                    "watchlist_id": watchlist_entry.watchlist_id,
                    "match_score": score,
                    "match_type": match_type,
                    "risk_level": after_risk_level,
                    "reason": f"Impact Radar: {reason}. Entry: '{watchlist_entry.name}'",
                    "review_status": "PENDING"
                }, evidence_items=evidence_list)

                # Save Before/After Impact Result
                self.impact_repo.create_result({
                    "analysis_id": analysis.analysis_id,
                    "application_id": applicant.application_id,
                    "screening_id": screening_result.screening_id,
                    "before_risk_level": before_state["risk_level"],
                    "before_watchlist_status": before_state["watchlist_status"],
                    "before_status": before_state["status"],
                    "after_risk_level": after_risk_level,
                    "after_watchlist_status": after_watchlist_status,
                    "after_status": after_status,
                    "risk_change": risk_changed,
                    "match_score": score,
                    "recommended_action": recommended_action,
                    "reason": f"Watchlist change for '{watchlist_entry.name}' produced {score:.1f}% match."
                })

                # Update Applicant State
                self.applicant_repo.update(applicant.application_id, {
                    "status": after_status,
                    "risk_level": after_risk_level
                })

                # Generate Compliance Alert
                self.alert_repo.create({
                    "application_id": applicant.application_id,
                    "screening_id": screening_result.screening_id,
                    "analysis_id": analysis.analysis_id,
                    "alert_type": "WATCHLIST_POTENTIAL_MATCH",
                    "priority": "HIGH" if after_risk_level in ["HIGH", "CRITICAL"] else "MEDIUM",
                    "title": f"KYC Impact Radar: Potential Match for {applicant.full_name}",
                    "description": f"New watchlist entry '{watchlist_entry.name}' matched with similarity score {score:.1f}%. Recommended Action: {recommended_action}",
                    "risk_level": after_risk_level,
                    "match_score": score,
                    "recommended_action": recommended_action,
                    "status": "OPEN"
                })

                # Log Immutable Audit Trail Event
                self.audit_repo.create({
                    "application_id": applicant.application_id,
                    "action": "IMPACT_RADAR_MATCH_DETECTED",
                    "entity_type": "APPLICATION",
                    "entity_id": applicant.application_id,
                    "old_value": f"Risk: {before_state['risk_level']}, Status: {before_state['status']}",
                    "new_value": f"Risk: {after_risk_level}, Status: {after_status}",
                    "performed_by": "KYC_IMPACT_RADAR_ENGINE",
                    "reason": f"Watchlist update '{watchlist_entry.name}' produced {score:.1f}% similarity. Action: {recommended_action}"
                })

        # Update Master Impact Analysis Record
        analysis.customers_scanned = len(all_applicants)
        analysis.potential_matches = potential_matches_count
        analysis.high_confidence_matches = high_confidence_count
        analysis.review_required = review_required_count
        analysis.analysis_status = "COMPLETED"
        self.db.commit()
        self.db.refresh(analysis)

        # Log Impact Analysis Completion Audit
        self.audit_repo.create({
            "action": "IMPACT_ANALYSIS_COMPLETED",
            "entity_type": "IMPACT_ANALYSIS",
            "entity_id": analysis.analysis_id,
            "old_value": "IN_PROGRESS",
            "new_value": f"Scanned: {len(all_applicants)}, Matches: {potential_matches_count}, Review Required: {review_required_count}",
            "performed_by": "KYC_IMPACT_RADAR_ENGINE",
            "reason": f"Impact Analysis completed for watchlist entry '{watchlist_entry.name}'"
        })

        return analysis
