-- Lab 11: Actividades 1 a 10 completas. Dialecto DuckDB.
-- Base: lab10/data/clinical.duckdb; abrir en modo de solo lectura.

-- ACTIVIDAD 1 — Consulta A: original literal (Actividad 5, auditoría 1).
-- Pregunta de calidad clínica: ¿cuántos IDs de paciente aparecen en varios registros?
-- 1. IDs de paciente que aparecen más de una vez.
SELECT COUNT(*) AS patient_ids_duplicados
FROM (
    SELECT id
    FROM patients
    GROUP BY id
    HAVING COUNT(*) > 1
) AS ids_repetidos;

-- Consulta A: transformación de subconsulta en FROM a CTE descriptiva.
-- Misma pregunta; se cuentan IDs repetidos, no filas duplicadas adicionales.
WITH duplicated_patient_ids AS (
    SELECT id FROM patients
    GROUP BY id HAVING COUNT(*) > 1
)
SELECT COUNT(*) AS patient_ids_duplicados FROM duplicated_patient_ids;

-- Consulta B: original literal (Actividad 7).
-- ¿Cuántos encuentros tienen diagnóstico y cuál es su costo medio registrado?
-- ¿Cómo altera esas métricas unir directamente todos sus diagnósticos?
-- Actividad 7: el JOIN que multiplica

-- Compara el conjunto correcto de encuentros con el resultado de unir
-- directamente encounters y conditions. La corrección recupera una sola fila
-- por encuentro antes de calcular el conteo y el promedio.
WITH correct_encounters AS (
    SELECT
        e.id AS encounter_id,
        e.total_claim_cost
    FROM encounters AS e
    WHERE EXISTS (
        SELECT 1
        FROM conditions AS c
        WHERE c.encounter_id = e.id
    )
), inflated_join AS (
    SELECT
        e.id AS encounter_id,
        e.total_claim_cost
    FROM encounters AS e
    JOIN conditions AS c
        ON e.id = c.encounter_id
), corrected_join AS (
    SELECT DISTINCT
        encounter_id,
        total_claim_cost
    FROM inflated_join
)
SELECT
    (SELECT COUNT(*) FROM correct_encounters) AS correct_rows,
    (SELECT COUNT(*) FROM inflated_join) AS inflated_rows,
    (SELECT COUNT(*) FROM corrected_join) AS corrected_rows,
    (SELECT ROUND(AVG(total_claim_cost), 2)
     FROM correct_encounters) AS correct_avg,
    (SELECT ROUND(AVG(total_claim_cost), 2)
     FROM inflated_join) AS inflated_avg,
    (SELECT ROUND(AVG(total_claim_cost), 2)
     FROM corrected_join) AS corrected_avg;


-- Consulta B: CTEs descriptivas, misma pregunta y mismas seis columnas.
WITH diagnosed_encounters AS (
    SELECT DISTINCT encounter_id FROM conditions
), correct_encounters AS (
    SELECT e.id AS encounter_id, e.total_claim_cost
    FROM encounters AS e
    SEMI JOIN diagnosed_encounters AS d ON e.id = d.encounter_id
), inflated_join AS (
    SELECT e.id AS encounter_id, e.total_claim_cost
    FROM encounters AS e JOIN conditions AS c ON e.id = c.encounter_id
), corrected_join AS (
    SELECT DISTINCT encounter_id, total_claim_cost FROM inflated_join
), correct_summary AS (
    SELECT COUNT(*) AS correct_rows, ROUND(AVG(total_claim_cost), 2) AS correct_avg
    FROM correct_encounters
), inflated_summary AS (
    SELECT COUNT(*) AS inflated_rows, ROUND(AVG(total_claim_cost), 2) AS inflated_avg
    FROM inflated_join
), corrected_summary AS (
    SELECT COUNT(*) AS corrected_rows, ROUND(AVG(total_claim_cost), 2) AS corrected_avg
    FROM corrected_join
)
SELECT c.correct_rows, i.inflated_rows, r.corrected_rows,
       c.correct_avg, i.inflated_avg, r.corrected_avg
