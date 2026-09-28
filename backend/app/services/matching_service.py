import re
from typing import Dict, Any, Tuple, List
from rapidfuzz import fuzz

class MatchingService:
    @staticmethod
    def normalize_name(name: str) -> str:
        if not name:
            return ""
        clean = re.sub(r'[^\w\s]', '', name.lower())
        titles = {'mr', 'mrs', 'ms', 'dr', 'prof', 'sir'}
        tokens = [t for t in clean.split() if t not in titles]
        return " ".join(tokens)

    @classmethod
    def calculate_similarity_with_evidence(
        cls, 
        applicant_name: str, 
        watchlist_name: str, 
        applicant_country: str = None, 
        watchlist_country: str = None,
        applicant_dob: str = None,
        applicant_address: str = None
    ) -> Tuple[float, str, str, List[Dict[str, Any]]]:
        """
        Returns (similarity_score, match_type, reason_description, evidence_list)
        """
        raw_app = applicant_name.strip()
        raw_wl = watchlist_name.strip()

        norm_app = cls.normalize_name(raw_app)
        norm_wl = cls.normalize_name(raw_wl)

        token_sort_score = float(fuzz.token_sort_ratio(norm_app, norm_wl))
        ratio_score = float(fuzz.ratio(norm_app, norm_wl))
        partial_score = float(fuzz.partial_ratio(norm_app, norm_wl))

        # Best match score
        best_score = max(token_sort_score, (ratio_score * 0.7 + partial_score * 0.3))
        if raw_app.lower() == raw_wl.lower() or norm_app == norm_wl:
            best_score = 100.0

        best_score = round(best_score, 2)

        # Match Type Classification
        if raw_app.lower() == raw_wl.lower():
            match_type = "EXACT"
        elif norm_app == norm_wl:
            match_type = "NORMALIZED"
        elif best_score >= 90.0:
            match_type = "FUZZY_HIGH"
        elif best_score >= 75.0:
            match_type = "FUZZY_MEDIUM"
        else:
            match_type = "NO_MATCH"

        # Evidence Signals Matrix
        evidence_list = []

        # Signal 1: Name Similarity
        evidence_list.append({
            "signal": "NAME_SIMILARITY",
            "score_value": best_score,
            "is_boolean_match": best_score >= 90.0,
            "description": f"Applicant name '{raw_app}' has {best_score:.1f}% similarity to watchlist entry '{raw_wl}'"
        })

        # Signal 2: Country Match
        country_match = False
        if applicant_country and watchlist_country:
            if applicant_country.strip().lower() == watchlist_country.strip().lower():
                country_match = True
        evidence_list.append({
            "signal": "COUNTRY_MATCH",
            "score_value": 100.0 if country_match else 0.0,
            "is_boolean_match": country_match,
            "description": f"Country match ({applicant_country})" if country_match else f"Country mismatch (Applicant: '{applicant_country}', Watchlist: '{watchlist_country}')"
        })

        # Signal 3: DOB Match Placeholder signal
        evidence_list.append({
            "signal": "DOB_MATCH",
            "score_value": 100.0 if applicant_dob else 0.0,
            "is_boolean_match": True if applicant_dob else False,
            "description": f"Applicant Date of Birth recorded: {applicant_dob}" if applicant_dob else "DOB not provided"
        })

        # Reason Text
        if match_type in ["EXACT", "NORMALIZED"]:
            reason = f"Exact or normalized name match: '{raw_app}' matches watchlist record '{raw_wl}'"
        elif best_score >= 75.0:
            reason = f"Potential match ({best_score:.1f}% similarity) between '{raw_app}' and watchlist record '{raw_wl}'"
            if country_match:
                reason += f" with matching country ({applicant_country})"
        else:
            reason = f"No significant watchlist match found ({best_score:.1f}% similarity)"

        return best_score, match_type, reason, evidence_list
