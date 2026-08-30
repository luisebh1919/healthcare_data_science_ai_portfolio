import pandas as pd
import pytest

from clinlab.data import memory_reduction_percent, missing_percentages


def test_missing_percentages_counts_missing_values_by_column() -> None:
    frame = pd.DataFrame(
        {
            "BIRTHDATE": ["2001-01-01", None, "1990-05-10", None],
            "DEATHDATE": [None, None, "2020-03-01", None],
        }
    )

    result = missing_percentages(frame)

    assert result["BIRTHDATE"] == pytest.approx(50.0)
    assert result["DEATHDATE"] == pytest.approx(75.0)


def test_missing_percentages_empty_frame_returns_empty_series() -> None:
    frame = pd.DataFrame()

    result = missing_percentages(frame)

    assert result.empty


def test_memory_reduction_percent_calculates_drop_from_baseline() -> None:
    result = memory_reduction_percent(before_mb=100.0, after_mb=25.0)

    assert result == pytest.approx(75.0)


def test_memory_reduction_percent_rejects_non_positive_baseline() -> None:
    with pytest.raises(ValueError):
        memory_reduction_percent(before_mb=0.0, after_mb=25.0)
