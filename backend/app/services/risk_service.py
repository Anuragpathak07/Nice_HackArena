from typing import Dict, Any, List, Tuple
from app.core.config import settings

class RiskEngineService:
    @classmethod
    def calculate_risk(
        cls, 
        match_score: float, 
        match_type: str, 
        country_match: bool, 
        consistency_passed: bool = True
    ) -> Tuple[str, str]:
        """
        Calculates Risk Level (LOW, MEDIUM, HIGH, CRITICAL) and Recommended Action (NO_ACTION, MANUAL_REVIEW, ENHANCED_REVIEW).
        Configurable via settings.FUZZY_HIGH_THRESHOLD (90.0) and settings.FUZZY_MEDIUM_THRESHOLD (75.0).
        """
        if match_type in ["EXACT", "NORMALIZED"] or match_score >= settings.FUZZY_HIGH_THRESHOLD:
            if country_match:
                risk_level = "CRITICAL"
                recommended_action = "ENHANCED_REVIEW"
            else:
                risk_level = "HIGH"
                recommended_action = "ENHANCED_REVIEW"
        elif match_score >= settings.FUZZY_MEDIUM_THRESHOLD:
            if country_match:
                risk_level = "HIGH"
                recommended_action = "ENHANCED_REVIEW"
            else:
                risk_level = "MEDIUM"
                recommended_action = "MANUAL_REVIEW"
        else:
            if not consistency_passed:
                risk_level = "MEDIUM"
                recommended_action = "MANUAL_REVIEW"
            else:
                risk_level = "LOW"
                recommended_action = "NO_ACTION"

        return risk_level, recommended_action
