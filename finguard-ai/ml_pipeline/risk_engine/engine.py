"""
ml_pipeline/risk_engine/engine.py
─────────────────────────────────
Combines the ML fraud probability, SHAP attribution magnitude,
and business rule penalty points into a calibrated 0–100 Risk Score.
Classifies outcomes into Low / Medium / High / Critical bands.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np

from ml_pipeline.risk_engine.rules import BusinessRuleEvaluator, RulesResult
from ml_pipeline.config.constants import (
    RISK_LOW_MAX,
    RISK_MEDIUM_MAX,
    RISK_HIGH_MAX,
)
from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)

# ── Score Weighting Coefficients ─────────────────────────────────────────────
# These weights control how much each input source influences the final score.
# They must sum to 1.0.
ML_WEIGHT   = 0.60   # 60%: primary ML model fraud probability
SHAP_WEIGHT = 0.15   # 15%: aggregate SHAP feature attribution magnitude
RULE_WEIGHT = 0.25   # 25%: business rule penalty contribution


@dataclass
class RiskAssessment:
    """
    Fully structured output of the Risk Engine for a single transaction.
    """
    # ── Score Components ──────────────────────────────────────────────────
    fraud_probability: float          # Raw ML output (0.0–1.0)
    shap_magnitude: float             # Normalized aggregate |SHAP| (0.0–1.0)
    rule_penalty: float               # Normalized business rule penalty (0.0–1.0)

    # ── Composite Score ───────────────────────────────────────────────────
    risk_score: float                 # Final weighted score (0.0–100.0)
    risk_level: str                   # "Low" | "Medium" | "High" | "Critical"

    # ── Audit Trail ───────────────────────────────────────────────────────
    triggered_rules: List[str] = field(default_factory=list)
    rule_details: List[Any] = field(default_factory=list)
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    investigation_recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the assessment to a JSON-compatible dictionary."""
        return {
            "fraud_probability": self.fraud_probability,
            "shap_magnitude": self.shap_magnitude,
            "rule_penalty": self.rule_penalty,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "triggered_rules": self.triggered_rules,
            "score_breakdown": self.score_breakdown,
            "investigation_recommendation": self.investigation_recommendation,
        }


class RiskEngine:
    """
    Fuses ML probability, SHAP amplification, and business rule penalties
    into a calibrated 0–100 risk score with labelled risk band classification.

    Scoring Formula:
        raw_score = (ML_prob × ML_WEIGHT + shap_norm × SHAP_WEIGHT + rule_norm × RULE_WEIGHT) × 100
        risk_score = clamp(raw_score, 0.0, 100.0)

    Risk Bands:
        Low      : 0  – 30
        Medium   : 31 – 60
        High     : 61 – 85
        Critical : 86 – 100
    """

    def __init__(self) -> None:
        self.rule_evaluator = BusinessRuleEvaluator()

    def calculate(
        self,
        fraud_probability: float,
        transaction: Dict[str, Any],
        shap_values: Optional[np.ndarray] = None,
    ) -> RiskAssessment:
        """
        Compute a full risk assessment for a transaction.

        Args:
            fraud_probability: Sigmoid output from the ML classifier (0.0–1.0).
            transaction:       Raw transaction metadata dictionary.
            shap_values:       1-D SHAP vector for this transaction (optional).

        Returns:
            A fully populated RiskAssessment object.
        """
        # ── 1. ML Component ───────────────────────────────────────────────
        ml_prob = float(np.clip(fraud_probability, 0.0, 1.0))
        ml_contribution = ml_prob * ML_WEIGHT * 100

        # ── 2. SHAP Component ─────────────────────────────────────────────
        # Use sum of positive SHAP values as a magnitude proxy
        shap_norm = 0.0
        if shap_values is not None and len(shap_values) > 0:
            pos_shap_sum = float(np.sum(np.maximum(shap_values, 0.0)))
            # Normalise to [0, 1] by clamping against a reasonable practical ceiling
            shap_norm = float(np.clip(pos_shap_sum / 2.0, 0.0, 1.0))
        shap_contribution = shap_norm * SHAP_WEIGHT * 100

        # ── 3. Business Rules Component ───────────────────────────────────
        rules_result: RulesResult = self.rule_evaluator.evaluate(transaction)
        # Maximum possible rule penalty to normalise against
        MAX_PENALTY = 140.0  # Sum of all rule penalties if every rule triggered
        rule_norm = float(np.clip(rules_result.total_rule_penalty / MAX_PENALTY, 0.0, 1.0))
        rule_contribution = rule_norm * RULE_WEIGHT * 100

        # ── 4. Final Composite Score ──────────────────────────────────────
        raw_score = ml_contribution + shap_contribution + rule_contribution
        risk_score = float(np.clip(raw_score, 0.0, 100.0))
        risk_level = self._classify_risk_level(risk_score)

        # ── 5. Investigation Recommendation ──────────────────────────────
        recommendation = self._build_recommendation(risk_level, rules_result)

        assessment = RiskAssessment(
            fraud_probability=ml_prob,
            shap_magnitude=shap_norm,
            rule_penalty=rule_norm,
            risk_score=risk_score,
            risk_level=risk_level,
            triggered_rules=rules_result.rule_summary,
            rule_details=[
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "description": r.description,
                    "severity": r.severity,
                    "penalty": r.penalty_points,
                }
                for r in rules_result.triggered_rules
            ],
            score_breakdown={
                "ml_contribution": round(ml_contribution, 4),
                "shap_contribution": round(shap_contribution, 4),
                "rule_contribution": round(rule_contribution, 4),
                "total": round(risk_score, 4),
            },
            investigation_recommendation=recommendation,
        )

        logger.info(
            f"Risk assessment complete. Score: {risk_score:.2f} | Level: {risk_level} | "
            f"Rules triggered: {len(rules_result.triggered_rules)} | "
            f"ML prob: {ml_prob:.4f}"
        )

        return assessment

    def _classify_risk_level(self, risk_score: float) -> str:
        """Maps a numeric score to a labelled risk band."""
        if risk_score <= RISK_LOW_MAX:
            return "Low"
        elif risk_score <= RISK_MEDIUM_MAX:
            return "Medium"
        elif risk_score <= RISK_HIGH_MAX:
            return "High"
        else:
            return "Critical"

    def _build_recommendation(self, risk_level: str, rules_result: RulesResult) -> str:
        """Generates an action recommendation based on risk level and triggered rules."""
        if risk_level == "Critical":
            return (
                "IMMEDIATE ACTION REQUIRED: Block this transaction and escalate to the Fraud Investigation Team. "
                f"Triggered rules: {', '.join(rules_result.rule_summary) or 'N/A'}."
            )
        elif risk_level == "High":
            return (
                "HIGH ALERT: Place transaction on hold and initiate automated challenger challenge. "
                "Assign to a Fraud Analyst for manual review within 30 minutes."
            )
        elif risk_level == "Medium":
            return (
                "CAUTION: Flag transaction for review queue. Monitor account for additional suspicious activity. "
                "No immediate block required."
            )
        else:
            return "CLEAR: Transaction falls within normal risk parameters. Proceed with processing."
