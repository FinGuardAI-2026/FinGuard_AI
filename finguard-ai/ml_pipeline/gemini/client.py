"""
ml_pipeline/gemini/client.py
─────────────────────────────
Thin, reusable wrapper around the Google Gemini Generative AI SDK.
Implements structured prompt dispatch, response parsing, and error handling.
Falls back to deterministic template-based responses if the SDK or API key is absent.
"""
# import os
from pathlib import Path
from typing import Optional
# from dotenv import load_dotenv
# PROJECT_ROOT = Path(__file__).resolve().parents[2]
# print("PROJECT_ROOT =", PROJECT_ROOT)
# print("ENV FILE =", PROJECT_ROOT / ".env.development")
# load_dotenv(PROJECT_ROOT / ".env.development", override=True)
from ml_pipeline.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)
# print("CLIENT.PY LOADED")

# Try loading Google Generative AI SDK
HAS_GEMINI = False
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    logger.warning("google-generativeai package not detected. Gemini will operate in offline simulation mode.")


class GeminiClient:
    """
    Manages the connection to Google Gemini and dispatches structured prompts.

    API Key Resolution Order:
      1. Explicit key passed to constructor.
      2. GEMINI_API_KEY environment variable.
      3. Offline simulation mode (graceful fallback).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
    ) -> None:
        self.model_name = model_name
        self.model = None
        self.active = False

        # print("ENV KEY =", os.environ.get("GEMINI_API_KEY"))
        # resolved_key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        resolved_key = api_key or settings.GEMINI_API_KEY

        if HAS_GEMINI and resolved_key:
            try:
                genai.configure(api_key=resolved_key)
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config={
                        "temperature": 0.3,     # Low temperature for consistent, factual tone
                        "top_p": 0.9,
                        "max_output_tokens": 2048,
                    },
                    safety_settings={
                        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                    },
                )
                self.active = True
                logger.info(f"Gemini client initialized with model '{self.model_name}'.")
            except Exception as e:
                logger.warning(f"Gemini initialization failed: {e}. Switching to offline mode.")
        else:
            if not HAS_GEMINI:
                logger.warning("google-generativeai SDK missing. Using offline simulation mode.")
            elif not resolved_key:
                logger.warning("GEMINI_API_KEY not set. Using offline simulation mode.")

    def generate(self, prompt: str, report_type: str = "unknown") -> str:
        """
        Sends a prompt to Gemini and returns the generated text response.

        Args:
            prompt:      Fully-rendered prompt string with all placeholders resolved.
            report_type: Label used for logging and fallback identification.

        Returns:
            Generated report text as a plain string.
        """
        if self.active and self.model:
            try:
                logger.info(f"Dispatching '{report_type}' prompt to Gemini ({self.model_name})...")
                response = self.model.generate_content(prompt)
                text = response.text.strip()
                logger.info(f"Gemini response received for '{report_type}'. Length: {len(text)} chars.")
                return text
            except Exception as e:
                logger.error(f"Gemini API call failed for '{report_type}': {e}. Using fallback response.")

        # Offline/fallback mode: return a structured placeholder report
        return self._generate_fallback_response(report_type)

    def _generate_fallback_response(self, report_type: str) -> str:
        """Generates a deterministic placeholder report for offline/demo modes."""
        fallback_bodies = {
            "fraud_investigation": (
                "## 1. Executive Case Summary\n"
                "This transaction has been flagged for investigation based on elevated fraud "
                "probability scores and multiple triggered business rule violations.\n\n"
                "## 2. Transaction Profile Analysis\n"
                "The transaction exhibits characteristics inconsistent with the account holder's "
                "established behavioral baseline, including unusual geographic patterns and device anomalies.\n\n"
                "## 3. Fraud Indicators Identified\n"
                "- Elevated ML fraud probability exceeding the 70% threshold.\n"
                "- Transaction originated from a high-risk country code.\n"
                "- New device fingerprint detected for this account.\n\n"
                "## 4. Risk Assessment Rationale\n"
                "The composite risk score was computed using a weighted combination of machine learning "
                "probability, feature attribution magnitudes, and business rule penalties.\n\n"
                "## 5. Evidence Evaluation\n"
                "Available telemetry supports the classification of this transaction as high-risk.\n\n"
                "## 6. Conclusion and Recommended Action\n"
                "The transaction is recommended for immediate hold and escalation to the Fraud Investigation Team.\n\n"
                "## 7. Case Disposition\n"
                "Status: Under Investigation — Pending manual review completion."
            ),
            "analyst_summary": (
                "## Quick Decision Guidance\n"
                "HOLD — Place transaction on hold and initiate challenger challenge.\n\n"
                "## Key Red Flags\n"
                "- ML fraud probability exceeds risk threshold.\n"
                "- High-risk country origin detected.\n"
                "- Rapid transaction velocity in past 5 minutes.\n\n"
                "## Mitigating Factors\n"
                "- Merchant category is not classified as highest-risk tier.\n\n"
                "## Suggested Next Steps\n"
                "1. Attempt customer callback verification.\n"
                "2. Initiate temporary account lock.\n"
                "3. Escalate case to senior fraud analyst if unresolved within 30 minutes."
            ),
            "executive_summary": (
                "## Incident Summary\n"
                "An automated fraud detection alert was raised for a transaction requiring executive awareness "
                "due to its elevated risk classification.\n\n"
                "## Business Impact Assessment\n"
                "The potential financial exposure associated with this incident has been assessed and the "
                "transaction has been placed on hold pending investigation.\n\n"
                "## Key Risk Indicators\n"
                "Multiple risk signals were detected including geographical anomalies, device irregularities, "
                "and pattern inconsistencies.\n\n"
                "## Immediate Action Taken\n"
                "The transaction has been flagged and placed under automated hold. The Fraud Investigation "
                "Team has been notified.\n\n"
                "## Escalation Recommendation\n"
                "Recommend escalation to the Risk Committee for review if manual investigation confirms fraud."
            ),
            "customer_notification": (
                "## Subject Line\n"
                "Important: Unusual Activity Detected on Your Account\n\n"
                "## Opening Greeting\n"
                "Dear Valued Customer,\n\n"
                "## Transaction Alert Body\n"
                "We have detected unusual activity on your account and have temporarily placed a transaction "
                "on hold as a precautionary measure to protect your financial security.\n\n"
                "## Verification Request\n"
                "If you authorized this transaction, please contact us immediately using the number on the "
                "back of your card or log in to your account portal to confirm the activity.\n\n"
                "## Security Reassurance\n"
                "Your account security is our highest priority. No action is required from you unless you "
                "believe this transaction was unauthorized.\n\n"
                "## Contact Details Placeholder\n"
                "Contact us 24/7 at: [BANK_PHONE_NUMBER] | [BANK_EMAIL] | [BANK_PORTAL_URL]"
            ),
        }

        return fallback_bodies.get(
            report_type,
            f"[Offline Mode] Report type '{report_type}' — Gemini API not available. "
            "Please configure GEMINI_API_KEY to enable live report generation."
        )
