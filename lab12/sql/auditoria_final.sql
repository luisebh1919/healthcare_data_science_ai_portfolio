-- nombre: reglas_visita
SELECT source_class,target_concept_id,target_concept_name,target_concept_code,evidence,changed_rows FROM visit_mapping_audit ORDER BY source_class;
-- nombre: temporalidad
SELECT 'visitas_antes_nacimiento' AS control,COUNT(*) AS discrepancias FROM visit_occurrence v JOIN person p USING(person_id) WHERE v.visit_start_date<CAST(p.birth_datetime AS DATE)
UNION ALL SELECT 'visitas_invertidas',COUNT(*) FROM visit_occurrence WHERE visit_start_datetime>visit_end_datetime
UNION ALL SELECT 'fuente_clinica_antes_nacimiento',COUNT(*) FROM src_conditions s JOIN person p ON p.person_source_value=s.PATIENT WHERE CAST(s.START AS DATE)<CAST(p.birth_datetime AS DATE)
UNION ALL SELECT 'periodo_no_reproduce_limites_visitas',COUNT(*) FROM observation_period o WHERE o.observation_period_start_date<>(SELECT MIN(visit_start_date) FROM visit_occurrence v WHERE v.person_id=o.person_id) OR o.observation_period_end_date<>(SELECT MAX(visit_end_date) FROM visit_occurrence v WHERE v.person_id=o.person_id)
UNION ALL SELECT 'eventos_clinicos_fin_antes_inicio',COUNT(*) FROM src_conditions WHERE CAST(STOP AS DATE)<CAST(START AS DATE);
-- nombre: fuera_periodo_por_tabla
WITH events AS (SELECT 'Condition' AS dominio,person_id,condition_start_date AS fecha FROM condition_occurrence
UNION ALL SELECT 'Observation',person_id,observation_date FROM observation
UNION ALL SELECT 'Measurement',person_id,measurement_date FROM measurement)
SELECT dominio,COUNT(*) AS eventos,COUNT(*) FILTER(WHERE NOT EXISTS (SELECT 1 FROM observation_period o WHERE o.person_id=e.person_id AND e.fecha BETWEEN o.observation_period_start_date AND o.observation_period_end_date)) AS fuera,
100.0*COUNT(*) FILTER(WHERE NOT EXISTS (SELECT 1 FROM observation_period o WHERE o.person_id=e.person_id AND e.fecha BETWEEN o.observation_period_start_date AND o.observation_period_end_date))/NULLIF(COUNT(*),0) AS porcentaje_fuera FROM events e GROUP BY 1 ORDER BY 1;
-- nombre: huecos_observacion
WITH previous AS (SELECT person_id,visit_start_date,
MAX(visit_end_date) OVER (PARTITION BY person_id ORDER BY visit_start_date,visit_occurrence_id ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS previo_fin FROM visit_occurrence),
gaps AS (SELECT person_id,MAX(greatest(date_diff('day',previo_fin,visit_start_date)-1,0)) AS max_dias_sin_visita FROM previous GROUP BY 1)
SELECT COUNT(DISTINCT person_id) AS denominador_personas,COUNT(DISTINCT person_id) FILTER(WHERE max_dias_sin_visita>365) AS personas_hueco_mayor_365,
MAX(max_dias_sin_visita) AS mayor_hueco_dias,MEDIAN(max_dias_sin_visita) AS mediana_maximo_hueco FROM gaps;
-- nombre: duplicados_y_traza
WITH events AS (SELECT 'condition_occurrence' AS tabla,condition_occurrence_id AS event_id,person_id FROM condition_occurrence
UNION ALL SELECT 'observation',observation_id,person_id FROM observation
UNION ALL SELECT 'measurement',measurement_id,person_id FROM measurement)
SELECT 'grupos_duplicados_fuente_exactos' AS control,COUNT(*) AS discrepancias FROM (SELECT PATIENT,ENCOUNTER,START,STOP,CODE,DESCRIPTION,SYSTEM FROM src_conditions GROUP BY ALL HAVING COUNT(*)>1)
UNION ALL SELECT 'eventos_sin_traza',COUNT(*) FROM events e WHERE NOT EXISTS (SELECT 1 FROM clinical_lineage l WHERE l.event_table=e.tabla AND l.event_id=e.event_id)
UNION ALL SELECT 'trazas_sin_evento',COUNT(*) FROM clinical_lineage l WHERE NOT EXISTS (SELECT 1 FROM events e WHERE e.tabla=l.event_table AND e.event_id=l.event_id)
UNION ALL SELECT 'traza_cambia_persona',COUNT(*) FROM clinical_lineage l JOIN events e ON e.tabla=l.event_table AND e.event_id=l.event_id JOIN src_conditions s ON s.source_row=l.source_row JOIN person p ON p.person_source_value=s.PATIENT WHERE e.person_id<>p.person_id;
-- nombre: cobertura_fuente_global
SELECT COUNT(*) AS denominador_eventos_fuente,
COUNT(*) FILTER(WHERE NOT EXISTS (SELECT 1 FROM clinical_lineage l WHERE l.source_row=s.source_row AND l.target_concept_id<>0)) AS sin_destino_estandar,
100.0*COUNT(*) FILTER(WHERE NOT EXISTS (SELECT 1 FROM clinical_lineage l WHERE l.source_row=s.source_row AND l.target_concept_id<>0))/NULLIF(COUNT(*),0) AS porcentaje_sin_destino_estandar
FROM src_conditions s;
-- nombre: sistemas_fuente
SELECT SYSTEM,COUNT(*) AS eventos FROM src_conditions GROUP BY 1 ORDER BY 1;
-- nombre: diccionarios
SELECT 'concept_vocabulary_fk' AS control,COUNT(*) AS discrepancias FROM concept c WHERE NOT EXISTS (SELECT 1 FROM vocabulary v WHERE v.vocabulary_id=c.vocabulary_id)
UNION ALL SELECT 'concept_domain_fk',COUNT(*) FROM concept c WHERE NOT EXISTS (SELECT 1 FROM domain d WHERE d.domain_id=c.domain_id)
UNION ALL SELECT 'concept_class_fk',COUNT(*) FROM concept c WHERE NOT EXISTS (SELECT 1 FROM concept_class d WHERE d.concept_class_id=c.concept_class_id);
