# Reporte de calidad — Lab 12

Estado de la ejecución: **lab12_validado_listo_revision_academica_con_limitaciones**. Implementación docente con alcance y
limitaciones explícitos; no se certifica un CDM completo ni utilidad clínica.

Ejecución: `c5f4d42e-004f-4fb1-ab25-c056bd999276`; construcción UTC: 2026-11-09T02:23:24.866967+00:00.
Consulta UTC: 2026-11-09T03:14:49.707351+00:00. Python 3.13.5; DuckDB 1.5.6.
Los agregados propios se recalcularon desde esta base, sin leer JSON anteriores.

## Actividades 1–4: conversión, vocabularios y modelo

Ruta manual inicialmente de cuatro tablas, ampliada por migración cuando corresponde, después de
revisar OHDSI. Compatibilidad y alternativa R en README.md. Huellas fuente y
vocabulario en resultados/resultados.json. Diagrama en docs/diagrama_er.md.
Comparación de columnas con DDL oficial v5.4.0 en docs/comparacion_esquema.json;
no certifica tipos, constraints físicos ni conformidad semántica completa.

| tabla | filas |
| --- | --- |
| person | 22851 |
| visit_occurrence | 1353311 |
| condition_occurrence | 390926 |
| observation_period | 22851 |
| concept | 2042800 |
| concept_relationship | 13945404 |
| concept_ancestor | 12073517 |
| rejected_domain | 430935 |
| observation | 439868 |
| measurement | 5 |

| conceptos | estandar |
| --- | --- |
| 2042800 | 846204 |

Vocabulario cargado en esta ejecución; revisar huellas y validación científica.

## Cierre técnico de las diez actividades

Se cotejó de nuevo el README oficial. Las actividades 1–10 tienen evidencia y resultados en esta entrega; actividad 9 usa el paquete ATHENA real conforme a la instrucción del estudiante. No se afirma acceso interactivo al portal. La rúbrica detallada está en docs/criterios_evaluacion.md.

### Corrección final de Visit

| source_class | target_concept_id | target_concept_name | target_concept_code | evidence | changed_rows |
| --- | --- | --- | --- | --- | --- |
| home | 581476 | Home Visit | OMOP4822459 | Correspondencia explícita: atención en domicilio / Home Visit | 6989 |
| snf | 42898160 | Non-hospital institution Visit | LTCP | SNF es institución de cuidados no hospitalaria; agregación a tipo más amplio | 3383 |
| urgentcare | 9203 | Emergency Room Visit | ER | Convención de OHDSI ETL-Synthea v5.4; no equivale a urgencias hospitalarias exclusivamente | 60319 |
| virtual | 722455 | Telehealth | OMOP5556618 | Correspondencia explícita: visita virtual / Telehealth | 3372 |

Se mapearon 74063 visitas, con denominador 1353311. Las clases aún sin mapear se detallan en la tabla Visit; hospice por sí sola no determina el lugar de atención. urgentcare se agrupa en Emergency Room según OHDSI ETL-Synthea: para estudiar urgencias hospitalarias hay que filtrar también la clase fuente. SNF se agrega al tipo institucional no hospitalario, perdiendo granularidad en el estándar pero conservando el origen.

### Completitud global y denominadores

| denominador_eventos_fuente | sin_destino_estandar | porcentaje_sin_destino_estandar |
| --- | --- | --- |
| 830799 | 11435 | 1.3763858646917004 |

Esta tasa global usa 830799 filas originales de conditions.csv y comprueba si cada una tiene algún destino estándar. Hay 11435 sin estándar: moverlas al dominio correcto no las convirtió artificialmente en mapeadas. Las tasas por tabla usan únicamente filas de esa tabla; Gender usa personas. Los dominios sin tabla en la ejecución inicial no tenían una tasa estimable.

## Actividad 5: mapeo y fuente

| dominio | eventos | sin_mapear | porcentaje |
| --- | --- | --- | --- |
| Condition | 390926 | 2497 | 0.6387398126499645 |
| Visit | 1353311 | 3166 | 0.2339447473640575 |
| Gender | 22851 | 0 | 0.0 |
| Observation | 439868 | 8938 | 2.031973228332136 |
| Measurement | 5 | 0 | 0.0 |

| condition_code | condition_patient |
| --- | --- |
| 0 | 0 |

Cada porcentaje anterior usa filas de su propia tabla como denominador; Gender usa personas. Un código ausente es distinto de un código presente sin mapeo. rejected_domain conserva el archivo de destinos inicialmente separados. Drug no se convirtió.

## Antes y después de las correcciones

| dominio | eventos | sin_mapear | porcentaje |
| --- | --- | --- | --- |
| Condition | 399864 | 11435 | 2.8597223055838987 |
| Visit | 1353311 | 77229 | 5.706670528799367 |
| Gender | 22851 | 22851 | 100.0 |

| tabla | antes | despues |
| --- | --- | --- |
| person | 22851 | 22851 |
| condition_occurrence | 399864 | 390926 |
| observation | No cargada | 439868 |
| measurement | No cargada | 5 |

