"""
ml_pipeline/run_training.py
───────────────────────────
CLI pipeline runner that loads the preprocessor, splits raw data, applies resampling,
tunes five classifiers via Stratified GridSearchCV, runs performance evaluations,
identifies the champion, and writes comparison reports.
"""
import sys
import pickle
import time
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split

# Add project root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from ml_pipeline.preprocessing.data_loader import DataLoader
from ml_pipeline.preprocessing.pipeline import FraudPreprocessor
from ml_pipeline.preprocessing.imbalance import ImbalanceHandler
from ml_pipeline.training.trainer import ModelTrainer
from ml_pipeline.training.evaluator import ModelEvaluator
from ml_pipeline.utils.logger import get_logger
from ml_pipeline.utils.file_utils import save_json, load_joblib
from ml_pipeline.utils.mlflow_tracker import MLflowTracker

logger = get_logger("run_training")


def compile_comparison_report(
    leaderboard: list,
    champion_name: str,
    output_dir: Path,
) -> None:
    """Writes model_comparison.md and training_report.md documents."""
    comp_path = output_dir / "model_comparison.md"
    rep_path = output_dir / "training_report.md"

    # Build Comparison Table
    comp_lines = []
    comp_lines.append("# FinGuard AI – Model Performance Comparison")
    comp_lines.append("")
    comp_lines.append("A benchmarking run comparing five classification models trained using Stratified K-Fold CV:")
    comp_lines.append("")
    comp_lines.append("| Model Name | F1-Score | Recall | Precision | Accuracy | ROC-AUC | PR-AUC | Tuning Time | Latency (Per Sample) |")
    comp_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    for entry in leaderboard:
        comp_lines.append(
            f"| `{entry['model']}` | {entry['f1']:.4f} | {entry['recall']:.4f} | {entry['precision']:.4f} | "
            f"{entry['accuracy']:.4f} | {entry['roc_auc']:.4f} | {entry['pr_auc']:.4f} | "
            f"{entry['training_time_s']:.2f}s | {entry['inference_time_per_sample_ms']:.4f}ms |"
        )
    comp_lines.append("")
    comp_lines.append(f"### Champion Recommendation")
    comp_lines.append(f"- **Champion Model Selected**: `{champion_name.upper()}`")
    comp_lines.append("")

    # Build Training Report
    rep_lines = []
    rep_lines.append("# FinGuard AI – Training and Hyperparameter Tuning Report")
    rep_lines.append("")
    rep_lines.append("## Cross-Validation Design")
    rep_lines.append("- **Folds**: Stratified 5-Fold Cross Validation")
    rep_lines.append("- **Optimizing Score Metric**: F1-Score")
    rep_lines.append("- **Minority Resampling**: SMOTE (or ROS fallback)")
    rep_lines.append("")
    rep_lines.append("## Tuned Model Summary List")
    rep_lines.append("")
    for entry in leaderboard:
        rep_lines.append(f"### Model: `{entry['model']}`")
        rep_lines.append(f"- **Best Parameters**: `{entry['best_params']}`")
        rep_lines.append(f"- **F1 Score**: {entry['f1']:.4f}")
        rep_lines.append(f"- **Recall Score (Sensitivity)**: {entry['recall']:.4f}")
        rep_lines.append(f"- **Precision Score**: {entry['precision']:.4f}")
        rep_lines.append(f"- **PR-AUC**: {entry['pr_auc']:.4f}")
        rep_lines.append(f"- **Tuning Duration**: {entry['training_time_s']:.2f} seconds")
        rep_lines.append("")

    rep_lines.append("## Champion Summary Profile")
    champion = next(item for item in leaderboard if item["model"] == champion_name)
    rep_lines.append(f"- **Model Type**: `{champion_name}`")
    rep_lines.append(f"- **F1-Score**: {champion['f1']:.4f}")
    rep_lines.append(f"- **PR-AUC**: {champion['pr_auc']:.4f}")
    rep_lines.append(f"- **Average Prediction Latency**: {champion['inference_time_per_sample_ms']:.4f} milliseconds")
    rep_lines.append("")
    rep_lines.append("### Recommendations for Production Deployment")
    rep_lines.append("1. **Latency Budgets**: Choose models like Logistic Regression or LightGBM if sub-millisecond execution times are mandated.")
    rep_lines.append("2. **Performance Champions**: If F1/Recall metrics are prioritized to detect maximum fraud occurrences, Ensemble Models (Random Forest or XGBoost) represent the top candidates.")
    rep_lines.append("")

    with open(comp_path, "w", encoding="utf-8") as f:
        f.write("\n".join(comp_lines))
    with open(rep_path, "w", encoding="utf-8") as f:
        f.write("\n".join(rep_lines))

    logger.info("Markdown report files written.")


