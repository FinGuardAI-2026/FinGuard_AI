"""
ml_pipeline/explainability/shap_explainer.py
─────────────────────────────────────────────
Explains machine learning predictions using SHAP (SHapley Additive exPlanations).
Generates global summary plots, local waterfalls, force diagrams, dependence plots,
decision curves, and translates raw values into analyst-friendly text narratives.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)

# Try loading SHAP, fallback to simulated engine if missing
HAS_SHAP = False
try:
    import shap
    HAS_SHAP = True
except ImportError:
    logger.warning("shap package not detected. Explainability module will run in simulation mode.")


class FinGuardSHAPExplainer:
    """
    Computes global and local feature attributions using Shapley values.
    """

    def __init__(self, model: Any, background_data: pd.DataFrame) -> None:
        self.model = model
        self.background_data = background_data
        self.feature_names = list(background_data.columns)
        self.active = HAS_SHAP

        # Store explainer instance
        self.explainer: Optional[Any] = None
        self.expected_value: float = 0.0

        if self.active:
            try:
                # Resolve explainer type based on algorithm
                model_class = model.__class__.__name__.lower()
                if any(x in model_class for x in ["forest", "tree", "xgboost", "lgbm"]):
                    self.explainer = shap.TreeExplainer(self.model)
                elif "logistic" in model_class:
                    self.explainer = shap.LinearExplainer(self.model, self.background_data)
                else:
                    self.explainer = shap.Explainer(self.model, self.background_data)

                # Set expected base value
                if hasattr(self.explainer, "expected_value"):
                    # TreeExplainer expected_value might be a list/array for multiclass/binary, pick positive class
                    ev = self.explainer.expected_value
                    if isinstance(ev, (list, np.ndarray)):
                        self.expected_value = float(ev[1]) if len(ev) > 1 else float(ev[0])
                    else:
                        self.expected_value = float(ev)
            except Exception as e:
                logger.warning(f"Error instantiating SHAP explainer: {e}. Switching to simulation mode.")
                self.active = False

        if not self.active:
            # Simulated base value matching average prediction prob
            self.expected_value = 0.02

    def calculate_shap_values(self, X: pd.DataFrame) -> Union[np.ndarray, Any]:
        """Computes SHAP attribution values for a given dataset."""
        if self.active and self.explainer:
            try:
                # TreeExplainer might output a list of arrays (one per class), pick fraud class (index 1)
                sh_vals = self.explainer.shap_values(X)
                if isinstance(sh_vals, list) and len(sh_vals) > 1:
                    return sh_vals[1]
                return sh_vals
            except Exception as e:
                logger.warning(f"Error computing raw SHAP values: {e}. Falling back to simulation.")

        # simulated fallback: weight by coefficients or feature importances
        return self._simulate_shap_values(X)

    def _simulate_shap_values(self, X: pd.DataFrame) -> np.ndarray:
        """Helper to generate simulated Shapley attributions aligned with feature profiles."""
        num_samples = len(X)
        num_features = len(self.feature_names)

        # Base importances from model if available
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
        elif hasattr(self.model, "coef_"):
            importances = np.abs(self.model.coef_[0])
        else:
            importances = np.linspace(0.1, 0.01, num_features)

        # Normalize
        importances /= importances.sum()

        # Generate fake local attributions centering around feature values
        np.random.seed(42)
        simulated = np.zeros((num_samples, num_features))
        for i in range(num_features):
            col_val = X.iloc[:, i].values
            # High amount / V12 values push score up, others down
            # trend = 1.0 if self.feature_names[i] in ["Amount", "V11", "V4"] else -1.0
            trend = 1.0 if self.feature_names[i] == "amount" else -1.0
            noise = np.random.normal(0, 0.05, num_samples)
            simulated[:, i] = (col_val * importances[i] * trend) + noise

        return simulated

    # ── Plot Generation ───────────────────────────────────────────────────

    def generate_summary_plot(self, shap_values: np.ndarray, X: pd.DataFrame, out_path: Path) -> None:
        """Saves a summary beeswarm plot demonstrating global feature distribution effects."""
        plt.figure(figsize=(10, 6))
        if self.active:
            try:
                shap.summary_plot(shap_values, X, show=False)
                plt.title("SHAP Global Feature Importance Beeswarm", fontsize=12, fontweight="bold")
                plt.tight_layout()
                plt.savefig(out_path, dpi=300)
                plt.close()
                logger.info(f"Saved summary plot to '{out_path}'")
                return
            except Exception as e:
                logger.warning(f"Error during SHAP summary plotting: {e}. Falling back to simulation.")

        # Simulated fallback Summary Plot
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        indices = np.argsort(mean_abs_shap)
        sorted_features = [self.feature_names[i] for i in indices[-15:]]
        sorted_scores = [mean_abs_shap[i] for i in indices[-15:]]

        plt.barh(sorted_features, sorted_scores, color="#EF4444")
        plt.xlabel("mean(|SHAP value|) (average impact on model output magnitude)")
        plt.title("Global Feature Importance (Simulated SHAP Summary)", fontsize=12, fontweight="bold")
        plt.tight_layout()
        plt.savefig(out_path, dpi=300)
        plt.close()
        logger.info(f"Saved simulated summary plot to '{out_path}'")

    def generate_waterfall_plot(self, base_value: float, shap_vector: np.ndarray, sample_row: pd.Series, out_path: Path) -> None:
        """Saves a local waterfall plot indicating specific drivers for a single transaction."""
        plt.figure(figsize=(8, 6))
        if self.active:
            try:
                # Construct SHAP Explanation object
                explanation = shap.Explanation(
                    values=shap_vector,
                    base_values=base_value,
                    data=sample_row.values,
                    feature_names=self.feature_names
                )
                shap.plots.waterfall(explanation, show=False)
                plt.title("Local Prediction Driver Waterfall", fontsize=12, fontweight="bold")
                plt.tight_layout()
                plt.savefig(out_path, dpi=300)
                plt.close()
                return
            except Exception as e:
                logger.warning(f"Error during SHAP waterfall plotting: {e}")

        # Simulated fallback Waterfall
        indices = np.argsort(np.abs(shap_vector))[::-1][:8]  # top 8 features
        y_pos = np.arange(len(indices))
        vals = shap_vector[indices]
        names = [f"{self.feature_names[i]} ({sample_row.iloc[i]:.2f})" for i in indices]

        colors = ["#EF4444" if v >= 0 else "#3B82F6" for v in vals]
        plt.barh(y_pos, vals, color=colors, align="center")
        plt.yticks(y_pos, names)
        plt.gca().invert_yaxis()
        plt.xlabel("SHAP Value (Attribution Impact)")
        plt.title("Local Feature Contribution Waterfall (Simulated)", fontsize=12, fontweight="bold")
        plt.tight_layout()
        plt.savefig(out_path, dpi=300)
        plt.close()
        logger.info(f"Saved simulated waterfall plot to '{out_path}'")

    def generate_force_plot(self, base_value: float, shap_vector: np.ndarray, sample_row: pd.Series, out_path: Path) -> None:
        """Saves a force plot displaying the balance of positive and negative attributions."""
        plt.figure(figsize=(10, 3))
        # force_plot rendering in static files is historically complex; we build an analyst-clear stacked bar
        pos_idx = np.where(shap_vector > 0)[0]
        neg_idx = np.where(shap_vector < 0)[0]

        pos_vals = shap_vector[pos_idx]
        neg_vals = shap_vector[neg_idx]

        pos_labels = [self.feature_names[i] for i in pos_idx]
        neg_labels = [self.feature_names[i] for i in neg_idx]

        # Plot positive forces stacking to the right, negative to the left
        left = base_value
        for val, label in zip(pos_vals, pos_labels):
            plt.barh([0], [val], left=left, color="#EF4444", edgecolor="white", height=0.5)
            left += val

        left = base_value
        for val, label in zip(neg_vals, neg_labels):
            plt.barh([0], [val], left=left, color="#3B82F6", edgecolor="white", height=0.5)
            left += val

        plt.axvline(base_value, color="black", linestyle="--", label=f"Base Val ({base_value:.4f})")
        plt.yticks([])
        plt.xlabel("Output Value (Higher pushes to Fraud)")
        plt.title("SHAP Force Plot (Balance of Predictive Drivers)", fontsize=11, fontweight="bold")
        plt.legend(loc="upper right", fontsize=8)
        plt.tight_layout()
        plt.savefig(out_path, dpi=300)
        plt.close()
        logger.info(f"Saved force plot to '{out_path}'")

    def generate_dependence_plot(self, shap_values: np.ndarray, X: pd.DataFrame, feature_name: str, out_path: Path) -> None:
        """Saves a dependence scatter plot demonstrating feature value vs SHAP impact."""
        if feature_name not in self.feature_names:
            return

        feat_idx = self.feature_names.index(feature_name)
        plt.figure(figsize=(7, 5))

        x_vals = X[feature_name].values
        y_vals = shap_values[:, feat_idx]

        plt.scatter(x_vals, y_vals, color="#EF4444", alpha=0.6, edgecolors="none")
        plt.xlabel(f"Feature value: {feature_name}")
        plt.ylabel(f"SHAP value for {feature_name}")
        plt.title(f"SHAP Dependence Plot – {feature_name}", fontsize=12, fontweight="bold")
        plt.grid(True, linestyle=":", alpha=0.5)
        plt.tight_layout()
        plt.savefig(out_path, dpi=300)
        plt.close()
        logger.info(f"Saved dependence plot for '{feature_name}' to '{out_path}'")

    def generate_decision_plot(self, base_value: float, shap_values: np.ndarray, out_path: Path) -> None:
        """Saves a cumulative decision plot displaying prediction trajectory lines."""
        plt.figure(figsize=(7, 8))

        # Order features by importance
        mean_abs = np.abs(shap_values).mean(axis=0)
        sorted_indices = np.argsort(mean_abs)

        # Plot trajectories for a subset of samples (up to 15)
        num_samples = min(len(shap_values), 15)
        y_pos = np.arange(len(sorted_indices) + 1)
        y_labels = ["Base Value"] + [self.feature_names[i] for i in sorted_indices]

        for s in range(num_samples):
            # Compute cumulative sum of attributions from base value
            x_traj = [base_value]
            current = base_value
            for idx in sorted_indices:
                current += shap_values[s, idx]
                x_traj.append(current)
            plt.plot(x_traj, y_pos, alpha=0.6, marker="o", markersize=3)

        plt.yticks(y_pos, y_labels, fontsize=8)
        plt.xlabel("Prediction Probability Trajectory")
        plt.title("SHAP Decision Plot (Attribution Trajectories)", fontsize=12, fontweight="bold")
        plt.grid(True, linestyle=":", alpha=0.5)
        plt.tight_layout()
        plt.savefig(out_path, dpi=300)
        plt.close()
        logger.info(f"Saved decision plot to '{out_path}'")

    # ── Narrative Generator ───────────────────────────────────────────────

    def generate_analyst_narrative(
        self,
        shap_vector: np.ndarray,
        sample_row: pd.Series,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Translates numeric Shapley values into a natural language risk driver analysis.
        """
        # Calculate dynamic threshold if not provided
        abs_vals = np.abs(shap_vector)
        max_abs = abs_vals.max() if len(abs_vals) > 0 else 0.0
        if threshold is None:
            if max_abs > 0:
                # 15% of the maximum absolute impact, minimum 0.001
                threshold = max(0.001, float(0.15 * max_abs))
            else:
                threshold = 0.005

        total_abs_impact = float(abs_vals.sum())

        positive_drivers = []
        negative_drivers = []

        def is_one_hot_feature(feature_name: str) -> bool:
            return feature_name.startswith((
                "merchant_category_",
                "payment_method_",
                "transaction_type_",
                "country_",
            ))

        # Human readable feature name and value mapper
        def map_feature(feature_name: str, processed_val: float) -> Tuple[str, Union[float, str]]:
            name_map = {
                "amount": "Transaction Amount",
                "merchant_category": "Merchant Category",
                "payment_method": "Payment Method",
                "transaction_type": "Transaction Type",
                "country": "Country",
            }
            # Check for one-hot encoded category features
            for prefix in ["merchant_category_", "payment_method_", "transaction_type_", "country_"]:
                if feature_name.startswith(prefix):
                    raw_feat = prefix[:-1]
                    category = feature_name[len(prefix):]
                    readable_name = name_map.get(raw_feat, raw_feat.replace("_", " ").title())
                    if processed_val == 1.0:
                        return readable_name, category
                    return readable_name, None
            
            readable_name = name_map.get(feature_name, feature_name.replace("_", " ").title())
            return readable_name, processed_val
        
        # print("\n========== SAMPLE ROW ==========")
        # print(sample_row)

        # print("\n========== FEATURE NAMES ==========")
        # print(self.feature_names)


        for idx, val in enumerate(shap_vector):
            # Safe index boundary check
            if idx >= len(self.feature_names):
                continue

            f_name = self.feature_names[idx]
            # Safe boundary check for sample_row
            f_val = sample_row.iloc[idx] if idx < len(sample_row) else 0.0

            # Map to human-readable feature name and value
            readable_name, readable_val = map_feature(f_name, f_val)
            # Skip inactive one-hot encoded categories
            if is_one_hot_feature(f_name) and f_val != 1.0:
                continue

            # Calculate normalized contribution percentage
            percentage = round((abs(val) / total_abs_impact) * 100, 2) if total_abs_impact > 0 else 0.0

            driver_info = {
                "feature": readable_name,
                "value": readable_val,
                "impact": float(val),
                "percentage": percentage
            }

            if val > threshold:
                positive_drivers.append(driver_info)
            elif val < -threshold:
                negative_drivers.append(driver_info)

        # Sort by impact strength descending
        positive_drivers.sort(key=lambda x: x["impact"], reverse=True)
        negative_drivers.sort(key=lambda x: abs(x["impact"]), reverse=True)

        # Helper to format values for text narrative
        def format_value_str(feature: str, val: Any) -> str:
            if feature == "Transaction Amount" and isinstance(val, (int, float)):
                return f"${val:.2f}"
            if isinstance(val, float):
                return f"{val:.2f}"
            return str(val)

        # Build natural explanations
        pos_sentences = []
        for d in positive_drivers[:5]:
            val_str = format_value_str(d["feature"], d["value"])
            pos_sentences.append(
                f"Feature `{d['feature']}` (value: {val_str}) increased the fraud likelihood by `+{d['impact']*100:.2f}%` (attribution: {d['percentage']}%)."
            )

        neg_sentences = []
        for d in negative_drivers[:5]:
            val_str = format_value_str(d["feature"], d["value"])
            neg_sentences.append(
                f"Feature `{d['feature']}` (value: {val_str}) lowered the fraud likelihood by `-{abs(d['impact'])*100:.2f}%` (attribution: {d['percentage']}%)."
            )

        return {
            "base_value": float(self.expected_value),
            "positive_drivers": positive_drivers[:5],
            "negative_drivers": negative_drivers[:5],
            "analyst_narrative": {
                "risk_drivers": pos_sentences,
                "mitigating_factors": neg_sentences,
            }
        }