Gender se complementó con los registros canónicos 8507 (MALE) y 8532 (FEMALE) de la referencia oficial OHDSI EunomiaDatasets/GiBleed_5.3. Es un suplemento explícito e histórico, no parte de la descarga ATHENA original. Su URL y SHA256 están en el manifiesto de migración. Se usó M/F explícito; valores desconocidos permanecen en cero.

| fuente | condition | observation | measurement | fuentes_con_destino | destinos | sin_destino | pendientes_otro_dominio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 830799 | 390926 | 439868 | 5 | 830799 | 830799 | 0 | 0 |

No hay pérdida de filas fuente ni rechazo clínico pendiente en esta migración. Se conserva la base anterior. Los eventos sin estándar se mantienen con concepto cero en el dominio conocido; no se inventa una correspondencia. Las tablas de trabajo y el archivo rejected_domain no se suman de nuevo a las tablas clínicas.

| measurement_concept_id | concept_name | eventos | sin_valor_numerico | sin_unidad | personas |
| --- | --- | --- | --- | --- | --- |
| 4178483 | Toxoplasma gondii antibody detected | 5 | 5 | 5 | 5 |

Los cinco hallazgos de anticuerpos conservan su concepto de detección; no se infirió concentración, unidad ni un resultado adicional.

### Auditoría de gingivitis

| concept_id | concept_name | eventos_fuente | personas_fuente_sin_ventana | eventos_transformados | eventos_en_ventana | personas_en_ventana | denominador_personas | porcentaje_personas | exceso_por_expansion_mapeo | grupos_duplicados_exactos_fuente | grupos_duplicados_destino |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4281516 | Gingivitis | 61993 | 18515 | 61993 | 61962 | 18512 | 22851 | 81.0117719137018 | 0 | 0 | 0 |

| grupos_mismo_inicio | grupos_mismo_encuentro | eventos_con_solapamiento_estricto | personas_con_solapamiento |
| --- | --- | --- | --- |
| 0 | 0 | 0 | 0 |

### Observation conservadas sin estándar

| observation_source_value | source_concept_id | source_concept_name | domain_id | standard_concept | invalid_reason | eventos | personas | tiene_destino_estandar_vigente |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 267020005 | 4149855 | H/O: tubal ligation | Observation | No disponible | No disponible | 2418 | 2418 | False |
| 399261000 | 4163883 | History of coronary artery bypass grafting | Observation | No disponible | No disponible | 1592 | 1592 | False |
| 428251008 | 4323208 | History of appendectomy | Observation | No disponible | No disponible | 1035 | 1035 | False |
| 399211009 | 4163874 | History of myocardial infarction | Observation | No disponible | No disponible | 988 | 988 | False |
| 446654005 | 40488824 | Refugee | Observation | No disponible | No disponible | 949 | 949 | False |
| 1290882004 | 1246980 | History of seizure | Observation | No disponible | No disponible | 788 | 788 | False |
| 161665007 | 4059356 | History of renal transplant | Observation | No disponible | No disponible | 671 | 671 | False |
| 449868002 | 42709996 | Smokes tobacco daily | Observation | No disponible | No disponible | 194 | 194 | False |
| 1231000119100 | 43530644 | History of aortic valve replacement | Observation | No disponible | No disponible | 171 | 171 | False |
| 108631000119101 | 46269898 | History of autologous bone marrow transplant | Observation | No disponible | No disponible | 56 | 56 | False |
| 153351000119102 | 45757492 | History of peripheral stem cell transplant | Observation | No disponible | No disponible | 33 | 33 | False |
| 161679004 | 4058431 | H/O: artificial joint | Observation | No disponible | No disponible | 15 | 15 | False |
| 152621000119105 | 46270148 | History of allotransplantation of bone marrow | Observation | No disponible | No disponible | 12 | 12 | False |
| 161622006 | 4058850 | H/O: lower limb amputation | Observation | No disponible | No disponible | 7 | 7 | False |
| 429280009 | 4323766 | History of amputation of foot | Observation | No disponible | No disponible | 6 | 6 | False |
| 119481000119105 | 44782435 | History of aortic valve repair | Observation | No disponible | No disponible | 1 | 1 | False |
| 120991000119102 | 46270016 | History of undergoing in utero procedure while a fetus | Observation | No disponible | No disponible | 1 | 1 | False |
| 161621004 | 4058421 | H/O: upper limb amputation | Observation | No disponible | No disponible | 1 | 1 | False |

El denominador es toda la población sintética (personas distintas), y el numerador personas con un registro dentro de OBSERVATION_PERIOD. Es frecuencia histórica acumulada en datos sintéticos, no prevalencia puntual ni estimación poblacional real. Los eventos repetidos de un paciente no multiplican el numerador. La auditoría compara filas fuente, expansión por mapeo y duplicados exactos; explicación del módulo local y sus límites en docs/correcciones_dominios.md.

### Inventario de vocabularios cargados

