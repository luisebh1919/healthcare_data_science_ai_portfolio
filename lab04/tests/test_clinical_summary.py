import pandas as pd
import pytest

from lab04.src.clinical_summary import median_age, validate_required_columns


def test_validate_required_columns_accepts_valid_dataframe():
    df = pd.DataFrame(
        {
            "patient_id": [1, 2],
            "age": [35, 58],
            "diagnosis": ["control", "case"],
        }
    )

    validate_required_columns(df, ["patient_id", "age", "diagnosis"])


def test_validate_required_columns_raises_for_one_missing_column():
    df = pd.DataFrame({"patient_id": [1, 2], "age": [35, 58]})

    with pytest.raises(ValueError, match="diagnosis"):
        validate_required_columns(df, ["patient_id", "age", "diagnosis"])


def test_validate_required_columns_raises_for_multiple_missing_columns():
    df = pd.DataFrame({"patient_id": [1, 2]})

    with pytest.raises(ValueError) as error:
        validate_required_columns(df, ["patient_id", "age", "diagnosis"])

    message = str(error.value)
    assert "age" in message
    assert "diagnosis" in message


def test_median_age_returns_age_median_as_float():
    df = pd.DataFrame({"edad": [20, 30, 40]})

    result = median_age(df)

    assert result == 30.0
    assert isinstance(result, float)


def test_median_age_raises_when_age_column_is_missing():
    df = pd.DataFrame({"patient_id": [1, 2, 3]})

    with pytest.raises(ValueError, match="edad"):
        median_age(df)
