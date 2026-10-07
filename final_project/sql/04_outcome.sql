CREATE OR REPLACE TABLE results.outcome_30d AS

WITH first_readmission AS (
    SELECT
        c.person_id,
        MIN(v.visit_start_datetime) AS first_readmission_datetime
    FROM results.cohort c
    JOIN omop.visit_occurrence v
      ON v.person_id = c.person_id
     AND v.visit_start_datetime > c.index_discharge
     AND v.visit_start_datetime <= c.index_discharge + INTERVAL 30 DAY
    GROUP BY c.person_id
)

SELECT
    c.person_id,
    c.index_visit_id,
    c.index_admission,
    c.index_discharge,
    CASE
        WHEN r.first_readmission_datetime IS NOT NULL THEN 1
        ELSE 0
    END AS readmission_30d,
    r.first_readmission_datetime,
    CASE
        WHEN r.first_readmission_datetime IS NOT NULL
        THEN DATE_DIFF(
            'day',
            CAST(c.index_discharge AS DATE),
            CAST(r.first_readmission_datetime AS DATE)
        )
        ELSE NULL
    END AS days_to_readmission
FROM results.cohort c
LEFT JOIN first_readmission r
  ON r.person_id = c.person_id;
