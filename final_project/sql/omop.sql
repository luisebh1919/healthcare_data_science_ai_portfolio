-- Minimal OMOP subset required for the final-project cohort.
-- Source: Synthea data previously loaded in lab10/data/clinical.duckdb.

CREATE SCHEMA IF NOT EXISTS omop;

CREATE OR REPLACE TABLE omop.person AS
SELECT
    ROW_NUMBER() OVER (ORDER BY id) AS person_id,
    CASE gender
        WHEN 'M' THEN 8507
        WHEN 'F' THEN 8532
        ELSE 0
    END AS gender_concept_id,
    YEAR(birth_date) AS year_of_birth,
    MONTH(birth_date) AS month_of_birth,
    DAY(birth_date) AS day_of_birth,
    birth_date::TIMESTAMP AS birth_datetime,
    CAST(id AS VARCHAR) AS person_source_value,
    gender AS gender_source_value
FROM raw.main.patients;

CREATE OR REPLACE TABLE omop.observation_period AS
SELECT
    ROW_NUMBER() OVER (ORDER BY p.person_id) AS observation_period_id,
    p.person_id,
    MIN(CAST(e.start_at AS DATE)) AS observation_period_start_date,
    MAX(CAST(e.stop_at AS DATE)) AS observation_period_end_date,
    32882 AS period_type_concept_id
FROM omop.person p
JOIN raw.main.encounters e
  ON p.person_source_value = CAST(e.patient_id AS VARCHAR)
GROUP BY p.person_id;

CREATE OR REPLACE TABLE omop.visit_occurrence AS
SELECT
    ROW_NUMBER() OVER (ORDER BY e.start_at, e.id) AS visit_occurrence_id,
    p.person_id,
    9201 AS visit_concept_id,
    CAST(e.start_at AS DATE) AS visit_start_date,
    e.start_at AS visit_start_datetime,
    CAST(e.stop_at AS DATE) AS visit_end_date,
    e.stop_at AS visit_end_datetime,
    32827 AS visit_type_concept_id,
    CAST(e.id AS VARCHAR) AS visit_source_value
FROM raw.main.encounters e
JOIN omop.person p
  ON p.person_source_value = CAST(e.patient_id AS VARCHAR)
WHERE e.encounter_class = 'inpatient';

CREATE OR REPLACE TABLE omop.condition_occurrence AS
SELECT
    ROW_NUMBER() OVER (
        ORDER BY c.patient_id, c.start_date, c.code
    ) AS condition_occurrence_id,
    p.person_id,
    0 AS condition_concept_id,
    c.start_date AS condition_start_date,
    c.stop_date AS condition_end_date,
    CAST(c.code AS VARCHAR) AS condition_source_value,
    c.description AS condition_source_description
FROM raw.main.conditions c
JOIN omop.person p
  ON p.person_source_value = CAST(c.patient_id AS VARCHAR);

CREATE OR REPLACE TABLE omop.death AS
SELECT
    p.person_id,
    r.death_date,
    CAST(r.death_date AS TIMESTAMP) AS death_datetime
FROM raw.main.patients r
JOIN omop.person p
  ON p.person_source_value = CAST(r.id AS VARCHAR)
WHERE r.death_date IS NOT NULL;
