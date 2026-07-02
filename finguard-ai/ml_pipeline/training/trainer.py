"""
ml_pipeline/training/trainer.py
───────────────────────────────
Tuning and training framework supporting Stratified 5-Fold Cross-Validation,
GridSearchCV, and RandomizedSearchCV. Includes fallbacks for XGBoost/LightGBM.
"""
import time
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)

# Fallback classifiers for environment flexibility
HAS_XGB = False
try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    from sklearn.ensemble import GradientBoostingClassifier as XGBClassifier
    logger.warning("xgboost not found. Substituting with sklearn GradientBoostingClassifier fallback.")

HAS_LGBM = False
try:
    from lightgbm import LGBMClassifier
    HAS_LGBM = True
except ImportError:
    from sklearn.ensemble import HistGradientBoostingClassifier as LGBMClassifier
    logger.warning("lightgbm not found. Substituting with sklearn HistGradientBoostingClassifier fallback.")


class ModelTrainer:
    """
    Manages grid searches and hyperparameter tuning across registered algorithms.
    """

    def __init__(self, random_state: int = 42) -> None:
        self.random_state = random_state
        self.cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=self.random_state)

    def get_search_space(self, model_name: str) -> Tuple[Any, Dict[str, Any]]:
        """
        Returns (EstimatorInstance, HyperparameterGrid) for the requested algorithm.
        """
        name = model_name.lower()

        if name == "logistic_regression":
            estimator = LogisticRegression(max_iter=1000, random_state=self.random_state, solver="liblinear")
            grid = {
                "C": [0.01, 0.1, 1.0, 10.0],
                "penalty": ["l2"],
            }
        elif name == "decision_tree":
            estimator = DecisionTreeClassifier(random_state=self.random_state)
            grid = {
                "max_depth": [5, 10, 15, None],
                "min_samples_split": [2, 5, 10],
            }
        elif name == "random_forest":
            estimator = RandomForestClassifier(random_state=self.random_state, n_jobs=1)
            grid = {
                "n_estimators": [50, 100],
                "max_depth": [10, 20, None],
            }
        elif name == "xgboost":
            if HAS_XGB:
                # Use standard XGBoost parameters
                estimator = XGBClassifier(random_state=self.random_state, eval_metric="logloss", n_jobs=1)
                grid = {
                    "n_estimators": [50, 100],
                    "max_depth": [3, 6],
                    "learning_rate": [0.05, 0.1],
                }
            else:
                # Fallback parameters
                estimator = XGBClassifier(random_state=self.random_state)
                grid = {
                    "n_estimators": [50, 100],
                    "max_depth": [3, 6],
                    "learning_rate": [0.05, 0.1],
                }
        elif name == "lightgbm":
            if HAS_LGBM:
                # Use standard LightGBM parameters
                estimator = LGBMClassifier(random_state=self.random_state, n_jobs=-1, verbose=-1)
                grid = {
                    "n_estimators": [50, 100],
                    "max_depth": [3, 6],
                    "learning_rate": [0.05, 0.1],
                }
            else:
                # Fallback parameters
                estimator = LGBMClassifier(random_state=self.random_state)
                grid = {
                    "max_iter": [50, 100],  # HistGradientBoosting uses max_iter instead of n_estimators
                    "max_depth": [3, 6],
                    "learning_rate": [0.05, 0.1],
                }
        else:
            raise ValueError(f"Unknown model name configuration: '{model_name}'")

        return estimator, grid

    def train_and_tune(
        self,
        model_name: str,
        X_train: pd.DataFrame,
        y_train: Union[pd.Series, np.ndarray],
    ) -> Tuple[Any, Dict[str, Any], float]:
        """
        Executes Grid Search Cross-Validation to tune parameters on the training dataset.

        Returns:
            (BestModelInstance, BestParametersDict, TuningTimeSeconds)
        """
        logger.info(f"Tuning hyperparameters for model: '{model_name}'...")
        estimator, grid = self.get_search_space(model_name)

        start_time = time.time()
        # Optimize using F1 Score since class distribution is highly imbalanced
        # search = GridSearchCV(
        #     estimator=estimator,
        #     param_grid=grid,
        #     cv=self.cv,
        #     scoring="f1",
        #     n_jobs=-1,
        #     refit=True,
        # )
        search=GridSearchCV(
            estimator=estimator,
            param_grid=grid,
            cv=self.cv,
            scoring="f1",
            n_jobs=1,
            refit=True,
        )
        search.fit(X_train, y_train)
        tuning_duration = time.time() - start_time

        logger.info(
            f"Tuning for '{model_name}' complete in {tuning_duration:.2f}s. "
            f"Best parameters: {search.best_params_}. Best F1: {search.best_score_:.4f}"
        )

        return search.best_estimator_, search.best_params_, tuning_duration
