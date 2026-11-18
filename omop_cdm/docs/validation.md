# Resultados de validación

## Revisión posterior — 16 de noviembre de 2026

El [estado de finalización](completion_status.md) incorpora la auditoría forense
de 02.4, almacenamiento, tablas persistentes y análisis detallado de los 418 casos.
**La carga completa sigue pendiente. Las 39 tablas OMOP persistentes están vacías.**
Las tablas clínicas que se enumeran más abajo pertenecen al experimento anterior
en memoria, no a la base persistente.

- [02.4](notebook_24_audit.md): hash actual estable desde el cierre anterior,
  pero falta el contenido correspondiente al hash inicial; no puede certificarse
  un diff exacto de código, Markdown, salidas ni metadatos. Implementación detenida.
- [Dominios](diagnosis_domain_audit.md): 418 pacientes, 1205 registros y 977 pares
  paciente–código implicados en entrenamiento. Los recuentos agregados cambian
  de 2449 a 1472 al usar la tabla Condition; no se modifican las variables originales.
- [Persistencia](persistent_tables.json): 39 tablas OMOP vacías y siete tablas de
  resultados en la base separada de auditoría.
- Equivalencia adicional: 165 pacientes de prueba temporal con pertenencias y
  seis valores originales idénticos. Las tres FE solo se comparan donde existe
  su referencia original: los 655 de entrenamiento.
- Pruebas repetidas: 13 aprobadas, cero fallidas. DQD sigue **sin ejecutar**:
  faltan DataQualityDashboard, DatabaseConnector, SqlRender y duckdb en R,
  además de CDM_SOURCE y datos persistentes. Sus cifras de pruebas no están
  disponibles; no se sustituyen por las pruebas locales.

Auditoría independiente de fuentes completas y núcleo OMOP en memoria. No se ejecutó el notebook 02.4 ni se recalcularon modelos.

## Esquema y almacenamiento

39 tablas y 432 campos oficiales; sin discrepancias de nombres, tipos normalizados o nulabilidad. La base persistente `local/omop54_schema_only.duckdb` está vacía.

Espacio disponible al último preflight: 224.0 MiB. Reserva estimada de carga: 20.60 GiB. Ver `preflight.json`; no se inició la carga completa.

## Tablas pobladas en la validación en memoria

| Tabla | Registros |
|---|---:|
| care_site | 1,181 |
| concept | 2,042,798 |
| concept_ancestor | 12,073,517 |
| concept_class | 433 |
| concept_relationship | 13,945,404 |
| concept_synonym | 2,503,953 |
| condition_occurrence | 399,864 |
| death | 2,851 |
| domain | 50 |
| drug_strength | 209,849 |
| measurement | 5 |
| observation | 430,930 |
| observation_period | 22,851 |
| person | 22,851 |
| provider | 1,181 |
| relationship | 724 |
| visit_occurrence | 1,353,311 |
| vocabulary | 43 |

Las restantes tablas existen y están vacías en esta validación. MEASUREMENT y OBSERVATION contienen aquí exclusivamente eventos procedentes de conditions.csv; no representan aún la carga de observations.csv. CDM_SOURCE se poblará en la ETL completa, no en el experimento en memoria.

## Cobertura de vocabularios de las fuentes completas

| Fuente | Filas | Filas con destino estándar | Cobertura | Códigos mapeados / distintos |
|---|---:|---:|---:|---:|
| conditions | 830,799 | 819,364 | 98.6236% | 291 / 313 |
| medications | 1,158,763 | 1,158,763 | 100.0000% | 391 / 391 |
| observations | 17,340,070 | 16,682,275 | 96.2065% | 277 / 305 |
| procedures | 3,729,996 | 3,705,850 | 99.3527% | 418 / 421 |
| immunizations | 329,742 | 0 | 0.0000% | 0 / 22 |
| devices | 131,652 | 106,145 | 80.6254% | 29 / 32 |

La cobertura cuenta filas fuente con al menos un destino, sin multiplicarlas por mappings múltiples. No es una tasa de carga ni certificación semántica. Incluye 1055 filas con destino Note aún no implementado. Los códigos no mapeados y sus razones están en [data_audit.json](data_audit.json). El sistema LOINC de observations.csv es un supuesto explícito del exportador pendiente de confirmar para códigos alternativos.

## Cohorte y entrenamiento originales

