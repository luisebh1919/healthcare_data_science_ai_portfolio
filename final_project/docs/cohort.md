# Cohort definition

## Population

Adults aged 18 years or older with confirmed invasive cancer and an eligible inpatient hospitalization. Each patient contributes only the first hospitalization satisfying all eligibility criteria.

## Temporal definition

Predictors use the 180 days before index admission:

`[index_admission - 180 days, index_admission)`

The index hospitalization is excluded from predictor construction. The outcome window begins after index discharge and extends for 30 days.

## Cancer definition

Cancer is defined using 12 SNOMED CT source codes present in the Synthea data. Suspected prostate cancer, suspected lung cancer, and carcinoma in situ of the prostate are excluded.

## Inpatient definition

Inpatient hospitalizations are Synthea encounters with:

`encounter_class = 'inpatient'`

They are represented in the minimal OMOP layer with `visit_concept_id = 9201`.

## Attrition

| Step | Criterion | Patients |
|---|---|---:|
| 1 | Inpatient hospitalization | 7,816 |
| 2 | Adults age >= 18 | 7,380 |
| 3 | Confirmed cancer before/on admission | 839 |
| 4 | At least 180 observable days before admission | 839 |
| 5 | Alive at index discharge | 836 |
| 6 | At least 30 observable days after discharge | 824 |

Final cohort: **824 patients**.

## Data representation

The project uses a minimal OMOP-compatible layer in DuckDB containing `person`, `observation_period`, `visit_occurrence`, `condition_occurrence`, and `death`.

Source SNOMED codes are retained explicitly. Full OMOP vocabulary mapping is not claimed.
