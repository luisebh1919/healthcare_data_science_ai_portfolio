# Protocol

## Clinical question

Among adult patients with cancer discharged from an inpatient hospitalization, does longitudinal clinical history during the previous 180 days improve prediction of 30-day hospital readmission compared with age and sex alone?

## Study design

This project will define a retrospective prediction study using Synthea data converted to the OMOP Common Data Model. The unit of analysis will be one row per patient, anchored on the first eligible inpatient hospitalization. No analyses, model training, or performance results are included in this protocol phase.

## Population

The cohort will include adults aged 18 years or older with a cancer diagnosis recorded before or on the index date. Eligible patients must have a first eligible inpatient hospitalization, be alive at discharge, have at least 180 days of observable history before discharge, and have at least 30 days of observation after discharge.

## Index date

The index date will be the discharge date of the first eligible inpatient hospitalization for each patient. Each patient will contribute only one index date and one analytical row.

## Outcome

The outcome will be a new inpatient hospitalization occurring after discharge from the index hospitalization and within 30 days after the index date.

## Lookback window

Predictors will be measured during the 180 days before the index date. The lookback window will include events with timestamps on or before the index date only. No predictor will use information recorded after the index date.

## Predictors

The initial predictor set will include no more than six variables: age, sex, number of previous hospitalizations, number of distinct diagnoses, number of distinct medications, and number of clinical measurements. Age and sex will define the baseline model.

## Models

Three models are planned: M0, a logistic regression model using age and sex; M1, a logistic regression model using all six predictors; and M2, an XGBoost model using all six predictors.

## Evaluation

Model performance will be evaluated using AUROC, AUPRC, Brier score, and calibration plots. Evaluation will compare whether adding longitudinal 180-day clinical history improves prediction relative to age and sex alone.

## Leakage prevention

All predictors must satisfy `feature_timestamp <= index_date`. Information after discharge from the index hospitalization must not be used for feature construction. The 30-day readmission outcome will be defined separately from the predictor window and must not influence any predictor.

## Expected deliverable

The expected deliverable is a small, reproducible final project that defines the cohort, constructs the planned predictors, trains the specified models, evaluates discrimination and calibration, and documents the findings without claiming clinical validity beyond the synthetic dataset.

## Limitations

The data will be synthetic. Predictive performance will not imply real clinical utility. There will be no external validation in real patients. The cancer definition will depend on the OMOP concept set used.
