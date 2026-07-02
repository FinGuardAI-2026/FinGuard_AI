"""
ml_pipeline/tests/test_risk_engine.py
──────────────────────────────────────
Unit tests validating the BusinessRuleEvaluator and RiskEngine scoring pipeline.
"""
import pytest
import numpy as np

from ml_pipeline.risk_engine.rules import BusinessRuleEvaluator
from ml_pipeline.risk_engine.engine import RiskEngine


# ── Rule Evaluator Tests ──────────────────────────────────────────────────────

class TestBusinessRuleEvaluator:
    def _eval(self, **kwargs):
        evaluator = BusinessRuleEvaluator()
        return evaluator.evaluate(kwargs)

    def test_clean_transaction_triggers_no_rules(self):
        """A low-risk genuine transaction should not trigger any business rules."""
        result = self._eval(
            amount=45.0,
            currency="USD",
            country="USA",
            merchant_category="GROCERY",
            device_id="DEV-abc123",
            is_new_device=False,
            tx_count_in_window=1,
            ip_country="USA",
        )
        assert len(result.triggered_rules) == 0
        assert result.total_rule_penalty == 0.0

    def test_high_amount_triggers_r001(self):
        """Transactions between $5,000 and $20,000 must trigger rule R001."""
        result = self._eval(amount=7500.0, country="USA", merchant_category="ELECTRONICS",
                            device_id="DEV-abc", is_new_device=False, tx_count_in_window=1,
                            ip_country="USA")
        rule_ids = [r.rule_id for r in result.triggered_rules]
        assert "R001" in rule_ids

    def test_critical_amount_triggers_r002(self):
        """Transactions at or above $20,000 must trigger rule R002 (not R001)."""
        result = self._eval(amount=25000.0, country="USA", merchant_category="ELECTRONICS",
                            device_id="DEV-abc", is_new_device=False, tx_count_in_window=1,
                            ip_country="USA")
        rule_ids = [r.rule_id for r in result.triggered_rules]
        assert "R002" in rule_ids
        assert "R001" not in rule_ids

    def test_high_risk_country_triggers_r003(self):
        """Transactions from high-risk country codes must trigger rule R003."""
        result = self._eval(amount=100.0, country="NG", merchant_category="GROCERY",
                            device_id="DEV-abc", is_new_device=False, tx_count_in_window=1,
                            ip_country="NG")
        rule_ids = [r.rule_id for r in result.triggered_rules]
        assert "R003" in rule_ids

    def test_ip_country_mismatch_triggers_r008(self):
        """Transactions with mismatched IP and declared country must trigger rule R008."""
        result = self._eval(amount=100.0, country="USA", merchant_category="GROCERY",
                            device_id="DEV-abc", is_new_device=False, tx_count_in_window=1,
                            ip_country="RU")
        rule_ids = [r.rule_id for r in result.triggered_rules]
        assert "R008" in rule_ids

    def test_rapid_transactions_triggers_r006(self):
        """3+ transactions in the velocity window must trigger rule R006."""
        result = self._eval(amount=50.0, country="USA", merchant_category="RETAIL",
                            device_id="DEV-abc", is_new_device=False, tx_count_in_window=4,
                            ip_country="USA")
        rule_ids = [r.rule_id for r in result.triggered_rules]
        assert "R006" in rule_ids


# ── Risk Engine Score Tests ───────────────────────────────────────────────────

class TestRiskEngine:
    def test_low_risk_genuine_transaction(self):
        """Genuine transaction with low ML probability and no rules should score Low."""
        engine = RiskEngine()
        tx = dict(amount=50.0, country="USA", merchant_category="GROCERY",
                  device_id="DEV-abc", is_new_device=False, tx_count_in_window=1, ip_country="USA")
        result = engine.calculate(fraud_probability=0.02, transaction=tx, shap_values=np.zeros(3))
        assert result.risk_level == "Low"
        assert result.risk_score <= 30.0

    def test_critical_risk_transaction(self):
        """High-probability fraud with stacked business rules should score Critical."""
        engine = RiskEngine()
        tx = dict(
            amount=25000.0,
            country="NG",
            merchant_category="CRYPTOCURRENCY",
            device_id="x",
            is_new_device=True,
            tx_count_in_window=5,
            ip_country="RU",
        )
        shap = np.array([0.40, 0.35, 0.30, 0.25, 0.20])
        result = engine.calculate(fraud_probability=0.95, transaction=tx, shap_values=shap)
        assert result.risk_level == "Critical"
        assert result.risk_score > 85.0

    def test_score_is_clamped_between_0_and_100(self):
        """Risk score must always remain within [0, 100] regardless of inputs."""
        engine = RiskEngine()
        tx = dict(amount=0.0, country="USA", merchant_category="GROCERY",
                  device_id="DEV-abc", is_new_device=False, tx_count_in_window=0, ip_country="USA")
        # Extreme inputs
        result_min = engine.calculate(fraud_probability=0.0, transaction=tx, shap_values=np.zeros(5))
        result_max = engine.calculate(fraud_probability=1.0, transaction=tx, shap_values=np.ones(5) * 10)
        assert 0.0 <= result_min.risk_score <= 100.0
        assert 0.0 <= result_max.risk_score <= 100.0

    def test_score_breakdown_keys(self):
        """RiskAssessment score_breakdown must contain all three source contributions."""
        engine = RiskEngine()
        tx = dict(amount=100.0, country="USA", merchant_category="RETAIL",
                  device_id="DEV-abc", is_new_device=False, tx_count_in_window=1, ip_country="USA")
        result = engine.calculate(fraud_probability=0.5, transaction=tx)
        assert "ml_contribution" in result.score_breakdown
        assert "shap_contribution" in result.score_breakdown
        assert "rule_contribution" in result.score_breakdown
        assert "total" in result.score_breakdown
