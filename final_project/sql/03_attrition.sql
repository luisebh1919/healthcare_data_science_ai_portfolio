WITH inpatient AS (
    SELECT
        v.*,
        p.birth_datetime,
        op.observation_period_start_date,
        op.observation_period_end_date
    FROM omop.visit_occurrence v
    JOIN omop.person p USING (person_id)
    JOIN omop.observation_period op USING (person_id)
),

adults AS (
    SELECT *
    FROM inpatient
    WHERE DATE_DIFF(
        'year',
        CAST(birth_datetime AS DATE),
        visit_start_date
    ) >= 18
),

cancer_before_index AS (
    SELECT a.*
    FROM adults a
    WHERE EXISTS (
        SELECT 1
        FROM omop.condition_occurrence c
        JOIN results.cancer_codes cc
          ON cc.source_code = c.condition_source_value
        WHERE c.person_id = a.person_id
          AND c.condition_start_date <= a.visit_start_date
    )
),

history_180 AS (
    SELECT *
    FROM cancer_before_index
    WHERE observation_period_start_date
          <= visit_start_date - INTERVAL 180 DAY
),

alive_at_discharge AS (
    SELECT h.*
    FROM history_180 h
    WHERE NOT EXISTS (
        SELECT 1
        FROM omop.death d
        WHERE d.person_id = h.person_id
          AND d.death_date <= h.visit_end_date
    )
),

followup_30 AS (
    SELECT *
    FROM alive_at_discharge
    WHERE observation_period_end_date
          >= visit_end_date + INTERVAL 30 DAY
)

SELECT 1 AS step, 'Inpatient hospitalization' AS criterion,
       COUNT(DISTINCT person_id) AS patients
FROM inpatient

UNION ALL

SELECT 2, 'Adults age >= 18',
       COUNT(DISTINCT person_id)
FROM adults

UNION ALL

SELECT 3, 'Confirmed cancer before/on admission',
       COUNT(DISTINCT person_id)
FROM cancer_before_index

UNION ALL

SELECT 4, 'At least 180 observable days before admission',
       COUNT(DISTINCT person_id)
FROM history_180

UNION ALL

SELECT 5, 'Alive at index discharge',
       COUNT(DISTINCT person_id)
FROM alive_at_discharge

UNION ALL

SELECT 6, 'At least 30 observable days after discharge',
       COUNT(DISTINCT person_id)
FROM followup_30

ORDER BY step;WITH inpatient AS (
    SELECT
        v.*,
        p.birth_datetime,
        op.observation_period_start_date,
        op.observation_period_end_date
    FROM omop.visit_occurrence v
    JOIN omop.person p USING (person_id)
    JOIN omop.observation_period op USING (person_id)
),

adults AS (
    SELECT *
    FROM inpatient
    WHERE DATE_DIFF(
        'year',
        CAST(birth_datetime AS DATE),
        visit_start_date
    ) >= 18
),

cancer_before_index AS (
    SELECT a.*
    FROM adults a
    WHERE EXISTS (
        SELECT 1
        FROM omop.condition_occurrence c
        JOIN results.cancer_codes cc
          ON cc.source_code = c.condition_source_value
        WHERE c.person_id = a.person_id
          AND c.condition_start_date <= a.visit_start_date
    )
),

history_180 AS (
    SELECT *
    FROM cancer_before_index
    WHERE observation_period_start_date
          <= visit_start_date - INTERVAL 180 DAY
),

alive_at_discharge AS (
    SELECT h.*
    FROM history_180 h
    WHERE NOT EXISTS (
        SELECT 1
        FROM omop.death d
        WHERE d.person_id = h.person_id
          AND d.death_date <= h.visit_end_date
    )
),

followup_30 AS (
    SELECT *
    FROM alive_at_discharge
    WHERE observation_period_end_date
          >= visit_end_date + INTERVAL 30 DAY
)

SELECT 1 AS step, 'Inpatient hospitalization' AS criterion,
       COUNT(DISTINCT person_id) AS patients
FROM inpatient

UNION ALL

SELECT 2, 'Adults age >= 18',
       COUNT(DISTINCT person_id)
FROM adults

UNION ALL

SELECT 3, 'Confirmed cancer before/on admission',
       COUNT(DISTINCT person_id)
FROM cancer_before_index

UNION ALL

SELECT 4, 'At least 180 observable days before admission',
       COUNT(DISTINCT person_id)
FROM history_180

UNION ALL

SELECT 5, 'Alive at index discharge',
       COUNT(DISTINCT person_id)
FROM alive_at_discharge

UNION ALL

SELECT 6, 'At least 30 observable days after discharge',
       COUNT(DISTINCT person_id)
FROM followup_30

ORDER BY step;
