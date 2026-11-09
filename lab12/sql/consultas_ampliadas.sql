-- nombre: ceros_nuevos
-- Denominador: filas de cada tabla clínica, no personas ni filas originales.
SELECT 'Observation' AS dominio,COUNT(*) AS eventos,COUNT(*) FILTER(WHERE observation_concept_id=0) AS sin_mapear,100.0*COUNT(*) FILTER(WHERE observation_concept_id=0)/NULLIF(COUNT(*),0) AS porcentaje FROM observation
UNION ALL SELECT 'Measurement',COUNT(*),COUNT(*) FILTER(WHERE measurement_concept_id=0),100.0*COUNT(*) FILTER(WHERE measurement_concept_id=0)/NULLIF(COUNT(*),0) FROM measurement;
-- nombre: reconciliacion_clinica
SELECT (SELECT COUNT(*) FROM src_conditions) AS fuente,
(SELECT COUNT(*) FROM condition_occurrence) AS condition,
(SELECT COUNT(*) FROM observation) AS observation,
(SELECT COUNT(*) FROM measurement) AS measurement,
(SELECT COUNT(DISTINCT source_row) FROM clinical_lineage) AS fuentes_con_destino,
(SELECT COUNT(*) FROM clinical_lineage) AS destinos,
(SELECT COUNT(*) FROM src_conditions s WHERE NOT EXISTS (SELECT 1 FROM clinical_lineage l WHERE l.source_row=s.source_row)) AS sin_destino,
(SELECT COUNT(*) FROM rejected_domain r WHERE NOT EXISTS (SELECT 1 FROM clinical_lineage l WHERE l.source_row=r.source_row AND l.target_concept_id=r.target_id AND l.event_table=lower(r.domain_id))) AS pendientes_otro_dominio;
-- nombre: gingivitis
-- Fracción histórica de personas sintéticas con registro, no prevalencia puntual.
WITH raw_g AS (SELECT * FROM src_conditions WHERE CODE='66383009'),
eligible AS (SELECT d.* FROM condition_occurrence d WHERE d.condition_concept_id=4281516 AND EXISTS (SELECT 1 FROM observation_period o WHERE o.person_id=d.person_id AND d.condition_start_date BETWEEN o.observation_period_start_date AND o.observation_period_end_date))
SELECT c.concept_id,c.concept_name,
(SELECT COUNT(*) FROM raw_g) AS eventos_fuente,
(SELECT COUNT(DISTINCT p.person_id) FROM raw_g g JOIN person p ON p.person_source_value=g.PATIENT) AS personas_fuente_sin_ventana,
(SELECT COUNT(*) FROM condition_occurrence WHERE condition_concept_id=c.concept_id) AS eventos_transformados,
(SELECT COUNT(*) FROM eligible) AS eventos_en_ventana,
(SELECT COUNT(DISTINCT person_id) FROM eligible) AS personas_en_ventana,
(SELECT COUNT(DISTINCT person_id) FROM person) AS denominador_personas,
100.0*(SELECT COUNT(DISTINCT person_id) FROM eligible)/NULLIF((SELECT COUNT(DISTINCT person_id) FROM person),0) AS porcentaje_personas,
(SELECT COUNT(*)-COUNT(DISTINCT source_row) FROM mapped WHERE CODE='66383009') AS exceso_por_expansion_mapeo,
(SELECT COUNT(*) FROM (SELECT PATIENT,ENCOUNTER,START,STOP,CODE FROM raw_g GROUP BY ALL HAVING COUNT(*)>1)) AS grupos_duplicados_exactos_fuente,
(SELECT COUNT(*) FROM (SELECT person_id,condition_start_date,condition_end_date,visit_occurrence_id FROM condition_occurrence WHERE condition_concept_id=c.concept_id GROUP BY ALL HAVING COUNT(*)>1)) AS grupos_duplicados_destino
FROM concept c WHERE c.concept_id=4281516;
-- nombre: gingivitis_temporal
-- Candidatos a repetición semántica: mismo inicio o intervalos que se solapan.
WITH g AS (SELECT * FROM src_conditions WHERE CODE='66383009'),
ordered AS (SELECT p.person_id,g.PATIENT,CAST(START AS DATE) AS inicio,
MAX(coalesce(CAST(STOP AS DATE),DATE '9999-12-31')) OVER (PARTITION BY PATIENT ORDER BY CAST(START AS DATE),source_row ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS fin_previo FROM g JOIN person p ON p.person_source_value=g.PATIENT)
SELECT (SELECT COUNT(*) FROM (SELECT PATIENT,START FROM g GROUP BY ALL HAVING COUNT(*)>1)) AS grupos_mismo_inicio,
(SELECT COUNT(*) FROM (SELECT PATIENT,ENCOUNTER FROM g GROUP BY ALL HAVING COUNT(*)>1)) AS grupos_mismo_encuentro,
COUNT(*) FILTER(WHERE inicio<fin_previo) AS eventos_con_solapamiento_estricto,
COUNT(DISTINCT person_id) FILTER(WHERE inicio<fin_previo) AS personas_con_solapamiento FROM ordered;
-- nombre: mediciones_categoricas
SELECT m.measurement_concept_id,c.concept_name,COUNT(*) AS eventos,
COUNT(*) FILTER(WHERE m.value_as_number IS NULL) AS sin_valor_numerico,
COUNT(*) FILTER(WHERE m.unit_concept_id IS NULL) AS sin_unidad,
COUNT(DISTINCT m.person_id) AS personas
FROM measurement m JOIN concept c ON c.concept_id=m.measurement_concept_id GROUP BY 1,2;
-- nombre: observation_sin_correspondencia
-- Completitud sobre todas las filas; no es una estimación clínica de prevalencia.
SELECT o.observation_source_value,c.concept_id AS source_concept_id,c.concept_name AS source_concept_name,c.domain_id,c.standard_concept,c.invalid_reason,
COUNT(*) AS eventos,COUNT(DISTINCT o.person_id) AS personas,
EXISTS (SELECT 1 FROM concept_relationship r JOIN concept t ON t.concept_id=r.concept_id_2 WHERE r.concept_id_1=c.concept_id AND r.relationship_id='Maps to' AND r.invalid_reason IS NULL AND t.standard_concept='S' AND t.invalid_reason IS NULL) AS tiene_destino_estandar_vigente
FROM observation o LEFT JOIN concept c ON c.concept_id=o.observation_source_concept_id
WHERE o.observation_concept_id=0 GROUP BY 1,2,3,4,5,6 ORDER BY eventos DESC,1;
