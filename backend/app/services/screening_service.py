from sqlalchemy.orm import Session
from app.models import Applicant, Watchlist, ScreeningResult, Alert, AuditLog
from app.services.matching_service import MatchingService
from app.services.consistency_service import ConsistencyService
from app.core.config import settings


class ScreeningService:
    """Shared, repeatable screening path. Risk is based only on watchlist evidence."""
    def __init__(self, db: Session):
        self.db = db

    def screen_applicant(self, application_id: str, commit: bool = True):
        applicant = self.db.get(Applicant, application_id)
        if not applicant:
            raise ValueError(f'Applicant {application_id} not found')
        old_status = applicant.status
        results = []
        new_matches = 0
        for entry in self.db.query(Watchlist).all():
            score, match_type, reason = MatchingService.calculate_similarity(applicant.full_name, entry.name, applicant.country, entry.country)
            if score < settings.FUZZY_MEDIUM_THRESHOLD:
                continue
            existing = self.db.query(ScreeningResult).filter_by(application_id=application_id, watchlist_id=entry.watchlist_id).first()
            if existing:
                results.append(existing)
                continue
            result = ScreeningResult(application_id=application_id, watchlist_id=entry.watchlist_id,
                match_score=score, match_type=match_type, risk_level='HIGH' if score >= settings.FUZZY_HIGH_THRESHOLD else 'MEDIUM',
                reason=f'{reason}. Watchlist reason: {entry.reason}', review_status='PENDING_REVIEW')
            self.db.add(result)
            self.db.flush()
            self.db.add(Alert(application_id=application_id, screening_id=result.screening_id, alert_type='WATCHLIST_MATCH', status='OPEN'))
            results.append(result)
            new_matches += 1
        self.db.flush()
        active = [r for r in results if r.review_status not in ('DISMISSED', 'FALSE_POSITIVE')]
        applicant.risk_level = 'HIGH' if any(r.match_score >= settings.FUZZY_HIGH_THRESHOLD for r in active) else 'MEDIUM' if active else 'LOW'
        consistent = ConsistencyService.verify_consistency(applicant, applicant.id_records[0] if applicant.id_records else None)
        if new_matches or (applicant.status == 'PENDING' and not consistent.passed):
            applicant.status = 'IN_REVIEW'
        self.db.add(AuditLog(application_id=application_id, action='SCREENING_COMPLETED', old_status=old_status,
            new_status=applicant.status, performed_by='Screening engine',
            reason=f'{new_matches} new watchlist match(es). Watchlist risk: {applicant.risk_level}. Identity findings are assessed separately.'))
        if commit:
            self.db.commit()
        return results
