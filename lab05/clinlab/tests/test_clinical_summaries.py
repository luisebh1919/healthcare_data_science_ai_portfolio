import pandas as pd
import pytest

from clinlab.clinical import (
    encounters_per_patient,
    patients_with_minimum_measurements,
    repeated_daily_measurements,
    systolic_blood_pressure_values,
    top_observation_codes,
    unique_patients_by_ethnicity_gender,
)
from clinlab.data import merge_indicator_percent
from clinlab.validation import after_death_day_mask, encounters_with_patient_dates


def test_unique_patients_by_ethnicity_gender_counts_people_once() -> None:
    patients = pd.DataFrame(
        {
            "Id": ["p1", "p1", "p2", "p3"],
            "ETHNICITY": ["hispanic", "hispanic", "hispanic", "nonhispanic"],
            "GENDER": ["F", "F", "M", "F"],
        }
    )

    result = unique_patients_by_ethnicity_gender(patients)

    hispanic_f = result.loc[
        (result["ETHNICITY"] == "hispanic") & (result["GENDER"] == "F"),
        "pacientes",
    ].iloc[0]
    assert hispanic_f == 1


def test_encounters_per_patient_counts_unique_encounters() -> None:
    encounters = pd.DataFrame(
        {
            "PATIENT": ["p1", "p1", "p1", "p2"],
            "Id": ["e1", "e1", "e2", "e3"],
        }
    )

    result = encounters_per_patient(encounters)

    assert result.loc["p1"] == 2
    assert result.loc["p2"] == 1


def test_top_observation_codes_orders_by_frequency() -> None:
    observations = pd.DataFrame(
        {
            "CODE": ["8480-6", "8480-6", "8462-4", "8867-4"],
            "DESCRIPTION": [
                "Systolic Blood Pressure",
                "Systolic Blood Pressure",
                "Diastolic Blood Pressure",
                "Heart rate",
            ],
        }
    )

    result = top_observation_codes(observations, limit=2)

    assert result["CODE"].tolist() == ["8480-6", "8462-4"]
    assert result["frecuencia"].tolist() == [2, 1]


def test_systolic_blood_pressure_values_converts_only_selected_code() -> None:
    observations = pd.DataFrame(
        {
            "PATIENT": ["p1", "p1", "p2"],
            "CODE": ["8480-6", "8462-4", "8480-6"],
            "VALUE": ["120", "80", "not recorded"],
        }
    )

    result = systolic_blood_pressure_values(observations)

    assert result["PATIENT"].tolist() == ["p1", "p2"]
    assert result["VALUE_num"].iloc[0] == pytest.approx(120.0)
    assert pd.isna(result["VALUE_num"].iloc[1])


def test_patients_with_minimum_measurements_counts_longitudinal_coverage() -> None:
    observations = pd.DataFrame({"PATIENT": ["p1", "p1", "p1", "p2", "p2"]})

    result = patients_with_minimum_measurements(observations, minimum=3)

    assert result == 1


def test_repeated_daily_measurements_returns_only_repeated_groups() -> None:
    observations = pd.DataFrame(
        {
            "PATIENT": ["p1", "p1", "p1"],
            "DATE": ["2023-01-01", "2023-01-01", "2023-01-02"],
            "CODE": ["8480-6", "8480-6", "8480-6"],
        }
    )

    result = repeated_daily_measurements(observations)

    assert len(result) == 1
    assert result.iloc[0] == 2


def test_merge_indicator_percent_counts_left_only_rows() -> None:
    merge_column = pd.Series(["both", "left_only", "both", "left_only"])

    result = merge_indicator_percent(merge_column)

    assert result == pytest.approx(50.0)


def test_encounters_with_patient_dates_prepares_temporal_audit() -> None:
    encounters = pd.DataFrame(
        {"PATIENT": ["p1", "p2"], "START": ["2023-01-01", "2023-01-02"]}
    )
    patients = pd.DataFrame(
        {
            "Id": ["p1", "p2"],
            "BIRTHDATE": ["1980-01-01", "1990-01-01"],
            "DEATHDATE": [None, "2023-01-01"],
        }
    )

    result = encounters_with_patient_dates(encounters, patients)

    assert result["Id"].tolist() == ["p1", "p2"]
    assert str(result["START"].dt.tz) == "UTC"


def test_after_death_day_mask_ignores_same_day_visits() -> None:
    encounters = pd.DataFrame(
        {
            "START": pd.to_datetime(
                ["2023-01-01 12:00", "2023-01-02 08:00", "2023-01-03 08:00"],
                utc=True,
            ),
            "DEATHDATE": pd.to_datetime(["2023-01-01", "2023-01-01", None], utc=True),
        }
    )

    result = after_death_day_mask(encounters)

    assert result.tolist() == [False, True, False]
