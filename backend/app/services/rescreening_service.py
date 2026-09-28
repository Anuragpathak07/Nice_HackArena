from sqlalchemy.orm import Session
from app.models import Applicant, Alert
from app.services.screening_service import ScreeningService


class ReScreeningService:
    def __init__(self, db: Session):
        self.db = db

    def rescreen_watchlist_entry(self, watchlist_entry, commit=True):
        before = self.db.query(Alert).count()
        for applicant in self.db.query(Applicant).all():
            ScreeningService(self.db).screen_applicant(applicant.application_id, commit=False)
        self.db.flush()
        count = self.db.query(Alert).count() - before
        if commit:
            self.db.commit()
        return count
