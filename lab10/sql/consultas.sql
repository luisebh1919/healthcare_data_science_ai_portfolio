-- Actividad 5: auditoría

-- 1. IDs de paciente que aparecen más de una vez.
SELECT COUNT(*) AS patient_ids_duplicados
FROM (
    SELECT id
    FROM patients
    GROUP BY id
    HAVING COUNT(*) > 1
) AS ids_repetidos;

-- 2. Encuentros registrados antes del nacimiento del paciente.
SELECT COUNT(*) AS encuentros_antes_del_nacimiento
FROM encounters AS e
JOIN patients AS p
    ON e.patient_id = p.id
WHERE CAST(e.start_at AS DATE) < p.birth_date;

-- 3. Valores de observación nulos o formados solo por espacios.
SELECT
    COUNT(*) AS total_observaciones,
    COUNT(*) FILTER (
        WHERE value IS NULL OR TRIM(value) = ''
    ) AS valores_nulos_o_vacios,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE value IS NULL OR TRIM(value) = ''
        ) / NULLIF(COUNT(*), 0),
        4
    ) AS porcentaje_nulo_o_vacio
FROM observations;

-- 4. Encuentros cuyo paciente no existe (anti-join).
SELECT COUNT(*) AS encuentros_sin_paciente
FROM encounters AS e
LEFT JOIN patients AS p
    ON e.patient_id = p.id
WHERE p.id IS NULL;

-- Actividad 6: 15 preguntas SQL

-- 1. ¿Cuántos pacientes hay y cuántos siguen vivos?
SELECT
    COUNT(*) AS total_patients,
    COUNT(*) FILTER (WHERE death_date IS NULL) AS alive_patients
FROM patients;

-- 2. ¿Cuál es la distribución de pacientes por sexo?
SELECT
    gender,
    COUNT(*) AS patient_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM patients
GROUP BY gender
ORDER BY patient_count DESC, gender;

-- 3. ¿Cuáles son los 10 diagnósticos/condiciones más frecuentes?
SELECT
    code,
    description,
    COUNT(*) AS condition_records,
    COUNT(DISTINCT patient_id) AS distinct_patients
FROM conditions
GROUP BY code, description
ORDER BY condition_records DESC, code
LIMIT 10;

-- 4. ¿Cuántos pacientes nacieron antes de 1960?
SELECT COUNT(*) AS patients_born_before_1960
FROM patients
WHERE birth_date < DATE '1960-01-01';

-- 5. ¿Cuántos encuentros se registraron por año?
SELECT
    EXTRACT(YEAR FROM start_at)::INTEGER AS encounter_year,
    COUNT(*) AS encounter_count
FROM encounters
GROUP BY encounter_year
ORDER BY encounter_year;

-- 6. ¿Cuál es el número medio y mediano de encuentros por paciente?
WITH encounters_per_patient AS (
    SELECT
        p.id AS patient_id,
        COUNT(e.id) AS encounter_count
    FROM patients AS p
    LEFT JOIN encounters AS e
        ON p.id = e.patient_id
    GROUP BY p.id
)
SELECT
    ROUND(AVG(encounter_count), 2) AS mean_encounters,
    MEDIAN(encounter_count) AS median_encounters
FROM encounters_per_patient;

-- 7. ¿Cuál es la edad media al primer diagnóstico de hipertensión esencial?
-- Condición elegida: SNOMED 59621000, Essential hypertension (disorder).
WITH first_hypertension AS (
    SELECT
        patient_id,
        MIN(start_date) AS first_diagnosis_date
    FROM conditions
    WHERE code = '59621000'
    GROUP BY patient_id
), ages_at_first_diagnosis AS (
    SELECT
        f.patient_id,
        DATE_DIFF('day', p.birth_date, f.first_diagnosis_date) / 365.2425
            AS age_years
    FROM first_hypertension AS f
    JOIN patients AS p
        ON f.patient_id = p.id
    WHERE f.first_diagnosis_date >= p.birth_date
)
SELECT
    COUNT(*) AS diagnosed_patients,
    ROUND(AVG(age_years), 2) AS mean_age_at_first_diagnosis
