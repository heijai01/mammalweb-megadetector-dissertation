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

    `actual_human_column` should identify whether the image truly contains a human.
    The predicted positive class is "filter as human" when the MegaDetector score is
    greater than or equal to the threshold.
    """

    if thresholds is None:
        thresholds = [round(x / 100, 2) for x in range(0, 101, 5)]

    actual = _as_bool_series(data[actual_human_column])
    scores = pd.to_numeric(data[score_column], errors="coerce")
    valid = scores.notna() & actual.notna()
    scores = scores[valid]
    actual = actual[valid].astype(bool)

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
                "n_images": int(len(scores)),
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
    result[output_column] = pd.to_numeric(result[score_column], errors="coerce") >= threshold
    return result


def _as_bool_series(values: pd.Series) -> pd.Series:
    """Convert common exported label values to booleans while preserving unknowns."""

    if values.dtype == bool:
        return values

    mapped = values.astype("string").str.strip().str.lower().map(
        {
            "true": True,
            "t": True,
            "yes": True,
            "y": True,
            "1": True,
            "human": True,
            "contains_human": True,
            "false": False,
            "f": False,
            "no": False,
            "n": False,
            "0": False,
            "not_human": False,
            "animal": False,
            "empty": False,
        }
    )
    return mapped
