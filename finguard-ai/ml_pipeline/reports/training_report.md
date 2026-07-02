# FinGuard AI – Training and Hyperparameter Tuning Report

## Cross-Validation Design
- **Folds**: Stratified 5-Fold Cross Validation
- **Optimizing Score Metric**: F1-Score
- **Minority Resampling**: SMOTE (or ROS fallback)

## Tuned Model Summary List

### Model: `decision_tree`
- **Best Parameters**: `{'max_depth': None, 'min_samples_split': 2}`
- **F1 Score**: 0.0116
- **Recall Score (Sensitivity)**: 0.1224
- **Precision Score**: 0.0061
- **PR-AUC**: 0.0197
- **Tuning Duration**: 11.09 seconds

### Model: `lightgbm`
- **Best Parameters**: `{'learning_rate': 0.1, 'max_depth': 6, 'n_estimators': 100}`
- **F1 Score**: 0.0100
- **Recall Score (Sensitivity)**: 0.4796
- **Precision Score**: 0.0051
- **PR-AUC**: 0.0105
- **Tuning Duration**: 9.15 seconds

### Model: `xgboost`
- **Best Parameters**: `{'learning_rate': 0.1, 'max_depth': 6, 'n_estimators': 100}`
- **F1 Score**: 0.0095
- **Recall Score (Sensitivity)**: 0.4184
- **Precision Score**: 0.0048
- **PR-AUC**: 0.0057
- **Tuning Duration**: 28.97 seconds

### Model: `random_forest`
- **Best Parameters**: `{'max_depth': 20, 'n_estimators': 50}`
- **F1 Score**: 0.0087
- **Recall Score (Sensitivity)**: 0.0918
- **Precision Score**: 0.0045
- **PR-AUC**: 0.0034
- **Tuning Duration**: 101.90 seconds

### Model: `logistic_regression`
- **Best Parameters**: `{'C': 1.0, 'penalty': 'l2'}`
- **F1 Score**: 0.0037
- **Recall Score (Sensitivity)**: 0.4898
- **Precision Score**: 0.0018
- **PR-AUC**: 0.0019
- **Tuning Duration**: 2.81 seconds

## Champion Summary Profile
- **Model Type**: `decision_tree`
- **F1-Score**: 0.0116
- **PR-AUC**: 0.0197
- **Average Prediction Latency**: 0.0001 milliseconds

### Recommendations for Production Deployment
1. **Latency Budgets**: Choose models like Logistic Regression or LightGBM if sub-millisecond execution times are mandated.
2. **Performance Champions**: If F1/Recall metrics are prioritized to detect maximum fraud occurrences, Ensemble Models (Random Forest or XGBoost) represent the top candidates.