| vocabulary_id | conceptos | estandar |
| --- | --- | --- |
| ATC | 7327 | 0 |
| CDM | 1109 | 1109 |
| Concept Class | 433 | 0 |
| Condition Status | 22 | 22 |
| Condition Type | 118 | 0 |
| Cost | 51 | 51 |
| Cost Type | 8 | 0 |
| Death Type | 14 | 0 |
| Device Type | 4 | 0 |
| Domain | 65 | 0 |
| Drug Type | 16 | 0 |
| Episode | 20 | 16 |
| Gender | 2 | 2 |
| ICD10 | 16638 | 0 |
| ICD10CM | 100273 | 0 |
| Korean Revenue Code | 7 | 7 |
| LOINC | 287814 | 125586 |
| Language | 1 | 1 |
| Meas Type | 12 | 0 |
| Metadata | 2 | 1 |
| None | 1 | 0 |
| Note Type | 10 | 0 |
| OSM | 203339 | 203339 |
| Obs Period Type | 6 | 0 |
| Observation Type | 29 | 0 |
| Plan | 11 | 11 |
| Plan Stop Reason | 13 | 13 |
| Procedure Type | 97 | 0 |
| Relationship | 746 | 14 |
| RxNorm | 316330 | 158086 |
| SNOMED | 1106309 | 356613 |
| SOPT | 168 | 162 |
| Sponsor | 6 | 6 |
| Type Concept | 81 | 81 |
| UB04 Point of Origin | 23 | 0 |
| UB04 Pri Typ of Adm | 6 | 6 |
| UB04 Pt dis status | 55 | 0 |
| UB04 Typ bill | 298 | 4 |
| UCUM | 1130 | 1041 |
| US Census | 13 | 13 |
| Visit | 20 | 20 |
| Visit Type | 18 | 0 |
| Vocabulary | 155 | 0 |

| vocabulary_id | vocabulary_version |
| --- | --- |
| ATC | ATC 2026-02-01 |
| ICD10CM | ICD10CM FY2027 code descriptions |
| LOINC | LOINC 2.82 |
| None | v5.0 29-AUG-26 |
| RxNorm | RxNorm 20260601 |
| SNOMED | 2026-02-01 SNOMED CT International Edition; 2026-03-01 SNOMED CT US Edition; 2026-04-08 SNOMED CT UK Edition |

| motivo | eventos |
| --- | --- |
| sin_codigo_fuente | 0 |
| codigo_no_presente_en_paquete | 0 |
| concepto_invalido_D | 2393 |
| concepto_obsoleto_U | 0 |
| concepto_vigente_sin_destino_condition | 104 |

### Causas verificadas de ausencia de mapeo

| motivo | eventos | personas |
| --- | --- | --- |
| concepto_invalido_D | 2393 | 2309 |
| concepto_vigente_sin_destino_condition | 104 | 104 |

| condition_source_value | eventos | personas | concept_id | concept_name | domain_id | standard_concept | invalid_reason | destinos_estandar_vigentes | maps_to_invalidos | reemplazos_vigentes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 62106007 | 1321 | 1285 | 378001 | Concussion with no loss of consciousness | Condition | No disponible | D | 0 | 0 | 0 |
| 6525002 | 1072 | 1072 | 4275756 | Dependent drug abuse | Condition | No disponible | D | 0 | 0 | 0 |
| 94503003 | 62 | 62 | 4314337 | Metastatic malignant neoplasm to prostate | Condition | No disponible | No disponible | 0 | 0 | 0 |
| 94260004 | 42 | 42 | 4311765 | Metastatic malignant neoplasm to colon | Condition | No disponible | No disponible | 0 | 0 | 0 |

La inexistencia se evalúa contra todos los conceptos del paquete, incluidos los inválidos: concept_source_id=0 no demuestra inexistencia. D indica concepto eliminado/inválido; U indica actualizado/obsoleto. No se inventan sustituciones ni se promueve un concepto no estándar a estándar.

### Correspondencia con otros dominios y cobertura

| dominio_destino | filas | registros_fuente |
| --- | --- | --- |
| Measurement | 5 | 5 |
| Observation | 430930 | 430930 |

| dominio_destino | eventos | mapeados_validos | porcentaje_sin_mapeo | porcentaje_fuera_tabla_clinica |
| --- | --- | --- | --- | --- |
| Measurement | 5 | 5 | 0.0 | 0.0 |
| Observation | 430930 | 430930 | 0.0 | 0.0 |

| fuente | fuente_en_condition | fuente_otro_dominio | fuente_sin_traza |
| --- | --- | --- | --- |
| 830799 | 390926 | 430935 | 0 |

Los destinos separados ya están integrados en sus tablas clínicas. rejected_domain queda como archivo de trazabilidad, no como lista actual de descartes.

