# Protocol

## Clinical question

Among adult patients with cancer discharged from an inpatient hospitalization, does longitudinal clinical history during the previous 180 days improve prediction of 30-day hospital readmission beyond prior hospital use?

## Study design

This project will define a retrospective prediction study using Synthea data transformed to the OMOP Common Data Model. The unit of analysis will be one row per patient, anchored on the first eligible inpatient hospitalization.

## Population

The cohort will include adults aged 18 years or older with a cancer diagnosis recorded before or on the start of the index hospitalization. Patients must be alive at discharge and have sufficient observable history to cover the 180-day predictor window and the 30-day outcome window.

Each patient will contribute only the first eligible inpatient hospitalization.

## Index hospitalization and temporal anchors

The index hospitalization will have two relevant timestamps:

- `index_admission`: start of the first eligible inpatient hospitalization.
- `index_discharge`: discharge from that hospitalization.

Predictors will use only information occurring before `index_admission`.

The readmission outcome will begin after `index_discharge`.

## Outcome

The outcome will be a new inpatient hospitalization that begins after the index discharge and within the following 30 days.

## Lookback window

Predictors will be constructed from the 180 days before `index_admission`:

`[index_admission - 180 days, index_admission)`

The index hospitalization itself will not contribute predictor information.

## Predictors

The predictor set will contain six variables:

1. age
2. sex
3. previous inpatient hospitalizations
4. distinct diagnoses
5. distinct medications
6. clinical measurement count

All longitudinal predictors will be calculated within the 180-day lookback window.

## Models

Three models will be compared:

- **M0 — Logistic regression:** age, sex, and previous hospitalizations.
- **M1 — Logistic regression:** all six predictors.
- **M2 — XGBoost:** the same six predictors used by M1.

M1 and M2 use the same information so that their comparison reflects model form rather than access to different predictor sets.

## Evaluation

Models will be evaluated using:

- AUROC
- AUPRC
- Brier score
- calibration

Because readmission is expected to be imbalanced, AUPRC and calibration will be interpreted alongside AUROC.

## Model interpretation

The final XGBoost model will be interpreted using global SHAP values. Feature importance will be summarized using mean absolute SHAP values and a SHAP summary plot.

SHAP values will be interpreted as explanations of model predictions, not as causal effects.

## Leakage prevention

No predictor may use information recorded at or after `index_admission`.

The index hospitalization is excluded from feature construction.

The outcome window begins only after `index_discharge`.

Feature construction and outcome construction will therefore be implemented separately.

## Expected deliverable

The expected deliverable is a small, reproducible project that defines the OMOP cohort, constructs the six planned predictors, trains three prespecified models, evaluates discrimination and calibration, and interprets the XGBoost model with SHAP.

The repository will include SQL cohort definitions, tests, documentation, containerization, continuous integration, a data dictionary, limitations, and a declaration of AI-assistant use.

## Limitations

The data are synthetic and predictive performance will not establish real clinical utility.

There will be no external validation in real patients.

The cancer definition will depend on the OMOP concept set used.

The limited number of predictors and models is intentional to preserve interpretability and project scope.
