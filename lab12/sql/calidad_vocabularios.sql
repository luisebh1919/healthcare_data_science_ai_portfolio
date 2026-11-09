-- nombre: inventario
SELECT vocabulary_id,COUNT(*) AS conceptos,COUNT(*) FILTER(WHERE standard_concept='S') AS estandar
FROM concept GROUP BY 1 ORDER BY 1;
-- nombre: fuera_condition
SELECT domain_id AS dominio_destino,COUNT(*) AS filas,COUNT(DISTINCT source_row) AS registros_fuente
FROM rejected_domain GROUP BY 1 ORDER BY 1;
-- nombre: cobertura_otros_dominios
-- Fuera de tablas OMOP propias, aunque sí mapeados y conservados en staging.
SELECT r.domain_id AS dominio_destino,COUNT(*) AS eventos,
COUNT(*) FILTER(WHERE c.standard_concept='S' AND c.invalid_reason IS NULL AND c.domain_id=r.domain_id) AS mapeados_validos,
100.0*COUNT(*) FILTER(WHERE c.concept_id IS NULL OR c.standard_concept IS DISTINCT FROM 'S' OR c.invalid_reason IS NOT NULL OR c.domain_id IS DISTINCT FROM r.domain_id)/NULLIF(COUNT(*),0) AS porcentaje_sin_mapeo,
100.0*COUNT(*) FILTER(WHERE NOT EXISTS (SELECT 1 FROM lab12_clinical_lineage l WHERE l.source_row=r.source_row AND l.target_concept_id=r.target_id AND l.event_table=lower(r.domain_id)))/NULLIF(COUNT(*),0) AS porcentaje_fuera_tabla_clinica
FROM rejected_domain r LEFT JOIN concept c ON c.concept_id=r.target_id GROUP BY 1 ORDER BY 1;
-- nombre: no_mapeados
-- Falta de código, código ausente del paquete y ausencia de Maps to son distintos.
SELECT CASE WHEN d.condition_source_value IS NULL OR trim(d.condition_source_value)='' THEN 'sin_codigo_fuente'
WHEN NOT EXISTS (SELECT 1 FROM concept s WHERE s.vocabulary_id='SNOMED' AND s.concept_code=d.condition_source_value) THEN 'codigo_no_presente_en_paquete'
WHEN EXISTS (SELECT 1 FROM concept s WHERE s.vocabulary_id='SNOMED' AND s.concept_code=d.condition_source_value AND s.invalid_reason='U') THEN 'concepto_obsoleto_U'
WHEN EXISTS (SELECT 1 FROM concept s WHERE s.vocabulary_id='SNOMED' AND s.concept_code=d.condition_source_value AND s.invalid_reason='D') THEN 'concepto_invalido_D'
ELSE 'concepto_vigente_sin_destino_condition' END AS motivo,
COUNT(*) AS eventos,COUNT(DISTINCT d.person_id) AS personas
FROM condition_occurrence d WHERE condition_concept_id=0 GROUP BY 1 ORDER BY 1;
-- nombre: detalle_no_mapeados
WITH n AS (SELECT condition_source_value,COUNT(*) AS eventos,COUNT(DISTINCT person_id) AS personas
FROM condition_occurrence WHERE condition_concept_id=0 GROUP BY 1)
SELECT n.condition_source_value,n.eventos,n.personas,s.concept_id,s.concept_name,s.domain_id,s.standard_concept,s.invalid_reason,
(SELECT COUNT(*) FROM concept_relationship r JOIN concept t ON t.concept_id=r.concept_id_2
WHERE r.concept_id_1=s.concept_id AND r.relationship_id='Maps to' AND r.invalid_reason IS NULL AND t.invalid_reason IS NULL AND t.standard_concept='S') AS destinos_estandar_vigentes,
(SELECT COUNT(*) FROM concept_relationship r WHERE r.concept_id_1=s.concept_id AND r.relationship_id='Maps to' AND r.invalid_reason IS NOT NULL) AS maps_to_invalidos,
(SELECT COUNT(*) FROM concept_relationship r WHERE r.concept_id_1=s.concept_id AND r.relationship_id='Concept replaced by' AND r.invalid_reason IS NULL) AS reemplazos_vigentes
FROM n LEFT JOIN concept s ON s.vocabulary_id='SNOMED' AND s.concept_code=n.condition_source_value ORDER BY n.eventos DESC,n.condition_source_value;
-- nombre: visitas_no_mapeadas
SELECT s.ENCOUNTERCLASS AS clase_fuente,COUNT(*) AS eventos FROM visit_occurrence v
JOIN src_encounters s ON s.Id=v.visit_source_value WHERE v.visit_concept_id=0 GROUP BY 1 ORDER BY 1;
-- nombre: codigos_del_estandar
-- Todos los códigos del estándar seleccionado para explicar diferencias de actividad 7.
WITH elegido AS (SELECT condition_concept_id FROM condition_occurrence WHERE condition_concept_id<>0
GROUP BY 1 ORDER BY COUNT(DISTINCT person_id) DESC,1 LIMIT 1)
SELECT d.condition_concept_id,c.concept_name,d.condition_source_value,COUNT(DISTINCT d.person_id) AS personas
FROM condition_occurrence d JOIN concept c ON c.concept_id=d.condition_concept_id
WHERE d.condition_concept_id=(SELECT condition_concept_id FROM elegido)
AND EXISTS (SELECT 1 FROM observation_period o WHERE o.person_id=d.person_id AND d.condition_start_date BETWEEN o.observation_period_start_date AND o.observation_period_end_date)
GROUP BY 1,2,3 ORDER BY personas DESC;
-- nombre: detalle_exclusiones
SELECT r.domain_id AS dominio_destino,r.CODE AS codigo_fuente,r.DESCRIPTION AS descripcion_fuente,
r.target_id AS concept_id,c.concept_name,c.standard_concept,c.invalid_reason,
COUNT(*) AS eventos,COUNT(DISTINCT r.source_row) AS registros_fuente,COUNT(DISTINCT r.person_id) AS personas
FROM rejected_domain r LEFT JOIN concept c ON c.concept_id=r.target_id GROUP BY ALL ORDER BY eventos DESC,codigo_fuente;
-- nombre: reconciliacion
SELECT (SELECT COUNT(*) FROM src_conditions) AS fuente,
(SELECT COUNT(DISTINCT source_row) FROM condition_lineage) AS fuente_en_condition,
(SELECT COUNT(DISTINCT source_row) FROM rejected_domain) AS fuente_otro_dominio,
(SELECT COUNT(*) FROM src_conditions s WHERE NOT EXISTS (SELECT 1 FROM lab12_clinical_lineage l WHERE l.source_row=s.source_row) AND NOT EXISTS (SELECT 1 FROM rejected_domain r WHERE r.source_row=s.source_row)) AS fuente_sin_traza;
-- nombre: dependencias
SELECT 'concept_relationship.origen' AS relacion,COUNT(*) AS huerfanos FROM concept_relationship r WHERE NOT EXISTS (SELECT 1 FROM concept c WHERE c.concept_id=r.concept_id_1)
UNION ALL SELECT 'concept_relationship.destino',COUNT(*) FROM concept_relationship r WHERE NOT EXISTS (SELECT 1 FROM concept c WHERE c.concept_id=r.concept_id_2)
UNION ALL SELECT 'concept_ancestor.ancestro',COUNT(*) FROM concept_ancestor r WHERE NOT EXISTS (SELECT 1 FROM concept c WHERE c.concept_id=r.ancestor_concept_id)
UNION ALL SELECT 'concept_ancestor.descendiente',COUNT(*) FROM concept_ancestor r WHERE NOT EXISTS (SELECT 1 FROM concept c WHERE c.concept_id=r.descendant_concept_id);
-- nombre: sexo_fuente
SELECT GENDER AS sexo_fuente,COUNT(*) AS registros FROM src_patients GROUP BY 1 ORDER BY 1;
-- nombre: relaciones_top
-- Prueba documental de Maps to: ambos IDs siempre con nombre legible.
WITH top AS (SELECT d.condition_concept_id FROM condition_occurrence d WHERE d.condition_concept_id<>0
AND EXISTS (SELECT 1 FROM observation_period o WHERE o.person_id=d.person_id AND d.condition_start_date BETWEEN o.observation_period_start_date AND o.observation_period_end_date)
GROUP BY 1 ORDER BY COUNT(DISTINCT d.person_id) DESC,1 LIMIT 3)
SELECT DISTINCT s.concept_id AS source_concept_id,s.concept_name AS source_concept_name,s.concept_code,
r.relationship_id,r.valid_start_date,r.valid_end_date,r.invalid_reason,
t.concept_id,t.concept_name,t.domain_id,t.standard_concept
FROM top JOIN concept t ON t.concept_id=top.condition_concept_id
JOIN concept_relationship r ON r.concept_id_2=t.concept_id AND r.relationship_id='Maps to' AND r.invalid_reason IS NULL
JOIN concept s ON s.concept_id=r.concept_id_1 AND s.vocabulary_id='SNOMED'
WHERE EXISTS (SELECT 1 FROM condition_occurrence d WHERE d.condition_concept_id=t.concept_id AND d.condition_source_value=s.concept_code)
ORDER BY t.concept_id,s.concept_code;
-- nombre: mapeos_condition_sin_relacion
SELECT COUNT(*) AS eventos_sin_maps_to_valido FROM condition_occurrence d WHERE d.condition_concept_id<>0
AND NOT EXISTS (SELECT 1 FROM concept s JOIN concept_relationship r ON r.concept_id_1=s.concept_id
WHERE s.vocabulary_id='SNOMED' AND s.concept_code=d.condition_source_value
AND r.concept_id_2=d.condition_concept_id AND r.relationship_id='Maps to' AND r.invalid_reason IS NULL);
-- nombre: dominio_fuente_sin_mapeo
-- Denominador por dominio declarado en el concepto fuente: no confundir con tabla destino.
SELECT coalesce(c.domain_id,'Ausente') AS dominio_fuente,COUNT(*) AS registros,
COUNT(*) FILTER(WHERE NOT EXISTS (SELECT 1 FROM mapping m WHERE m.concept_code=s.CODE)) AS sin_destino_estandar,
100.0*COUNT(*) FILTER(WHERE NOT EXISTS (SELECT 1 FROM mapping m WHERE m.concept_code=s.CODE))/NULLIF(COUNT(*),0) AS porcentaje
FROM src_conditions s LEFT JOIN concept c ON c.vocabulary_id='SNOMED' AND c.concept_code=s.CODE GROUP BY 1 ORDER BY 1;
