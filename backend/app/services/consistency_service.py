import re
from datetime import datetime
from typing import Optional
from app.models import Applicant, IDRecord
from app.schemas import ConsistencyCheckResponse, FieldCheckResult


class ConsistencyService:
    @staticmethod
    def _normalize_str(value: Optional[str]) -> str:
        return ' '.join(re.sub(r'[^\w\s]', ' ', (value or '').casefold()).split())

    @staticmethod
    def _normalize_date(value: Optional[str]) -> str:
        for pattern in ('%Y-%m-%d', '%d/%m/%Y'):
            try:
                return datetime.strptime((value or '').strip(), pattern).date().isoformat()
            except ValueError:
                pass
        return ''

    @classmethod
    def check_id_number_format(cls, id_number: str, country: str) -> FieldCheckResult:
        value = (id_number or '').strip()
        rules = {
            'india': (r'\d{12}', re.sub(r'\s', '', value), 'Expected 12 digits for an Aadhaar number.'),
            'united states': (r'\d{9}', re.sub(r'[\s-]', '', value), 'Expected 9 digits for a US SSN.'),
            'united arab emirates': (r'784-\d{4}-\d{7}-\d', value, 'Expected 784-YYYY-XXXXXXX-X for an Emirates ID.'),
        }
        rule = rules.get((country or '').strip().casefold())
        if not value:
            return FieldCheckResult(field='id_number', status='FORMAT_INVALID', reason='ID number is missing.')
        if rule:
            valid = bool(re.fullmatch(rule[0], rule[1]))
            return FieldCheckResult(field='id_number', status='MATCH' if valid else 'FORMAT_INVALID', reason='ID number matches the expected format; authenticity is not verified.' if valid else rule[2])
        return FieldCheckResult(field='id_number', status='NOT_VERIFIED', reason='No country-specific format rule is configured. Manual verification is required.')

    @classmethod
    def verify_consistency(cls, applicant: Applicant, id_record: Optional[IDRecord]) -> ConsistencyCheckResponse:
        checks = []
        if not id_record:
            checks.append(FieldCheckResult(field='id_record', status='MISSING', reason='No ID record is available for comparison.'))
        else:
            titles = {'mr', 'mrs', 'ms', 'dr', 'prof', 'sir'}
            left = [t for t in cls._normalize_str(applicant.full_name).split() if t not in titles]
            right = [t for t in cls._normalize_str(id_record.name_on_id).split() if t not in titles]
            if left and right and sorted(left) == sorted(right):
                name_status, reason = 'MATCH', 'Names match after normalizing titles, punctuation and word order.'
            elif set(left) & set(right):
                name_status, reason = 'PARTIAL_MATCH', 'Some name components match, but the full names differ.'
            else:
                name_status, reason = 'MISMATCH', 'The applicant name differs from the ID record.'
            checks.append(FieldCheckResult(field='name', status=name_status, reason=reason))
            a, b = cls._normalize_date(applicant.dob), cls._normalize_date(id_record.dob_on_id)
            checks.append(FieldCheckResult(field='dob', status='MATCH' if a and b and a == b else 'MISMATCH', reason='Dates of birth match.' if a and b and a == b else 'Dates of birth differ or contain an invalid date.'))
            a, b = cls._normalize_str(applicant.address), cls._normalize_str(id_record.address_on_id)
            checks.append(FieldCheckResult(field='address', status='MATCH' if a and b and a == b else 'MISMATCH', reason='Addresses match after normalizing punctuation and spacing.' if a and b and a == b else 'Addresses differ or are missing. Review the complete address.'))
        checks.append(cls.check_id_number_format(applicant.id_number, applicant.country))
        return ConsistencyCheckResponse(passed=all(c.status == 'MATCH' for c in checks), checks=checks)
