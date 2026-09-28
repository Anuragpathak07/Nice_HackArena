import os
import csv
import sys
from sqlalchemy.orm import Session

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.core.database import SessionLocal, engine, Base
from app.models import Applicant, IDRecord, Watchlist
from app.services.screening_service import ScreeningService
from app.services.impact_service import ImpactService
from app.services.matching_service import MatchingService

def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    base_dir = os.path.abspath(os.path.dirname(__file__))
    applicants_csv = os.path.join(base_dir, "..", "applicants.csv")
    id_records_csv = os.path.join(base_dir, "..", "id_records.csv")
    watchlist_csv = os.path.join(base_dir, "..", "watchlist.csv")

    print(f"Ingesting synthetic compliance dataset into Supabase PostgreSQL from:\n - {applicants_csv}\n - {id_records_csv}\n - {watchlist_csv}")

    try:
        # 1. Seed Applicants
        if os.path.exists(applicants_csv):
            with open(applicants_csv, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    existing = db.query(Applicant).filter(Applicant.application_id == row["applicant_id"]).first()
                    if not existing:
                        income = float(row["annual_income"]) if row.get("annual_income") else 0.0
                        app = Applicant(
                            application_id=row["applicant_id"].strip(),
                            full_name=row["full_name"].strip(),
                            dob=row["dob"].strip(),
                            address=row["address"].strip(),
                            id_number=row["id_number"].strip(),
                            occupation=row.get("occupation", "").strip(),
                            annual_income=income,
                            country=row["country"].strip(),
                            status="PENDING",
                            risk_level="LOW"
                        )
                        db.add(app)
                        count += 1
            db.commit()
            print(f"Applicants seeded ({count} new entries)!")

        # 2. Seed ID Records
        if os.path.exists(id_records_csv):
            with open(id_records_csv, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    existing = db.query(IDRecord).filter(IDRecord.application_id == row["applicant_id"]).first()
                    if not existing:
                        id_rec = IDRecord(
                            application_id=row["applicant_id"].strip(),
                            name_on_id=row["name_on_id"].strip(),
                            dob_on_id=row["dob_on_id"].strip(),
                            address_on_id=row["address_on_id"].strip()
                        )
                        db.add(id_rec)
                        count += 1
            db.commit()
            print(f"ID Records seeded ({count} new entries)!")

        # 3. Seed Watchlist Entries & Trigger KYC Impact Radar
        if os.path.exists(watchlist_csv):
            impact_service = ImpactService(db)
            with open(watchlist_csv, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    entry_name = row["name"].strip()
                    existing = db.query(Watchlist).filter(Watchlist.name == entry_name).first()
                    if not existing:
                        norm_name = MatchingService.normalize_name(entry_name)
                        w = Watchlist(
                            name=entry_name,
                            normalized_name=norm_name,
                            country=row.get("country", "").strip(),
                            reason=row.get("reason", "").strip(),
                            status="ACTIVE",
                            version=1
                        )
                        db.add(w)
                        db.commit()
                        db.refresh(w)
                        count += 1

                        # Trigger KYC Impact Radar Pipeline for each watchlist entry
                        impact_service.run_impact_analysis(w.watchlist_id, event_type="WATCHLIST_ADDED")

            print(f"Watchlist entries seeded ({count} new entries) & KYC Impact Radar Executed!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
