"""Clinical summaries extracted from the Lab02 notebook."""

from __future__ import annotations

import pandas as pd


def unique_patients_by_ethnicity_gender(patients: pd.DataFrame) -> pd.DataFrame:
    """Count unique patients by ethnicity and gender."""
    return (
        patients.groupby(["ETHNICITY", "GENDER"], observed=True)["Id"]
        .nunique()
        .reset_index(name="pacientes")
        .sort_values("pacientes", ascending=False)
    )


def encounters_per_patient(encounters: pd.DataFrame) -> pd.Series:
    """Count unique clinical encounters per patient."""
    return encounters.groupby("PATIENT", observed=True)["Id"].nunique()


def top_observation_codes(
    observations: pd.DataFrame,
    *,
    limit: int = 10,
) -> pd.DataFrame:
    """Return the most frequent observation codes with their descriptions."""
    return (
        observations.groupby(["CODE", "DESCRIPTION"], observed=True)
        .size()
        .reset_index(name="frecuencia")
        .sort_values("frecuencia", ascending=False)
        .head(limit)
    )


def systolic_blood_pressure_values(observations: pd.DataFrame) -> pd.DataFrame:
    """Return systolic blood pressure values in mmHg.

    The function filters LOINC `8480-6`. Null or non-numeric values in `VALUE`
    become missing values in `VALUE_num`.
    """
    systolic = observations.loc[
        observations["CODE"] == "8480-6",
        ["PATIENT", "VALUE"],
    ].copy()
    systolic["VALUE_num"] = pd.to_numeric(systolic["VALUE"], errors="coerce")

    return systolic


def patients_with_minimum_measurements(
    observations: pd.DataFrame,
    *,
    patient_column: str = "PATIENT",
    minimum: int = 3,
) -> int:
    """Count patients with at least `minimum` measurements."""
    measurements = observations.groupby(patient_column, observed=True).size()
    return int((measurements >= minimum).sum())


def observations_to_daily_wide(
    observations: pd.DataFrame,
    codes: list[str],
) -> pd.DataFrame:
    """Create a daily wide table for selected numeric observations.

    `VALUE` is interpreted as numeric in the units defined by each observation
    code. Null or non-numeric values become missing values before aggregation.
    Multiple measurements for the same patient, date and code are averaged.
    """
    selected = observations.loc[
        observations["CODE"].isin(codes),
        ["PATIENT", "DATE", "CODE", "VALUE"],
    ].copy()

    selected["VALUE"] = pd.to_numeric(selected["VALUE"], errors="coerce")
    selected["DATE"] = pd.to_datetime(selected["DATE"]).dt.date

    return selected.pivot_table(
        index=["PATIENT", "DATE"],
        columns="CODE",
        values="VALUE",
        aggfunc="mean",
        observed=True,
        sort=False,
    ).reset_index()


def repeated_daily_measurements(observations: pd.DataFrame) -> pd.Series:
    """Count repeated measurements per patient, day and observation code."""
    grouped = observations.groupby(["PATIENT", "DATE", "CODE"], observed=True).size()
    return grouped[grouped > 1]


def implausible_value_summary(
    wide_observations: pd.DataFrame,
    limits: dict[str, tuple[float, float]],
) -> pd.DataFrame:
    """Summarize values outside broad physiologic limits.

    Limits use the units represented by each code: blood pressure in mmHg,
    heart rate in beats/minute and respiratory rate in breaths/minute. Missing
    values are not counted as implausible.
    """
    rows: list[dict[str, float | int | str]] = []

    for code, (minimum, maximum) in limits.items():
        values = wide_observations[code]
        outside_range = (values < minimum) | (values > maximum)

        rows.append(
            {
                "CODE": code,
                "n_implausibles": int(outside_range.sum()),
                "porcentaje": float(outside_range.mean() * 100),
            }
        )

    return pd.DataFrame(rows)


def calculate_egfr_2021(
    creatinine_mg_dl: float,
    age_years: float,
    sex: str,
) -> float:
    """Calculate eGFR with the race-free CKD-EPI 2021 equation.

    Uses standardized serum creatinine in mg/dL, age in years and sex
    (`"female"` or `"male"`). Returns eGFR in mL/min/1.73 m². Reference:
    National Kidney Foundation, CKD-EPI Creatinine Equation (2021).
    """
    if creatinine_mg_dl <= 0:
        raise ValueError("creatinine_mg_dl must be greater than zero")
    if age_years <= 0:
        raise ValueError("age_years must be greater than zero")
    if sex not in {"female", "male"}:
        raise ValueError("sex must be female or male")

    if sex == "female":
        kappa = 0.7
        alpha = -0.241
        sex_factor = 1.012
    else:
        kappa = 0.9
        alpha = -0.302
        sex_factor = 1.0

    creatinine_ratio = creatinine_mg_dl / kappa

    egfr = (
        142
        * min(creatinine_ratio, 1) ** alpha
        * max(creatinine_ratio, 1) ** -1.200
        * 0.9938**age_years
        * sex_factor
    )

    return float(egfr)