| dominio_destino | codigo_fuente | descripcion_fuente | concept_id | concept_name | standard_concept | invalid_reason | eventos | registros_fuente | personas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Observation | 314529007 | Medication review due (situation) | 4199788 | Medication review due | S | No disponible | 163616 | 163616 | 22851 |
| Observation | 73595000 | Stress (finding) | 4251306 | Stress | S | No disponible | 64815 | 64815 | 18045 |
| Observation | 160903007 | Full-time employment (finding) | 4053118 | Full-time employment | S | No disponible | 59985 | 59985 | 18042 |
| Observation | 160904001 | Part-time employment (finding) | 4059634 | Part-time employment | S | No disponible | 37497 | 37497 | 14601 |
| Observation | 741062008 | Not in labor force (finding) | 42538208 | Not in labor force | S | No disponible | 20839 | 20839 | 10780 |
| Observation | 706893006 | Victim of intimate partner abuse (finding) | 45768458 | Victim of intimate partner abuse | S | No disponible | 14994 | 14994 | 9835 |
| Observation | 424393004 | Reports of violence in the environment (finding) | 4313322 | Reports of violence in the environment | S | No disponible | 12206 | 12206 | 7583 |
| Observation | 224299000 | Received higher education (finding) | 4076230 | Received higher education | S | No disponible | 10866 | 10866 | 10866 |
| Observation | 73438004 | Unemployed (finding) | 4251171 | Unemployed | S | No disponible | 8440 | 8440 | 6891 |
| Observation | 473461003 | Educated to high school level (finding) | 43021808 | Educated to high school level | S | No disponible | 5432 | 5432 | 5432 |
| Observation | 266948004 | Has a criminal record (finding) | 4145802 | Has a criminal record | S | No disponible | 4434 | 4434 | 4434 |
| Observation | 161744009 | Past pregnancy history of miscarriage (situation) | 4060188 | Past pregnancy history of miscarriage | S | No disponible | 4306 | 4306 | 4306 |
| Observation | 10939881000119105 | Unhealthy alcohol drinking behavior (finding) | 36712761 | Unhealthy alcohol drinking behavior | S | No disponible | 3806 | 3806 | 3380 |
| Observation | 384709000 | Sprain (morphologic abnormality) | 4298490 | Sprain | S | No disponible | 3276 | 3276 | 3062 |
| Observation | 105531004 | Housing unsatisfactory (finding) | 4022661 | Housing problem | S | No disponible | 2784 | 2784 | 2784 |
| Observation | 266934004 | Transport problem (finding) | 4141789 | Transport problem | S | No disponible | 2220 | 2220 | 2220 |
| Observation | 713458007 | Lack of access to transportation (finding) | 37017222 | Lack of access to transportation | S | No disponible | 2210 | 2210 | 2210 |
| Observation | 224295006 | Only received primary school education (finding) | 4072733 | Only received primary school education | S | No disponible | 2111 | 2111 | 2111 |
| Observation | 840544004 | Suspected disease caused by Severe acute respiratory coronavirus 2 (situation) | 37311060 | Suspected COVID-19 | S | No disponible | 1932 | 1932 | 1932 |
| Observation | 1187604002 | Serving in military service (finding) | 37162400 | Serving in military service | S | No disponible | 1029 | 1029 | 1029 |
| Observation | 48333001 | Burn injury (morphologic abnormality) | 4168004 | Burn injury | S | No disponible | 875 | 875 | 859 |
| Observation | 698306007 | Awaiting transplantation of kidney (situation) | 44784262 | Awaiting transplantation of kidney | S | No disponible | 775 | 775 | 774 |
| Observation | 248595008 | Sputum finding (finding) | 4089228 | Sputum finding | S | No disponible | 663 | 663 | 663 |
| Observation | 183996000 | Sterilization requested (situation) | 4086788 | Sterilization requested | S | No disponible | 579 | 579 | 579 |
| Observation | 32911000 | Homeless (finding) | 4139934 | Homeless | S | No disponible | 416 | 416 | 399 |
| Observation | 315268008 | Suspected prostate cancer (situation) | 4197714 | Malignant neoplasm of prostate suspected | S | No disponible | 382 | 382 | 293 |
| Observation | 162573006 | Suspected lung cancer (situation) | 4038238 | Malignant neoplasm of lung suspected | S | No disponible | 217 | 217 | 217 |
| Observation | 876882001 | Died in hospice (finding) | 618845 | Died in hospice | S | No disponible | 154 | 154 | 154 |
| Observation | 698303004 | Awaiting transplantation of bone marrow (situation) | 44782657 | Awaiting transplantation of bone marrow | S | No disponible | 55 | 55 | 54 |
| Observation | 160701002 | Social migrant (finding) | 4053080 | Social migrant | S | No disponible | 13 | 13 | 13 |
| Measurement | 428915008 | Toxoplasma gondii antibody detected (finding) | 4178483 | Toxoplasma gondii antibody detected | S | No disponible | 5 | 5 | 5 |
| Observation | 1003755004 | Allergy to Hevea brasiliensis latex protein (finding) | 43530807 | Allergic disposition | S | No disponible | 2 | 2 | 2 |
| Observation | 287185009 | Attempted suicide by cutting or stabbing | 443279 | Attempted suicide by cutting or stabbing | S | No disponible | 1 | 1 | 1 |

### Visitas y sexo

| clase_fuente | eventos |
| --- | --- |
| hospice | 3166 |

| sexo_fuente | registros |
| --- | --- |
| F | 11446 |
| M | 11405 |

El sexo se corrigió con el suplemento canónico documentado; las clases de visita sin mapeo siguen siendo una limitación del CASE conservado.

### Dominio del concepto fuente frente a tabla destino

| dominio_fuente | registros | sin_destino_estandar | porcentaje |
| --- | --- | --- | --- |
| Condition | 390926 | 2497 | 0.6387398126499645 |
| Measurement | 5 | 0 | 0.0 |
| Observation | 439868 | 8938 | 2.031973228332136 |

