from typing import List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Applicant, IDRecord, Watchlist, ScreeningResult, Alert, AuditLog
from app.schemas import ApplicantCreate, ApplicantUpdate, WatchlistCreate

class ApplicantRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, application_id: str) -> Optional[Applicant]:
        return self.db.query(Applicant).filter(Applicant.application_id == application_id).first()

    def get_all(self, skip: int = 0, limit: int = 100, status: Optional[str] = None, risk_level: Optional[str] = None) -> List[Applicant]:
        query = self.db.query(Applicant)
        if status:
            query = query.filter(Applicant.status == status)
        if risk_level:
            query = query.filter(Applicant.risk_level == risk_level)
        return query.offset(skip).limit(limit).all()

    def create(self, applicant_data: ApplicantCreate) -> Applicant:
        db_applicant = Applicant(**applicant_data.model_dump(exclude_unset=True))
        self.db.add(db_applicant)
        self.db.commit()
        self.db.refresh(db_applicant)
        return db_applicant

    def update(self, application_id: str, update_data: Union[ApplicantUpdate, dict]) -> Optional[Applicant]:
        db_applicant = self.get_by_id(application_id)
        if not db_applicant:
            return None
        data_dict = update_data if isinstance(update_data, dict) else update_data.model_dump(exclude_unset=True)
        for key, value in data_dict.items():
            if value is not None:
                setattr(db_applicant, key, value)
        self.db.commit()
        self.db.refresh(db_applicant)
        return db_applicant

    def count(self) -> int:
        return self.db.query(Applicant).count()

    def count_by_status(self) -> dict:
        results = self.db.query(Applicant.status, func.count(Applicant.application_id)).group_by(Applicant.status).all()
        return {status: count for status, count in results}

    def count_by_risk(self) -> dict:
        results = self.db.query(Applicant.risk_level, func.count(Applicant.application_id)).group_by(Applicant.risk_level).all()
        return {risk: count for risk, count in results}

class IDRecordRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_applicant_id(self, application_id: str) -> Optional[IDRecord]:
        return self.db.query(IDRecord).filter(IDRecord.application_id == application_id).first()

    def create(self, id_record_data: dict) -> IDRecord:
        db_id = IDRecord(**id_record_data)
        self.db.add(db_id)
        self.db.commit()
        self.db.refresh(db_id)
        return db_id

class WatchlistRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, watchlist_id: str) -> Optional[Watchlist]:
        return self.db.query(Watchlist).filter(Watchlist.watchlist_id == watchlist_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Watchlist]:
        return self.db.query(Watchlist).offset(skip).limit(limit).all()

    def create(self, watchlist_data: WatchlistCreate) -> Watchlist:
        db_watchlist = Watchlist(**watchlist_data.model_dump(exclude_unset=True))
        self.db.add(db_watchlist)
        self.db.commit()
        self.db.refresh(db_watchlist)
        return db_watchlist

class ScreeningRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, screening_data: dict) -> ScreeningResult:
        db_screening = ScreeningResult(**screening_data)
        self.db.add(db_screening)
        self.db.commit()
        self.db.refresh(db_screening)
        return db_screening

    def get_by_applicant_id(self, application_id: str) -> List[ScreeningResult]:
        return self.db.query(ScreeningResult).filter(ScreeningResult.application_id == application_id).all()

class AlertRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, alert_data: dict) -> Alert:
        db_alert = Alert(**alert_data)
        self.db.add(db_alert)
        self.db.commit()
        self.db.refresh(db_alert)
        return db_alert

    def get_all(self, status: Optional[str] = None) -> List[Alert]:
        query = self.db.query(Alert)
        if status:
            query = query.filter(Alert.status == status)
        return query.all()

    def get_by_id(self, alert_id: str) -> Optional[Alert]:
        return self.db.query(Alert).filter(Alert.alert_id == alert_id).first()

    def count_open(self) -> int:
        return self.db.query(Alert).filter(Alert.status == "OPEN").count()

class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, audit_data: dict) -> AuditLog:
        db_audit = AuditLog(**audit_data)
        self.db.add(db_audit)
        self.db.commit()
        self.db.refresh(db_audit)
        return db_audit

    def get_all(self, application_id: Optional[str] = None) -> List[AuditLog]:
        query = self.db.query(AuditLog)
        if application_id:
            query = query.filter(AuditLog.application_id == application_id)
        return query.order_by(AuditLog.timestamp.desc()).all()
