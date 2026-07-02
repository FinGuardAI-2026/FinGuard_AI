"""
ml_pipeline/run_gemini.py
─────────────────────────
CLI demonstration pipeline for the Gemini AI Report Generator.

Builds a high-risk FraudContext from simulated ML pipeline outputs,
generates all four report types, and compiles gemini_report.md documentation.

Usage:
    python ml_pipeline/run_gemini.py
    python ml_pipeline/run_gemini.py --api-key YOUR_KEY
"""
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from ml_pipeline.gemini.client import GeminiClient
from ml_pipeline.gemini.report_generator import FraudContext, FraudReportGenerator
from ml_pipeline.gemini.prompts import PROMPT_TEMPLATES
from ml_pipeline.utils.logger import get_logger

logger = get_logger("run_gemini")

REPORTS_DIR = Path("ml_pipeline/reports/gemini")


# ── Demo FraudContext Scenarios ────────────────────────────────────────────────

def build_demo_context() -> FraudContext:
    """
    Constructs a representative high-risk transaction context
    simulating the combined output of the full ML pipeline.
    """
    return FraudContext(
        # Transaction Metadata
        transaction_id="TX-2024-00449872",
        amount=18_450.00,
        currency="USD",
        merchant_name="GlobalCryptoExchange Ltd.",
        merchant_category="CRYPTOCURRENCY",
        payment_method="Debit Card",
        transaction_type="Transfer",
        country="NG",
        city="Lagos",
        ip_address="41.203.77.21",
        device_id="DEV-NEW-XZ99",
        browser="Chrome 124 (Mobile)",
        operating_system="Android 14",
        transaction_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),

        # ML Assessment
        prediction="FRAUD",
        fraud_probability=87.3,
        confidence_score=92.0,

        # Risk Engine Output
        risk_score=91.5,
        risk_level="Critical",
        triggered_rules=[
            "R001 — High Transaction Amount ($5K–$20K)",
            "R003 — High-Risk Country Origin (NG)",
            "R004 — High-Risk Merchant Category (CRYPTOCURRENCY)",
            "R005 — New or Unrecognized Device",
            "R006 — Rapid Transaction Velocity (4 transactions in 5 minutes)",
            "R008 — IP-Country Location Mismatch (IP: RU ≠ Country: NG)",
        ],
        investigation_recommendation=(
            "IMMEDIATE ACTION REQUIRED: Block this transaction and escalate to the "
            "Fraud Investigation Team."
        ),

        # SHAP Explanation
        shap_risk_drivers=[
            "amount (+0.38): Transaction amount significantly above customer baseline.",
            "country_risk_score (+0.29): High-risk geography detected.",
            "merchant_category_risk (+0.27): Crypto exchange category has elevated fraud rate.",
            "device_is_new (+0.21): Device has never been used for this account.",
            "tx_velocity_5min (+0.19): Four transactions detected in the rolling window.",
        ],
        shap_mitigating_factors=[
            "account_age (-0.04): Account has been open for 4+ years.",
            "avg_transaction_amount (-0.02): Previous average transaction amount is moderate.",
        ],
    )


# ── Report Documentation Compiler ─────────────────────────────────────────────

