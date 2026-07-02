"""
ml_pipeline/reports/report_generator.py
────────────────────────────────────────
Compiles the dictionary produced by DatasetInspector into a clean markdown summary
and a structured JSON metadata document.
"""
from pathlib import Path
from typing import Any, Dict, Union

from ml_pipeline.config.paths import paths
from ml_pipeline.utils.file_utils import save_json
from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """
    Formats dataset audit statistics into human-readable Markdown and structured JSON.
    """

    def __init__(self, output_dir: Union[str, Path] = None) -> None:
        self.output_dir = Path(output_dir) if output_dir else paths.reports_dir

    def generate(self, inspect_data: Dict[str, Any]) -> None:
        """
        Saves dataset_statistics.json and formats dataset_summary.md.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        json_path = self.output_dir / "dataset_statistics.json"
        md_path = self.output_dir / "dataset_summary.md"

        # 1. Save JSON
        save_json(inspect_data, json_path)

        # 2. Build Markdown
        md_content = self._build_markdown(inspect_data)

        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            logger.info(f"Successfully generated Markdown report at '{md_path}'")
        except Exception as e:
            logger.error(f"Error saving Markdown report at '{md_path}': {e}")
            raise

    def _build_markdown(self, data: Dict[str, Any]) -> str:
        """Constructs the markdown string from statistics dictionary."""
        shape = data.get("dataset_shape", {"rows": 0, "columns": 0})
        memory = data.get("memory_usage_mb", 0.0)
        duplicates = data.get("duplicate_rows", 0)
        target = data.get("target_column", "N/A")
        fraud_pct = data.get("fraud_percentage")
        class_dist = data.get("class_distribution") or {}

        # Title and Overview
        md = []
        md.append("# FinGuard AI – Dataset Profile Report")
        md.append("")
        md.append("This report lists telemetry profile results for the loaded transaction dataset.")
        md.append("")
        md.append("## Overview")
        md.append("")
        md.append(f"- **Total Rows**: {shape['rows']:,}")
        md.append(f"- **Total Columns**: {shape['columns']:,}")
        md.append(f"- **Memory Usage**: {memory:.2f} MB")
        md.append(f"- **Duplicate Rows**: {duplicates:,}")
        md.append(f"- **Target Column**: `{target}`")
        if fraud_pct is not None:
            md.append(f"- **Imbalance Rate (Fraud %)**: {fraud_pct:.4f}%")
        md.append("")

        # Class Distribution Table
        if class_dist:
            md.append("## Class Distribution")
            md.append("")
            md.append("| Class (Target Value) | Record Count | Percentage |")
            md.append("| :--- | :--- | :--- |")
            for cls_val, info in class_dist.items():
                label = "Fraudulent" if str(cls_val) in ("1", "1.0", "True", "true") else "Genuine"
                md.append(f"| `{cls_val}` ({label}) | {info['count']:,} | {info['percentage']:.4f}% |")
            md.append("")

        # Columns Metadata Table
        cols = data.get("columns", {})
        if cols:
            md.append("## Schema Details")
            md.append("")
            md.append("| Column Name | Data Type | Null Count | Null % | Unique Values |")
            md.append("| :--- | :--- | :--- | :--- | :--- |")
            for name, meta in cols.items():
                md.append(
                    f"| `{name}` | `{meta['dtype']}` | {meta['null_count']:,} | "
                    f"{meta['null_percentage']:.2f}% | {meta['unique_count']:,} |"
                )
            md.append("")

        # Numeric statistics summary table
        num_summary = data.get("numeric_summary", {})
        if num_summary:
            md.append("## Numeric Feature Statistics")
            md.append("")
            # Get stats keys
            first_col = list(num_summary.keys())[0]
            stat_keys = list(num_summary[first_col].keys()) # e.g. count, mean, std, min, 25%, 50%, 75%, max

            # Header row
            header = "| Statistic | " + " | ".join([f"`{c}`" for c in num_summary.keys()]) + " |"
            divider = "| :--- | " + " | ".join([":---" for _ in num_summary.keys()]) + " |"
            md.append(header)
            md.append(divider)

            for key in stat_keys:
                row_vals = []
                for col in num_summary.keys():
                    val = num_summary[col].get(key, 0.0)
                    row_vals.append(f"{val:,.4f}")
                md.append(f"| **{key}** | " + " | ".join(row_vals) + " |")
            md.append("")

        return "\n".join(md)
