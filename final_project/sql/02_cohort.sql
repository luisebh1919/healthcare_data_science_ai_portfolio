CREATE OR REPLACE TABLE results.cohort AS

WITH eligible_visits AS (
    SELECT
        v.visit_occurrence_id,
        v.person_id,
        v.visit_start_date,
        v.visit_start_datetime,
        v.visit_end_date,
        v.visit_end_datetime,
        p.birth_datetime,
        op.observation_period_start_date,
        op.observation_period_end_date
    FROM omop.visit_occurrence v
    JOIN omop.person p
      ON p.person_id = v.person_id
    JOIN omop.observation_period op
      ON op.person_id = v.person_id
    WHERE
        DATE_DIFF('year', CAST(p.birth_datetime AS DATE), v.visit_start_date) >= 18
        AND op.observation_period_start_date <= v.visit_start_date - INTERVAL 180 DAY
        AND op.observation_period_end_date >= v.visit_end_date + INTERVAL 30 DAY
        AND NOT EXISTS (
            SELECT 1
            FROM omop.death d
            WHERE d.person_id = v.person_id
              AND d.death_date <= v.visit_end_date
        )
        AND EXISTS (
            SELECT 1
            FROM omop.condition_occurrence c
            JOIN results.cancer_codes cc
              ON cc.source_code = c.condition_source_value
            WHERE c.person_id = v.person_id
              AND c.condition_start_date <= v.visit_start_date
        )
),

first_eligible AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY person_id
               ORDER BY visit_start_datetime, visit_occurrence_id
           ) AS rn
    FROM eligible_visits
)

SELECT
    person_id,
    visit_occurrence_id AS index_visit_id,
    visit_start_datetime AS index_admission,
    visit_end_datetime AS index_discharge
FROM first_eligible
WHERE rn = 1;
