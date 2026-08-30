import pandas as pd

from clinlab.validation import duplicated_id_count, non_numeric_mask


def test_duplicated_id_count_counts_repeated_patient_ids() -> None:
    ids = pd.Series(["p1", "p2", "p1", "p3", "p2"])

    assert duplicated_id_count(ids) == 2


def test_duplicated_id_count_returns_zero_for_unique_ids() -> None:
    ids = pd.Series(["p1", "p2", "p3"])

    assert duplicated_id_count(ids) == 0


def test_non_numeric_mask_marks_text_values_but_not_numbers_or_nulls() -> None:
    values = pd.Series(["120", "Never smoked tobacco", None, "98.5"])

    result = non_numeric_mask(values)

    assert result.tolist() == [False, True, False, False]


def test_non_numeric_mask_treats_blank_strings_as_missing() -> None:
    values = pd.Series(["", "   ", None, "No", "42"])

    result = non_numeric_mask(values)

    assert result.tolist() == [False, False, False, True, False]