| Comprobación | Resultado |
|---|---|
| Cohorte general / eventos | 824 / 85; mismos pacientes y hospitalizaciones índice |
| Corte temporal de 02.4 | 2022-11-27 07:16:42 |
| Bloque antiguo / exclusiones de seguimiento | 659 / 4 |
| Entrenamiento / eventos | 655 / 76 |
| Pacientes de entrenamiento ausentes / adicionales | 0 / 0 |
| IDs numéricos de persona diferentes en entrenamiento | 0 |
| Orden de pacientes idéntico | True |
| Diferencias de valores: seis predictores con definición original | 0 en cada variable |
| Diferencias: dx_cardiovascular, med_antihipertensivos y diagnósticos no oncológicos | 0 en cada variable |
| Códigos/descripciones de diagnósticos de entrenamiento: EXCEPT ALL en ambos sentidos | 0 / 0 |

Las tres variables derivadas conservan las reglas regex históricas de 02.4, extraídas como literales AST, sin ejecutar celdas ni inventar clasificaciones. Se reconstruyen independientemente los datos de comparación. En entrenamiento se reproducen 37 pacientes con dx_cardiovascular y 197 con med_antihipertensivos. El total de recuentos no oncológicos es 698 (no es un número de pacientes).

Las medicaciones y mediciones de los predictores se leen nuevamente de los CSV originales; no se afirma que ya existan en DRUG_EXPOSURE/MEASUREMENT de una base persistente completa. Los identificadores nuevos de visita incluyen todos los encuentros y difieren del rango inpatient de la base mínima; se comparan las hospitalizaciones por UUID fuente. Ningún identificador de las bases originales fue modificado.

## Discrepancia investigada

Al restringir diagnósticos a CONDITION_OCCURRENCE, cambia distinct_diagnoses_180d en **515 de 824** pacientes, incluidos **418 de los 655** de entrenamiento. El archivo conditions.csv contiene también hallazgos y situaciones cuyo dominio oficial es Observation o Measurement. El predictor original contaba todos sus códigos, no solo enfermedades del dominio Condition. El linaje conserva los 830799 registros fuente: no hay pérdidas de conditions.csv ni filas rechazadas en esta auditoría.

Preservar la definición fuente reproduce todos los valores originales. Adoptar el recuento por dominio estándar supone redefinir ese predictor y requiere una decisión científica separada; no se aplica al notebook ni se reentrenan modelos para acomodar el cambio.

## Integridad y plausibilidad

218 controles SQL de unicidad, referencias, dominio y conciliación ejecutados: 0 con violaciones. Son controles propios, no el resultado de DQD.

Advertencias no nulas:

- `condition_occurrence.outside_visit`: 84542.
- `condition_occurrence.outside_observation_period`: 1832.
- `measurement.outside_visit`: 1.
- `observation.outside_visit`: 96451.
- `observation.outside_observation_period`: 3594.
- `person.gender_concept_id.unmapped`: 22851.
- `person.race_concept_id.unmapped`: 22851.
- `person.ethnicity_concept_id.unmapped`: 22851.
- `visit_occurrence.visit_concept_id.unmapped`: 3166.

Las bases originales conservaron sus SHA-256. Los hashes previos de notebooks protegidos y entregables se verifican aparte con `tools/audit_repository.py verify`. Las pruebas pequeñas de ETL cubren precisión, dominio, fechas, referencias, conflictos de vocabulario, rechazo de sobrescritura y repetición idempotente.

**Incidencia de integridad de 02.4:** el SHA-256 inicial fue `15a515fb86bea687abe4809c75e94509d88163a05c65c7e68d1c38c39d30d3a3` y durante la tarea pasó a `c7e863db914575105c4b77a124297473d195c752f49489f9979e0c1c771fc93a` (tamaño de 1947610 a 2597958 bytes, mtime local 15/nov 23:39). Ningún comando de esta migración escribió ni ejecutó ese notebook. Se conserva la versión local sin revertirla ni atribuir el cambio a un autor. La comparación de 655 pacientes se refiere al hash final leído. El control de protección falla expresamente por esa diferencia; los otros diez archivos protegidos coinciden.

**DQD: no ejecutado.** Faltan los paquetes R, almacenamiento y la carga persistente completa. Los controles sobre tablas vacías no aportan evidencia sobre fuentes todavía no cargadas. Consultar [limitaciones y pendientes](limitations.md).

## Artefactos revisables

- `docs/data_audit.json`: controles agregados, conciliación, cobertura y comparación por campo.
- `docs/preflight.json`: bloqueo de almacenamiento cuantificado.
- `docs/official_sources.json`: fuentes oficiales, tamaños y hashes.
- `local/omop54_schema_only.duckdb`: esquema oficial vacío.
- `local/cohort_comparison.duckdb`: tablas de auditoría original/reconstruida si se solicita esa salida; no es un CDM completo.

Todos los archivos por paciente y bases se conservan fuera del índice de Git.
