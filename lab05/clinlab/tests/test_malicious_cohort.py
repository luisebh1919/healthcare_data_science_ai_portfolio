import pandas as pd


def test_malicious_cohort_has_expected_size(malicious_cohort: pd.DataFrame) -> None:
    assert len(malicious_cohort) == 6
