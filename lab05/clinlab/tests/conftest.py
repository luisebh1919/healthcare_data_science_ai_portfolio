import pandas as pd
import pytest


@pytest.fixture
def malicious_cohort() -> pd.DataFrame:
    """Small cohort with duplicate ID, nulls, impossible date and sentinel value."""
    return pd.DataFrame(
        {
            "person_id": ["p001", "p002", "p003", "p003", "p004", "p005"],
            "Id": ["p001", "p002", "p003", "p003", "p004", "p005"],
            "PATIENT": ["p001", "p002", "p003", "p003", "p004", "p005"],
            "BIRTHDATE": pd.to_datetime(
                [
                    "1980-04-10",
                    "2012-08-20",
                    "1970-01-01",
                    "1970-01-01",
                    "1995-06-15",
                    "1965-02-02",
                ],
                utc=True,
            ),
            "DEATHDATE": pd.to_datetime(
                [None, None, None, None, None, None],
                utc=True,
            ),
            "START": pd.to_datetime(
                [
                    "2023-01-05",
                    "2023-02-10",
                    "1969-12-31",
                    "2023-03-03",
                    "2023-04-01",
                    "2023-05-12",
                ],
                utc=True,
            ),
            "DATE": pd.to_datetime(
                [
                    "2023-01-05",
                    "2023-02-10",
                    "1969-12-31",
                    "2023-03-03",
                    "2023-04-01",
                    "2023-05-12",
                ]
            ),
            "CODE": ["8480-6", "8480-6", "8480-6", "8462-4", "8867-4", "8480-6"],
            "DESCRIPTION": [
                "Systolic Blood Pressure",
                "Systolic Blood Pressure",
                "Systolic Blood Pressure",
                "Diastolic Blood Pressure",
                "Heart rate",
                "Systolic Blood Pressure",
            ],
            "VALUE": ["118", "110", "120", "85", None, "0"],
            "UNITS": ["mmHg", "mmHg", "mmHg", "mmHg", None, "mmHg"],
        }
    )
