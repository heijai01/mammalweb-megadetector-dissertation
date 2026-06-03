"""Threshold analysis helpers for MegaDetector human filtering."""

from __future__ import annotations

import pandas as pd


def threshold_metrics(
    data: pd.DataFrame,
    score_column: str,
    actual_human_column: str,
    thresholds: list[float] | None = None,
) -> pd.DataFrame:
    """Calculate precision, recall, and error counts across confidence thresholds.

    `actual_human_column` should contain booleans where True means the image truly contains a human.
    The predicted positive class is "filter as human" when the MegaDetector score is >= threshold.
    """

    if thresholds is None:
        thresholds = [round(x / 100, 2) for x in range(0, 101, 5)]

    actual = data[actual_human_column].astype(bool)
    scores = data[score_column].astype(float)
    rows = []

    for threshold in thresholds:
        predicted = scores >= threshold
        tp = int((predicted & actual).sum())
        fp = int((predicted & ~actual).sum())
        fn = int((~predicted & actual).sum())
        tn = int((~predicted & ~actual).sum())

        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        false_positive_rate = fp / (fp + tn) if fp + tn else None
        false_negative_rate = fn / (fn + tp) if fn + tp else None

        rows.append(
            {
                "threshold": threshold,
                "true_positive": tp,
                "false_positive": fp,
                "false_negative": fn,
                "true_negative": tn,
                "precision": precision,
                "recall": recall,
                "false_positive_rate": false_positive_rate,
                "false_negative_rate": false_negative_rate,
            }
        )

    return pd.DataFrame(rows)


def add_human_filter_flag(
    data: pd.DataFrame,
    score_column: str,
    threshold: float,
    output_column: str = "would_filter_as_human",
) -> pd.DataFrame:
    """Return a copy with a boolean flag for the selected confidence threshold."""

    result = data.copy()
    result[output_column] = result[score_column].astype(float) >= threshold
    return result
