import os
import csv
import sys
from sqlalchemy.orm import Session

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.core.database import SessionLocal, engine, Base
from app.models import Applicant, IDRecord, Watchlist
from app.services.screening_service import ScreeningService

def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    base_dir = os.path.abspath(os.path.dirname(__file__))
    applicants_csv = os.path.join(base_dir, "..", "applicants.csv")
    id_records_csv = os.path.join(base_dir, "..", "id_records.csv")
    watchlist_csv = os.path.join(base_dir, "..", "watchlist.csv")

    print(f"Loading synthetic data from:\n - {applicants_csv}\n - {id_records_csv}\n - {watchlist_csv}")

    try:
        # 1. Seed Watchlist
        if os.path.exists(watchlist_csv):
            with open(watchlist_csv, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    existing = db.query(Watchlist).filter(Watchlist.name == row["name"]).first()
                    if not existing:
                        w = Watchlist(
                            name=row["name"].strip(),
                            country=row.get("country", "").strip(),
                            reason=row.get("reason", "").strip()
                        )
                        db.add(w)
                        count += 1
            db.commit()
            print(f"Watchlist seeded ({count} entries)!")

        # 2. Seed Applicants
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
            print(f"Applicants seeded ({count} entries)!")

        # 3. Seed ID Records
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
            print(f"ID Records seeded ({count} entries)!")

        # 4. Trigger Initial Automated Screening across all applicants
        print("Running automated watchlist screening across seeded applicants...")
        screening_service = ScreeningService(db)
        all_applicants = db.query(Applicant).all()
        matches_found = 0
        for applicant in all_applicants:
            results = screening_service.screen_applicant(applicant.application_id)
            if results:
                matches_found += len(results)

        print(f"Initial automated screening completed! Found {matches_found} potential watchlist matches across {len(all_applicants)} applicants.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