Los eventos de Observation sin Maps to se reubicaron con concepto cero en OBSERVATION. No se interpretan como diagnósticos.

| eventos_sin_maps_to_valido |
| --- |
| 0 |

## Actividad 6: caracterización actual

### personas

| personas |
| --- |
| 22851 |

### sexo

| gender_concept_id | concept_name | personas |
| --- | --- | --- |
| 8507 | MALE | 11405 |
| 8532 | FEMALE | 11446 |

### nacimiento

| year_of_birth | personas |
| --- | --- |
| 1915 | 17 |
| 1916 | 96 |
| 1917 | 59 |
| 1918 | 90 |
| 1919 | 44 |
| 1920 | 74 |
| 1921 | 62 |
| 1922 | 89 |
| 1923 | 83 |
| 1924 | 42 |
| 1925 | 64 |
| 1926 | 17 |
| 1927 | 27 |
| 1928 | 90 |
| 1929 | 51 |
| 1930 | 30 |
| 1931 | 59 |
| 1932 | 68 |
| 1933 | 59 |
| 1934 | 54 |
| 1935 | 41 |
| 1936 | 60 |
| 1937 | 48 |
| 1938 | 30 |
| 1939 | 46 |
| 1940 | 38 |
| 1941 | 62 |
| 1942 | 157 |
| 1943 | 121 |
| 1944 | 123 |
| 1945 | 141 |
| 1946 | 113 |
| 1947 | 140 |
| 1948 | 155 |
| 1949 | 144 |
| 1950 | 158 |
| 1951 | 190 |
| 1952 | 221 |
| 1953 | 181 |
| 1954 | 203 |
| 1955 | 205 |
| 1956 | 203 |
| 1957 | 258 |
| 1958 | 274 |
| 1959 | 258 |
| 1960 | 239 |
| 1961 | 266 |
| 1962 | 309 |
| 1963 | 290 |
| 1964 | 319 |
| 1965 | 274 |
| 1966 | 317 |
| 1967 | 319 |
| 1968 | 310 |
| 1969 | 278 |
| 1970 | 349 |
| 1971 | 332 |
| 1972 | 328 |
| 1973 | 324 |
| 1974 | 290 |
| 1975 | 319 |
| 1976 | 333 |
| 1977 | 290 |
| 1978 | 303 |
| 1979 | 280 |
| 1980 | 318 |
| 1981 | 295 |
| 1982 | 269 |
| 1983 | 270 |
| 1984 | 257 |
| 1985 | 251 |
| 1986 | 243 |
| 1987 | 222 |
| 1988 | 254 |
| 1989 | 282 |
| 1990 | 228 |
| 1991 | 270 |
| 1992 | 290 |
| 1993 | 266 |
| 1994 | 309 |
| 1995 | 265 |
| 1996 | 287 |
| 1997 | 269 |
| 1998 | 283 |
| 1999 | 289 |
| 2000 | 259 |
| 2001 | 311 |
| 2002 | 283 |
| 2003 | 291 |
| 2004 | 313 |
| 2005 | 315 |
| 2006 | 298 |
| 2007 | 257 |
| 2008 | 302 |
| 2009 | 257 |
| 2010 | 264 |
| 2011 | 272 |
| 2012 | 218 |
| 2013 | 235 |
| 2014 | 236 |
| 2015 | 232 |
| 2016 | 220 |
| 2017 | 242 |
| 2018 | 225 |
| 2019 | 217 |
| 2020 | 225 |
| 2021 | 210 |
| 2022 | 199 |
| 2023 | 231 |
| 2024 | 201 |
| 2025 | 184 |
| 2026 | 123 |

### observacion

| mediana_dias | personas_con_periodo |
| --- | --- |
| 10564.0 | 22851 |

### diagnosticos

| condition_concept_id | concept_name | eventos | personas |
| --- | --- | --- | --- |
| 4281516 | Gingivitis | 61962 | 18512 |
| 40481087 | Viral sinusitis | 23432 | 14634 |
| 4309238 | Social isolation | 23113 | 12223 |
| 4172829 | Limited social contact | 22951 | 12198 |
| 4060985 | Body mass index 30+ - obesity | 11026 | 11026 |
| 4090111 | Gingival disease | 18191 | 10669 |
| 4112343 | Acute viral pharyngitis | 13403 | 10050 |
| 40274283 | Primary dental caries | 13918 | 9537 |
| 260139 | Acute bronchitis | 10984 | 8912 |
| 37018196 | Prediabetes | 8713 | 8713 |
| 439777 | Anemia | 8246 | 8246 |
| 436096 | Chronic pain | 5496 | 5496 |
| 320128 | Essential hypertension | 5182 | 5182 |
| 4059650 | Risk activity involvement | 5512 | 5130 |
| 257012 | Chronic sinusitis | 4430 | 4426 |
| 4217975 | Normal pregnancy | 9580 | 4085 |
| 4132891 | Chronic low back pain | 4081 | 4081 |
| 435081 | Abnormal findings diagnostic imaging heart+coronary circulat | 3801 | 3801 |
| 4185932 | Ischemic heart disease | 3781 | 3781 |
| 4322737 | Infection of tooth | 4085 | 3451 |