def compile_gemini_documentation(reports_dir: Path) -> None:
    """Writes gemini_report.md documenting the Gemini integration architecture."""
    doc_path = Path("ml_pipeline/reports") / "gemini_report.md"

    lines = [
        "# FinGuard AI — Gemini AI Integration Report",
        "",
        "This document describes the architecture, prompt engineering strategy, and report "
        "output format for the Gemini AI report generation module integrated into the "
        "FinGuard AI fraud detection pipeline.",
        "",
        "## 1. Architecture Overview",
        "",
        "```",
        "FraudContext (unified input)",
        "       │",
        "       ▼",
        "Prompt Renderer  ──── prompts.py (template registry)",
        "       │",
        "       ▼",
        "GeminiClient     ──── google-generativeai SDK",
        "       │              (falls back to simulation if SDK/key absent)",
        "       ▼",
        "Report Parser    ──── Standardized header + Gemini output",
        "       │",
        "       ▼",
        "File Writer      ──── Individual .md files + report_index.json",
        "```",
        "",
        "## 2. Report Types",
        "",
        "| Report | Audience | Tone | Target Length |",
        "| :--- | :--- | :--- | :--- |",
        "| Fraud Investigation Report | Fraud Investigation Team | Formal, legal | ~600 words |",
        "| Analyst Summary | Fraud Analyst | Concise, operational | ~300 words |",
        "| Executive Summary | Senior Leadership | Strategic, non-technical | ~250 words |",
        "| Customer Notification | Account Holder | Empathetic, clear | ~200 words |",
        "",
        "## 3. Prompt Engineering Design",
        "",
        "Each prompt template is implemented as a `string.Template` object in `prompts.py`.",
        "Templates use `$placeholder` syntax for runtime substitution and enforce strict "
        "section headings to ensure consistent, parseable output.",
        "",
        "### Key Design Decisions",
        "- **Temperature 0.3**: Low temperature ensures factual, consistent tone across runs.",
        "- **Audience-specific persona**: Each prompt opens with a role assignment to steer the model's voice.",
        "- **Section enforcement**: Required section headings are listed explicitly in each prompt "
        "so the output can be reliably parsed or displayed.",
        "- **Confidentiality guards**: The Customer Notification template explicitly prohibits "
        "disclosure of risk scores, ML model details, or fraud probabilities.",
        "",
        "## 4. FraudContext Fields",
        "",
        "| Field | Type | Description |",
        "| :--- | :--- | :--- |",
        "| `transaction_id` | str | Unique transaction identifier |",
        "| `amount` | float | Transaction amount |",
        "| `currency` | str | ISO currency code |",
        "| `merchant_name` | str | Merchant name |",
        "| `merchant_category` | str | Merchant category code |",
        "| `country` | str | Transaction country |",
        "| `ip_address` | str | Originating IP address |",
        "| `device_id` | str | Device fingerprint |",
        "| `prediction` | str | FRAUD or GENUINE |",
        "| `fraud_probability` | float | ML fraud probability (%) |",
        "| `risk_score` | float | Final risk score 0–100 |",
        "| `risk_level` | str | Low / Medium / High / Critical |",
        "| `triggered_rules` | List[str] | Business rules triggered |",
        "| `shap_risk_drivers` | List[str] | Top SHAP risk attributions |",
        "| `shap_mitigating_factors` | List[str] | Negative SHAP mitigating features |",
        "",
        "## 5. Generated Files",
        "",
        f"All reports are written to `{reports_dir.as_posix()}/`:",
        "",
        "| File | Description |",
        "| :--- | :--- |",
        "| `fraud_investigation_report.md` | Full formal investigation case file |",
        "| `analyst_summary.md` | Operational analyst decision brief |",
        "| `executive_summary.md` | Strategic leadership briefing note |",
        "| `customer_notification.md` | Customer-facing notification message |",
        "| `report_index.json` | Machine-readable metadata index of all generated reports |",
        "",
        "## 6. Environment Configuration",
        "",
        "```bash",
        "# Set your Gemini API key before running",
        "set GEMINI_API_KEY=your_api_key_here    # Windows",
        "export GEMINI_API_KEY=your_api_key_here  # macOS/Linux",
        "",
        "# Run the pipeline",
        "python ml_pipeline/run_gemini.py",
        "```",
        "",
        "If `GEMINI_API_KEY` is not set, the module operates in **offline simulation mode**, "
        "returning deterministic structured placeholder reports suitable for testing and development.",
    ]

    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Gemini documentation written to '{doc_path}'.")


# ── CLI Entry Point ────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="FinGuard AI — Gemini Report Generation Pipeline",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Google Gemini API key (overrides GEMINI_API_KEY env var).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-1.5-flash",
        help="Gemini model name to use (default: gemini-1.5-flash).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    logger.info("Starting FinGuard AI Gemini Report Generation Pipeline...")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Build demo context
    context = build_demo_context()
    logger.info(f"FraudContext built for transaction '{context.transaction_id}'.")

    # 2. Initialise Gemini client
    client = GeminiClient(api_key=args.api_key, model_name=args.model)
    mode = "LIVE (Gemini API)" if client.active else "OFFLINE (Simulation)"
    logger.info(f"Client mode: {mode}")

    # 3. Generate all four reports
    generator = FraudReportGenerator(output_dir=REPORTS_DIR, gemini_client=client)
    results = generator.generate_all(context)

    # 4. Print summary table
    print("\n" + "=" * 70)
    print(f"  FinGuard AI Gemini Report Generation - {mode}")
    print("=" * 70)
    print(f"  Transaction : {context.transaction_id}")
    print(f"  Risk Level  : {context.risk_level}")
    print(f"  Risk Score  : {context.risk_score:.2f} / 100")
    print(f"  Prediction  : {context.prediction}")
    print("=" * 70)
    for r in results:
        print(f"  [OK] [{r.report_type:<26}] -> {Path(r.file_path).name} ({r.char_count:,} chars)")
    print("=" * 70)

    # 5. Compile documentation
    compile_gemini_documentation(REPORTS_DIR)

    print(f"\n  Documentation -> ml_pipeline/reports/gemini_report.md")
    print(f"  Reports Dir  -> {REPORTS_DIR.as_posix()}/")
    print()
    logger.info("Gemini pipeline completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
