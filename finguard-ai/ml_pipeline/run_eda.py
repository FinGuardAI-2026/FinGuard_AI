"""
ml_pipeline/run_eda.py
───────────────────────
Executes the full Exploratory Data Analysis (EDA) pipeline, creating charts
and compile markdown/JSON reports.
"""
import sys
from pathlib import Path

# Add project root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from ml_pipeline.preprocessing.data_loader import DataLoader
from ml_pipeline.eda.analyzer import EDAAnalyzer
from ml_pipeline.eda.visualizer import EDAVisualizer
from ml_pipeline.eda.report import EDAReportCompiler
from ml_pipeline.utils.logger import get_logger

logger = get_logger("run_eda")


def main() -> int:
    """Orchestrates loading, analyzing, visualising, and reporting EDA details."""
    logger.info("Initializing EDA Pipeline...")

    # Define output locations
    reports_dir = Path("ml_pipeline/reports")
    figures_dir = reports_dir / "figures"
    reports_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load Dataset
        loader = DataLoader()
        df = loader.load_dataset()

        # Determine target column dynamically
        # Standard Credit Card dataset has 'Class'; FinGuard default is 'is_fraud'
        target_col = "Class" if "Class" in df.columns else "is_fraud"
        logger.info(f"Target column detected as: '{target_col}'")

        # 2. Run statistical profile calculations
        analyzer = EDAAnalyzer(target_column=target_col)
        analysis_data = analyzer.analyze(df)

        # 3. Choose a subset of columns for plotting grids
        # (avoid plotting all 30+ columns for scalability/memory limits)
        all_numeric = [
            c for c in df.select_dtypes(include=["number"]).columns
            if c != target_col
        ]
        # Choose V1-V4, Amount, Time if they exist, or default to first 6 numeric features
        candidates = ["Time", "Amount", "V1", "V2", "V3", "V4", "V10", "V11", "V12", "V14", "V17"]
        plot_cols = [c for c in candidates if c in all_numeric]
        if not plot_cols:
            plot_cols = all_numeric[:6]

        logger.info(f"Selecting features for visualization: {plot_cols}")

        # 4. Generate distribution, boxplot, density, and heatmap visualizations
        visualizer = EDAVisualizer(output_dir=figures_dir)
        visualizer.plot_histograms(df, plot_cols)
        visualizer.plot_boxplots(df, plot_cols, target_col=target_col)
        visualizer.plot_violin_plots(df, plot_cols, target_col=target_col)
        visualizer.plot_density_plots(df, plot_cols, target_col=target_col)

        # Build correlation heatmap using correlation matrix dictionary
        corr_matrix = analysis_data["correlations"]["correlation_matrix"]
        visualizer.plot_correlation_heatmap(corr_matrix)

        # 5. Compile reports
        compiler = EDAReportCompiler(output_dir=reports_dir)
        compiler.compile(analysis_data)

        logger.info("EDA Pipeline completed successfully. Output files saved in 'ml_pipeline/reports/'")
        return 0

    except FileNotFoundError as e:
        logger.error(f"FileNotFound Error: {e}")
        logger.error("Please place your raw CSV file under 'ml_pipeline/data/raw/transactions.csv'")
        return 1
    except ValueError as e:
        logger.error(f"Validation Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"EDA pipeline execution failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
