from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import (
    ApplicantCreate, ApplicantUpdate, ApplicantResponse, 
    ConsistencyCheckResponse, ScreeningResultResponse
)
from app.repositories import ApplicantRepository, IDRecordRepository
from app.services.consistency_service import ConsistencyService
from app.services.screening_service import ScreeningService

router = APIRouter(prefix="/applicants", tags=["Applicants"])

@router.post("", response_model=ApplicantResponse, status_code=status.HTTP_201_CREATED)
def create_applicant(applicant_in: ApplicantCreate, db: Session = Depends(get_db)):
    repo = ApplicantRepository(db)
    if applicant_in.application_id and repo.get_by_id(applicant_in.application_id):
        raise HTTPException(status_code=400, detail=f"Applicant with ID {applicant_in.application_id} already exists")
    
    applicant = repo.create(applicant_in)
    
    # Auto-screen new applicant upon creation
    screening_service = ScreeningService(db)
    screening_service.screen_applicant(applicant.application_id)
    
    # Refresh to return updated status/risk_level
    return repo.get_by_id(applicant.application_id)

@router.get("", response_model=List[ApplicantResponse])
def list_applicants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    repo = ApplicantRepository(db)
    return repo.get_all(skip=skip, limit=limit, status=status, risk_level=risk_level)

@router.get("/{application_id}", response_model=ApplicantResponse)
def get_applicant(application_id: str, db: Session = Depends(get_db)):
    repo = ApplicantRepository(db)
    applicant = repo.get_by_id(application_id)
    if not applicant:
        raise HTTPException(status_code=404, detail=f"Applicant {application_id} not found")
    return applicant

@router.patch("/{application_id}", response_model=ApplicantResponse)
def update_applicant(application_id: str, update_in: ApplicantUpdate, db: Session = Depends(get_db)):
    repo = ApplicantRepository(db)
    updated = repo.update(application_id, update_in)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Applicant {application_id} not found")
    return updated

@router.post("/{application_id}/consistency-check", response_model=ConsistencyCheckResponse)
def run_consistency_check(application_id: str, db: Session = Depends(get_db)):
    app_repo = ApplicantRepository(db)
    id_repo = IDRecordRepository(db)
    
    applicant = app_repo.get_by_id(application_id)
    if not applicant:
        raise HTTPException(status_code=404, detail=f"Applicant {application_id} not found")
        
    id_record = id_repo.get_by_applicant_id(application_id)
    return ConsistencyService.verify_consistency(applicant, id_record)

@router.post("/{application_id}/screen", response_model=List[ScreeningResultResponse])
def trigger_applicant_screening(application_id: str, db: Session = Depends(get_db)):
    app_repo = ApplicantRepository(db)
    if not app_repo.get_by_id(application_id):
        raise HTTPException(status_code=404, detail=f"Applicant {application_id} not found")
        
    service = ScreeningService(db)
    return service.screen_applicant(application_id)
