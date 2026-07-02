"""
ml_pipeline/gemini/report_generator.py
────────────────────────────────────────
Orchestrates all four Gemini report types from a single FraudContext object.

Flow:
  FraudContext → Prompt Renderer → GeminiClient → Report Parser → File Writer

Each report is:
  - Generated independently from its own prompt template.
  - Saved as an individual Markdown file.
  - Tracked in a shared metadata JSON index.
"""
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from ml_pipeline.gemini.client import GeminiClient
from ml_pipeline.gemini.prompts import PROMPT_TEMPLATES
from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)


# ── Fraud Context ─────────────────────────────────────────────────────────────

@dataclass
class FraudContext:
    """
    Unified input container for the Gemini Report Generator.
    Aggregates the transaction metadata, ML assessment, SHAP explanation,
    and Risk Engine output into a single serializable object.
    """
    # Transaction metadata
    transaction_id: str
    amount: float
    currency: str = "USD"
    merchant_name: str = "Unknown Merchant"
    merchant_category: str = "UNKNOWN"
    payment_method: str = "Credit Card"
    transaction_type: str = "Purchase"
    country: str = "USA"
    city: str = "Unknown"
    ip_address: str = "0.0.0.0"
    device_id: str = "Unknown"
    browser: str = "Unknown"
    operating_system: str = "Unknown"
    transaction_time: str = ""

    # ML assessment
    prediction: str = "GENUINE"          # "FRAUD" | "GENUINE"
    fraud_probability: float = 0.0       # 0.0 – 100.0 (already ×100)
    confidence_score: float = 100.0

    # Risk engine output
    risk_score: float = 0.0              # 0.0 – 100.0
    risk_level: str = "Low"
    triggered_rules: List[str] = field(default_factory=list)
    investigation_recommendation: str = ""

    # SHAP output
    shap_risk_drivers: List[str] = field(default_factory=list)
    shap_mitigating_factors: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.transaction_time:
            self.transaction_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


# ── Report Result ─────────────────────────────────────────────────────────────

@dataclass
class ReportResult:
    """Stores the generated text and file path for a single report."""
    report_type: str
    report_text: str
    file_path: str
    generated_at: str
    char_count: int
    model_used: str


# ── Prompt Renderer ───────────────────────────────────────────────────────────

def _render_prompt(report_type: str, context: FraudContext) -> str:
    """
    Substitutes all named placeholders in a prompt template
    using fields from a FraudContext instance.

    Args:
        report_type: Key into PROMPT_TEMPLATES registry.
        context:     Populated FraudContext object.

    Returns:
        Fully rendered prompt string ready for Gemini dispatch.
    """
    template = PROMPT_TEMPLATES.get(report_type)
    if template is None:
        raise ValueError(f"Unknown report type '{report_type}'. Available: {list(PROMPT_TEMPLATES.keys())}")

    # Format list fields into human-readable bullet lists
    triggered_rules_str = (
        "\n".join(f"  - {r}" for r in context.triggered_rules)
        if context.triggered_rules else "  None"
    )
    shap_risk_str = (
        "\n".join(f"  - {d}" for d in context.shap_risk_drivers)
        if context.shap_risk_drivers else "  None detected"
    )
    shap_mitigating_str = (
        "\n".join(f"  - {m}" for m in context.shap_mitigating_factors)
        if context.shap_mitigating_factors else "  None detected"
    )

    return template.substitute(
        transaction_id=context.transaction_id,
        amount=f"{context.amount:,.2f}",
        currency=context.currency,
        merchant_name=context.merchant_name,
        merchant_category=context.merchant_category,
        payment_method=context.payment_method,
        transaction_type=context.transaction_type,
        country=context.country,
        city=context.city,
        ip_address=context.ip_address,
        device_id=context.device_id,
        browser=context.browser,
        operating_system=context.operating_system,
        transaction_time=context.transaction_time,
        prediction=context.prediction,
        fraud_probability=f"{context.fraud_probability:.1f}",
        confidence_score=f"{context.confidence_score:.1f}",
        risk_score=f"{context.risk_score:.2f}",
        risk_level=context.risk_level,
        triggered_rules=triggered_rules_str,
        shap_risk_drivers=shap_risk_str,
        shap_mitigating_factors=shap_mitigating_str,
        investigation_recommendation=context.investigation_recommendation,
    )


# ── Report Generator ──────────────────────────────────────────────────────────

