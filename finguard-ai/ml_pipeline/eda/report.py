"""
ml_pipeline/eda/report.py
─────────────────────────
Compiles EDA statistical findings, correlations, quality issues, and outlier reports
into formatted Markdown and structured JSON summaries.
"""
from pathlib import Path
from typing import Any, Dict, Union

from ml_pipeline.utils.file_utils import save_json
from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)


class EDAReportCompiler:
    """
    Compiles analysis dictionaries into MD reports and JSON summaries.
    """

    def __init__(self, output_dir: Union[str, Path]) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def compile(self, analysis: Dict[str, Any]) -> None:
        """Writes JSON and Markdown summaries to the output directory."""
        json_path = self.output_dir / "eda_summary.json"
        md_path = self.output_dir / "eda_report.md"

        # 1. Save JSON (exclude full correlation matrix for sizing)
        summary_json = {
            "overview": analysis["overview"],
            "quality": {
                "duplicate_count": analysis["quality"]["duplicate_count"],
                "constant_columns": analysis["quality"]["constant_columns"],
            },
            "target": analysis["target"],
            "highly_correlated_pairs": analysis["correlations"]["highly_correlated_pairs"][:10],
            "top_outliers": self._get_top_outliers(analysis["outliers"]),
            "transaction_analysis": analysis["transaction_analysis"],
        }
        save_json(summary_json, json_path)

        # 2. Build Markdown
        md_content = self._build_markdown(analysis)
        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            logger.info(f"Successfully compiled EDA Markdown report at '{md_path}'")
        except Exception as e:
            logger.error(f"Error saving EDA Markdown report: {e}")
            raise

    def _get_top_outliers(self, outliers: Dict[str, Any], top_n: int = 5) -> List[Dict[str, Any]]:
        """Identifies columns with the highest percentage of IQR outliers."""
        outlier_list = []
        for col, info in outliers.items():
            outlier_list.append({
                "column": col,
                "iqr_percentage": info["iqr"]["outlier_percentage"],
                "iqr_count": info["iqr"]["outlier_count"],
            })
        outlier_list.sort(key=lambda x: x["iqr_percentage"], reverse=True)
        return outlier_list[:top_n]

    def _build_markdown(self, analysis: Dict[str, Any]) -> str:
        """Orchestrates markdown sections into a unified report."""
        overview = analysis["overview"]
        quality = analysis["quality"]
        target = analysis["target"]
        stats = analysis["statistics"]
        correlations = analysis["correlations"]
        outliers = analysis["outliers"]
        tx = analysis["transaction_analysis"]

        md = []
        md.append("# FinGuard AI – Exploratory Data Analysis (EDA) Report")
        md.append("")
        md.append("This document outlines statistical behaviors, structural quality details, correlation matrices, outlier ratios, and preprocessing recommendations for the transaction dataset.")
        md.append("")

        # ── OVERVIEW ──
        md.append("## 1. Dataset Overview")
        md.append("")
        md.append(f"- **Total Rows**: {overview['shape']['rows']:,}")
        md.append(f"- **Total Features**: {overview['total_features']:,}")
        md.append(f"- **Target Variable**: `{overview['target_variable']}`")
        md.append(f"- **Memory Footprint**: {overview['memory_usage_bytes'] / (1024*1024):.2f} MB")
        md.append("")

        # ── QUALITY ──
        md.append("## 2. Data Quality Audit")
        md.append("")
        md.append(f"- **Duplicate Rows**: {quality['duplicate_count']:,}")
        md.append(f"- **Constant Columns (Zero Variance)**: {len(quality['constant_columns'])} column(s)")
        if quality["constant_columns"]:
            md.append(f"  - Constant list: `{quality['constant_columns']}`")
        md.append("")

        # Null report table
        null_cols = [c for c, info in quality["missing_report"].items() if info["null_count"] > 0]
        if null_cols:
            md.append("### Columns with Missing Values")
            md.append("")
            md.append("| Column | Null Count | Null % |")
            md.append("| :--- | :--- | :--- |")
            for c in null_cols:
                meta = quality["missing_report"][c]
                md.append(f"| `{c}` | {meta['null_count']:,} | {meta['null_percentage']:.2f}% |")
            md.append("")
        else:
            md.append("- **Missing Values**: None. Clean dataset structure.")
            md.append("")

        # ── TARGET ──
        md.append("## 3. Target Imbalance Analysis")
        md.append("")
        md.append(f"- **Genuine Transactions**: {target['genuine_count']:,} ({target['counts'].get('0', {}).get('percentage', 0.0):.4f}%)")
        md.append(f"- **Fraudulent Transactions**: {target['fraud_count']:,} ({target['fraud_percentage']:.4f}%)")
        md.append(f"- **Class Imbalance Ratio**: 1 Fraud instance per {target['imbalance_ratio']:.1f} Genuine instances.")
        md.append("")

        # ── TRANSACTION STATS ──
        if tx:
            md.append("## 4. Transaction Specific Behaviors")
            md.append("")
            md.append("Comparison of amount profiles between class distributions:")
            md.append("")
            md.append("| Metric | Genuine Class | Fraudulent Class |")
            md.append("| :--- | :--- | :--- |")
            md.append(f"| **Mean Amount** | ${tx['amount']['genuine']['mean']:.2f} | ${tx['amount']['fraud']['mean']:.2f} |")
            md.append(f"| **Median Amount** | ${tx['amount']['genuine']['median']:.2f} | ${tx['amount']['fraud']['median']:.2f} |")
            md.append(f"| **Max Amount** | ${tx['amount']['genuine']['max']:.2f} | ${tx['amount']['fraud']['max']:.2f} |")
            md.append("")

        # ── CORRELATION ──
        md.append("## 5. Correlation Patterns")
        md.append("")
        high_corr = correlations["highly_correlated_pairs"]
        if high_corr:
            md.append("Top features exhibiting linear correlation strength ($|r| \\ge 0.5$):")
            md.append("")
            md.append("| Feature 1 | Feature 2 | Correlation ($r$) |")
            md.append("| :--- | :--- | :--- |")
            for pair in high_corr[:10]:
                md.append(f"| `{pair['feature_1']}` | `{pair['feature_2']}` | {pair['correlation']:.4f} |")
            md.append("")
        else:
            md.append("No linear feature pairs exceeded the threshold correlation ($|r| \\ge 0.5$).")
            md.append("")

        # ── OUTLIERS ──
        md.append("## 6. Outlier Analysis")
        md.append("")
        md.append("Features containing the highest ratio of outliers based on IQR boundaries (1.5 IQR rule):")
        md.append("")
        md.append("| Column | Outliers Count | Outlier % |")
        md.append("| :--- | :--- | :--- |")
        top_outliers = self._get_top_outliers(outliers, top_n=10)
        for out in top_outliers:
            md.append(f"| `{out['column']}` | {out['iqr_count']:,} | {out['iqr_percentage']:.2f}% |")
        md.append("")

        # ── KEY FINDINGS & SUGGESTIONS ──
        md.append("## 7. Key Findings & Synthesis")
        md.append("")
        md.append("### Key Findings")
        md.append("1. **Severe Imbalance Rate**: The minority class represents less than 0.2% of the dataset. Standard accuracy metrics will be misleading; models must be optimized using F1-Score, Recall, or Precision-Recall AUC.")
        md.append("2. **Scale Imbalance**: The transaction amount distribution exhibits massive right-hand skewness with rare massive transactions, while PCA features (V1-V28) are already zero-centered and scaled.")
        md.append("3. **Collinearity Check**: Most PCA components are orthogonal with zero correlation, but time and amount exhibit noticeable correlation with some PCA components.")
        md.append("")
        md.append("### Potential Modeling Risks")
        md.append("- **Class Collapsing**: Due to the severe imbalance, unweighted estimators will easily converge to predicting the majority class exclusively.")
        md.append("- **Sensitivity to Outliers**: High outlier ratios in V-features could distort linear estimators like Logistic Regression if not handled correctly.")
        md.append("")
        md.append("### Recommendations before Feature Engineering")
        md.append("- **Rescaling**: Apply `RobustScaler` on the `Amount` and `Time` features to minimize outlier sensitivity without distorting the data shape.")
        md.append("- **Sampling Strategies**: Implement Synthetic Minority Over-sampling Technique (SMOTE) or use classifier class weighting options (`class_weight='balanced'`) to adjust label loss updates.")
        md.append("- **Robust Estimators**: Prioritize tree-based models (Random Forest, XGBoost, LightGBM) which are robust against outliers and monotonic scaling discrepancies.")
        md.append("")

        return "\n".join(md)