### visitas

| media_visitas | personas |
| --- | --- |
| 59.22327250448558 | 22851 |

### tipos_visita

| visit_concept_id | concept_name | visitas | personas | media_por_persona |
| --- | --- | --- | --- | --- |
| 0 | No matching concept | 3166 | 2630 | 0.13854973524134612 |
| 9201 | Inpatient Visit | 21602 | 7816 | 0.9453415605443963 |
| 9202 | Outpatient Visit | 1203843 | 22851 | 52.68228961533412 |
| 9203 | Emergency Room Visit | 110956 | 17826 | 4.85562995054921 |
| 581476 | Home Visit | 6989 | 411 | 0.3058509474421251 |
| 722455 | Telehealth | 3372 | 1590 | 0.147564658001838 |
| 42898160 | Non-hospital institution Visit | 3383 | 3094 | 0.14804603737254388 |

## Actividad 7: estándar frente a origen

Se elige el código fuente más frecuente por personas distintas. Cada destino
se cuenta por separado: no sumar personas entre destinos. Varios códigos pueden
confluir en un estándar y un código puede tener varios destinos.

| codigo | personas_origen | condition_concept_id | concept_name | personas_estandar |
| --- | --- | --- | --- | --- |
| 66383009 | 18512 | 4281516 | Gingivitis | 18512 |

Diferencias actuales (estándar menos origen):

| condition_concept_id | concept_name | diferencia_personas |
| --- | --- | --- |
| 4281516 | Gingivitis | 0 |

La consulta usa eventos dentro de OBSERVATION_PERIOD. Si ambos conteos coinciden, no se fuerza una diferencia: se verifica qué códigos fuente contribuyen al mismo estándar.

| condition_concept_id | concept_name | condition_source_value | personas |
| --- | --- | --- | --- |
| 4281516 | Gingivitis | 66383009 | 18512 |

## Actividad 8: observación

| todos | dentro | porcentaje_fuera |
| --- | --- | --- |
| 390926 | 389254 | 0.4277024296158352 |

Eventos fuera de ventana: **1672**.

Ventana aproximada inclusiva de primera visita a último fin de visita. No demuestra seguimiento continuo. EXISTS evita multiplicación por períodos. Ignorar cobertura puede alterar numeradores y tiempo en riesgo.

## Actividad 9: candidatos para verificar en ATHENA

Datos locales: no acreditan búsqueda interactiva en ATHENA. Hijos directos usan min_levels=1 y descendientes excluyen el propio concepto. Una jerarquía vacía no prueba ausencia de hijos.

| condition_concept_id | concept_name | vocabulary_id | domain_id | standard_concept | hijos_directos | descendientes | codigo_origen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4281516 | Gingivitis | SNOMED | Condition | S | 35 | 76 | 66383009 |
| 40481087 | Viral sinusitis | SNOMED | Condition | S | 1 | 1 | 444814009 |
| 4309238 | Social isolation | SNOMED | Condition | S | 6 | 6 | 422650009 |

## Actividad 10: referencia

### Auditoría temporal por dominio

| dominio | eventos | fuera | porcentaje_fuera |
| --- | --- | --- | --- |
| Condition | 390926 | 1672 | 0.4277024296158352 |
| Measurement | 5 | 0 | 0.0 |
| Observation | 439868 | 3754 | 0.8534378495366792 |

| denominador_personas | personas_hueco_mayor_365 | mayor_hueco_dias | mediana_maximo_hueco |
| --- | --- | --- | --- |
| 22851 | 21165 | 20404 | 3252.0 |

La aritmética temporal es coherente, pero primera/última visita no prueba observación continua: 21165 personas tienen al menos un hueco mayor de 365 días sin visitas registradas. No se usa esta aproximación como tiempo-persona clínicamente validado. Se preservan eventos externos y se excluyen mediante EXISTS en las consultas que requieren cobertura; no se amplió la ventana para ocultarlos.

Referencia independiente: OHDSI/EunomiaDatasets Synthea27NjParquet_5.4; ZIP SHA256 `456cbf60024dddab17a2ff68f4001872200cf3a24c32cb5ce2db79b52ef20a48`.

Eunomia es sintética con vocabulario reducido. Se usó el mismo SQL; interpretar diferencias por tamaño, período y vocabulario.

La referencia tiene 28 personas; es demostración, no una población clínica real. Nombres Gender ausentes en su CONCEPT reducido se presentan con los nombres canónicos OHDSI 8507/8532, sin añadir conceptos ni cambiar conteos de esa referencia. Las versiones distintas de vocabulario pueden explicar diferencias de asignación de dominio.

| metrica | propia | referencia |
| --- | --- | --- |
| personas | 22851 | 28 |
| mediana_dias | 10564.0 | 8700.0 |
| media_visitas | 59.22327250448558 | 63.964285714285715 |

### Referencia: sexo

| gender_concept_id | concept_name | personas |
| --- | --- | --- |
| 8507 | MALE | 15 |
| 8532 | FEMALE | 13 |

### Referencia: nacimiento

