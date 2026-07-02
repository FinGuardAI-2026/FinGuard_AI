"""
ml_pipeline/run_risk_engine.py
──────────────────────────────
Demonstrates the Risk Engine on representative sample transactions
and compiles a detailed risk_engine_report.md documentation file.
"""
import sys
import pickle
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from ml_pipeline.risk_engine.engine import RiskEngine
from ml_pipeline.risk_engine.rules import HIGH_RISK_COUNTRIES, HIGH_RISK_MERCHANT_CATEGORIES
from ml_pipeline.utils.logger import get_logger
from ml_pipeline.utils.file_utils import save_json

logger = get_logger("run_risk_engine")


# ── Sample Transaction Profiles ───────────────────────────────────────────────
SAMPLE_TRANSACTIONS: List[Dict[str, Any]] = [
    {
        "transaction_id": "DEMO-0001",
        "amount": 150.00,
        "currency": "USD",
        "country": "USA",
        "merchant_category": "GROCERY",
        "device_id": "DEV-a1b2c3",
        "is_new_device": False,
        "tx_count_in_window": 1,
        "ip_country": "USA",
        "_label": "Low Risk (Baseline Genuine)",
    },
    {
        "transaction_id": "DEMO-0002",
        "amount": 8_500.00,
        "currency": "USD",
        "country": "USA",
        "merchant_category": "ELECTRONICS",
        "device_id": "DEV-xyz999",
        "is_new_device": True,
        "tx_count_in_window": 1,
        "ip_country": "USA",
        "_label": "Medium Risk (High Amount + New Device)",
    },
    {
        "transaction_id": "DEMO-0003",
        "amount": 2_000.00,
        "currency": "USD",
        "country": "NG",  # Nigeria — High Risk
        "merchant_category": "CASH_ADVANCE",
        "device_id": "DEV-xx1",
        "is_new_device": False,
        "tx_count_in_window": 4,
        "ip_country": "CN",  # Mismatch
        "_label": "Critical Risk (High-Risk Country + Category + Velocity + IP Mismatch)",
    },
    {
        "transaction_id": "DEMO-0004",
        "amount": 25_000.00,
        "currency": "USD",
        "country": "RU",  # Russia — High Risk
        "merchant_category": "CRYPTOCURRENCY",
        "device_id": "DEV-crypto88",
        "is_new_device": True,
        "tx_count_in_window": 5,
        "ip_country": "UA",  # Mismatch
        "_label": "Critical Risk (Maximum Rule Stack)",
    },
]

# Representative ML fraud probabilities matched to each sample
SAMPLE_ML_PROBABILITIES = [0.03, 0.41, 0.78, 0.95]

# Simulated SHAP vectors (7-feature simulation aligned to sample complexity)
SAMPLE_SHAP_VECTORS = [
    np.array([ 0.001,  0.002, -0.010,  0.005, -0.001,  0.001,  0.000]),
    np.array([ 0.120,  0.080, -0.040,  0.100,  0.050, -0.010,  0.030]),
    np.array([ 0.250,  0.180,  0.200, -0.020,  0.150,  0.090,  0.110]),
    np.array([ 0.380,  0.290,  0.310,  0.270,  0.200,  0.150,  0.175]),
]


