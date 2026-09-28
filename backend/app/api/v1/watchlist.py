from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import WatchlistCreate, WatchlistResponse
from app.repositories import WatchlistRepository
from app.services.rescreening_service import ReScreeningService

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

@router.get("", response_model=List[WatchlistResponse])
def list_watchlist_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    repo = WatchlistRepository(db)
    return repo.get_all(skip=skip, limit=limit)

@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
def add_watchlist_entry(entry_in: WatchlistCreate, db: Session = Depends(get_db)):
    repo = WatchlistRepository(db)
    entry = repo.create(entry_in)
    
    # Feature 5: Automatically re-screen all active applicants against this new watchlist record
    rescreening_service = ReScreeningService(db)
    rescreening_service.rescreen_watchlist_entry(entry)
    
    return entry

@router.get("/{watchlist_id}", response_model=WatchlistResponse)
def get_watchlist_entry(watchlist_id: str, db: Session = Depends(get_db)):
    repo = WatchlistRepository(db)
    entry = repo.get_by_id(watchlist_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Watchlist entry {watchlist_id} not found")
    return entry

@router.post("/{watchlist_id}/rescreen")
def trigger_watchlist_rescreen(watchlist_id: str, db: Session = Depends(get_db)):
    repo = WatchlistRepository(db)
    entry = repo.get_by_id(watchlist_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Watchlist entry {watchlist_id} not found")
        
    service = ReScreeningService(db)
    alerts_count = service.rescreen_watchlist_entry(entry)
    return {
        "message": f"Re-screening complete for watchlist entry '{entry.name}'.",
        "alerts_generated": alerts_count
    }
