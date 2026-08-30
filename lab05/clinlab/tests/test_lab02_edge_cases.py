import pandas as pd
import pytest
from pandas.errors import MergeError

from clinlab.clinical import implausible_value_summary, observations_to_daily_wide
from clinlab.data import left_join_with_audit, missing_percentages
from clinlab.validation import before_birth_mask, duplicated_id_count, non_numeric_mask


def test_empty_observations_return_empty_missing_percentages() -> None:
    # Lab02 calcula faltantes por tabla; una tabla vacía debe devolver una serie vacía.
    empty_observations = pd.DataFrame()

    result = missing_percentages(empty_observations)

    assert result.empty


def test_all_nan_value_column_is_not_treated_as_non_numeric() -> None:
    # Lab02 distingue VALUE no numérico de valores faltantes reales.
    values = pd.Series([None, pd.NA, float("nan")])

    result = non_numeric_mask(values)

    assert result.tolist() == [False, False, False]


def test_visit_before_birth_is_flagged_from_malicious_cohort(
    malicious_cohort: pd.DataFrame,
) -> None:
    # Lab02 buscó incoherencias temporales entre START y BIRTHDATE.
    result = before_birth_mask(malicious_cohort)
    flagged_patients = malicious_cohort.loc[result, "PATIENT"].tolist()

    assert flagged_patients == ["p003"]


def test_duplicate_person_id_and_join_cardinality_are_flagged(
    malicious_cohort: pd.DataFrame,
) -> None:
    # Lab02 valida IDs únicos porque un merge many-to-one no debe multiplicar filas.
    left = pd.DataFrame({"person_id": ["p001", "p003"]})
    duplicated_people = malicious_cohort[["person_id", "BIRTHDATE"]]

    assert duplicated_id_count(malicious_cohort["person_id"]) == 1
    with pytest.raises(MergeError):
        left_join_with_audit(
            left,
            duplicated_people,
            left_on="person_id",
            right_on="person_id",
            validate="many_to_one",
        )


def test_sentinel_systolic_pressure_is_flagged_as_implausible(
    malicious_cohort: pd.DataFrame,
) -> None:
    # Lab02 revisa presión sistólica con límites amplios para detectar centinelas.
    wide = observations_to_daily_wide(malicious_cohort, ["8480-6"])

    result = implausible_value_summary(wide, {"8480-6": (40, 300)})

    assert result.loc[0, "n_implausibles"] == 1
    assert result.loc[0, "porcentaje"] == pytest.approx(25.0)
