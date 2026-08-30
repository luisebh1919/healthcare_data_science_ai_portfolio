import pytest

from clinlab.clinical import calculate_egfr_2021


@pytest.mark.parametrize(
    ("creatinine_mg_dl", "age_years", "sex", "expected_egfr"),
    [
        (0.5, 25, "female", 133.401441883410),
        (0.8, 40, "male", 114.735048231263),
        (1.0, 50, "female", 68.633496658801),
        (1.2, 60, "male", 69.231127567482),
        (2.0, 70, "female", 26.380315105832),
        (3.0, 75, "male", 21.001885226118),
        (4.5, 80, "female", 9.368086262813),
        (6.0, 85, "male", 8.590376727513),
        (0.6, 30, "female", 123.757864121642),
        (0.9, 35, "male", 114.222872769349),
    ],
)
def test_calculate_egfr_2021_matches_nkf_equation(
    creatinine_mg_dl: float,
    age_years: float,
    sex: str,
    expected_egfr: float,
) -> None:
    """Expected values were computed independently from the NKF 2021 equation."""
    # The table reproduces clinical cases calculated with race-free CKD-EPI 2021.
    result = calculate_egfr_2021(creatinine_mg_dl, age_years, sex)

    assert result == pytest.approx(expected_egfr, rel=1e-6)


def test_calculate_egfr_2021_rejects_zero_creatinine() -> None:
    with pytest.raises(ValueError, match="creatinine_mg_dl"):
        calculate_egfr_2021(0.0, 40, "female")


def test_calculate_egfr_2021_rejects_zero_age() -> None:
    with pytest.raises(ValueError, match="age_years"):
        calculate_egfr_2021(0.8, 0, "male")


def test_calculate_egfr_2021_rejects_unknown_sex() -> None:
    with pytest.raises(ValueError, match="sex"):
        calculate_egfr_2021(0.8, 40, "unknown")