FROM correct_summary AS c
CROSS JOIN inflated_summary AS i CROSS JOIN corrected_summary AS r;

-- ACTIVIDAD 2 — Conteos de cada bloque de la consulta B.
-- Cada bloque también se ejecutó por separado con este WITH y SELECT COUNT(*).
WITH diagnosed_encounters AS (
    SELECT DISTINCT encounter_id FROM conditions
), correct_encounters AS (
    SELECT e.id AS encounter_id, e.total_claim_cost
    FROM encounters AS e
    SEMI JOIN diagnosed_encounters AS d ON e.id = d.encounter_id
), inflated_join AS (
    SELECT e.id AS encounter_id, e.total_claim_cost
    FROM encounters AS e JOIN conditions AS c ON e.id = c.encounter_id
), corrected_join AS (
    SELECT DISTINCT encounter_id, total_claim_cost FROM inflated_join
), correct_summary AS (
    SELECT COUNT(*) AS correct_rows, ROUND(AVG(total_claim_cost), 2) AS correct_avg
    FROM correct_encounters
), inflated_summary AS (
    SELECT COUNT(*) AS inflated_rows, ROUND(AVG(total_claim_cost), 2) AS inflated_avg
    FROM inflated_join
), corrected_summary AS (
    SELECT COUNT(*) AS corrected_rows, ROUND(AVG(total_claim_cost), 2) AS corrected_avg
    FROM corrected_join
)
SELECT 1 AS block_order, 'diagnosed_encounters' AS block_name, COUNT(*) AS row_count FROM diagnosed_encounters
UNION ALL
SELECT 2 AS block_order, 'correct_encounters' AS block_name, COUNT(*) AS row_count FROM correct_encounters
UNION ALL
SELECT 3 AS block_order, 'inflated_join' AS block_name, COUNT(*) AS row_count FROM inflated_join
UNION ALL
SELECT 4 AS block_order, 'corrected_join' AS block_name, COUNT(*) AS row_count FROM corrected_join
UNION ALL
SELECT 5 AS block_order, 'correct_summary' AS block_name, COUNT(*) AS row_count FROM correct_summary
UNION ALL
SELECT 6 AS block_order, 'inflated_summary' AS block_name, COUNT(*) AS row_count FROM inflated_summary
UNION ALL
SELECT 7 AS block_order, 'corrected_summary' AS block_name, COUNT(*) AS row_count FROM corrected_summary
ORDER BY block_order;

-- ACTIVIDAD 3 — ¿Cuál fue la primera y última visita y cuántas tuvo cada paciente?
-- A. GROUP BY: una fila por paciente con encuentros registrados.
WITH grouped_visits AS (
    SELECT patient_id, MIN(start_at) AS first_visit, MAX(start_at) AS last_visit,
           COUNT(*) AS visit_count
    FROM encounters GROUP BY patient_id
)
SELECT patient_id, first_visit, last_visit, visit_count
FROM grouped_visits ORDER BY patient_id;

