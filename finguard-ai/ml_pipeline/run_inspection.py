"""
ml_pipeline/run_inspection.py
──────────────────────────────
CLI entry point to execute data loader validation and generate dataset reports.
"""
import sys
from pathlib import Path

# Add project root to path if needed, though local workspace import should suffice
sys.path.append(str(Path(__file__).resolve().parent.parent))

from ml_pipeline.preprocessing.data_loader import DataLoader
from ml_pipeline.preprocessing.dataset_inspector import DatasetInspector
from ml_pipeline.reports.report_generator import ReportGenerator
from ml_pipeline.utils.logger import get_logger

logger = get_logger("run_inspection")


def main() -> int:
    """Runs the loader, inspector, and report builder pipeline."""
    logger.info("Initializing FinGuard AI dataset analysis script...")

    try:
        # 1. Load raw dataset
        loader = DataLoader()
        df = loader.load_dataset()

        # 2. Extract profile inspection statistics
        inspector = DatasetInspector()
        stats = inspector.inspect(df)

        # 3. Write structured JSON and markdown summary reports
        generator = ReportGenerator()
        generator.generate(stats)

        logger.info("Pipeline executed successfully. Reports written to reports/ directory.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"FileNotFound Error: {e}")
        logger.error("Please place your raw CSV file under 'ml_pipeline/data/raw/transactions.csv'")
        return 1
    except ValueError as e:
        logger.error(f"Validation Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"An unexpected error occurred during execution: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
