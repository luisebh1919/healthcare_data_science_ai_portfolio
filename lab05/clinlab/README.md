# clinlab

`clinlab` is a small Python package for clinical data quality control, validation, and reproducible testing with `pandas`.

The goal of Lab 05 is to transform logic that originally lived inside exploratory notebooks into reusable, installable, and automatically tested Python functions.

---

## Main functions

### `non_numeric_fraction(values)`

Calculates the proportion of present values that cannot be converted to numeric values.

Example:

```python
values = pd.Series(["10", "20.5", "No", None])

result = non_numeric_fraction(values)
```

Interpretation:

| Value | Present? | Numeric? |
|---|:---:|:---:|
| `"10"` | Yes | Yes |
| `"20.5"` | Yes | Yes |
| `"No"` | Yes | No |
| `None` | No | Not applicable |

There are three present values and one non-numeric value:

```text
1 / 3 = 0.3333
```

Missing values are not treated as invalid text.

---

### `memory_mb(df)`

Estimates the amount of memory used by a pandas `DataFrame`, expressed in megabytes.

This is useful when comparing data representations, data types, and memory-optimization strategies for large clinical datasets.

---

### `find_temporal_inconsistencies(patients, encounters)`

Detects temporally impossible clinical encounters.

Examples include:

- encounters occurring before the recorded date of birth;
- encounters occurring after the recorded date of death.

Example:

```text
Birth date: 2000-01-01
Encounter:  1999-12-31

Result: before_birth
```

Death dates are compared at day resolution.

```text
DEATHDATE = 2020-05-10

Encounter 2020-05-10 23:59 -> allowed
Encounter 2020-05-11 00:00 -> after_death
```

This avoids falsely flagging an encounter that occurred on the same calendar day as a date-only death record.

---

### `merge_with_cardinality(...)`

Performs controlled pandas joins using:

```python
validate="many_to_one"
```

Several encounters may belong to the same patient, but the reference table must contain only one row per patient.

Example:

```text
encounters                    patients

patient_id encounter_id       patient_id sex
1          10                 1          F
1          11                 2          M
2          12

               ↓ many-to-one merge

patient_id encounter_id sex
1          10           F
1          11           F
2          12           M
```

If the right-hand table contains duplicated patient keys, pandas raises a `MergeError` instead of silently multiplying rows.

This is important in clinical datasets because an incorrect join may inflate encounters, diagnoses, exposures, or cohort size.

---

### `find_implausible_values(df, limits)`

Identifies measurements outside externally supplied plausibility limits.

Example:

```python
limits = {
    "heart_rate": (30.0, 220.0),
    "temperature_c": (34.0, 42.0),
}
```

The function returns boolean masks identifying measurements outside the configured interval.

These limits are intended for data-quality checks and should not automatically be interpreted as normal clinical ranges.

---

## Data plausibility vs clinical severity

Data quality and clinical severity are different concepts.

A value can be extreme and clinically concerning while still representing a real physiological measurement.

A sentinel such as `-999`, in contrast, should not be interpreted as a physiological value.

| Example | Data plausibility | Interpretation |
|---:|---|---|
| 72 bpm | Plausible | Typical heart rate |
| 45 bpm | Plausible | Low; clinical context required |
| 135 bpm | Plausible | High and potentially concerning |
| -999 bpm | Implausible | Sentinel / data error |
| NaN | Missing | No measurement available |

The conceptual workflow is therefore:

```text
data quality
    ↓
plausibility
    ↓
clinical category
    ↓
urgency
```

---

## `classify_clinical_value()`

This function separates:

- clinical category;
- data plausibility;
- urgency.

It receives externally supplied thresholds rather than hard-coding clinical policy inside the function.

Example output:

```python
{
    "category": "very_high",
    "is_plausible": True,
    "is_urgent": True,
}
```

For example:

```python
classification = classify_clinical_value(
    value=135,
    measurement="heart_rate",
    limits=clinical_policy,
)
```

A sentinel such as `-999` can instead produce:

```python
{
    "category": "implausible",
    "is_plausible": False,
    "is_urgent": False,
}
```

Here, `is_urgent=False` does **not** mean the value is clinically safe.

It means the value should not be interpreted clinically because it first represents a data-quality problem.

---

## Heart-rate example

The American Heart Association describes a resting heart rate of approximately **60–100 beats per minute** as typical for most adults.

Clinical alert systems may use different thresholds because their goal is not simply to define a "normal range", but to detect physiological deterioration.

For example, NEWS2 uses pulse ranges to assign different warning scores:

