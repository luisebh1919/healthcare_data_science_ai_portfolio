"""Small data transformations used by the clinical lab workflow."""

from __future__ import annotations

from collections.abc import Hashable
from typing import Literal

import pandas as pd


def missing_percentages(frame: pd.DataFrame) -> pd.Series:
    """Return the percentage of missing values in each column."""
    return (frame.isna().mean() * 100).round(2)


def memory_reduction_percent(before_mb: float, after_mb: float) -> float:
    """Calculate memory reduction from two measurements in MB."""
    if before_mb <= 0:
        raise ValueError("before_mb must be greater than zero")

    return (1 - after_mb / before_mb) * 100


def left_join_with_audit(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    left_on: Hashable,
    right_on: Hashable,
    validate: Literal[
        "one_to_one",
        "one_to_many",
        "many_to_one",
        "many_to_many",
        "1:1",
        "1:m",
        "m:1",
        "m:m",
    ],
    suffixes: tuple[str, str] = ("_left", "_right"),
) -> pd.DataFrame:
    """Run a left join and keep pandas' merge audit column."""
    return left.merge(
        right,
        left_on=left_on,
        right_on=right_on,
        how="left",
        validate=validate,
        indicator=True,
        suffixes=suffixes,
    )


def merge_indicator_percent(merge_column: pd.Series, value: str = "left_only") -> float:
    """Return the percentage of rows with a selected merge indicator value."""
    return float((merge_column == value).mean() * 100)