FROM ages_at_first_diagnosis;

-- 8. ¿Qué diagnósticos aparecen en más de 50 pacientes distintos?
SELECT
    code,
    description,
    COUNT(DISTINCT patient_id) AS distinct_patients
FROM conditions
GROUP BY code, description
HAVING COUNT(DISTINCT patient_id) > 50
ORDER BY distinct_patients DESC, code;

-- 9. ¿Cómo se distribuye la presión arterial sistólica?
-- Analito elegido: LOINC 8480-6, Systolic Blood Pressure, en mm[Hg].
WITH systolic_bp AS (
    SELECT TRY_CAST(value AS DOUBLE) AS value_mm_hg
    FROM observations
    WHERE code = '8480-6'
      AND units = 'mm[Hg]'
      AND TRY_CAST(value AS DOUBLE) IS NOT NULL
)
SELECT
    COUNT(*) AS measurement_count,
    ROUND(AVG(value_mm_hg), 2) AS mean_mm_hg,
    ROUND(MEDIAN(value_mm_hg), 2) AS median_mm_hg,
    ROUND(QUANTILE_CONT(value_mm_hg, 0.10), 2) AS p10_mm_hg,
    ROUND(QUANTILE_CONT(value_mm_hg, 0.90), 2) AS p90_mm_hg
FROM systolic_bp;

-- 10. ¿Cómo se distribuyen los pacientes por grupo etario y sexo?
-- Edad al 2026-09-29 para pacientes vivos y edad al morir para fallecidos.
-- Grupos: menores (0-17), adultos jóvenes (18-39), adultos (40-64)
-- y adultos mayores (65+).
WITH patient_ages AS (
    SELECT
        id,
        gender,
        DATE_DIFF(
            'year',
            birth_date,
            COALESCE(death_date, DATE '2026-09-29')
        ) - CASE
            WHEN STRFTIME(COALESCE(death_date, DATE '2026-09-29'), '%m-%d')
                 < STRFTIME(birth_date, '%m-%d')
            THEN 1 ELSE 0
        END AS age_years
    FROM patients
), grouped_patients AS (
    SELECT
        id,
        gender,
        CASE
            WHEN age_years BETWEEN 0 AND 17 THEN '0-17'
            WHEN age_years BETWEEN 18 AND 39 THEN '18-39'
            WHEN age_years BETWEEN 40 AND 64 THEN '40-64'
            WHEN age_years >= 65 THEN '65+'
            ELSE 'edad no válida'
        END AS age_group,
        CASE
            WHEN age_years BETWEEN 0 AND 17 THEN 1
            WHEN age_years BETWEEN 18 AND 39 THEN 2
            WHEN age_years BETWEEN 40 AND 64 THEN 3
            WHEN age_years >= 65 THEN 4
            ELSE 5
        END AS age_group_order
    FROM patient_ages
)
SELECT
    age_group,
    gender,
    COUNT(*) AS patient_count
FROM grouped_patients
GROUP BY age_group, age_group_order, gender
ORDER BY age_group_order, gender;

-- 11. ¿Cuántos pacientes distintos tienen diabetes tipo 2 e hipertensión?
-- Diabetes: SNOMED 44054006. Hipertensión esencial: SNOMED 59621000.
WITH diabetes_patients AS (
    SELECT DISTINCT patient_id
    FROM conditions
    WHERE code = '44054006'
), hypertension_patients AS (
    SELECT DISTINCT patient_id
    FROM conditions
    WHERE code = '59621000'
)
SELECT COUNT(*) AS patients_with_diabetes_and_hypertension
FROM diabetes_patients AS d
JOIN hypertension_patients AS h
    ON d.patient_id = h.patient_id;

