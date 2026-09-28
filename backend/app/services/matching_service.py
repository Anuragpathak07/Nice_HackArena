import re
from typing import Dict, Any, Tuple
from rapidfuzz import fuzz

class MatchingService:
    @staticmethod
    def normalize_name(name: str) -> str:
        if not name:
            return ""
        # Lowercase, remove special characters/punctuation
        clean = re.sub(r'[^\w\s]', '', name.lower())
        # Strip common titles
        titles = {'mr', 'mrs', 'ms', 'dr', 'prof', 'sir'}
        tokens = [t for t in clean.split() if t not in titles]
        return " ".join(tokens)

    @classmethod
    def calculate_similarity(cls, applicant_name: str, watchlist_name: str, applicant_country: str = None, watchlist_country: str = None) -> Tuple[float, str, str]:
        """
        Returns (similarity_score, match_type, reason_description)
        """
        raw_app = applicant_name.strip()
        raw_wl = watchlist_name.strip()

        # 1. Exact Match
        if raw_app.lower() == raw_wl.lower():
            return 100.0, "EXACT", f"Exact name match: '{raw_app}' matches watchlist record '{raw_wl}'"

        norm_app = cls.normalize_name(raw_app)
        norm_wl = cls.normalize_name(raw_wl)

        # 2. Normalized Match
        if norm_app == norm_wl:
            return 100.0, "NORMALIZED", f"Normalized match: '{raw_app}' matches watchlist record '{raw_wl}' after removing titles/punctuation"

        # 3. Fuzzy Matching via RapidFuzz
        # token_sort_ratio handles reversed order e.g. "Kumar, Rajesh" vs "Rajesh Kumar"
        ratio_score = fuzz.ratio(norm_app, norm_wl)
        token_sort_score = fuzz.token_sort_ratio(norm_app, norm_wl)
        partial_score = fuzz.partial_ratio(norm_app, norm_wl)

        # Take weighted best score
        best_score = float(max(token_sort_score, (ratio_score * 0.7 + partial_score * 0.3)))

        # Country boosting flag
        country_match = False
        if applicant_country and watchlist_country:
            if applicant_country.strip().lower() == watchlist_country.strip().lower():
                country_match = True

        # Generate clear reason
        if best_score >= 90.0:
            match_type = "FUZZY_HIGH"
            reason = f"High fuzzy match similarity ({best_score:.1f}%) between '{raw_app}' and watchlist record '{raw_wl}'"
        elif best_score >= 75.0:
            match_type = "FUZZY_MEDIUM"
            reason = f"Potential match with {best_score:.1f}% similarity between '{raw_app}' and watchlist record '{raw_wl}'"
        else:
            match_type = "NO_MATCH"
            reason = f"Low similarity ({best_score:.1f}%)"

        if country_match and best_score >= 75.0:
            reason += f" (Country match: {applicant_country})"

        return round(best_score, 2), match_type, reason
