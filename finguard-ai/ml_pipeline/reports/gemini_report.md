# FinGuard AI — Gemini AI Integration Report

This document describes the architecture, prompt engineering strategy, and report output format for the Gemini AI report generation module integrated into the FinGuard AI fraud detection pipeline.

## 1. Architecture Overview

```
FraudContext (unified input)
       │
       ▼
Prompt Renderer  ──── prompts.py (template registry)
       │
       ▼
GeminiClient     ──── google-generativeai SDK
       │              (falls back to simulation if SDK/key absent)
       ▼
Report Parser    ──── Standardized header + Gemini output
       │
       ▼
File Writer      ──── Individual .md files + report_index.json
```

## 2. Report Types

| Report | Audience | Tone | Target Length |
| :--- | :--- | :--- | :--- |
| Fraud Investigation Report | Fraud Investigation Team | Formal, legal | ~600 words |
| Analyst Summary | Fraud Analyst | Concise, operational | ~300 words |
| Executive Summary | Senior Leadership | Strategic, non-technical | ~250 words |
| Customer Notification | Account Holder | Empathetic, clear | ~200 words |

## 3. Prompt Engineering Design

Each prompt template is implemented as a `string.Template` object in `prompts.py`.
Templates use `$placeholder` syntax for runtime substitution and enforce strict section headings to ensure consistent, parseable output.

### Key Design Decisions
- **Temperature 0.3**: Low temperature ensures factual, consistent tone across runs.
- **Audience-specific persona**: Each prompt opens with a role assignment to steer the model's voice.
- **Section enforcement**: Required section headings are listed explicitly in each prompt so the output can be reliably parsed or displayed.
- **Confidentiality guards**: The Customer Notification template explicitly prohibits disclosure of risk scores, ML model details, or fraud probabilities.

## 4. FraudContext Fields

| Field | Type | Description |
| :--- | :--- | :--- |
| `transaction_id` | str | Unique transaction identifier |
| `amount` | float | Transaction amount |
| `currency` | str | ISO currency code |
| `merchant_name` | str | Merchant name |
| `merchant_category` | str | Merchant category code |
| `country` | str | Transaction country |
| `ip_address` | str | Originating IP address |
| `device_id` | str | Device fingerprint |
| `prediction` | str | FRAUD or GENUINE |
| `fraud_probability` | float | ML fraud probability (%) |
| `risk_score` | float | Final risk score 0–100 |
| `risk_level` | str | Low / Medium / High / Critical |
| `triggered_rules` | List[str] | Business rules triggered |
| `shap_risk_drivers` | List[str] | Top SHAP risk attributions |
| `shap_mitigating_factors` | List[str] | Negative SHAP mitigating features |

## 5. Generated Files

All reports are written to `ml_pipeline/reports/gemini/`:

| File | Description |
| :--- | :--- |
| `fraud_investigation_report.md` | Full formal investigation case file |
| `analyst_summary.md` | Operational analyst decision brief |
| `executive_summary.md` | Strategic leadership briefing note |
| `customer_notification.md` | Customer-facing notification message |
| `report_index.json` | Machine-readable metadata index of all generated reports |

## 6. Environment Configuration

```bash
# Set your Gemini API key before running
set GEMINI_API_KEY=your_api_key_here    # Windows
export GEMINI_API_KEY=your_api_key_here  # macOS/Linux

# Run the pipeline
python ml_pipeline/run_gemini.py
```

If `GEMINI_API_KEY` is not set, the module operates in **offline simulation mode**, returning deterministic structured placeholder reports suitable for testing and development.