-- B. Ventanas: el frame completo permite que LAST_VALUE vea la última visita.
WITH window_visits AS (
    SELECT patient_id, FIRST_VALUE(start_at) OVER full_history AS first_visit,
           LAST_VALUE(start_at) OVER full_history AS last_visit,
           COUNT(*) OVER (PARTITION BY patient_id) AS visit_count,
           ROW_NUMBER() OVER (PARTITION BY patient_id ORDER BY start_at, id) AS visit_order
    FROM encounters
    WINDOW full_history AS (PARTITION BY patient_id ORDER BY start_at, id
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
), patient_visit_summary AS (
    SELECT patient_id, first_visit, last_visit, visit_count
    FROM window_visits WHERE visit_order = 1
)
SELECT patient_id, first_visit, last_visit, visit_count
FROM patient_visit_summary ORDER BY patient_id;

-- Validación ejecutable: igualdad de resultados y multiplicidades en ambos sentidos.
WITH grouped_visits AS (
    SELECT patient_id, MIN(start_at) AS first_visit, MAX(start_at) AS last_visit,
           COUNT(*) AS visit_count
    FROM encounters GROUP BY patient_id
), window_visits AS (
    SELECT patient_id, FIRST_VALUE(start_at) OVER full_history AS first_visit,
           LAST_VALUE(start_at) OVER full_history AS last_visit,
           COUNT(*) OVER (PARTITION BY patient_id) AS visit_count,
           ROW_NUMBER() OVER (PARTITION BY patient_id ORDER BY start_at, id) AS visit_order
    FROM encounters
    WINDOW full_history AS (PARTITION BY patient_id ORDER BY start_at, id
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
), patient_visit_summary AS (
    SELECT patient_id, first_visit, last_visit, visit_count
    FROM window_visits WHERE visit_order = 1
), grouped_minus_window AS (
    SELECT patient_id, first_visit, last_visit, visit_count FROM grouped_visits
    EXCEPT ALL
    SELECT patient_id, first_visit, last_visit, visit_count FROM patient_visit_summary
), window_minus_grouped AS (
    SELECT patient_id, first_visit, last_visit, visit_count FROM patient_visit_summary
    EXCEPT ALL
    SELECT patient_id, first_visit, last_visit, visit_count FROM grouped_visits
)
SELECT (SELECT COUNT(*) FROM grouped_visits) AS grouped_rows,
       (SELECT COUNT(*) FROM patient_visit_summary) AS window_rows,
       (SELECT COUNT(*) FROM grouped_minus_window) AS grouped_minus_window,
       (SELECT COUNT(*) FROM window_minus_grouped) AS window_minus_grouped;

-- ACTIVIDAD 4 — ¿Cuál es la mediana de días entre visitas consecutivas del paciente?
WITH visits_with_previous AS (
    SELECT patient_id, id AS encounter_id, start_at,
           LAG(start_at) OVER (PARTITION BY patient_id ORDER BY start_at, id) AS previous_visit
    FROM encounters
), visit_intervals AS (
    SELECT patient_id, encounter_id, start_at, previous_visit,
           DATE_DIFF('day', previous_visit, start_at) AS days_between_visits
    FROM visits_with_previous
)
SELECT COUNT(*) AS total_visits,
       COUNT(*) FILTER (WHERE previous_visit IS NULL) AS first_visits,
       MEDIAN(days_between_visits) AS median_days
FROM visit_intervals;

-- ACTIVIDAD 5 — ¿Qué proporción de altas inpatient tiene readmisión entre 1 y 30 días?
-- Solo inpatient; cada alta es una oportunidad, incluso la última del paciente.
-- La siguiente admisión debe ser posterior al alta; día 30 incluido.
-- Definición del Lab 11, todavía no es la cohorte oncológica final del proyecto.
WITH inpatient_stays AS (
    SELECT patient_id, id AS encounter_id, start_at, stop_at AS discharge_at
    FROM encounters WHERE encounter_class = 'inpatient'
), stays_with_next_admission AS (
    SELECT patient_id, encounter_id, start_at, discharge_at,
           LEAD(start_at) OVER (PARTITION BY patient_id ORDER BY start_at, encounter_id)
               AS next_admission_at
    FROM inpatient_stays
), eligible_discharges AS (
    SELECT patient_id, encounter_id, discharge_at, next_admission_at,
           DATE_DIFF('day', discharge_at, next_admission_at) AS days_to_readmission
    FROM stays_with_next_admission
    WHERE discharge_at IS NOT NULL AND discharge_at >= start_at
), readmission_summary AS (
    SELECT COUNT(*) AS eligible_discharges,
           COUNT(*) FILTER (WHERE next_admission_at > discharge_at
                            AND days_to_readmission BETWEEN 1 AND 30) AS readmissions_30d
    FROM eligible_discharges
)
SELECT eligible_discharges, readmissions_30d,
       ROUND(100.0 * readmissions_30d / NULLIF(eligible_discharges, 0), 2) AS readmission_rate
FROM readmission_summary;


-- ACTIVIDAD 6 — ¿Cómo se agrupan las exposiciones a sodium fluoride en episodios?
-- Gap 30: exactamente 30 días conserva el episodio; se usa el máximo fin previo.
WITH valid_exposures AS (
    SELECT patient_id, start_at, stop_at
    FROM medications
    WHERE description = 'sodium fluoride 0.0272 MG/MG Oral Gel'
      AND stop_at IS NOT NULL AND stop_at >= start_at
), exposure_history AS (
    SELECT patient_id, start_at, stop_at,
           MAX(stop_at) OVER (PARTITION BY patient_id ORDER BY start_at, stop_at
               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS max_prior_stop
    FROM valid_exposures
), episode_boundaries AS (
    SELECT patient_id, start_at, stop_at,
           CASE WHEN max_prior_stop IS NULL
                     OR start_at > max_prior_stop + INTERVAL '30 days'
                THEN 1 ELSE 0 END AS new_episode
    FROM exposure_history
), numbered_exposures AS (
    SELECT patient_id, start_at, stop_at,
           SUM(new_episode) OVER (PARTITION BY patient_id ORDER BY start_at, stop_at
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS episode_id
    FROM episode_boundaries
), medication_episodes AS (
    SELECT patient_id, episode_id, MIN(start_at) AS episode_start,
           MAX(stop_at) AS episode_end,
           DATE_DIFF('day', MIN(start_at), MAX(stop_at)) AS duration_days,
           COUNT(*) AS exposure_count
    FROM numbered_exposures GROUP BY patient_id, episode_id
)
SELECT patient_id, episode_id, episode_start, episode_end, duration_days, exposure_count
FROM medication_episodes ORDER BY patient_id, episode_id;

-- Validación y duración de episodios con gap de 30 días.
WITH valid_exposures AS (
    SELECT patient_id, start_at, stop_at
    FROM medications
    WHERE description = 'sodium fluoride 0.0272 MG/MG Oral Gel'
      AND stop_at IS NOT NULL AND stop_at >= start_at
), exposure_history AS (
    SELECT patient_id, start_at, stop_at,
           MAX(stop_at) OVER (PARTITION BY patient_id ORDER BY start_at, stop_at
               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS max_prior_stop
    FROM valid_exposures
), episode_boundaries AS (
    SELECT patient_id, start_at, stop_at,
           CASE WHEN max_prior_stop IS NULL
                     OR start_at > max_prior_stop + INTERVAL '30 days'
                THEN 1 ELSE 0 END AS new_episode
    FROM exposure_history
), numbered_exposures AS (
    SELECT patient_id, start_at, stop_at,
           SUM(new_episode) OVER (PARTITION BY patient_id ORDER BY start_at, stop_at
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS episode_id
    FROM episode_boundaries
), medication_episodes AS (
    SELECT patient_id, episode_id, MIN(start_at) AS episode_start,
           MAX(stop_at) AS episode_end,
           DATE_DIFF('day', MIN(start_at), MAX(stop_at)) AS duration_days,
           COUNT(*) AS exposure_count
    FROM numbered_exposures GROUP BY patient_id, episode_id
)
SELECT 30 AS gap_days, SUM(exposure_count) AS valid_exposures,
       COUNT(DISTINCT patient_id) AS patients, COUNT(*) AS episodes,
       MIN(duration_days) AS min_days, MEDIAN(duration_days) AS median_days,
       QUANTILE_CONT(duration_days, 0.90) AS p90_days,
       QUANTILE_CONT(duration_days, 0.95) AS p95_days,
       QUANTILE_CONT(duration_days, 0.99) AS p99_days, MAX(duration_days) AS max_days
FROM medication_episodes;

-- Validación y duración de episodios con gap de 60 días.
WITH valid_exposures AS (
    SELECT patient_id, start_at, stop_at
    FROM medications
    WHERE description = 'sodium fluoride 0.0272 MG/MG Oral Gel'
      AND stop_at IS NOT NULL AND stop_at >= start_at
), exposure_history AS (
    SELECT patient_id, start_at, stop_at,
           MAX(stop_at) OVER (PARTITION BY patient_id ORDER BY start_at, stop_at
               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS max_prior_stop
    FROM valid_exposures
), episode_boundaries AS (
    SELECT patient_id, start_at, stop_at,
           CASE WHEN max_prior_stop IS NULL
                     OR start_at > max_prior_stop + INTERVAL '60 days'
                THEN 1 ELSE 0 END AS new_episode
    FROM exposure_history
), numbered_exposures AS (
    SELECT patient_id, start_at, stop_at,
           SUM(new_episode) OVER (PARTITION BY patient_id ORDER BY start_at, stop_at
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS episode_id
    FROM episode_boundaries
), medication_episodes AS (
    SELECT patient_id, episode_id, MIN(start_at) AS episode_start,
           MAX(stop_at) AS episode_end,
           DATE_DIFF('day', MIN(start_at), MAX(stop_at)) AS duration_days,
           COUNT(*) AS exposure_count
    FROM numbered_exposures GROUP BY patient_id, episode_id
)
SELECT 60 AS gap_days, SUM(exposure_count) AS valid_exposures,
       COUNT(DISTINCT patient_id) AS patients, COUNT(*) AS episodes,
       MIN(duration_days) AS min_days, MEDIAN(duration_days) AS median_days,
       QUANTILE_CONT(duration_days, 0.90) AS p90_days,
       QUANTILE_CONT(duration_days, 0.95) AS p95_days,
       QUANTILE_CONT(duration_days, 0.99) AS p99_days, MAX(duration_days) AS max_days
FROM medication_episodes;

-- Validación y duración de episodios con gap de 90 días.
WITH valid_exposures AS (
    SELECT patient_id, start_at, stop_at
    FROM medications
    WHERE description = 'sodium fluoride 0.0272 MG/MG Oral Gel'
      AND stop_at IS NOT NULL AND stop_at >= start_at
), exposure_history AS (
    SELECT patient_id, start_at, stop_at,
           MAX(stop_at) OVER (PARTITION BY patient_id ORDER BY start_at, stop_at
               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS max_prior_stop
    FROM valid_exposures
), episode_boundaries AS (
    SELECT patient_id, start_at, stop_at,
           CASE WHEN max_prior_stop IS NULL
                     OR start_at > max_prior_stop + INTERVAL '90 days'
                THEN 1 ELSE 0 END AS new_episode
    FROM exposure_history
), numbered_exposures AS (
    SELECT patient_id, start_at, stop_at,
           SUM(new_episode) OVER (PARTITION BY patient_id ORDER BY start_at, stop_at
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS episode_id
    FROM episode_boundaries
), medication_episodes AS (
    SELECT patient_id, episode_id, MIN(start_at) AS episode_start,
           MAX(stop_at) AS episode_end,
           DATE_DIFF('day', MIN(start_at), MAX(stop_at)) AS duration_days,
           COUNT(*) AS exposure_count
    FROM numbered_exposures GROUP BY patient_id, episode_id
)
SELECT 90 AS gap_days, SUM(exposure_count) AS valid_exposures,
       COUNT(DISTINCT patient_id) AS patients, COUNT(*) AS episodes,
       MIN(duration_days) AS min_days, MEDIAN(duration_days) AS median_days,
       QUANTILE_CONT(duration_days, 0.90) AS p90_days,
       QUANTILE_CONT(duration_days, 0.95) AS p95_days,
       QUANTILE_CONT(duration_days, 0.99) AS p99_days, MAX(duration_days) AS max_days
FROM medication_episodes;

-- ACTIVIDAD 7 — ¿Cuál es la última medición de presión arterial sistólica por paciente?
-- LOINC 8480-6; fecha descendente y encuentro descendente para desempatar.
WITH ranked_systolic_measurements AS (
    SELECT patient_id, observed_at, value, units,
           ROW_NUMBER() OVER (PARTITION BY patient_id
               ORDER BY observed_at DESC, encounter_id DESC) AS rn
    FROM observations WHERE code = '8480-6'
), latest_systolic_measurements AS (
    SELECT patient_id, observed_at, value, units
    FROM ranked_systolic_measurements WHERE rn = 1
)
SELECT patient_id, observed_at, value, units
FROM latest_systolic_measurements ORDER BY patient_id;

-- Validación de mediciones antes, pacientes distintos y mediciones después.
WITH ranked_systolic_measurements AS (
    SELECT patient_id, observed_at, value, units,
           ROW_NUMBER() OVER (PARTITION BY patient_id
               ORDER BY observed_at DESC, encounter_id DESC) AS rn
    FROM observations WHERE code = '8480-6'
), latest_systolic_measurements AS (
    SELECT patient_id, observed_at, value, units
    FROM ranked_systolic_measurements WHERE rn = 1
)
SELECT (SELECT COUNT(*) FROM ranked_systolic_measurements) AS measurements_before,
       (SELECT COUNT(DISTINCT patient_id) FROM ranked_systolic_measurements) AS patients,
       (SELECT COUNT(*) FROM latest_systolic_measurements) AS measurements_after;

-- ACTIVIDAD 8 — ¿Cómo difieren el promedio acumulado y la media de las últimas 3 mediciones sistólicas?
-- LOINC 8480-6; solo valores convertibles a DOUBLE. Selección reproducible del paciente.
-- Frames ROWS explícitos; redondeo solo en la salida, no en los cálculos de ventana.
WITH numeric_systolic_measurements AS (
    SELECT patient_id, observed_at, encounter_id, TRY_CAST(value AS DOUBLE) AS systolic
    FROM observations
    WHERE code = '8480-6' AND TRY_CAST(value AS DOUBLE) IS NOT NULL
), selected_patient AS (
    SELECT patient_id FROM numeric_systolic_measurements
    GROUP BY patient_id HAVING COUNT(*) >= 5
    ORDER BY COUNT(*) DESC, patient_id LIMIT 1
), patient_systolic_history AS (
    SELECT m.patient_id, m.observed_at, m.encounter_id, m.systolic
    FROM numeric_systolic_measurements AS m
    JOIN selected_patient AS p ON m.patient_id = p.patient_id
), systolic_window_means AS (
    SELECT patient_id, observed_at, encounter_id, systolic,
           AVG(systolic) OVER (PARTITION BY patient_id ORDER BY observed_at, encounter_id
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_mean,
           AVG(systolic) OVER (PARTITION BY patient_id ORDER BY observed_at, encounter_id
               ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_mean_3
    FROM patient_systolic_history
)
SELECT patient_id, observed_at, systolic,
       ROUND(cumulative_mean, 2) AS cumulative_mean,
       ROUND(moving_mean_3, 2) AS moving_mean_3
FROM systolic_window_means ORDER BY observed_at, encounter_id;

-- ACTIVIDAD 9 — ¿Qué medición sistólica está más cerca del alta índice y cuál puede usarse sin leakage?
-- Índice: stop_at de la primera inpatient, preservando la hora del alta.
-- A. Exploración ±90 días: cercanía en días, empate a favor de pre-index/en índice.
WITH ranked_inpatient_stays AS (
    SELECT patient_id, stop_at,
           ROW_NUMBER() OVER (PARTITION BY patient_id ORDER BY start_at, id) AS rn
    FROM encounters WHERE encounter_class = 'inpatient'
), index_discharges AS (
    SELECT patient_id, stop_at AS index_date
    FROM ranked_inpatient_stays WHERE rn = 1 AND stop_at IS NOT NULL
), numeric_systolic_measurements AS (
    SELECT patient_id, observed_at, encounter_id, value
    FROM observations
    WHERE code = '8480-6' AND TRY_CAST(value AS DOUBLE) IS NOT NULL
), ranked_nearby_measurements AS (
    SELECT i.patient_id, i.index_date, o.observed_at, o.encounter_id, o.value,
           ROW_NUMBER() OVER (PARTITION BY i.patient_id ORDER BY
               ABS(DATE_DIFF('day', i.index_date, o.observed_at)),
               CASE WHEN o.observed_at <= i.index_date THEN 0 ELSE 1 END,
               o.observed_at DESC, o.encounter_id DESC) AS rn
    FROM index_discharges AS i
    JOIN numeric_systolic_measurements AS o ON i.patient_id = o.patient_id
    WHERE o.observed_at BETWEEN i.index_date - INTERVAL '90 days'
                            AND i.index_date + INTERVAL '90 days'
), closest_measurements AS (
    SELECT patient_id, index_date, observed_at, encounter_id, value
    FROM ranked_nearby_measurements WHERE rn = 1
)
SELECT COUNT(*) AS patients_with_measurement,
       COUNT(*) FILTER (WHERE observed_at <= index_date) AS closest_pre_or_index,
       COUNT(*) FILTER (WHERE observed_at > index_date) AS closest_post_index,
       COUNT(*) FILTER (WHERE DATE_DIFF('day', index_date, observed_at) <= 0)
           AS closest_pre_or_same_calendar_day,
       COUNT(*) FILTER (WHERE DATE_DIFF('day', index_date, observed_at) > 0)
           AS closest_later_calendar_day
FROM closest_measurements;

-- B. Política predictiva final: solo información disponible hasta el instante índice.
WITH ranked_inpatient_stays AS (
    SELECT patient_id, stop_at,
           ROW_NUMBER() OVER (PARTITION BY patient_id ORDER BY start_at, id) AS rn
    FROM encounters WHERE encounter_class = 'inpatient'
), index_discharges AS (
    SELECT patient_id, stop_at AS index_date
    FROM ranked_inpatient_stays WHERE rn = 1 AND stop_at IS NOT NULL
), numeric_systolic_measurements AS (
    SELECT patient_id, observed_at, encounter_id, value
    FROM observations
    WHERE code = '8480-6' AND TRY_CAST(value AS DOUBLE) IS NOT NULL
), ranked_preindex_measurements AS (
    SELECT i.patient_id, i.index_date, o.observed_at, o.encounter_id, o.value,
           ROW_NUMBER() OVER (PARTITION BY i.patient_id
               ORDER BY o.observed_at DESC, o.encounter_id DESC) AS rn
    FROM index_discharges AS i
    JOIN numeric_systolic_measurements AS o ON i.patient_id = o.patient_id
    WHERE o.observed_at BETWEEN i.index_date - INTERVAL '90 days' AND i.index_date
), latest_preindex_measurements AS (
    SELECT patient_id, index_date, observed_at, value,
           DATE_DIFF('day', observed_at, index_date) AS days_before_index
    FROM ranked_preindex_measurements WHERE rn = 1
)
SELECT patient_id, index_date, observed_at, value, days_before_index
FROM latest_preindex_measurements ORDER BY patient_id;

-- Validación de la política pre-index.
WITH ranked_inpatient_stays AS (
    SELECT patient_id, stop_at,
           ROW_NUMBER() OVER (PARTITION BY patient_id ORDER BY start_at, id) AS rn
    FROM encounters WHERE encounter_class = 'inpatient'
), index_discharges AS (
    SELECT patient_id, stop_at AS index_date
    FROM ranked_inpatient_stays WHERE rn = 1 AND stop_at IS NOT NULL
), numeric_systolic_measurements AS (
    SELECT patient_id, observed_at, encounter_id, value
    FROM observations
    WHERE code = '8480-6' AND TRY_CAST(value AS DOUBLE) IS NOT NULL
), ranked_preindex_measurements AS (
    SELECT i.patient_id, i.index_date, o.observed_at, o.encounter_id, o.value,
           ROW_NUMBER() OVER (PARTITION BY i.patient_id
               ORDER BY o.observed_at DESC, o.encounter_id DESC) AS rn
    FROM index_discharges AS i
    JOIN numeric_systolic_measurements AS o ON i.patient_id = o.patient_id
    WHERE o.observed_at BETWEEN i.index_date - INTERVAL '90 days' AND i.index_date
), latest_preindex_measurements AS (
    SELECT patient_id, index_date, observed_at, value,
           DATE_DIFF('day', observed_at, index_date) AS days_before_index
    FROM ranked_preindex_measurements WHERE rn = 1
)
SELECT COUNT(*) AS patients_with_preindex_measurement,
       MIN(days_before_index) AS min_days_before,
       MEDIAN(days_before_index) AS median_days_before,
       MAX(days_before_index) AS max_days_before
FROM latest_preindex_measurements;

-- ACTIVIDAD 10 — ¿Cómo reproducir los intervalos entre visitas sin funciones de ventana?
-- Comparación limitada a los mismos primeros 100 patient_id de encounters: 6,079 visitas.
-- NO quitar selected_patients ni ejecutar este self-join sobre toda la tabla.
-- A. LAG: visita anterior en el orden start_at, id.
WITH selected_patients AS (
    SELECT DISTINCT patient_id FROM encounters
    ORDER BY patient_id LIMIT 100
), selected_visits AS (
    SELECT e.patient_id, e.id, e.start_at
    FROM encounters AS e
    JOIN selected_patients AS p ON e.patient_id = p.patient_id
), lag_previous_visits AS (
    SELECT patient_id, id, start_at,
           LAG(start_at) OVER (PARTITION BY patient_id ORDER BY start_at, id) AS previous_visit
    FROM selected_visits
)
SELECT COUNT(*) AS total_visits,
       COUNT(*) FILTER (WHERE previous_visit IS NULL) AS first_visits,
       MEDIAN(DATE_DIFF('day', previous_visit, start_at)) AS median_days
FROM lag_previous_visits;

-- B. Self-join sin ventanas: máximo inicio de todas las visitas previas del paciente.
-- El LEFT JOIN conserva la primera visita; el desempate por id conserva visitas simultáneas.
WITH selected_patients AS (
    SELECT DISTINCT patient_id FROM encounters
    ORDER BY patient_id LIMIT 100
), selected_visits AS (
    SELECT e.patient_id, e.id, e.start_at
    FROM encounters AS e
    JOIN selected_patients AS p ON e.patient_id = p.patient_id
), self_join_previous_visits AS (
    SELECT curr.patient_id, curr.id, curr.start_at, MAX(prev.start_at) AS previous_visit
    FROM selected_visits AS curr
    LEFT JOIN selected_visits AS prev ON curr.patient_id = prev.patient_id
        AND (prev.start_at < curr.start_at
             OR (prev.start_at = curr.start_at AND prev.id < curr.id))
    GROUP BY curr.patient_id, curr.id, curr.start_at
)
SELECT COUNT(*) AS total_visits,
       COUNT(*) FILTER (WHERE previous_visit IS NULL) AS first_visits,
       MEDIAN(DATE_DIFF('day', previous_visit, start_at)) AS median_days
FROM self_join_previous_visits;

-- Validación de igualdad por visita (incluidas multiplicidades y valores NULL).
WITH selected_patients AS (
    SELECT DISTINCT patient_id FROM encounters
    ORDER BY patient_id LIMIT 100
), selected_visits AS (
    SELECT e.patient_id, e.id, e.start_at
    FROM encounters AS e
    JOIN selected_patients AS p ON e.patient_id = p.patient_id
), lag_previous_visits AS (
    SELECT patient_id, id, start_at,
           LAG(start_at) OVER (PARTITION BY patient_id ORDER BY start_at, id) AS previous_visit
    FROM selected_visits
), self_join_previous_visits AS (
    SELECT curr.patient_id, curr.id, curr.start_at, MAX(prev.start_at) AS previous_visit
    FROM selected_visits AS curr
    LEFT JOIN selected_visits AS prev ON curr.patient_id = prev.patient_id
        AND (prev.start_at < curr.start_at
             OR (prev.start_at = curr.start_at AND prev.id < curr.id))
    GROUP BY curr.patient_id, curr.id, curr.start_at
)
, lag_minus_self AS (
    SELECT patient_id, id, start_at, previous_visit FROM lag_previous_visits
    EXCEPT ALL
    SELECT patient_id, id, start_at, previous_visit FROM self_join_previous_visits
), self_minus_lag AS (
    SELECT patient_id, id, start_at, previous_visit FROM self_join_previous_visits
    EXCEPT ALL
    SELECT patient_id, id, start_at, previous_visit FROM lag_previous_visits
)
SELECT (SELECT COUNT(*) FROM lag_minus_self) AS lag_minus_self,
       (SELECT COUNT(*) FROM self_minus_lag) AS self_minus_lag,
       NOT EXISTS (SELECT 1 FROM lag_minus_self)
           AND NOT EXISTS (SELECT 1 FROM self_minus_lag) AS results_equal;
