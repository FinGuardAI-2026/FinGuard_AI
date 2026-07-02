"""
ml_pipeline/gemini/prompts.py
─────────────────────────────
Structured prompt templates for all four Gemini-generated report types.
Each template is a standalone string with named placeholders populated at runtime.
Templates enforce strict output formatting to ensure consistent parsing.
"""
from string import Template


# ── 1. Fraud Investigation Report ─────────────────────────────────────────────
# Audience: Internal Fraud Investigation Team
# Tone: Formal, technical, legally defensible
FRAUD_INVESTIGATION_TEMPLATE = Template("""
You are a Senior Fraud Investigation Analyst at a financial institution. 
You are writing a formal investigation report for an internal fraud investigation case file.

Write a FORMAL, DETAILED, STRUCTURED fraud investigation report for the following transaction.
Do NOT include any disclaimers. Do NOT mention AI. Use past tense throughout.
Use clear section headings and bullet points.

=== TRANSACTION DETAILS ===
Transaction ID:        $transaction_id
Amount:                $$$amount $currency
Merchant:              $merchant_name
Merchant Category:     $merchant_category
Payment Method:        $payment_method
Transaction Type:      $transaction_type
Country:               $country
City:                  $city
IP Address:            $ip_address
Device ID:             $device_id
Browser:               $browser
Operating System:      $operating_system
Transaction Time:      $transaction_time

=== ML ASSESSMENT ===
Fraud Prediction:      $prediction
Fraud Probability:     $fraud_probability%
Confidence Score:      $confidence_score%
Risk Score:            $risk_score / 100
Risk Level:            $risk_level

=== EXPLAINABILITY (SHAP DRIVERS) ===
Top Risk Drivers:
$shap_risk_drivers

Mitigating Factors:
$shap_mitigating_factors

=== BUSINESS RULES TRIGGERED ===
$triggered_rules

=== REQUIRED REPORT SECTIONS ===
Write EXACTLY the following sections:

## 1. Executive Case Summary
## 2. Transaction Profile Analysis
## 3. Fraud Indicators Identified
## 4. Risk Assessment Rationale
## 5. Evidence Evaluation
## 6. Conclusion and Recommended Action
## 7. Case Disposition

Keep the tone formal and investigative. The report should be legally defensible.
""")


# ── 2. Analyst Summary ────────────────────────────────────────────────────────
# Audience: Fraud Analyst (operational review)
# Tone: Professional, concise, actionable
ANALYST_SUMMARY_TEMPLATE = Template("""
You are a Fraud Analyst assistant. 
Write a concise, actionable operational summary for a Fraud Analyst to quickly review and decide on a transaction.

=== TRANSACTION ===
ID:             $transaction_id
Amount:         $$$amount $currency
Merchant:       $merchant_name ($merchant_category)
Country:        $country
Time:           $transaction_time
Device:         $device_id

=== RISK ASSESSMENT ===
Prediction:     $prediction
Probability:    $fraud_probability%
Risk Score:     $risk_score / 100
Risk Level:     $risk_level

=== TOP SHAP RISK DRIVERS ===
$shap_risk_drivers

=== BUSINESS RULES TRIGGERED ===
$triggered_rules

=== RECOMMENDATION ===
$investigation_recommendation

Write a SHORT, STRUCTURED analyst operational summary under these headings:
## Quick Decision Guidance
## Key Red Flags
## Mitigating Factors
## Suggested Next Steps

Keep it under 300 words. Use bullet points. Be direct and action-oriented.
""")


# ── 3. Executive Summary ──────────────────────────────────────────────────────
# Audience: Senior Leadership / Risk Committee
# Tone: Strategic, high-level, minimal technical detail
EXECUTIVE_SUMMARY_TEMPLATE = Template("""
You are a Chief Risk Officer's assistant. 
Write an executive-level briefing note for a fraud incident detected by the automated fraud detection system.

The summary must be non-technical, high-level, and focused on business impact and strategic risk.
Do NOT mention model names, SHAP, or technical implementation details.

=== INCIDENT OVERVIEW ===
Transaction ID:   $transaction_id
Amount at Risk:   $$$amount $currency
Merchant:         $merchant_name
Country:          $country
Risk Level:       $risk_level
Risk Score:       $risk_score / 100
Prediction:       $prediction

=== KEY RISK SIGNALS ===
$triggered_rules

=== RECOMMENDATION ===
$investigation_recommendation

Write the briefing note under these headings:
## Incident Summary
## Business Impact Assessment
## Key Risk Indicators
## Immediate Action Taken
## Escalation Recommendation

Use executive-level language. Keep it under 250 words. No bullet points — use short paragraphs.
""")


# ── 4. Customer Notification ──────────────────────────────────────────────────
# Audience: Customer / Account Holder
# Tone: Empathetic, clear, non-alarming, professional
CUSTOMER_NOTIFICATION_TEMPLATE = Template("""
You are a Customer Service specialist at a bank.
Write a clear, empathetic, and professional notification message for a bank customer about a potentially suspicious transaction on their account.

You MUST NOT:
- Reveal fraud detection methodology, ML models, or risk scores.
- Use alarming language or make definitive fraud accusations.
- Include any personal financial advice.

=== CONTEXT ===
Transaction Amount:     $$$amount $currency
Merchant:               $merchant_name
Transaction Time:       $transaction_time
Risk Level (Internal):  $risk_level (DO NOT disclose this directly to the customer)

Write the message with the following structure:
## Subject Line
## Opening Greeting
## Transaction Alert Body
## Verification Request
## Security Reassurance
## Contact Details Placeholder

Keep it under 200 words. Use friendly, reassuring, professional tone. Never mention fraud probability or risk scores.
""")


# ── Template Registry ─────────────────────────────────────────────────────────
PROMPT_TEMPLATES = {
    "fraud_investigation": FRAUD_INVESTIGATION_TEMPLATE,
    "analyst_summary":     ANALYST_SUMMARY_TEMPLATE,
    "executive_summary":   EXECUTIVE_SUMMARY_TEMPLATE,
    "customer_notification": CUSTOMER_NOTIFICATION_TEMPLATE,
}
