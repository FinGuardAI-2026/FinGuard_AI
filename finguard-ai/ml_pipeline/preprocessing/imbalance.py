"""
ml_pipeline/preprocessing/imbalance.py
──────────────────────────────────────
Compares and executes class-balancing strategies (SMOTE, RandomOverSampler, RandomUnderSampler).
Includes fallback pandas implementations if the 'imblearn' library is not installed.
"""
from typing import Any, Dict, Tuple
import pandas as pd
import numpy as np

from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import imbalanced-learn packages, flag if missing
HAS_IMBLEARN = False
try:
    from imblearn.over_sampling import SMOTE, RandomOverSampler
    from imblearn.under_sampling import RandomUnderSampler
    HAS_IMBLEARN = True
except ImportError:
    logger.warning("imbalanced-learn library not detected. SMOTE will be disabled; falling back to pandas-based ROS/RUS.")


class ImbalanceHandler:
    """
    Applies and evaluates resampling techniques on imbalanced targets.
    """

    def __init__(self, random_state: int = 42) -> None:
        self.random_state = random_state

    def resample_smote(self, X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """Applies SMOTE to oversample the minority class."""
        if not HAS_IMBLEARN:
            raise ImportError(
                "SMOTE requires the 'imbalanced-learn' package. "
                "Install it or run with Random Over Sampling fallback instead."
            )
        smote = SMOTE(random_state=self.random_state)
        X_res, y_res = smote.fit_resample(X, y)
        logger.info(f"SMOTE complete. Resampled shape: {X_res.shape}")
        return pd.DataFrame(X_res, columns=X.columns), pd.Series(y_res, name=y.name)

    def resample_ros(self, X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """Applies Random Over Sampling to match minority class counts to majority."""
        if HAS_IMBLEARN:
            ros = RandomOverSampler(random_state=self.random_state)
            X_res, y_res = ros.fit_resample(X, y)
            return pd.DataFrame(X_res, columns=X.columns), pd.Series(y_res, name=y.name)

        # Fallback pandas implementation
        logger.info("Running pandas-based Random Over Sampling...")
        majority_label = y.value_counts().idxmax()
        minority_label = y.value_counts().idxmin()

        df = X.copy()
        df[y.name] = y

        df_maj = df[df[y.name] == majority_label]
        df_min = df[df[y.name] == minority_label]

        df_min_over = df_min.sample(len(df_maj), replace=True, random_state=self.random_state)
        df_res = pd.concat([df_maj, df_min_over], axis=0).sample(frac=1.0, random_state=self.random_state)

        X_res = df_res.drop(columns=[y.name])
        y_res = df_res[y.name]
        logger.info(f"Pandas ROS complete. Resampled shape: {X_res.shape}")
        return X_res, y_res

    def resample_rus(self, X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """Applies Random Under Sampling to reduce majority class counts to match minority."""
        if HAS_IMBLEARN:
            rus = RandomUnderSampler(random_state=self.random_state)
            X_res, y_res = rus.fit_resample(X, y)
            return pd.DataFrame(X_res, columns=X.columns), pd.Series(y_res, name=y.name)

        # Fallback pandas implementation
        logger.info("Running pandas-based Random Under Sampling...")
        majority_label = y.value_counts().idxmax()
        minority_label = y.value_counts().idxmin()

        df = X.copy()
        df[y.name] = y

        df_maj = df[df[y.name] == majority_label]
        df_min = df[df[y.name] == minority_label]

        df_maj_under = df_maj.sample(len(df_min), replace=False, random_state=self.random_state)
        df_res = pd.concat([df_maj_under, df_min], axis=0).sample(frac=1.0, random_state=self.random_state)

        X_res = df_res.drop(columns=[y.name])
        y_res = df_res[y.name]
        logger.info(f"Pandas RUS complete. Resampled shape: {X_res.shape}")
        return X_res, y_res

    def compare_strategies(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Runs and measures target class distributions under different balancing options.
        """
        counts = y.value_counts()
        original_dist = {str(k): int(v) for k, v in counts.items()}

        comparison = {
            "original": {"shape": X.shape, "distribution": original_dist},
            "smote_available": HAS_IMBLEARN,
        }

        # Measure ROS
        _, y_ros = self.resample_ros(X, y)
        comparison["random_over_sampling"] = {
            "shape": (_, y_ros)[0].shape,
            "distribution": {str(k): int(v) for k, v in y_ros.value_counts().items()},
        }

        # Measure RUS
        _, y_rus = self.resample_rus(X, y)
        comparison["random_under_sampling"] = {
            "shape": (_, y_rus)[0].shape,
            "distribution": {str(k): int(v) for k, v in y_rus.value_counts().items()},
        }

        if HAS_IMBLEARN:
            _, y_smote = self.resample_smote(X, y)
            comparison["smote"] = {
                "shape": (_, y_smote)[0].shape,
                "distribution": {str(k): int(v) for k, v in y_smote.value_counts().items()},
            }

        return comparison

    def recommend_strategy(self, X: pd.DataFrame, y: pd.Series) -> str:
        """
        Suggests the best class balancing technique.

        - If imblearn is missing, defaults to ROS.
        - If dataset has very few minority cases (< 100), ROS is preferred over SMOTE
          to avoid generating noisy interpolated samples.
        - Otherwise, SMOTE is recommended.
        """
        if not HAS_IMBLEARN:
            return "random_over_sampling"

        minority_count = int(y.value_counts().min())
        if minority_count < 100:
            return "random_over_sampling"
        return "smote"