| Pulse (bpm) | NEWS2 score | Interpretation |
|---:|:---:|---|
| ≤ 40 | 3 | Marked abnormality |
| 41–50 | 1 | Abnormal |
| 51–90 | 0 | Lowest alert score |
| 91–110 | 1 | Abnormal |
| 111–130 | 2 | Important abnormality |
| ≥ 131 | 3 | Marked abnormality |

These thresholds represent **clinical warning levels**, not absolute limits of physiological possibility.

Therefore:

```text
135 bpm
```

may represent a real, plausible, and clinically important measurement.

In contrast:

```text
-999 bpm
```

should be treated as an invalid or sentinel value rather than interpreted as an extremely low heart rate.

The classification thresholds currently used in the test suite are educational examples. They must be replaced or justified with validated clinical references or institutional policies before use in a real clinical system.

---

## Automated testing

The package uses `pytest`.

A basic test follows the pattern:

```text
Arrange -> prepare the input
Act     -> execute the function
Assert  -> verify the expected behavior
```

Example:

```python
values = pd.Series(["10", "20.5", "No", None])

result = non_numeric_fraction(values)

assert result == pytest.approx(1 / 3)
```

The `assert` does not provide the answer to the function.

The function calculates the result independently, and the test compares that result with the expected behavior.

---

## Fixtures

The test suite contains reusable pytest fixtures representing intentionally problematic clinical data.

Examples include:

- missing values;
- duplicated patient identifiers;
- encounters before birth;
- encounters after death;
- sentinel values such as `-999`;
- physiologically extreme measurements.

Fixtures allow multiple tests to reuse the same controlled dataset.

---

## Parametrized tests

`pytest.mark.parametrize` is used to test the same behavior across multiple inputs.

Example:

```python
@pytest.mark.parametrize(
    "value, expected",
    [
        (72, False),
        (500, True),
        (-999, True),
    ],
)
```

Instead of writing three nearly identical test functions, pytest runs the same test once for each input.

The Lab 05 suite also tests values:

- exactly at thresholds;
- immediately below thresholds;
- immediately above thresholds;
- missing values;
- plausible extremes;
- implausible values.

---

## Edge cases

The suite explicitly tests situations that may break otherwise reasonable code:

- empty DataFrames;
- completely missing columns;
- duplicated identifiers;
- sentinel values;
- impossible dates;
- exact interval boundaries;
- out-of-range measurements.

One edge-case test identified a real bug in `non_numeric_fraction()`.

A series containing only missing values:

```python
pd.Series([None, float("nan")])
```

originally produced a `0 / 0` calculation.

The implementation was updated so that a completely missing series returns:

```python
0.0
```

rather than `NaN`.

---

## Project structure

```text
clinlab/
├── README.md
├── pyproject.toml
├── .pre-commit-config.yaml
├── src/
│   └── clinlab/
│       ├── __init__.py
│       └── data_quality.py
└── tests/
    └── test_data_quality.py
```

The project uses a **src layout**:

```text
src/       -> reusable package code
tests/     -> automated tests
notebooks/ -> exploratory analysis
```

Separating these components helps prevent notebook logic, test code, and package code from becoming mixed together.

---

## Installation

From `lab05/clinlab/`:

```bash
python -m pip install -e ".[dev]"
```

The editable installation means changes made inside `src/clinlab/` are immediately available without reinstalling the package after every edit.

---

## Software-quality checks

Run:

```bash
pytest --cov=clinlab --cov-report=term-missing
mypy src/
ruff check .
```

Current Lab 05 status:

```text
32 tests passed
~96% test coverage
mypy: passed
Ruff: passed
```

High coverage does not prove that software is correct.

For that reason, coverage is combined with:

- explicit expected behavior;
- edge cases;
- malicious test data;
- parametrized tests;
- type checking;
- linting.

---

## Pre-commit

The repository uses `pre-commit` with:

```text
Ruff
Ruff Format
```

These checks run before accepting a commit and help prevent avoidable style and quality problems from entering version control.

---

## References

1. American Heart Association. **Target Heart Rates Chart / resting heart rate guidance.**  
   https://www.heart.org/en/healthy-living/exercise-and-physical-activity/fitness-basics/target-heart-rates

2. Royal College of Physicians. **National Early Warning Score 2 (NEWS2).**  
   https://www.rcplondon.ac.uk/projects/outputs/national-early-warning-score-news2

---

## Limitations

This package was developed for educational purposes.

The clinical categories and plausibility thresholds used in the tests do not replace:

- clinical evaluation;
- validated medical guidelines;
- institutional protocols;
- population-specific reference ranges.

Thresholds must be clinically validated for the intended population and use case before deployment in any patient-care application.
