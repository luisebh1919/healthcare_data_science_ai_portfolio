import pandas as pd
import pytest

from lab04.src.clinical_summary import validate_required_columns


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