def main() -> int:
    """Tunes five estimators, evaluates performances, identifies champion, and saves pickles."""
    logger.info("Initializing FinGuard AI training suite...")

    models_dir = Path("ml_pipeline/models")
    reports_dir = Path("ml_pipeline/reports")
    figures_dir = reports_dir / "figures"
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    preprocessor_path = models_dir / "preprocessor.joblib"
    if not preprocessor_path.is_file():
        logger.error(f"Preprocessor artifact not found at '{preprocessor_path}'. Run run_preprocessing.py first.")
        return 1

    try:
        # 1. Load fitted Preprocessor
        preprocessor = load_joblib(preprocessor_path)
        logger.info("Fitted preprocessor successfully loaded.")

        # 2. Load dataset
        loader = DataLoader()
        df = loader.load_dataset()
        df_clean = df.drop_duplicates()

        target_col = "Class" if "Class" in df_clean.columns else "is_fraud"

        # Split identically as in preprocessing phase
        # X = df_clean.drop(columns=[target_col])
        # y = df_clean[target_col]
        drop_cols = [target_col]
        if "transaction_id" in df_clean.columns:
            drop_cols.append("transaction_id")
        X = df_clean.drop(columns=drop_cols)
        y = df_clean[target_col]
        print(X.dtypes)
        print(X.columns)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42, stratify=y
        )

        # 3. Transform inputs using fitted preprocessor parameters
        X_train_trans = preprocessor.transform(X_train)
        X_test_trans = preprocessor.transform(X_test)

        # Save fresh background dataset for SHAP
        background_data = X_train_trans.sample(
            n=min(200, len(X_train_trans)),
            random_state=42
        )

        joblib.dump(
            background_data,
            models_dir / "background_data.joblib"
        )

        logger.info(
            f"Saved SHAP background dataset with {background_data.shape[1]} features."
        )

        # 4. Handle training set class imbalance via SMOTE/ROS
        handler = ImbalanceHandler(random_state=42)
        balancing_strategy = handler.recommend_strategy(X_train, y_train)
        logger.info(f"Applying balancing strategy: '{balancing_strategy}'...")

        if balancing_strategy == "smote":
            X_train_bal, y_train_bal = handler.resample_smote(X_train_trans, y_train)
        else:
            X_train_bal, y_train_bal = handler.resample_ros(X_train_trans, y_train)
        print("Balanced Shape:", X_train_bal.shape)
        MAX_ROWS = 100000
        if len(X_train_bal) > MAX_ROWS:
            sample_idx = np.random.choice(
                len(X_train_bal),
                MAX_ROWS,
                replace=False,
            )
            X_train_bal = X_train_bal.iloc[sample_idx].reset_index(drop=True)
            y_train_bal = y_train_bal.iloc[sample_idx].reset_index(drop=True)
            print("Reduced Shape:", X_train_bal.shape)

        # 5. Train & Evaluate loop
        model_names = ["logistic_regression", "decision_tree", "random_forest", "xgboost", "lightgbm"]
        trainer = ModelTrainer(random_state=42)
        evaluator = ModelEvaluator(output_plots_dir=figures_dir)
        tracker = MLflowTracker()
        leaderboard = []

        for name in model_names:
            # Tune hyperparameters
            tuned_model, best_params, tuning_time = trainer.train_and_tune(
                model_name=name,
                X_train=X_train_bal,
                y_train=y_train_bal,
            )

            # Evaluate model
            eval_metrics = evaluator.evaluate(
                model=tuned_model,
                X_test=X_test_trans,
                y_test=y_test,
            )

            # Save curves & diagrams
            evaluator.save_plots(
                model_name=name,
                y_test=y_test,
                y_prob=eval_metrics["y_prob"],
                y_pred=eval_metrics["y_pred"],
            )

            # Save individual model joblib
            joblib.dump(tuned_model, models_dir / f"{name}.joblib")

            # Store in leaderboard
            leaderboard.append({
                "model": name,
                "f1": eval_metrics["f1"],
                "recall": eval_metrics["recall"],
                "precision": eval_metrics["precision"],
                "accuracy": eval_metrics["accuracy"],
                "roc_auc": eval_metrics["roc_auc"],
                "pr_auc": eval_metrics["pr_auc"],
                "training_time_s": tuning_time,
                "inference_time_per_sample_ms": eval_metrics["inference_time_per_sample_ms"],
                "best_params": best_params,
            })

            # MLOps Tracing via MLflow
            tracker.start_run(run_name=f"{name}_training")
            tracker.log_params({
                "model_type": name,
                "balancing_strategy": balancing_strategy,
                "random_state": 42,
                **best_params
            })
            tracker.log_metrics({
                "accuracy": eval_metrics["accuracy"],
                "precision": eval_metrics["precision"],
                "recall": eval_metrics["recall"],
                "f1": eval_metrics["f1"],
                "roc_auc": eval_metrics["roc_auc"],
                "pr_auc": eval_metrics["pr_auc"],
                "tuning_time_s": tuning_time,
                "inference_time_per_sample_ms": eval_metrics["inference_time_per_sample_ms"],
            })
            # Log figures
            tracker.log_figure(figures_dir / f"roc_curve_{name}.png", "plots")
            tracker.log_figure(figures_dir / f"pr_curve_{name}.png", "plots")
            tracker.log_figure(figures_dir / f"confusion_matrix_{name}.png", "plots")
            
            # Log model as challenger initially
            tracker.log_model(
                model=tuned_model,
                artifact_path="model",
                registered_name=f"FinGuard_Challenger_{name.upper()}"
            )
            tracker.end_run()

        # 6. Champion Model Selection
        # Primary Metric: F1 score (best balance of precision and recall in CC fraud detection)
        leaderboard.sort(key=lambda x: x["f1"], reverse=True)
        champion_name = leaderboard[0]["model"]
        logger.info(f"Champion Model identified: '{champion_name}' with F1={leaderboard[0]['f1']:.4f}")

        # Save leaderboard JSON
        save_json(leaderboard, reports_dir / "leaderboard.json")

        # Load and save Champion as best_model.pkl
        best_model_path = models_dir / f"{champion_name}.joblib"
        champion_model = joblib.load(best_model_path)

        pkl_path = models_dir / "best_model.pkl"
        with open(pkl_path, "wb") as f:
            pickle.dump(champion_model, f)
        logger.info(f"Champion model saved to pickle format at '{pkl_path}'")

        # Register Champion in MLflow Model Registry
        tracker.start_run(run_name="champion_model_registration")
        tracker.log_params({"champion_model_type": champion_name})
        tracker.log_metrics({
            "champion_f1": leaderboard[0]["f1"],
            "champion_pr_auc": leaderboard[0]["pr_auc"],
        })
        tracker.log_model(
            model=champion_model,
            artifact_path="champion_model",
            registered_name="FinGuard_AI_Champion"
        )
        tracker.end_run()

        # 7. Compile Markdown Reports
        compile_comparison_report(
            leaderboard=leaderboard,
            champion_name=champion_name,
            output_dir=reports_dir,
        )

        logger.info("Training pipeline executed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Training pipeline execution failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
