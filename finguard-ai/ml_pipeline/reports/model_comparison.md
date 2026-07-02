# FinGuard AI – Model Performance Comparison

A benchmarking run comparing five classification models trained using Stratified K-Fold CV:

| Model Name | F1-Score | Recall | Precision | Accuracy | ROC-AUC | PR-AUC | Tuning Time | Latency (Per Sample) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `decision_tree` | 0.0116 | 0.1224 | 0.0061 | 0.9641 | 0.5446 | 0.0197 | 11.09s | 0.0001ms |
| `lightgbm` | 0.0100 | 0.4796 | 0.0051 | 0.8372 | 0.7325 | 0.0105 | 9.15s | 0.0010ms |
| `xgboost` | 0.0095 | 0.4184 | 0.0048 | 0.8501 | 0.7184 | 0.0057 | 28.97s | 0.0025ms |
| `random_forest` | 0.0087 | 0.0918 | 0.0045 | 0.9638 | 0.5711 | 0.0034 | 101.90s | 0.0045ms |
| `logistic_regression` | 0.0037 | 0.4898 | 0.0018 | 0.5417 | 0.5230 | 0.0019 | 2.81s | 0.0001ms |

### Champion Recommendation
- **Champion Model Selected**: `DECISION_TREE`
