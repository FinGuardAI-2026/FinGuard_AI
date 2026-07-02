"""
ml_pipeline/run_explainability.py
─────────────────────────────────
Orchestrates SHAP calculations on the champion model.
Saves global and local explanation plots and writes shap_report.md.
"""
import sys
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split

# Add project root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from ml_pipeline.preprocessing.data_loader import DataLoader
from ml_pipeline.explainability.shap_explainer import FinGuardSHAPExplainer
from ml_pipeline.utils.logger import get_logger
from ml_pipeline.utils.file_utils import load_joblib

logger = get_logger("run_explainability")


def compile_shap_report(
    global_features: list,
    local_narrative: dict,
    sample_index: int,
    true_label: int,
    pred_prob: float,
    output_dir: Path,
) -> None:
    """Compiles the shap_report.md markdown file explaining SHAP theory and local attributions."""
    report_path = output_dir / "shap_report.md"

    lines = []
    lines.append("# FinGuard AI – Explainable AI (SHAP) Interpretation Report")
    lines.append("")
    lines.append("This document outlines the explainability layer for the FinGuard AI champion classifier using SHAP (SHapley Additive exPlanations). It provides global feature rankings, local transaction interpretations, and theory guidelines.")
    lines.append("")
    lines.append("## 1. What are SHAP Values and How are They Calculated?")
    lines.append("")
    lines.append("SHAP values are rooted in **coalitional game theory (Shapley values)**. ")
    lines.append("In an ML context:")
    lines.append("- **The Game**: The machine learning model making a prediction (e.g. predicting a fraud probability of $84\%$).")
    lines.append("- **The Players**: The input features (e.g. transaction `Amount`, geographical coordinates, PCA components `V1-V28`).")
    lines.append("- **The Payoff**: The difference between the actual prediction output and the base rate prediction (expected value of the dataset, e.g. $2\%$).")
    lines.append("")
    lines.append("To calculate the contribution of a single feature, SHAP measures how the prediction changes when that feature is included versus excluded across all possible combinations of other features. This ensures that the attributions satisfy key game-theoretic properties:")
    lines.append("1. **Efficiency**: The sum of SHAP values of all features equals the difference between the model's prediction and the base expected value.")
    lines.append("2. **Symmetry**: If two features contribute equally in all coalitions, their SHAP values are identical.")
    lines.append("3. **Dummy**: Features that have no impact on the model's output receive a SHAP value of $0$.")
    lines.append("4. **Additivity**: Attributions can be summed linearly, which makes local interpretations intuitive.")
    lines.append("")

    lines.append("## 2. Global Feature Importance")
    lines.append("")
    lines.append("Based on global Shapley attributions, the features exerting the strongest average influence on fraud prediction probabilities are:")
    lines.append("")
    lines.append("| Rank | Feature | Mean (|SHAP|) | Description |")
    lines.append("| :--- | :--- | :--- | :--- |")
    for idx, (feat, score) in enumerate(global_features[:10]):
        lines.append(f"| {idx+1} | `{feat}` | {score:.6f} | Global predictive feature. |")
    lines.append("")

    lines.append("## 3. Local Transaction Explanation Case Run")
    lines.append("")
    lines.append("The following analysis breaks down a specific transaction prediction selected for auditing:")
    lines.append("")
    lines.append(f"- **Sample Row Index**: `{sample_index}`")
    lines.append(f"- **True Label**: `{'Fraud' if true_label == 1 else 'Genuine'}`")
    lines.append(f"- **Model Prediction Probability**: `{pred_prob*100:.2f}%`")
    lines.append(f"- **Base Expected Probability**: `{local_narrative['base_value']*100:.2f}%`")
    lines.append("")

    lines.append("### Analyst-Friendly Risk Narrative")
    lines.append("")
    lines.append("#### 🔴 Fraud Risk Drivers (Positive Attributions)")
    for s in local_narrative["analyst_narrative"]["risk_drivers"]:
        lines.append(f"- {s}")
    if not local_narrative["analyst_narrative"]["risk_drivers"]:
        lines.append("- No significant risk drivers identified.")
    lines.append("")

    lines.append("#### 🔵 Mitigating Factors (Negative Attributions)")
    for s in local_narrative["analyst_narrative"]["risk_factors"] if "risk_factors" in local_narrative["analyst_narrative"] else local_narrative["analyst_narrative"].get("mitigating_factors", []):
        lines.append(f"- {s}")
    if not local_narrative["analyst_narrative"].get("mitigating_factors") and not local_narrative["analyst_narrative"].get("risk_factors"):
        lines.append("- No mitigating factors identified.")
    lines.append("")

    lines.append("---")
    lines.append("## 4. Explanation Figures Catalog")
    lines.append("")
    lines.append("All output figures are saved in the `ml_pipeline/reports/figures/` directory:")
    lines.append("")
    lines.append("1. **`summary_plot.png`** (Beeswarm chart showing feature impact directionality across the entire test set).")
    lines.append("2. **`decision_plot.png`** (Visual path tracking how individual feature values construct prediction trajectories).")
    lines.append("3. **`dependence_plot.png`** (Scatter plot showing feature value scale vs SHAP contribution values).")
    lines.append("4. **`waterfall_plot.png`** (Step-wise attribution breakdown of the audited local transaction).")
    lines.append("5. **`force_plot.png`** (Balance visual showing forces pushing prediction probability away from the base value).")
    lines.append("")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("SHAP markdown report written successfully.")