-- 12. ¿Cuántos pacientes con diabetes no tienen ninguna medición de HbA1c?
-- Diabetes: SNOMED 44054006. HbA1c: LOINC 4548-4.
WITH diabetes_patients AS (
    SELECT DISTINCT patient_id
    FROM conditions
    WHERE code = '44054006'
)
SELECT COUNT(*) AS diabetic_patients_without_hba1c
FROM diabetes_patients AS d
WHERE NOT EXISTS (
    SELECT 1
    FROM observations AS o
    WHERE o.patient_id = d.patient_id
      AND o.code = '4548-4'
);

-- 13. ¿Cuál fue el primer y el último encuentro de cada paciente?
SELECT
    p.id AS patient_id,
    MIN(e.start_at) AS first_encounter_at,
    MAX(e.start_at) AS last_encounter_at
FROM patients AS p
LEFT JOIN encounters AS e
    ON p.id = e.patient_id
GROUP BY p.id
ORDER BY p.id;

-- 14. ¿Qué medicamento alcanzó a más pacientes con hipertensión esencial?
-- "Más frecuente" significa mayor número de pacientes distintos expuestos.
WITH hypertension_patients AS (
    SELECT DISTINCT patient_id
    FROM conditions
    WHERE code = '59621000'
), patient_medications AS (
    SELECT DISTINCT
        m.patient_id,
        m.code,
        m.description
    FROM medications AS m
    JOIN hypertension_patients AS h
        ON m.patient_id = h.patient_id
)
SELECT
    code,
    description,
    COUNT(*) AS distinct_exposed_patients
FROM patient_medications
GROUP BY code, description
ORDER BY distinct_exposed_patients DESC, code
LIMIT 1;

-- 15. ¿Cuántos encuentros de urgencias no tienen diagnóstico registrado?
SELECT COUNT(DISTINCT e.id) AS emergency_encounters_without_diagnosis
FROM encounters AS e
LEFT JOIN conditions AS c
    ON e.id = c.encounter_id
WHERE e.encounter_class = 'emergency'
  AND c.encounter_id IS NULL;

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

-- Actividad 8: la trampa del LEFT JOIN

-- A. Filtro de la tabla derecha en WHERE.
-- Las combinaciones encounter_id + code se deduplican para aislar el efecto
-- del filtro y no repetir el problema de multiplicación de la Actividad 7.
WITH condition_codes AS (
    SELECT DISTINCT
        encounter_id,
        code
    FROM conditions
)
SELECT COUNT(*) AS rows_with_filter_in_where
FROM encounters AS e
LEFT JOIN condition_codes AS c
    ON e.id = c.encounter_id
WHERE c.code = '59621000';

-- B. El mismo filtro dentro de ON.
WITH condition_codes AS (
    SELECT DISTINCT
        encounter_id,
        code
    FROM conditions
)
SELECT COUNT(*) AS rows_with_filter_in_on
FROM encounters AS e
LEFT JOIN condition_codes AS c
    ON e.id = c.encounter_id
   AND c.code = '59621000';

-- Actividad 9: medir rendimiento

-- Versión original de la consulta 12: NOT EXISTS.
EXPLAIN ANALYZE
WITH diabetes_patients AS (
    SELECT DISTINCT patient_id
    FROM conditions
    WHERE code = '44054006'
)
SELECT COUNT(*) AS diabetic_patients_without_hba1c
FROM diabetes_patients AS d
WHERE NOT EXISTS (
    SELECT 1
    FROM observations AS o
    WHERE o.patient_id = d.patient_id
      AND o.code = '4548-4'
);

-- Versión reescrita: filtrar y deduplicar ambas cohortes antes del anti-join.
EXPLAIN ANALYZE
WITH diabetes_patients AS (
    SELECT DISTINCT patient_id
    FROM conditions
    WHERE code = '44054006'
), hba1c_patients AS (
    SELECT DISTINCT patient_id
    FROM observations
    WHERE code = '4548-4'
)
SELECT COUNT(*) AS diabetic_patients_without_hba1c
FROM diabetes_patients AS d
LEFT JOIN hba1c_patients AS h
    ON d.patient_id = h.patient_id
WHERE h.patient_id IS NULL;
