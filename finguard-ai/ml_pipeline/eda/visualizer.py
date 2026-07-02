"""
ml_pipeline/eda/visualizer.py
─────────────────────────────
Generates high-resolution EDA charts (histograms, boxplots, violin plots,
density curves, and correlation heatmaps) saved as PNG files.
"""
from pathlib import Path
from typing import List, Union
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)


class EDAVisualizer:
    """
    Creates standardized charts for Exploratory Data Analysis.
    """

    def __init__(self, output_dir: Union[str, Path]) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Harmonious color palette: Blue for Genuine, Red for Fraud
        self.colors = {"genuine": "#3B82F6", "fraud": "#EF4444"}

    def plot_histograms(self, df: pd.DataFrame, columns: List[str]) -> None:
        """Saves a multi-panel histogram grid for the specified columns."""
        num_cols = len(columns)
        grid_size = int(np.ceil(np.sqrt(num_cols)))

        fig, axes = plt.subplots(grid_size, grid_size, figsize=(15, 12))
        axes = axes.flatten()

        for idx, col in enumerate(columns):
            ax = axes[idx]
            series = df[col].dropna()
            ax.hist(series, bins=50, color=self.colors["genuine"], alpha=0.75, edgecolor="none")
            ax.set_title(f"Distribution of {col}", fontsize=11, fontweight="bold")
            ax.set_xlabel("Value")
            ax.set_ylabel("Count")
            ax.grid(True, linestyle=":", alpha=0.5)

        # Deactivate unused axes
        for idx in range(num_cols, len(axes)):
            fig.delaxes(axes[idx])

        fig.suptitle("Feature Histograms Overview", fontsize=16, fontweight="bold")
        plt.tight_layout()
        out_path = self.output_dir / "histograms_grid.png"
        plt.savefig(out_path, dpi=300)
        plt.close()
        logger.info(f"Saved Histograms Grid to '{out_path}'")

    def plot_boxplots(self, df: pd.DataFrame, columns: List[str], target_col: str) -> None:
        """Saves boxplots comparing features grouped by target class."""
        if target_col not in df.columns:
            return

        num_cols = len(columns)
        grid_size = int(np.ceil(np.sqrt(num_cols)))

        fig, axes = plt.subplots(grid_size, grid_size, figsize=(15, 12))
        axes = axes.flatten()

        for idx, col in enumerate(columns):
            ax = axes[idx]

            # Separate classes
            g0 = df.loc[df[target_col] == 0, col].dropna()
            g1 = df.loc[df[target_col] == 1, col].dropna()

            box = ax.boxplot(
                [g0, g1],
                patch_artist=True,
                labels=["Genuine", "Fraud"],
                widths=0.6,
                showfliers=False,  # Keep clean by hiding extreme outliers
            )

            # Apply custom colors
            box["boxes"][0].set_facecolor(self.colors["genuine"])
            box["boxes"][0].set_alpha(0.6)
            box["boxes"][1].set_facecolor(self.colors["fraud"])
            box["boxes"][1].set_alpha(0.6)

            for median in box["medians"]:
                median.set(color="black", linewidth=2)

            ax.set_title(f"{col} by Class", fontsize=11, fontweight="bold")
            ax.set_ylabel("Value")
            ax.grid(True, linestyle=":", alpha=0.5)

        # Deactivate unused axes
        for idx in range(num_cols, len(axes)):
            fig.delaxes(axes[idx])

        fig.suptitle("Feature Boxplots by Class (Outliers Excluded)", fontsize=16, fontweight="bold")
        plt.tight_layout()
        out_path = self.output_dir / "boxplots_grid.png"
        plt.savefig(out_path, dpi=300)
        plt.close()
        logger.info(f"Saved Boxplots Grid to '{out_path}'")

    def plot_violin_plots(self, df: pd.DataFrame, columns: List[str], target_col: str) -> None:
        """Saves violin plots comparing distribution density by target class."""
        if target_col not in df.columns:
            return

        num_cols = len(columns)
        grid_size = int(np.ceil(np.sqrt(num_cols)))

        fig, axes = plt.subplots(grid_size, grid_size, figsize=(15, 12))
        axes = axes.flatten()

        for idx, col in enumerate(columns):
            ax = axes[idx]

            # Separate classes
            g0 = df.loc[df[target_col] == 0, col].dropna()
            g1 = df.loc[df[target_col] == 1, col].dropna()

            # Violin plot requires numeric array list
            parts = ax.violinplot(
                [g0, g1],
                showmeans=False,
                showmedians=True,
                showextrema=False,
            )

            # Customize body colors
            parts["bodies"][0].set_facecolor(self.colors["genuine"])
            parts["bodies"][0].set_edgecolor("black")
            parts["bodies"][0].set_alpha(0.6)

            parts["bodies"][1].set_facecolor(self.colors["fraud"])
            parts["bodies"][1].set_edgecolor("black")
            parts["bodies"][1].set_alpha(0.6)

            parts["cmedians"].set_color("black")
            parts["cmedians"].set_linewidth(2)

            ax.set_xticks([1, 2])
            ax.set_xticklabels(["Genuine", "Fraud"])
            ax.set_title(f"{col} Density Distribution", fontsize=11, fontweight="bold")
            ax.grid(True, linestyle=":", alpha=0.5)

        # Deactivate unused axes
        for idx in range(num_cols, len(axes)):
            fig.delaxes(axes[idx])

        fig.suptitle("Feature Violin Plots by Class", fontsize=16, fontweight="bold")
        plt.tight_layout()
        out_path = self.output_dir / "violin_plots_grid.png"
        plt.savefig(out_path, dpi=300)
        plt.close()
        logger.info(f"Saved Violin Plots Grid to '{out_path}'")

    def plot_density_plots(self, df: pd.DataFrame, columns: List[str], target_col: str) -> None:
        """Saves kernel density estimator (KDE) approximation curves by target class."""
        if target_col not in df.columns:
            return

        num_cols = len(columns)
        grid_size = int(np.ceil(np.sqrt(num_cols)))

        fig, axes = plt.subplots(grid_size, grid_size, figsize=(15, 12))
        axes = axes.flatten()

        for idx, col in enumerate(columns):
            ax = axes[idx]

            # Separate classes
            g0 = df.loc[df[target_col] == 0, col].dropna()
            g1 = df.loc[df[target_col] == 1, col].dropna()

            # Plot KDE estimation using pandas built-in plotter
            try:
                g0.plot(kind="kde", ax=ax, color=self.colors["genuine"], label="Genuine", lw=2)
                g1.plot(kind="kde", ax=ax, color=self.colors["fraud"], label="Fraud", lw=2)
            except Exception:
                # Fallback if density calculation fails due to singular matrix
                ax.hist(g0, bins=30, density=True, color=self.colors["genuine"], alpha=0.5, label="Genuine")
                ax.hist(g1, bins=30, density=True, color=self.colors["fraud"], alpha=0.5, label="Fraud")

            ax.set_title(f"{col} Kernel Density", fontsize=11, fontweight="bold")
            ax.set_xlabel("Value")
            ax.set_ylabel("Density")
            ax.legend(loc="upper right", fontsize=8)
            ax.grid(True, linestyle=":", alpha=0.5)

        # Deactivate unused axes
        for idx in range(num_cols, len(axes)):
            fig.delaxes(axes[idx])

        fig.suptitle("Feature Density Comparisons", fontsize=16, fontweight="bold")
        plt.tight_layout()
        out_path = self.output_dir / "density_plots_grid.png"
        plt.savefig(out_path, dpi=300)
        plt.close()
        logger.info(f"Saved Density Plots Grid to '{out_path}'")

    def plot_correlation_heatmap(self, corr_matrix_dict: dict) -> None:
        """Saves a heatmap plot of the correlation matrix."""
        # Convert dictionary back to pandas DataFrame
        df_corr = pd.DataFrame(corr_matrix_dict)
        if df_corr.empty:
            return

        fig, ax = plt.subplots(figsize=(12, 10))
        cax = ax.imshow(df_corr.values, cmap="coolwarm", vmin=-1.0, vmax=1.0)
        fig.colorbar(cax, fraction=0.046, pad=0.04)

        # Label ticks
        labels = df_corr.columns
        ax.set_xticks(np.arange(len(labels)))
        ax.set_yticks(np.arange(len(labels)))
        ax.set_xticklabels(labels, rotation=90, fontsize=8)
        ax.set_yticklabels(labels, fontsize=8)

        ax.set_title("Feature Correlation Heatmap (Pearson)", fontsize=14, fontweight="bold")
        plt.tight_layout()
        out_path = self.output_dir / "correlation_heatmap.png"
        plt.savefig(out_path, dpi=300)
        plt.close()
        logger.info(f"Saved Correlation Heatmap to '{out_path}'")
