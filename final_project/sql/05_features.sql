CREATE OR REPLACE TABLE results.analytic_dataset AS

WITH base AS (
    SELECT
        o.person_id,
        o.index_visit_id,
        o.index_admission,
        o.index_discharge,
        o.readmission_30d,
        p.person_source_value,
        p.birth_datetime,
        p.gender_source_value,
        o.index_admission - INTERVAL 180 DAY AS lookback_start
    FROM results.outcome_30d o
    JOIN omop.person p
      ON p.person_id = o.person_id
),

prior_hospitalizations AS (
    SELECT
        b.person_id,
        COUNT(DISTINCT v.visit_occurrence_id)
            AS prior_inpatient_hospitalizations_180d
    FROM base b
    LEFT JOIN omop.visit_occurrence v
      ON v.person_id = b.person_id
     AND v.visit_start_datetime >= b.lookback_start
     AND v.visit_start_datetime < b.index_admission
    GROUP BY b.person_id
),

diagnoses AS (
    SELECT
        b.person_id,
        COUNT(DISTINCT c.condition_source_value)
            AS distinct_diagnoses_180d
    FROM base b
    LEFT JOIN omop.condition_occurrence c
      ON c.person_id = b.person_id
     AND c.condition_start_date >= CAST(b.lookback_start AS DATE)
     AND c.condition_start_date < CAST(b.index_admission AS DATE)
    GROUP BY b.person_id
),

medications AS (
    SELECT
        b.person_id,
        COUNT(DISTINCT m.code)
            AS distinct_medications_180d
    FROM base b
    LEFT JOIN raw.main.medications m
      ON CAST(m.patient_id AS VARCHAR) = b.person_source_value
     AND m.start_at >= b.lookback_start
     AND m.start_at < b.index_admission
    GROUP BY b.person_id
),

measurements AS (
    SELECT
        b.person_id,
        COUNT(obs.observed_at)
            AS measurement_count_180d
    FROM base b
    LEFT JOIN raw.main.observations obs
      ON CAST(obs.patient_id AS VARCHAR) = b.person_source_value
     AND obs.observed_at >= b.lookback_start
     AND obs.observed_at < b.index_admission
     AND obs.observation_type = 'numeric'
     AND obs.category IN ('laboratory', 'vital-signs')
    GROUP BY b.person_id
)

SELECT
    b.person_id,
    b.index_visit_id,
    b.index_admission,
    b.index_discharge,

    YEAR(CAST(b.index_admission AS DATE))
        - YEAR(CAST(b.birth_datetime AS DATE))
        - CASE
            WHEN STRFTIME(CAST(b.index_admission AS DATE), '%m-%d')
               < STRFTIME(CAST(b.birth_datetime AS DATE), '%m-%d')
            THEN 1
            ELSE 0
          END AS age,

    b.gender_source_value AS sex,

    COALESCE(h.prior_inpatient_hospitalizations_180d, 0)
        AS prior_inpatient_hospitalizations_180d,

    COALESCE(d.distinct_diagnoses_180d, 0)
        AS distinct_diagnoses_180d,

    COALESCE(m.distinct_medications_180d, 0)
        AS distinct_medications_180d,

    COALESCE(x.measurement_count_180d, 0)
        AS measurement_count_180d,

    b.readmission_30d

FROM base b
LEFT JOIN prior_hospitalizations h
  ON h.person_id = b.person_id
LEFT JOIN diagnoses d
  ON d.person_id = b.person_id
LEFT JOIN medications m
  ON m.person_id = b.person_id
LEFT JOIN measurements x
  ON x.person_id = b.person_id;