| year_of_birth | personas |
| --- | --- |
| 1938 | 2 |
| 1953 | 2 |
| 1964 | 1 |
| 1967 | 1 |
| 1968 | 1 |
| 1970 | 2 |
| 1971 | 1 |
| 1978 | 1 |
| 1979 | 1 |
| 1980 | 1 |
| 1983 | 1 |
| 1986 | 1 |
| 1987 | 1 |
| 1988 | 1 |
| 1996 | 1 |
| 1997 | 1 |
| 1998 | 2 |
| 2000 | 1 |
| 2003 | 1 |
| 2011 | 1 |
| 2014 | 1 |
| 2015 | 1 |
| 2019 | 1 |
| 2022 | 1 |

### Referencia: diagnosticos

| condition_concept_id | concept_name | eventos | personas |
| --- | --- | --- | --- |
| 40481087 | Viral sinusitis | 61 | 23 |
| 4251306 | Stress | 113 | 22 |
| 4172829 | Limited social contact | 35 | 19 |
| 4309238 | Social isolation | 40 | 17 |
| 4112343 | Acute viral pharyngitis | 29 | 16 |
| 45768458 | Victim of intimate partner abuse | 16 | 12 |
| 260139 | Acute bronchitis | 19 | 10 |
| 372328 | Otitis media | 13 | 9 |
| 439777 | Anemia | 8 | 8 |
| 4059650 | Risk activity involvement | 9 | 7 |
| 28060 | Streptococcal sore throat | 6 | 6 |
| 4217975 | Normal pregnancy | 12 | 6 |
| 257012 | Chronic sinusitis | 5 | 5 |
| 320128 | Essential hypertension | 5 | 5 |
| 4078393 | Miscarriage in first trimester | 5 | 5 |
| 4132891 | Chronic low back pain | 5 | 5 |
| 4214746 | Severe anxiety (panic) | 5 | 4 |
| 43530622 | Chronic neck pain | 4 | 4 |
| 81151 | Sprain of ankle | 3 | 3 |
| 254761 | Cough | 3 | 3 |

### Referencia: tipos_visita

| visit_concept_id | concept_name | visitas | personas | media_por_persona |
| --- | --- | --- | --- | --- |
| 9201 | Inpatient Visit | 13 | 7 | 0.4642857142857143 |
| 9202 | Outpatient Visit | 1722 | 28 | 61.5 |
| 9203 | Emergency Room Visit | 56 | 21 | 2.0 |

## Relaciones verificadas de los conceptos principales

| source_concept_id | source_concept_name | concept_code | relationship_id | valid_start_date | valid_end_date | invalid_reason | concept_id | concept_name | domain_id | standard_concept |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4281516 | Gingivitis | 66383009 | Maps to | 1970-01-01 | 2099-12-31 | No disponible | 4281516 | Gingivitis | Condition | S |
| 4309238 | Social isolation | 422650009 | Maps to | 1970-01-01 | 2099-12-31 | No disponible | 4309238 | Social isolation | Condition | S |
| 40481087 | Viral sinusitis | 444814009 | Maps to | 2010-07-31 | 2099-12-31 | No disponible | 40481087 | Viral sinusitis | Condition | S |

Verificación local sobre el paquete ATHENA identificado por huellas; enlaces y limitación de acceso web en docs/athena_revision.md. La búsqueda interactiva no pudo certificarse: no hay navegador conectado y el lector web no devuelve el contenido de los conceptos.

| relacion | huerfanos |
| --- | --- |
| concept_relationship.origen | 0 |
| concept_relationship.destino | 0 |
| concept_ancestor.ancestro | 0 |
| concept_ancestor.descendiente | 0 |

## Auditoría final de temporalidad, duplicación y relaciones

| control | discrepancias |
| --- | --- |
| visitas_antes_nacimiento | 0 |
| visitas_invertidas | 0 |
| fuente_clinica_antes_nacimiento | 0 |
| periodo_no_reproduce_limites_visitas | 0 |
| eventos_clinicos_fin_antes_inicio | 0 |

| control | discrepancias |
| --- | --- |
| grupos_duplicados_fuente_exactos | 0 |
| eventos_sin_traza | 0 |
| trazas_sin_evento | 0 |
| traza_cambia_persona | 0 |

| control | discrepancias |
| --- | --- |
| concept_vocabulary_fk | 0 |
| concept_domain_fk | 0 |
| concept_class_fk | 0 |

| control | discrepancias |
| --- | --- |
| concept_synonym.concept_id_fk | 0 |
| concept_synonym.language_concept_id_fk | 0 |
| drug_strength.drug_concept_id_fk | 0 |
| drug_strength.ingredient_concept_id_fk | 0 |
| drug_strength.amount_unit_concept_id_fk | 0 |
| drug_strength.numerator_unit_concept_id_fk | 0 |
| drug_strength.denominator_unit_concept_id_fk | 0 |
| pack_content.pack_concept_id_fk | 0 |
| pack_content.drug_concept_id_fk | 0 |
| concept_metadata.concept_id_fk | 0 |
| concept_relationship_metadata.concept_id_1_fk | 0 |
| concept_relationship_metadata.concept_id_2_fk | 0 |
| vocabulary.vocabulary_concept_id_fk | 0 |
| domain.domain_concept_id_fk | 0 |
| concept_class.concept_class_concept_id_fk | 0 |
| relationship.relationship_concept_id_fk | 0 |
| concept_pk | 0 |

