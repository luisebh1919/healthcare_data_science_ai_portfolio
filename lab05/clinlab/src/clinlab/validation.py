"""Validation helpers for patient and encounter data."""

from __future__ import annotations

from typing import cast

import pandas as pd


def duplicated_id_count(ids: pd.Series) -> int:
    """Count duplicated identifiers, ignoring the first occurrence."""
    return int(ids.duplicated().sum())


def non_numeric_mask(values: pd.Series) -> pd.Series:
    """Mark non-blank values that cannot be converted to numbers."""
    numeric_values = pd.to_numeric(values, errors="coerce")
    text_values = values.astype("string")
    has_content = text_values.str.strip().ne("") & values.notna()

    return numeric_values.isna() & has_content


def encounters_with_patient_dates(
    encounters: pd.DataFrame,
    patients: pd.DataFrame,
) -> pd.DataFrame:
    """Attach patient birth and death dates to encounters."""
    patient_dates = patients[["Id", "BIRTHDATE", "DEATHDATE"]].copy()
    patient_dates["BIRTHDATE"] = pd.to_datetime(patient_dates["BIRTHDATE"], utc=True)
    patient_dates["DEATHDATE"] = pd.to_datetime(patient_dates["DEATHDATE"], utc=True)

    encounter_dates = encounters[["PATIENT", "START"]].copy()
    encounter_dates["START"] = pd.to_datetime(encounter_dates["START"], utc=True)

    return encounter_dates.merge(
        patient_dates,
        left_on="PATIENT",
        right_on="Id",
        how="left",
        validate="many_to_one",
    )


def before_birth_mask(encounters_with_dates: pd.DataFrame) -> pd.Series:
    """Mark encounters that start before the patient's birth date."""
    return encounters_with_dates["START"] < encounters_with_dates["BIRTHDATE"]


def after_death_day_mask(encounters_with_dates: pd.DataFrame) -> pd.Series:
    """Mark encounters after the recorded death day.

    `DEATHDATE` is interpreted at day precision. Null death dates are treated as
    patients without recorded death and are not flagged.
    """
    death_dates = encounters_with_dates["DEATHDATE"]
    start_days = encounters_with_dates["START"].dt.date
    death_days = death_dates.dt.date

    mask = death_dates.notna() & (start_days > death_days)
    return cast(pd.Series, mask)