def main() -> int:
    """Loads champion, computes SHAP matrix, generates plots, and registers report."""
    logger.info("Initializing FinGuard AI explainability pipeline...")

    models_dir = Path("ml_pipeline/models")
    reports_dir = Path("ml_pipeline/reports")
    figures_dir = reports_dir / "figures"
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    champion_path = models_dir / "best_model.pkl"
    preprocessor_path = models_dir / "preprocessor.joblib"

    if not champion_path.is_file() or not preprocessor_path.is_file():
        logger.error("Champion model or preprocessor files missing. Run run_training.py first.")
        return 1

    try:
        # 1. Load fitted model and preprocessor
        with open(champion_path, "rb") as f:
            model = pickle.load(f)
        preprocessor = load_joblib(preprocessor_path)

        # 2. Load dataset
        loader = DataLoader()
        df = loader.load_dataset()
        df_clean = df.drop_duplicates()

        target_col = "Class" if "Class" in df_clean.columns else "is_fraud"

        X = df_clean.drop(columns=[target_col])
        y = df_clean[target_col]
        _, X_test, _, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42, stratify=y
        )

        X_test_trans = preprocessor.transform(X_test)

        # 3. Instantiate SHAP Wrapper
        # Sample background data for speed and stability (up to 150 rows)
        sample_size = min(len(X_test_trans), 150)
        X_sample = X_test_trans.iloc[:sample_size]
        y_sample = y_test.iloc[:sample_size]

        xai = FinGuardSHAPExplainer(model, X_sample)

        # 4. Calculate SHAP values
        logger.info("Calculating SHAP values...")
        shap_values = xai.calculate_shap_values(X_sample)

        # 5. Generate Global Plots
        xai.generate_summary_plot(shap_values, X_sample, figures_dir / "summary_plot.png")
        xai.generate_decision_plot(xai.expected_value, shap_values, figures_dir / "decision_plot.png")

        # Pick key numeric column for dependence plot (prefer Amount if present)
        dep_col = "Amount" if "Amount" in X_sample.columns else X_sample.columns[0]
        xai.generate_dependence_plot(shap_values, X_sample, dep_col, figures_dir / "dependence_plot.png")

        # 6. Generate Local Explanation for Audit
        # Look for the first fraud instance, or default to first row if none in sample
        fraud_indices = np.where(y_sample.values == 1)[0]
        audit_idx = int(fraud_indices[0]) if len(fraud_indices) > 0 else 0

        # Run predictions to get local outputs
        pred_prob = float(model.predict_proba(X_sample.iloc[[audit_idx]])[0, 1])

        # Get attributions and write local plots
        xai.generate_waterfall_plot(
            xai.expected_value,
            shap_vector=shap_values[audit_idx],
            sample_row=X_sample.iloc[audit_idx],
            out_path=figures_dir / "waterfall_plot.png"
        )
        xai.generate_force_plot(
            xai.expected_value,
            shap_vector=shap_values[audit_idx],
            sample_row=X_sample.iloc[audit_idx],
            out_path=figures_dir / "force_plot.png"
        )

        # Get local text narrative
        narrative = xai.generate_analyst_narrative(
            shap_vector=shap_values[audit_idx],
            sample_row=X_sample.iloc[audit_idx]
        )

        # Compute mean global impact ranking
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        global_rankings = sorted(
            zip(X_sample.columns, mean_abs_shap),
            key=lambda x: x[1],
            reverse=True
        )

        # 7. Compile Markdown Report
        compile_shap_report(
            global_features=global_rankings,
            local_narrative=narrative,
            sample_index=audit_idx,
            true_label=int(y_sample.iloc[audit_idx]),
            pred_prob=pred_prob,
            output_dir=reports_dir,
        )

        logger.info("Explainability pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Explainability pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