La verificación reproducible de insumos y consultas repetidas está en resultados/reproducibilidad.json. Su alcance es repetición analítica e identidad de archivos, no una nueva generación Synthea con semilla desconocida.

## Validación automática

| comprobacion | discrepancias |
| --- | --- |
| person_pk | 0 |
| visit_occurrence_pk | 0 |
| visit_occurrence_person_fk | 0 |
| condition_occurrence_pk | 0 |
| condition_occurrence_person_fk | 0 |
| observation_period_pk | 0 |
| observation_period_person_fk | 0 |
| condition_visit_fk | 0 |
| periodos_invertidos | 0 |
| periodos_solapados | 0 |
| conceptos_condition_invalidos | 0 |
| person_concept_fk | 0 |
| visit_occurrence_concept_fk | 0 |
| person_count | 0 |
| visit_count | 0 |
| condition_reconciliation | 0 |
| clinical_population | 0 |
| clinical_window | 0 |
| observation_pk | 0 |
| observation_person_fk | 0 |
| observation_visit_fk | 0 |
| observation_domain | 0 |
| observation_source_count | 0 |
| observation_lineage | 0 |
| observation_maps_to | 0 |
| measurement_pk | 0 |
| measurement_person_fk | 0 |
| measurement_visit_fk | 0 |
| measurement_domain | 0 |
| measurement_source_count | 0 |
| measurement_lineage | 0 |
| measurement_maps_to | 0 |
| source_without_clinical_trace | 0 |
| lineage_without_source | 0 |
| duplicate_lineage | 0 |
| gender_mapping | 0 |
| gender_standard | 0 |
| measurement_without_numeric_invention | 0 |
| visit_standard_domain | 0 |
| visit_rule_concordance | 0 |
| visitas_antes_nacimiento | 0 |
| visitas_invertidas | 0 |
| fuente_clinica_antes_nacimiento | 0 |
| periodo_no_reproduce_limites_visitas | 0 |
| eventos_clinicos_fin_antes_inicio | 0 |
| grupos_duplicados_fuente_exactos | 0 |
| eventos_sin_traza | 0 |
| trazas_sin_evento | 0 |
| traza_cambia_persona | 0 |
| concept_vocabulary_fk | 0 |
| concept_domain_fk | 0 |
| concept_class_fk | 0 |
| concept_synonym.concept_id_fk | 0 |
| concept_synonym.language_concept_id_fk | 0 |
| drug_strength.drug_concept_id_fk | 0 |
| drug_strength.ingredient_concept_id_fk | 0 |
| drug_strength.amount_unit_concept_id_fk | 0 |
| drug_strength.numerator_unit_concept_id_fk | 0 |
| drug_strength.denominator_unit_concept_id_fk | 0 |
| pack_content.pack_concept_id_fk | 0 |
| pack_content.drug_concept_id_fk | 0 |
| concept_metadata.concept_id_fk | 0 |
| concept_relationship_metadata.concept_id_1_fk | 0 |
| concept_relationship_metadata.concept_id_2_fk | 0 |
| vocabulary.vocabulary_concept_id_fk | 0 |
| domain.domain_concept_id_fk | 0 |
| concept_class.concept_class_concept_id_fk | 0 |
| relationship.relationship_concept_id_fk | 0 |
| concept_pk | 0 |

Cero discrepancias no acredita completitud semántica: sin vocabulario parte
de la validación terminológica es vacua. La transición del informe se prueba con
vocabulario artificial aislado, no con ATHENA real.

## Evaluación de las diez actividades

| Actividad | Evaluación |
| --- | --- |
| 1 | Ruta y compatibilidad documentadas |
| 2 | Conversión ejecutada; conteos actuales arriba |
| 3 | Carga e inventario verificados; suplemento Gender identificado por separado |
| 4 | Diagrama y comparación 5.4 conservados; subconjunto docente |
| 5 | Porcentajes y causas cuantificados; límites y denominadores explícitos |
| 6 | Consultas ejecutadas; nombres ausentes no se inventan |
| 7 | Conteos, igualdad y relaciones explicados; frecuencia sintética no extrapolable |
| 8 | Efecto y huecos cuantificados; aproximación no certificada como seguimiento continuo |
| 9 | Verificada en ATHENA descargado; acceso al portal no realizado, limitación permitida |
| 10 | Referencia solo si se solicitó explícitamente |

## Pendientes científicos y técnicos

- Validar seguimiento continuo, huecos y censura; ausencia de registros no implica
  ausencia de enfermedad.
- Revisar situaciones/hallazgos de Synthea y destinos fuera de Condition; confirmar
  la condición frecuente elegida para comparar estándar y origen.
- Completar raza, etnia y tipos/procedencia actualmente cero; validar sexo y visita.
- Verificar jerarquías y tres conceptos en ATHENA, sin sustituir la descarga por Eunomia.
- Ruta R preparada pero no ejecutada; compatibilidad del JAR local no certificada.

Acciones exactas para actividades 3, 7 y 9: README.md. Sin merge a main.
