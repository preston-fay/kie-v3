"""
KIE Statistical Analyzer

Performs statistical analysis on data to detect patterns,
outliers, correlations, and significant differences.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class StatisticalResult:
    """Result of a statistical test."""
    test_name: str
    statistic: float
    p_value: Optional[float]
    is_significant: bool
    interpretation: str
    details: Dict[str, Any]


class StatisticalAnalyzer:
    """
    Performs statistical analysis on data.

    Provides methods for:
    - Descriptive statistics
    - Outlier detection
    - Trend analysis
    - Correlation analysis
    - Distribution analysis
    - Variance analysis
    """

    def __init__(self, significance_level: float = 0.05):
        """
        Initialize analyzer.

        Args:
            significance_level: P-value threshold for significance (default 0.05)
        """
        self.significance_level = significance_level

    def describe(self, series: pd.Series) -> Dict[str, Any]:
        """
        Get comprehensive descriptive statistics.

        Args:
            series: Numeric series to analyze

        Returns:
            Dict with statistics
        """
        if not pd.api.types.is_numeric_dtype(series):
            return {"error": "Series must be numeric"}

        clean = series.dropna()
        if len(clean) == 0:
            return {"error": "No valid data"}

        stats = {
            "count": len(clean),
            "mean": float(clean.mean()),
            "median": float(clean.median()),
            "std": float(clean.std()),
            "min": float(clean.min()),
            "max": float(clean.max()),
            "range": float(clean.max() - clean.min()),
            "q25": float(clean.quantile(0.25)),
            "q75": float(clean.quantile(0.75)),
            "iqr": float(clean.quantile(0.75) - clean.quantile(0.25)),
            "skewness": float(clean.skew()),
            "kurtosis": float(clean.kurtosis()),
            "cv": float(clean.std() / clean.mean()) if clean.mean() != 0 else None,
        }

        # Add interpretation
        if abs(stats["skewness"]) < 0.5:
            stats["distribution"] = "approximately symmetric"
        elif stats["skewness"] > 0:
            stats["distribution"] = "right-skewed (positive)"
        else:
            stats["distribution"] = "left-skewed (negative)"

        return stats

    def detect_outliers(
        self,
        series: pd.Series,
        method: str = "iqr",
        threshold: float = 1.5,
    ) -> Dict[str, Any]:
        """
        Detect outliers in a numeric series.

        Args:
            series: Numeric series to analyze
            method: "iqr" (interquartile range) or "zscore"
            threshold: IQR multiplier or z-score threshold

        Returns:
            Dict with outlier information
        """
        clean = series.dropna()

        if method == "iqr":
            q1 = clean.quantile(0.25)
            q3 = clean.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

            outliers = clean[(clean < lower_bound) | (clean > upper_bound)]
            lower_outliers = clean[clean < lower_bound]
            upper_outliers = clean[clean > upper_bound]

        elif method == "zscore":
            mean = clean.mean()
            std = clean.std()
            z_scores = (clean - mean) / std if std > 0 else pd.Series([0] * len(clean))

            outliers = clean[abs(z_scores) > threshold]
            lower_bound = mean - threshold * std
            upper_bound = mean + threshold * std
            lower_outliers = clean[z_scores < -threshold]
            upper_outliers = clean[z_scores > threshold]

        else:
            raise ValueError(f"Unknown method: {method}")

        return {
            "method": method,
            "threshold": threshold,
            "lower_bound": float(lower_bound),
            "upper_bound": float(upper_bound),
            "total_outliers": len(outliers),
            "lower_outliers": len(lower_outliers),
            "upper_outliers": len(upper_outliers),
            "outlier_percentage": float(len(outliers) / len(clean) * 100),
            "outlier_indices": outliers.index.tolist(),
            "outlier_values": outliers.values.tolist(),
        }

    def analyze_trend(
        self,
        values: List[float],
        periods: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze trend in sequential data.

        Args:
            values: Sequential values
            periods: Optional period labels

        Returns:
            Dict with trend analysis
        """
        if len(values) < 2:
            return {"error": "Need at least 2 values"}

        arr = np.array(values)
        n = len(arr)
        x = np.arange(n)

        # Linear regression
        slope, intercept = np.polyfit(x, arr, 1)

        # Calculate R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((arr - y_pred) ** 2)
        ss_tot = np.sum((arr - np.mean(arr)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Calculate changes
        total_change = arr[-1] - arr[0]
        pct_change = (total_change / arr[0] * 100) if arr[0] != 0 else 0

        # Period-over-period changes
        changes = np.diff(arr)
        avg_change = np.mean(changes)
        pct_changes = []
        for i in range(len(arr) - 1):
            if arr[i] != 0:
                pct_changes.append((arr[i + 1] - arr[i]) / arr[i] * 100)
            else:
                pct_changes.append(0)

        # Determine trend direction
        if slope > 0 and r_squared > 0.5:
            direction = "increasing"
        elif slope < 0 and r_squared > 0.5:
            direction = "decreasing"
        elif r_squared < 0.3:
            direction = "no clear trend"
        else:
            direction = "stable"

        # Detect volatility
        volatility = np.std(pct_changes) if pct_changes else 0

        return {
            "direction": direction,
            "slope": float(slope),
            "intercept": float(intercept),
            "r_squared": float(r_squared),
            "start_value": float(arr[0]),
            "end_value": float(arr[-1]),
            "total_change": float(total_change),
            "pct_change": float(pct_change),
            "avg_period_change": float(avg_change),
            "volatility": float(volatility),
            "min_value": float(arr.min()),
            "max_value": float(arr.max()),
            "min_period": int(np.argmin(arr)),
            "max_period": int(np.argmax(arr)),
        }

    def analyze_correlation(
        self,
        x: pd.Series,
        y: pd.Series,
        method: str = "pearson",
    ) -> Dict[str, Any]:
        """
        Analyze correlation between two variables.

        Args:
            x: First variable
            y: Second variable
            method: "pearson", "spearman", or "kendall"

        Returns:
            Dict with correlation analysis
        """
        # Align and clean data
        combined = pd.DataFrame({"x": x, "y": y}).dropna()

        if len(combined) < 3:
            return {"error": "Need at least 3 data points"}

        # Calculate correlation
        correlation = combined["x"].corr(combined["y"], method=method)

        # Interpret strength
        abs_corr = abs(correlation)
        if abs_corr >= 0.8:
            strength = "very strong"
        elif abs_corr >= 0.6:
            strength = "strong"
        elif abs_corr >= 0.4:
            strength = "moderate"
        elif abs_corr >= 0.2:
            strength = "weak"
        else:
            strength = "negligible"

        direction = "positive" if correlation > 0 else "negative"

        return {
            "method": method,
            "correlation": float(correlation),
            "strength": strength,
            "direction": direction if abs_corr >= 0.2 else "none",
            "n_observations": len(combined),
            "interpretation": f"{strength} {direction} correlation"
            if abs_corr >= 0.2
            else "no meaningful correlation",
        }

    def analyze_distribution(
        self,
        series: pd.Series,
        n_bins: int = 10,
    ) -> Dict[str, Any]:
        """
        Analyze the distribution of a numeric series.

        Args:
            series: Numeric series to analyze
            n_bins: Number of bins for histogram

        Returns:
            Dict with distribution analysis
        """
        clean = series.dropna()

        if len(clean) < 10:
            return {"error": "Need at least 10 data points"}

        # Basic stats
        stats = self.describe(series)

        # Histogram
        counts, bin_edges = np.histogram(clean, bins=n_bins)
        total = counts.sum()
        frequencies = (counts / total * 100).tolist()

        # Find mode bin
        mode_idx = np.argmax(counts)
        mode_range = (float(bin_edges[mode_idx]), float(bin_edges[mode_idx + 1]))

        # Concentration
        top_3_bins = sorted(range(len(counts)), key=lambda i: counts[i], reverse=True)[
            :3
        ]
        top_3_pct = sum(frequencies[i] for i in top_3_bins)

        return {
            "n_observations": len(clean),
            "n_bins": n_bins,
            "bin_edges": [float(e) for e in bin_edges],
            "frequencies": frequencies,
            "mode_range": mode_range,
            "top_3_bins_pct": float(top_3_pct),
            "is_concentrated": top_3_pct > 60,
            **stats,
        }

    def compare_groups(
        self,
        data: pd.DataFrame,
        value_column: str,
        group_column: str,
    ) -> Dict[str, Any]:
        """
        Compare a metric across groups.

        Args:
            data: DataFrame with data
            value_column: Column with values to compare
            group_column: Column with group labels

        Returns:
            Dict with group comparison
        """
        groups = data.groupby(group_column)[value_column]

        group_stats = {}
        for name, group in groups:
            group_stats[str(name)] = {
                "count": len(group),
                "mean": float(group.mean()),
                "median": float(group.median()),
                "std": float(group.std()),
                "sum": float(group.sum()),
            }

        # Calculate totals and shares
        total = sum(s["sum"] for s in group_stats.values())
        for name, stats in group_stats.items():
            stats["share"] = float(stats["sum"] / total * 100) if total > 0 else 0

        # Find leader
        sorted_groups = sorted(
            group_stats.items(), key=lambda x: x[1]["sum"], reverse=True
        )
        leader = sorted_groups[0][0] if sorted_groups else None
        leader_share = sorted_groups[0][1]["share"] if sorted_groups else 0

        # Check concentration (Herfindahl index)
        hhi = sum((s["share"] / 100) ** 2 for s in group_stats.values()) * 10000

        return {
            "n_groups": len(group_stats),
            "groups": group_stats,
            "leader": leader,
            "leader_share": float(leader_share),
            "total": float(total),
            "hhi": float(hhi),
            "is_concentrated": hhi > 2500,  # HHI > 2500 indicates high concentration
            "concentration_level": "high"
            if hhi > 2500
            else "moderate"
            if hhi > 1500
            else "low",
        }

    def detect_significant_changes(
        self,
        values: List[float],
        threshold_pct: float = 10.0,
    ) -> List[Dict[str, Any]]:
        """
        Detect significant period-over-period changes.

        Args:
            values: Sequential values
            threshold_pct: Percentage change to flag as significant

        Returns:
            List of significant changes
        """
        changes = []

        for i in range(1, len(values)):
            if values[i - 1] != 0:
                pct_change = (values[i] - values[i - 1]) / values[i - 1] * 100
                if abs(pct_change) >= threshold_pct:
                    changes.append(
                        {
                            "period": i,
                            "from_value": float(values[i - 1]),
                            "to_value": float(values[i]),
                            "absolute_change": float(values[i] - values[i - 1]),
                            "pct_change": float(pct_change),
                            "direction": "increase" if pct_change > 0 else "decrease",
                        }
                    )

        return changes

    def calculate_growth_metrics(
        self,
        values: List[float],
        periods: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate various growth metrics.

        Args:
            values: Sequential values
            periods: Optional period labels

        Returns:
            Dict with growth metrics
        """
        if len(values) < 2:
            return {"error": "Need at least 2 values"}

        arr = np.array(values)

        # Simple growth
        total_growth = (arr[-1] - arr[0]) / arr[0] * 100 if arr[0] != 0 else 0

        # Compound annual growth rate (CAGR)
        n_periods = len(arr) - 1
        if arr[0] > 0 and arr[-1] > 0:
            cagr = ((arr[-1] / arr[0]) ** (1 / n_periods) - 1) * 100
        else:
            cagr = None

        # Average growth rate
        period_changes = []
        for i in range(1, len(arr)):
            if arr[i - 1] != 0:
                period_changes.append((arr[i] - arr[i - 1]) / arr[i - 1] * 100)

        avg_growth = np.mean(period_changes) if period_changes else 0

        # Momentum (recent vs earlier growth)
        if len(arr) >= 4:
            mid = len(arr) // 2
            early_growth = (arr[mid] - arr[0]) / arr[0] * 100 if arr[0] != 0 else 0
            late_growth = (arr[-1] - arr[mid]) / arr[mid] * 100 if arr[mid] != 0 else 0
            momentum = "accelerating" if late_growth > early_growth else "decelerating"
        else:
            momentum = "insufficient data"

        return {
            "total_growth_pct": float(total_growth),
            "cagr": float(cagr) if cagr is not None else None,
            "avg_period_growth_pct": float(avg_growth),
            "n_periods": n_periods,
            "momentum": momentum,
            "start_value": float(arr[0]),
            "end_value": float(arr[-1]),
        }
