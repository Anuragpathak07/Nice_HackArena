import os
from typing import List, Optional
from groq import Groq
from app.models import Applicant, ScreeningResult, IDRecord

class LLMService:
    @staticmethod
    def generate_case_summary(
        applicant: Applicant,
        screening_results: List[ScreeningResult],
        consistency_passed: bool
    ) -> str:
        """
        Generates a structured compliance officer case summary using Groq (llama-3.3-70b-versatile).
        If GROQ_API_KEY is not configured or an error occurs, falls back to a deterministic summary.
        """
        groq_api_key = os.getenv("GROQ_API_KEY")

        if groq_api_key:
            try:
                client = Groq(api_key=groq_api_key)
                
                # Format deterministic signals for Groq LLM
                match_details = "\n".join([
                    f"- Watchlist Match Score: {r.match_score}%, Risk: {r.risk_level}, Reason: {r.reason}"
                    for r in screening_results
                ]) if screening_results else "No Watchlist Matches Found."

                system_prompt = (
                    "You are a senior banking AML & KYC Compliance Analyst AI. "
                    "Analyze the provided factual applicant signals and generate a concise 2-paragraph "
                    "executive summary for a human compliance officer. Be objective, explain risk factors, "
                    "and provide clear reasoning without making unsupported claims."
                )

                user_prompt = f"""
                Applicant Name: {applicant.full_name}
                Country: {applicant.country}
                DOB: {applicant.dob}
                Annual Income: ${applicant.annual_income:,.2f}
                Current Application Status: {applicant.status}
                Calculated Risk Level: {applicant.risk_level}
                Document Consistency Check Passed: {consistency_passed}

                Watchlist Matches Details:
                {match_details}

                Provide a 2-paragraph executive compliance summary emphasizing why review is needed or why the profile is low risk.
                """

                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.2,
                    max_tokens=350,
                )

                return chat_completion.choices[0].message.content.strip()

            except Exception as e:
                print(f"[LLMService] Groq API call failed or unconfigured, using deterministic fallback: {e}")

        # Fallback Deterministic Synthesis Engine (Ensures 100% reliability without LLM dependency)
        match_count = len(screening_results)
        if match_count == 0:
            summary = f"Applicant {applicant.full_name} ({applicant.country}) presented no watchlist matches during automated screening. "
            if consistency_passed:
                summary += "Application demographics fully align with provided ID records. Standard low-risk profile."
            else:
                summary += "However, ID consistency check flagged minor discrepancies that require manual document verification."
            return summary

        highest_match = max(screening_results, key=lambda r: r.match_score)
        summary = (
            f"EXECUTIVE SUMMARY FOR COMPLIANCE OFFICER (Groq Fallback Engine):\n\n"
            f"Applicant {applicant.full_name} has been flagged with {applicant.risk_level} risk due to {match_count} potential watchlist match(es). "
            f"The primary match signal indicates a {highest_match.match_score:.1f}% similarity score ({highest_match.match_type}) against watchlist entry.\n\n"
            f"Key Audit Findings:\n"
            f"- Watchlist Detail: {highest_match.reason}\n"
            f"- Document Verification: {'PASSED' if consistency_passed else 'DISCREPANCY DETECTED'}\n"
            f"- Recommended Action: Compliance officer review required before approving onboarding status."
        )
        return summary
