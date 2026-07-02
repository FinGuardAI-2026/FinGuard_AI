# FinGuard AI – MLOps Experiment Tracking & Model Registry Documentation

This document describes the MLOps setup for FinGuard AI, explaining how to use MLflow to track parameters, monitor training history, inspect execution runs, and manage the Model Registry.

---

## 1. Local MLflow Server Setup

MLflow tracks all metrics, hyperparameters, performance plots, and registered models locally inside:
`ml_pipeline/experiments/mlruns`

### Launching the Experiment Dashboard (UI)

To launch the MLflow visualization web server, open a terminal at the project root folder and execute:

```bash
mlflow ui --backend-store-uri ml_pipeline/experiments/mlruns
```

Alternatively, if you run the command inside the `ml_pipeline/experiments/` folder:
```bash
mlflow ui
```

* **Web UI URL**: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 2. Tracking Details

Each run inside the **`FinGuard_AI_Fraud_Detection`** experiment logs the following structures:

### A. Parameters Logged
* **Model Parameters**: Grid Search parameters (e.g., `max_depth`, `n_estimators`, `C`, `learning_rate`).
* **Environment Parameters**: `random_state` (42), `balancing_strategy` (`smote` or `random_over_sampling`), `model_type` (e.g. `random_forest`).

### B. Metrics Logged
* **Performance Scores**: Accuracy, Precision, Recall, F1-Score, ROC-AUC, and PR-AUC.
* **Duration Metrics**: `tuning_time_s` (total tuning run length in seconds), `inference_time_per_sample_ms` (latency to score a single transaction).

### C. Artifacts Logged
Saved inside each run folder's `plots/` subfolder:
* `roc_curve_[model_name].png` (Receiver Operating Characteristic)
* `pr_curve_[model_name].png` (Precision-Recall Curve)
* `confusion_matrix_[model_name].png` (Confusion Matrix Heatmap)

---

## 3. Model Registry & Lifecycles

Model versions are registered in the MLflow Model Registry.

### A. Challenger Models
During the training loop, every tuned model is saved and registered as a **Challenger Model**:
* `FinGuard_Challenger_LOGISTIC_REGRESSION`
* `FinGuard_Challenger_DECISION_TREE`
* `FinGuard_Challenger_RANDOM_FOREST`
* `FinGuard_Challenger_XGBOOST`
* `FinGuard_Challenger_LIGHTGBM`

### B. Champion Model
Once all five models have completed evaluation, the orchestrator sorts them by F1-Score, identifies the winner, and registers it as:
* **`FinGuard_AI_Champion`** (Version 1, Version 2, etc.)

---

## 4. How to Compare Models in the UI

1. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.
2. Select the **`FinGuard_AI_Fraud_Detection`** experiment from the left pane.
3. Select the checkboxes next to the runs you wish to benchmark (e.g. compare XGBoost vs Random Forest).
4. Click **Compare** in the table header.
5. Review metrics (F1-score vs Inference Latency) in side-by-side lists, or create Scatter Plots comparing `inference_time_per_sample_ms` on the X-axis against `f1` on the Y-axis.
