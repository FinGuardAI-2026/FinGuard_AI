"""
ml_pipeline/tests/test_eda.py
─────────────────────────────
Unit tests for the EDAAnalyzer component.
"""
import pytest
import pandas as pd
import numpy as np

from ml_pipeline.eda.analyzer import EDAAnalyzer


def test_eda_analyzer_output_structure():
    """Asserts that the analyzer returns a complete dictionary with expected sections."""
    df = pd.DataFrame({
        "Amount": [100.0, 200.0, 150.0],
        "V1": [0.5, -0.2, 0.1],
        "Class": [0, 0, 1],
    })

    analyzer = EDAAnalyzer(target_column="Class")
    results = analyzer.analyze(df)

    assert "overview" in results
    assert "quality" in results
    assert "statistics" in results
    assert "target" in results
    assert "correlations" in results
    assert "outliers" in results
    assert "transaction_analysis" in results

    # Check overview dimensions
    assert results["overview"]["shape"]["rows"] == 3
    assert results["overview"]["shape"]["columns"] == 3
    assert results["overview"]["total_features"] == 2


def test_eda_analyzer_outlier_counts():
    """Asserts that outliers are computed correctly via IQR/Z-score thresholds."""
    # Data with a clear extreme outlier
    df = pd.DataFrame({
        "V1": [1.0, 1.1, 1.05, 1.2, 1.15, 1.08, 1.12, 1.09, 100.0],  # 100.0 is an outlier
    })

    analyzer = EDAAnalyzer(target_column="Class")
    outliers = analyzer._analyze_outliers(df)

    assert "V1" in outliers
    assert outliers["V1"]["iqr"]["outlier_count"] == 1
    assert outliers["V1"]["z_score"]["outlier_count"] == 1


def test_eda_analyzer_correlation_matrix():
    """Asserts that Pearson correlations are calculated correctly and highly correlated pairs are flagged."""
    df = pd.DataFrame({
        "A": [1.0, 2.0, 3.0, 4.0],
        "B": [2.0, 4.0, 6.0, 8.0],  # Perfect positive correlation r = 1.0
        "C": [-1.0, -2.0, -3.0, -4.0],  # Perfect negative correlation r = -1.0
    })

    analyzer = EDAAnalyzer(target_column="Class")
    corrs = analyzer._analyze_correlations(df, threshold=0.8)

    assert len(corrs["highly_correlated_pairs"]) == 3  # A-B, A-C, B-C
    # Check perfect correlation values
    assert abs(corrs["correlation_matrix"]["A"]["B"] - 1.0) < 1e-9
    assert abs(corrs["correlation_matrix"]["A"]["C"] - (-1.0)) < 1e-9