class FraudReportGenerator:
    """
    Generates all four Gemini AI-powered reports from a FraudContext.

    Report Types:
      - fraud_investigation    : Full formal investigation case file
      - analyst_summary        : Concise operational decision brief
      - executive_summary      : High-level strategic briefing note
      - customer_notification  : Empathetic customer-facing message
    """

    REPORT_FILENAMES = {
        "fraud_investigation":   "fraud_investigation_report.md",
        "analyst_summary":       "analyst_summary.md",
        "executive_summary":     "executive_summary.md",
        "customer_notification": "customer_notification.md",
    }

    def __init__(
        self,
        output_dir: Path,
        gemini_client: Optional[GeminiClient] = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = gemini_client or GeminiClient()

    def generate_all(self, context: FraudContext) -> List[ReportResult]:
        """
        Generates all four report types for a given FraudContext.

        Args:
            context: Fully populated FraudContext object.

        Returns:
            List of ReportResult objects for each generated report.
        """
        logger.info(f"Generating all 4 Gemini reports for transaction '{context.transaction_id}'...")
        results: List[ReportResult] = []

        for report_type in self.REPORT_FILENAMES:
            result = self.generate_single(context, report_type)
            results.append(result)

        # Save metadata index
        self._save_metadata_index(context, results)

        logger.info(f"All 4 reports generated for transaction '{context.transaction_id}'.")
        return results

    def generate_single(self, context: FraudContext, report_type: str) -> ReportResult:
        """
        Renders the prompt, calls Gemini, and saves a single report to disk.

        Args:
            context:     Populated FraudContext object.
            report_type: One of the keys in REPORT_FILENAMES.

        Returns:
            A populated ReportResult object.
        """
        # 1. Render the prompt
        prompt = _render_prompt(report_type, context)

        # 2. Call Gemini (or fallback)
        report_text = self.client.generate(prompt=prompt, report_type=report_type)

        # 3. Assemble the final file with a standardized header
        header = self._build_header(context, report_type)
        full_document = header + "\n\n---\n\n" + report_text

        # 4. Save to disk
        filename = self.REPORT_FILENAMES[report_type]
        file_path = self.output_dir / filename
        file_path.write_text(full_document, encoding="utf-8")

        generated_at = datetime.now(timezone.utc).isoformat()
        model_label = self.client.model_name if self.client.active else "offline-simulation"

        logger.info(f"Report '{report_type}' saved to '{file_path}'.")

        return ReportResult(
            report_type=report_type,
            report_text=full_document,
            file_path=str(file_path),
            generated_at=generated_at,
            char_count=len(full_document),
            model_used=model_label,
        )

    def _build_header(self, context: FraudContext, report_type: str) -> str:
        """Builds a standardized metadata header block for each report file."""
        type_labels = {
            "fraud_investigation":   "Fraud Investigation Report",
            "analyst_summary":       "Analyst Summary",
            "executive_summary":     "Executive Summary",
            "customer_notification": "Customer Notification",
        }
        label = type_labels.get(report_type, report_type.replace("_", " ").title())

        return (
            f"# FinGuard AI — {label}\n\n"
            f"| Field | Value |\n"
            f"| :--- | :--- |\n"
            f"| **Transaction ID** | `{context.transaction_id}` |\n"
            f"| **Generated At** | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} |\n"
            f"| **Risk Level** | {context.risk_level} |\n"
            f"| **Risk Score** | {context.risk_score:.2f} / 100 |\n"
            f"| **Fraud Probability** | {context.fraud_probability:.1f}% |\n"
            f"| **Prediction** | {context.prediction} |\n"
        )

    def _save_metadata_index(
        self,
        context: FraudContext,
        results: List[ReportResult],
    ) -> None:
        """Saves a JSON metadata index of all generated reports for this transaction."""
        index_path = self.output_dir / "report_index.json"

        # Load existing index if present
        existing: List[Dict[str, Any]] = []
        if index_path.exists():
            try:
                existing = json.loads(index_path.read_text(encoding="utf-8"))
            except Exception:
                existing = []

        record = {
            "transaction_id": context.transaction_id,
            "risk_level": context.risk_level,
            "risk_score": context.risk_score,
            "fraud_probability": context.fraud_probability,
            "prediction": context.prediction,
            "reports": [
                {
                    "type": r.report_type,
                    "file": Path(r.file_path).name,
                    "generated_at": r.generated_at,
                    "char_count": r.char_count,
                    "model": r.model_used,
                }
                for r in results
            ],
        }

        existing.append(record)
        index_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        logger.info(f"Report metadata index updated at '{index_path}'.")