def compile_risk_engine_report(
    assessments: List[Dict[str, Any]],
    output_dir: Path,
) -> None:
    """Writes risk_engine_report.md documenting scoring methodology and sample outputs."""
    report_path = output_dir / "risk_engine_report.md"
    lines = []

    lines.append("# FinGuard AI – Risk Engine Technical Report")
    lines.append("")
    lines.append("This document describes the architecture and scoring methodology of the FinGuard AI Risk Engine. It combines ML model outputs, Explainable AI feature magnitudes, and domain-driven business rules into a unified, calibrated risk score.")
    lines.append("")

    # ── Scoring Formula ──
    lines.append("## 1. Scoring Architecture")
    lines.append("")
    lines.append("The Risk Engine computes a composite score across three independent data channels:")
    lines.append("")
    lines.append("| Source | Weight | Description |")
    lines.append("| :--- | :--- | :--- |")
    lines.append("| ML Fraud Probability | **60%** | Raw sigmoid output from the Champion Classifier (0.0–1.0) |")
    lines.append("| SHAP Feature Magnitude | **15%** | Sum of positive SHAP attributions, normalised to [0, 1] |")
    lines.append("| Business Rule Penalties | **25%** | Cumulative points from triggered domain rules, normalised to [0, 1] |")
    lines.append("")
    lines.append("**Formula**:")
    lines.append("```")
    lines.append("risk_score = (ML_prob × 0.60 + shap_norm × 0.15 + rule_norm × 0.25) × 100")
    lines.append("risk_score = clamp(risk_score, 0.0, 100.0)")
    lines.append("```")
    lines.append("")

    # ── Risk Bands ──
    lines.append("## 2. Risk Band Classification")
    lines.append("")
    lines.append("| Risk Level | Score Range | Action |")
    lines.append("| :--- | :--- | :--- |")
    lines.append("| 🟢 **Low** | 0 – 30 | Proceed normally |")
    lines.append("| 🟡 **Medium** | 31 – 60 | Flag for review queue |")
    lines.append("| 🟠 **High** | 61 – 85 | Hold and assign to analyst within 30 minutes |")
    lines.append("| 🔴 **Critical** | 86 – 100 | Block immediately and escalate |")
    lines.append("")

    # ── Business Rules Catalog ──
    lines.append("## 3. Business Rules Catalog")
    lines.append("")
    lines.append("| Rule ID | Rule Name | Severity | Penalty Points |")
    lines.append("| :--- | :--- | :--- | :--- |")
    lines.append("| R001 | High Transaction Amount (>$5,000) | Medium | +15 |")
    lines.append("| R002 | Critical Transaction Amount (>$20,000) | Critical | +30 |")
    lines.append("| R003 | High-Risk Country Origin | High | +20 |")
    lines.append("| R004 | High-Risk Merchant Category | High | +20 |")
    lines.append("| R005 | New or Unrecognized Device | Medium | +15 |")
    lines.append("| R006 | Rapid Transaction Velocity (≥3 in 5 min) | High | +25 |")
    lines.append("| R007 | Suspicious Round Amount (≥$100, exact) | Low | +5 |")
    lines.append("| R008 | IP-Country Location Mismatch | Critical | +25 |")
    lines.append("")

    # ── Sample Outputs ──
    lines.append("## 4. Sample Transaction Assessments")
    lines.append("")
    for a in assessments:
        lines.append(f"### {a['transaction_id']} — {a['label']}")
        lines.append("")
        lines.append(f"- **ML Fraud Probability**: `{a['fraud_probability'] * 100:.1f}%`")
        lines.append(f"- **Risk Score**: `{a['risk_score']:.2f} / 100`")
        lines.append(f"- **Risk Level**: `{a['risk_level']}`")
        lines.append(f"- **Score Breakdown**: ML `{a['score_breakdown']['ml_contribution']:.2f}` + SHAP `{a['score_breakdown']['shap_contribution']:.2f}` + Rules `{a['score_breakdown']['rule_contribution']:.2f}`")
        if a["triggered_rules"]:
            lines.append(f"- **Rules Triggered**: {', '.join([f'`{r}`' for r in a['triggered_rules']])}")
        else:
            lines.append(f"- **Rules Triggered**: None")
        lines.append(f"- **Recommendation**: _{a['investigation_recommendation']}_")
        lines.append("")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Risk Engine report written to '{report_path}'.")


def main() -> int:
    """Executes the Risk Engine demo across sample transactions."""
    logger.info("Starting Risk Engine demonstration pipeline...")

    reports_dir = Path("ml_pipeline/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    try:
        engine = RiskEngine()
        assessment_records = []

        for i, (tx, ml_prob, shap_vec) in enumerate(
            zip(SAMPLE_TRANSACTIONS, SAMPLE_ML_PROBABILITIES, SAMPLE_SHAP_VECTORS)
        ):
            label = tx.pop("_label", f"Sample {i+1}")
            assessment = engine.calculate(
                fraud_probability=ml_prob,
                transaction=tx,
                shap_values=shap_vec,
            )

            record = assessment.to_dict()
            record["transaction_id"] = tx["transaction_id"]
            record["label"] = label
            assessment_records.append(record)

            logger.info(
                f"[{tx['transaction_id']}] Score: {assessment.risk_score:.2f} | "
                f"Level: {assessment.risk_level} | Rules: {len(assessment.triggered_rules)}"
            )

        # Save JSON summaries
        save_json(assessment_records, reports_dir / "risk_engine_results.json")

        # Compile markdown report
        compile_risk_engine_report(assessment_records, reports_dir)

        logger.info("Risk Engine pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Risk Engine pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
