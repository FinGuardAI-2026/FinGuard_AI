"""
ml_pipeline/risk_engine/rules.py
─────────────────────────────────
Domain-driven business rule evaluator for fraud detection.
Each rule is independently scored and tagged, allowing granular audit trails.
Rules are deliberately separate from ML logic to ensure interpretability.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── High-Risk Reference Sets ──────────────────────────────────────────────────

HIGH_RISK_COUNTRIES = {
    "NG", "GH", "RO", "UA", "RU", "KP", "IR", "VE",
    "SY", "LY", "IQ", "MM", "SD", "CF", "SS",
}

HIGH_RISK_MERCHANT_CATEGORIES = {
    "GAMBLING", "CRYPTOCURRENCY", "CASH_ADVANCE",
    "ADULT_ENTERTAINMENT", "WIRE_TRANSFER", "MONEY_ORDER",
    "PAWN_SHOP", "PAYDAY_LOAN",
}

# Thresholds
HIGH_AMOUNT_USD = 5_000.0        # Transactions above this are considered high value
CRITICAL_AMOUNT_USD = 20_000.0   # Transactions above this are critical
RAPID_TX_WINDOW_SECONDS = 300    # 5-minute window for velocity checks
RAPID_TX_COUNT = 3               # More than 3 transactions in window = suspicious


@dataclass
class RuleTrigger:
    """Represents a single triggered business rule."""
    rule_id: str
    rule_name: str
    description: str
    severity: str       # "low", "medium", "high", "critical"
    penalty_points: float


@dataclass
class RulesResult:
    """Aggregated output from the business rules evaluation pass."""
    triggered_rules: List[RuleTrigger] = field(default_factory=list)
    total_rule_penalty: float = 0.0
    rule_summary: List[str] = field(default_factory=list)


class BusinessRuleEvaluator:
    """
    Evaluates a transaction against domain-defined fraud indicator rules.
    
    Each rule is self-contained and contributes a fixed penalty score (0–100 scale)
    to the overall risk calculation. Rules are additive.
    """

    def evaluate(self, transaction: Dict[str, Any]) -> RulesResult:
        """
        Applies all business rules to a transaction metadata dictionary.

        Args:
            transaction: Dict containing raw transaction fields.

        Returns:
            RulesResult with triggered rules and cumulative penalty points.
        """
        result = RulesResult()

        self._check_high_amount(transaction, result)
        self._check_critical_amount(transaction, result)
        self._check_foreign_high_risk_country(transaction, result)
        self._check_high_risk_merchant_category(transaction, result)
        self._check_new_or_unknown_device(transaction, result)
        self._check_rapid_transactions(transaction, result)
        self._check_round_amount(transaction, result)
        self._check_ip_country_mismatch(transaction, result)

        result.total_rule_penalty = sum(r.penalty_points for r in result.triggered_rules)
        result.rule_summary = [r.rule_name for r in result.triggered_rules]

        return result

    # ── Individual Rules ──────────────────────────────────────────────────────

    def _check_high_amount(self, tx: Dict, result: RulesResult) -> None:
        """Flag transactions exceeding the high-value threshold."""
        amount = float(tx.get("amount", 0.0))
        if HIGH_AMOUNT_USD <= amount < CRITICAL_AMOUNT_USD:
            result.triggered_rules.append(RuleTrigger(
                rule_id="R001",
                rule_name="High Transaction Amount",
                description=f"Amount ${amount:,.2f} exceeds the high-value threshold of ${HIGH_AMOUNT_USD:,}.",
                severity="medium",
                penalty_points=15.0,
            ))

    def _check_critical_amount(self, tx: Dict, result: RulesResult) -> None:
        """Flag transactions that cross the critical amount level."""
        amount = float(tx.get("amount", 0.0))
        if amount >= CRITICAL_AMOUNT_USD:
            result.triggered_rules.append(RuleTrigger(
                rule_id="R002",
                rule_name="Critical Transaction Amount",
                description=f"Amount ${amount:,.2f} exceeds the critical threshold of ${CRITICAL_AMOUNT_USD:,}.",
                severity="critical",
                penalty_points=30.0,
            ))

    def _check_foreign_high_risk_country(self, tx: Dict, result: RulesResult) -> None:
        """Flag transactions originating from known high-risk country codes."""
        country = str(tx.get("country", "")).upper().strip()
        if country in HIGH_RISK_COUNTRIES:
            result.triggered_rules.append(RuleTrigger(
                rule_id="R003",
                rule_name="High-Risk Country Origin",
                description=f"Transaction originates from high-risk country code '{country}'.",
                severity="high",
                penalty_points=20.0,
            ))

    def _check_high_risk_merchant_category(self, tx: Dict, result: RulesResult) -> None:
        """Flag transactions at merchants associated with elevated fraud rates."""
        category = str(tx.get("merchant_category", "")).upper().strip()
        if category in HIGH_RISK_MERCHANT_CATEGORIES:
            result.triggered_rules.append(RuleTrigger(
                rule_id="R004",
                rule_name="High-Risk Merchant Category",
                description=f"Transaction category '{category}' is associated with elevated fraud rates.",
                severity="high",
                penalty_points=20.0,
            ))

    def _check_new_or_unknown_device(self, tx: Dict, result: RulesResult) -> None:
        """Flag transactions where device_id is missing, short, or flagged as new."""
        device_id = str(tx.get("device_id", "")).strip()
        is_new_device = tx.get("is_new_device", False)
        if not device_id or len(device_id) < 5 or is_new_device:
            result.triggered_rules.append(RuleTrigger(
                rule_id="R005",
                rule_name="New or Unrecognized Device",
                description="Transaction was submitted from an unregistered or new device fingerprint.",
                severity="medium",
                penalty_points=15.0,
            ))

    def _check_rapid_transactions(self, tx: Dict, result: RulesResult) -> None:
        """Flag if velocity counter exceeds the threshold in the rolling time window."""
        tx_count_in_window = int(tx.get("tx_count_in_window", 0))
        if tx_count_in_window >= RAPID_TX_COUNT:
            result.triggered_rules.append(RuleTrigger(
                rule_id="R006",
                rule_name="Rapid Transaction Velocity",
                description=(
                    f"{tx_count_in_window} transactions were detected within the "
                    f"{RAPID_TX_WINDOW_SECONDS // 60}-minute velocity window."
                ),
                severity="high",
                penalty_points=25.0,
            ))

    def _check_round_amount(self, tx: Dict, result: RulesResult) -> None:
        """Flag perfectly round transaction amounts which are a known fraud indicator."""
        amount = float(tx.get("amount", 0.0))
        # Check for round amounts above a minimum threshold
        if amount >= 100.0 and amount % 100.0 == 0.0:
            result.triggered_rules.append(RuleTrigger(
                rule_id="R007",
                rule_name="Suspicious Round Amount",
                description=(
                    f"Transaction amount of ${amount:,.2f} is perfectly round, "
                    "which is a known indicator of structured payments."
                ),
                severity="low",
                penalty_points=5.0,
            ))

    def _check_ip_country_mismatch(self, tx: Dict, result: RulesResult) -> None:
        """Flag if IP geo-location does not match the declared transaction country."""
        ip_country = str(tx.get("ip_country", "")).upper().strip()
        declared_country = str(tx.get("country", "")).upper().strip()
        if ip_country and declared_country and ip_country != declared_country:
            result.triggered_rules.append(RuleTrigger(
                rule_id="R008",
                rule_name="IP-Country Location Mismatch",
                description=(
                    f"Declared country '{declared_country}' does not match "
                    f"IP-resolved country '{ip_country}'."
                ),
                severity="critical",
                penalty_points=25.0,
            ))
