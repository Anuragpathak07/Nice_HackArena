import re
from typing import Optional, Dict, Any
from app.models import Applicant, IDRecord
from app.schemas import ConsistencyCheckResponse, FieldCheckResult

class ConsistencyService:
    @staticmethod
    def _normalize_str(s: Optional[str]) -> str:
        if not s:
            return ""
        cleaned = re.sub(r'[^\w\s]', '', s.lower())
        return " ".join(cleaned.split())

    @staticmethod
    def _normalize_date(d: Optional[str]) -> str:
        if not d:
            return ""
        d = d.strip()
        if re.match(r'^\d{4}-\d{2}-\d{2}$', d):
            return d
        if re.match(r'^\d{2}/\d{2}/\d{4}$', d):
            parts = d.split('/')
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
        return d

    @classmethod
    def check_id_number_format(cls, id_number: str, country: str) -> FieldCheckResult:
        id_clean = id_number.strip() if id_number else ""
        if not id_clean:
            return FieldCheckResult(
                field="id_number",
                status="FORMAT_INVALID",
                application_value=id_number,
                reason="ID Number is blank"
            )
        if country.upper() == "INDIA":
            clean_digits = re.sub(r'\s+', '', id_clean)
            if re.match(r'^\d{12}$', clean_digits):
                return FieldCheckResult(field="id_number", status="MATCH", application_value=id_number, reason="Valid Indian Aadhaar format (12 digits)")
            return FieldCheckResult(field="id_number", status="FORMAT_INVALID", application_value=id_number, reason="Invalid Indian Aadhaar format (Expected 12 digits)")

        elif country.upper() == "UNITED STATES":
            clean_ssn = re.sub(r'[\s\-]+', '', id_clean)
            if re.match(r'^\d{9}$', clean_ssn):
                return FieldCheckResult(field="id_number", status="MATCH", application_value=id_number, reason="Valid US SSN format (9 digits)")
            return FieldCheckResult(field="id_number", status="FORMAT_INVALID", application_value=id_number, reason="Invalid US SSN format (Expected 9 digits)")

        elif country.upper() == "UNITED ARAB EMIRATES":
            if re.match(r'^784-\d{4}-\d{7}-\d{1}$', id_clean):
                return FieldCheckResult(field="id_number", status="MATCH", application_value=id_number, reason="Valid UAE Emirates ID format (784-YYYY-XXXXXXX-X)")
            return FieldCheckResult(field="id_number", status="FORMAT_INVALID", application_value=id_number, reason="Invalid UAE Emirates ID format structure")

        if len(id_clean) >= 5:
            return FieldCheckResult(field="id_number", status="MATCH", application_value=id_number, reason=f"ID number format accepted for {country}")
        return FieldCheckResult(field="id_number", status="FORMAT_INVALID", application_value=id_number, reason=f"ID number too short for country {country}")

    @classmethod
    def verify_consistency(cls, applicant: Applicant, id_record: Optional[IDRecord]) -> ConsistencyCheckResponse:
        checks = []
        overall_passed = True
        mismatch_count = 0

        if not id_record:
            checks.append(FieldCheckResult(
                field="id_record",
                status="MISSING",
                reason="No corresponding ID record found for application verification"
            ))
            return ConsistencyCheckResponse(
                passed=False, 
                mismatch_count=1, 
                explanation="No ID record found to compare application against.",
                checks=checks
            )

        # 1. Name Check
        app_name_norm = cls._normalize_str(applicant.full_name)
        id_name_norm = cls._normalize_str(id_record.name_on_id)
        app_tokens = [t for t in app_name_norm.split() if t not in {'mr', 'ms', 'mrs', 'dr'}]
        id_tokens = [t for t in id_name_norm.split() if t not in {'mr', 'ms', 'mrs', 'dr'}]

        if set(app_tokens) == set(id_tokens) or app_name_norm == id_name_norm:
            checks.append(FieldCheckResult(field="name", status="MATCH", application_value=applicant.full_name, id_value=id_record.name_on_id, reason="Names match exactly"))
        elif any(t in id_tokens for t in app_tokens if len(t) > 2):
            checks.append(FieldCheckResult(field="name", status="PARTIAL_MATCH", application_value=applicant.full_name, id_value=id_record.name_on_id, reason=f"Names share common tokens"))
        else:
            checks.append(FieldCheckResult(field="name", status="MISMATCH", application_value=applicant.full_name, id_value=id_record.name_on_id, reason=f"Application name '{applicant.full_name}' differs from ID record '{id_record.name_on_id}'"))
            overall_passed = False
            mismatch_count += 1

        # 2. DOB Check
        app_dob_norm = cls._normalize_date(applicant.dob)
        id_dob_norm = cls._normalize_date(id_record.dob_on_id)
        if app_dob_norm == id_dob_norm:
            checks.append(FieldCheckResult(field="dob", status="MATCH", application_value=applicant.dob, id_value=id_record.dob_on_id, reason="Date of Birth matches"))
        else:
            checks.append(FieldCheckResult(field="dob", status="MISMATCH", application_value=applicant.dob, id_value=id_record.dob_on_id, reason=f"Application DOB ({applicant.dob}) differs from ID record ({id_record.dob_on_id})"))
            overall_passed = False
            mismatch_count += 1

        # 3. Address Check
        app_addr_norm = cls._normalize_str(applicant.address)
        id_addr_norm = cls._normalize_str(id_record.address_on_id)
        if app_addr_norm == id_addr_norm:
            checks.append(FieldCheckResult(field="address", status="MATCH", application_value=applicant.address, id_value=id_record.address_on_id, reason="Addresses match"))
        elif any(part in id_addr_norm for part in app_addr_norm.split() if len(part) > 3):
            checks.append(FieldCheckResult(field="address", status="MATCH", application_value=applicant.address, id_value=id_record.address_on_id, reason="Address key details match"))
        else:
            checks.append(FieldCheckResult(field="address", status="MISMATCH", application_value=applicant.address, id_value=id_record.address_on_id, reason=f"Application address differs from ID record"))
            overall_passed = False
            mismatch_count += 1

        # 4. ID Format Check
        id_format_result = cls.check_id_number_format(applicant.id_number, applicant.country)
        checks.append(id_format_result)
        if id_format_result.status == "FORMAT_INVALID":
            overall_passed = False
            mismatch_count += 1

        explanation = "All identity fields match the submitted ID document." if overall_passed else f"Identity verification detected {mismatch_count} field mismatch(es) or format error(s)."

        return ConsistencyCheckResponse(
            passed=overall_passed,
            mismatch_count=mismatch_count,
            explanation=explanation,
            checks=checks
        )
