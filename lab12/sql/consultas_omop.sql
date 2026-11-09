-- nombre: personas
-- Actividad 6: población, sin multiplicar personas por visitas.
SELECT COUNT(DISTINCT person_id) AS personas FROM person;
-- nombre: sexo
-- Nombres canónicos de Gender también para referencias reducidas sin esas filas CONCEPT.
-- Solo presentación (OHDSI OMOP-Queries PE02); no cambia IDs ni conteos del vocabulario.
SELECT p.gender_concept_id, COALESCE(c.concept_name,CASE p.gender_concept_id WHEN 8507 THEN 'MALE' WHEN 8532 THEN 'FEMALE' WHEN 0 THEN 'Sin correspondencia' ELSE 'Nombre no disponible en paquete' END) AS concept_name, COUNT(DISTINCT p.person_id) AS personas
FROM person p LEFT JOIN concept c ON c.concept_id=p.gender_concept_id GROUP BY 1,2 ORDER BY 1;
-- nombre: nacimiento
SELECT year_of_birth, COUNT(DISTINCT person_id) AS personas FROM person GROUP BY 1 ORDER BY 1;
-- nombre: observacion
-- Días inclusivos acumulados por persona; se validan períodos sin solapamiento.
WITH dias AS (SELECT person_id, SUM(date_diff('day',observation_period_start_date,observation_period_end_date)+1) AS dias FROM observation_period GROUP BY 1)
SELECT median(dias) AS mediana_dias, COUNT(DISTINCT person_id) AS personas_con_periodo FROM dias;
-- nombre: diagnosticos
-- Eventos y pacientes son magnitudes distintas. Solo eventos dentro del período.
SELECT d.condition_concept_id, c.concept_name, COUNT(*) AS eventos, COUNT(DISTINCT d.person_id) AS personas
FROM condition_occurrence d LEFT JOIN concept c ON c.concept_id=d.condition_concept_id
WHERE EXISTS (SELECT 1 FROM observation_period o WHERE o.person_id=d.person_id AND d.condition_start_date BETWEEN o.observation_period_start_date AND o.observation_period_end_date)
GROUP BY 1,2 ORDER BY personas DESC,1 LIMIT 20;
-- nombre: visitas
WITH n AS (SELECT p.person_id, COUNT(v.visit_occurrence_id) AS visitas FROM person p LEFT JOIN visit_occurrence v ON v.person_id=p.person_id GROUP BY 1)
SELECT AVG(visitas) AS media_visitas, COUNT(DISTINCT person_id) AS personas FROM n;
-- nombre: tipos_visita
-- Denominador: todas las personas, incluidos quienes tienen cero visitas del tipo.
SELECT v.visit_concept_id, c.concept_name, COUNT(*) AS visitas, COUNT(DISTINCT v.person_id) AS personas,
COUNT(*)::DOUBLE / NULLIF((SELECT COUNT(DISTINCT person_id) FROM person),0) AS media_por_persona
FROM visit_occurrence v LEFT JOIN concept c ON c.concept_id=v.visit_concept_id GROUP BY 1,2 ORDER BY 1;
-- nombre: vocabularios
SELECT COUNT(*) AS conceptos, COUNT(*) FILTER(WHERE standard_concept='S') AS estandar FROM concept;
-- nombre: ceros
-- Actividad 5: denominador de eventos, nunca confundir con pacientes.
SELECT 'Condition' AS dominio, COUNT(*) AS eventos, COUNT(*) FILTER(WHERE condition_concept_id=0) AS sin_mapear,
100.0*COUNT(*) FILTER(WHERE condition_concept_id=0)/NULLIF(COUNT(*),0) AS porcentaje FROM condition_occurrence
UNION ALL SELECT 'Visit',COUNT(*),COUNT(*) FILTER(WHERE visit_concept_id=0),100.0*COUNT(*) FILTER(WHERE visit_concept_id=0)/NULLIF(COUNT(*),0) FROM visit_occurrence
UNION ALL SELECT 'Gender',COUNT(*),COUNT(*) FILTER(WHERE gender_concept_id=0),100.0*COUNT(*) FILTER(WHERE gender_concept_id=0)/NULLIF(COUNT(*),0) FROM person;
-- nombre: estandar_origen
-- Actividad 7: código fuente más frecuente; si no hay mapeo, estándar queda NULL.
WITH elegibles AS (SELECT d.* FROM condition_occurrence d WHERE EXISTS (SELECT 1 FROM observation_period o WHERE o.person_id=d.person_id AND d.condition_start_date BETWEEN o.observation_period_start_date AND o.observation_period_end_date)),
elegido AS (SELECT condition_source_value AS codigo FROM elegibles GROUP BY 1 ORDER BY COUNT(DISTINCT person_id) DESC,1 LIMIT 1),
targets AS (SELECT DISTINCT condition_concept_id FROM elegibles WHERE condition_source_value=(SELECT codigo FROM elegido) AND condition_concept_id<>0)
SELECT e.codigo, (SELECT COUNT(DISTINCT person_id) FROM elegibles WHERE condition_source_value=e.codigo) AS personas_origen,
t.condition_concept_id, c.concept_name,
CASE WHEN t.condition_concept_id IS NOT NULL THEN (SELECT COUNT(DISTINCT person_id) FROM elegibles d WHERE d.condition_concept_id=t.condition_concept_id) END AS personas_estandar
FROM elegido e LEFT JOIN targets t ON TRUE LEFT JOIN concept c ON c.concept_id=t.condition_concept_id;
-- nombre: ventana
-- Actividad 8: EXISTS evita duplicación por varios períodos.
WITH n AS (SELECT COUNT(*) AS todos, COUNT(*) FILTER(WHERE EXISTS (SELECT 1 FROM observation_period o WHERE o.person_id=d.person_id AND d.condition_start_date BETWEEN o.observation_period_start_date AND o.observation_period_end_date)) AS dentro FROM condition_occurrence d)
SELECT todos,dentro,100.0*(todos-dentro)/NULLIF(todos,0) AS porcentaje_fuera FROM n;
-- nombre: athena
-- Actividad 9: hijos directos (min_levels=1); descendientes excluyen el propio concepto.
WITH elegibles AS (SELECT d.* FROM condition_occurrence d WHERE EXISTS (SELECT 1 FROM observation_period o WHERE o.person_id=d.person_id AND d.condition_start_date BETWEEN o.observation_period_start_date AND o.observation_period_end_date)),
top AS (SELECT condition_concept_id,COUNT(DISTINCT person_id) AS personas FROM elegibles WHERE condition_concept_id<>0 GROUP BY 1 ORDER BY 2 DESC,1 LIMIT 3)
SELECT t.condition_concept_id,c.concept_name,c.vocabulary_id,c.domain_id,c.standard_concept,
(SELECT COUNT(DISTINCT descendant_concept_id) FROM concept_ancestor a WHERE a.ancestor_concept_id=t.condition_concept_id AND a.min_levels_of_separation=1) AS hijos_directos,
(SELECT COUNT(DISTINCT descendant_concept_id) FROM concept_ancestor a WHERE a.ancestor_concept_id=t.condition_concept_id AND a.min_levels_of_separation>0) AS descendientes,
(SELECT MIN(condition_source_value) FROM elegibles d WHERE d.condition_concept_id=t.condition_concept_id) AS codigo_origen
FROM top t JOIN concept c ON c.concept_id=t.condition_concept_id ORDER BY t.personas DESC;
