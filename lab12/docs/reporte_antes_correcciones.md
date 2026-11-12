# Reporte de calidad — Lab 12

Estado: **con_vocabulario_pendiente_revision**. Laboratorio pendiente de validación científica y
verificación manual de ATHENA. No se certifica un CDM completo.

Ejecución: `976e8ad6-69eb-4b7d-9308-92383369ea1e`; construcción UTC: 2026-11-09T02:23:24.866967+00:00.
Consulta UTC: 2026-11-09T02:45:49.685565+00:00. Python 3.13.5; DuckDB 1.5.6.
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
| condition_occurrence | 399864 |
| observation_period | 22851 |
| concept | 2042798 |
| concept_relationship | 13945404 |
| concept_ancestor | 12073517 |
| rejected_domain | 430935 |

| conceptos | estandar |
| --- | --- |
| 2042798 | 846202 |

Vocabulario cargado en esta ejecución; revisar huellas y validación científica.

## Actividad 5: mapeo y fuente

| dominio | eventos | sin_mapear | porcentaje |
| --- | --- | --- | --- |
| Condition | 399864 | 11435 | 2.8597223055838987 |
| Visit | 1353311 | 77229 | 5.706670528799367 |
| Gender | 22851 | 22851 | 100.0 |

| condition_code | condition_patient |
| --- | --- |
| 0 | 0 |

Cada porcentaje anterior usa filas de su propia tabla como denominador; Gender usa personas. Un código ausente es distinto de un código presente sin mapeo. rejected_domain conserva el archivo de destinos inicialmente separados. Drug no se convirtió.

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
| concepto_vigente_sin_destino_condition | 9042 |

### Causas verificadas de ausencia de mapeo

| motivo | eventos | personas |
| --- | --- | --- |
| concepto_invalido_D | 2393 | 2309 |
| concepto_vigente_sin_destino_condition | 9042 | 6976 |

| condition_source_value | eventos | personas | concept_id | concept_name | domain_id | standard_concept | invalid_reason | destinos_estandar_vigentes | maps_to_invalidos | reemplazos_vigentes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 267020005 | 2418 | 2418 | 4149855 | H/O: tubal ligation | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 399261000 | 1592 | 1592 | 4163883 | History of coronary artery bypass grafting | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 62106007 | 1321 | 1285 | 378001 | Concussion with no loss of consciousness | Condition | No disponible | D | 0 | 0 | 0 |
| 6525002 | 1072 | 1072 | 4275756 | Dependent drug abuse | Condition | No disponible | D | 0 | 0 | 0 |
| 428251008 | 1035 | 1035 | 4323208 | History of appendectomy | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 399211009 | 988 | 988 | 4163874 | History of myocardial infarction | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 446654005 | 949 | 949 | 40488824 | Refugee | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 1290882004 | 788 | 788 | 1246980 | History of seizure | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 161665007 | 671 | 671 | 4059356 | History of renal transplant | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 449868002 | 194 | 194 | 42709996 | Smokes tobacco daily | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 1231000119100 | 171 | 171 | 43530644 | History of aortic valve replacement | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 94503003 | 62 | 62 | 4314337 | Metastatic malignant neoplasm to prostate | Condition | No disponible | No disponible | 0 | 0 | 0 |
| 108631000119101 | 56 | 56 | 46269898 | History of autologous bone marrow transplant | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 94260004 | 42 | 42 | 4311765 | Metastatic malignant neoplasm to colon | Condition | No disponible | No disponible | 0 | 0 | 0 |
| 153351000119102 | 33 | 33 | 45757492 | History of peripheral stem cell transplant | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 161679004 | 15 | 15 | 4058431 | H/O: artificial joint | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 152621000119105 | 12 | 12 | 46270148 | History of allotransplantation of bone marrow | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 161622006 | 7 | 7 | 4058850 | H/O: lower limb amputation | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 429280009 | 6 | 6 | 4323766 | History of amputation of foot | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 119481000119105 | 1 | 1 | 44782435 | History of aortic valve repair | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 120991000119102 | 1 | 1 | 46270016 | History of undergoing in utero procedure while a fetus | Observation | No disponible | No disponible | 0 | 0 | 0 |
| 161621004 | 1 | 1 | 4058421 | H/O: upper limb amputation | Observation | No disponible | No disponible | 0 | 0 | 0 |

La inexistencia se evalúa contra todos los conceptos del paquete, incluidos los inválidos: concept_source_id=0 no demuestra inexistencia. D indica concepto eliminado/inválido; U indica actualizado/obsoleto. No se inventan sustituciones ni se promueve un concepto no estándar a estándar.

### Correspondencia con otros dominios y cobertura

| dominio_destino | filas | registros_fuente |
| --- | --- | --- |
| Measurement | 5 | 5 |
| Observation | 430930 | 430930 |

| dominio_destino | eventos | mapeados_validos | porcentaje_sin_mapeo | porcentaje_fuera_tabla_clinica |
| --- | --- | --- | --- | --- |
| Measurement | 5 | 5 | 0.0 | 100.0 |
| Observation | 430930 | 430930 | 0.0 | 100.0 |

| fuente | fuente_en_condition | fuente_otro_dominio | fuente_sin_traza |
| --- | --- | --- | --- |
| 830799 | 399864 | 430935 | 0 |

Los destinos separados se conservan en staging, pero todavía faltan sus tablas clínicas.

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
| home | 6989 |
| hospice | 3166 |
| snf | 3383 |
| urgentcare | 60319 |
| virtual | 3372 |

| sexo_fuente | registros |
| --- | --- |
| F | 11446 |
| M | 11405 |

Los valores fuente de sexo están presentes; conceptos Gender cero por falta de vocabulario no son datos ausentes. Las clases Visit sin mapeo siguen siendo una limitación del CASE.

### Dominio del concepto fuente frente a tabla destino

| dominio_fuente | registros | sin_destino_estandar | porcentaje |
| --- | --- | --- | --- |
| Condition | 390926 | 2497 | 0.6387398126499645 |
| Measurement | 5 | 0 | 0.0 |
| Observation | 439868 | 8938 | 2.031973228332136 |

Los eventos de Observation sin Maps to todavía quedan como cero en CONDITION: es una limitación del ETL inicial.

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
| 0 | No matching concept | 22851 |

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
| 0 | No matching concept | 11273 | 8403 |
| 439777 | Anemia | 8246 | 8246 |
| 436096 | Chronic pain | 5496 | 5496 |
| 320128 | Essential hypertension | 5182 | 5182 |
| 4059650 | Risk activity involvement | 5512 | 5130 |
| 257012 | Chronic sinusitis | 4430 | 4426 |
| 4217975 | Normal pregnancy | 9580 | 4085 |
| 4132891 | Chronic low back pain | 4081 | 4081 |
| 435081 | Abnormal findings diagnostic imaging heart+coronary circulat | 3801 | 3801 |
| 4185932 | Ischemic heart disease | 3781 | 3781 |

### visitas

| media_visitas | personas |
| --- | --- |
| 59.22327250448558 | 22851 |

### tipos_visita

| visit_concept_id | concept_name | visitas | personas | media_por_persona |
| --- | --- | --- | --- | --- |
| 0 | No matching concept | 77229 | 11832 | 3.3796770382040173 |
| 9201 | Inpatient Visit | 21602 | 7816 | 0.9453415605443963 |
| 9202 | Outpatient Visit | 1203843 | 22851 | 52.68228961533412 |
| 9203 | Emergency Room Visit | 50637 | 16040 | 2.2159642904030457 |

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
| 399864 | 398032 | 0.45815577296280735 |

Eventos fuera de ventana: **1832**.

Ventana aproximada inclusiva de primera visita a último fin de visita. No demuestra seguimiento continuo. EXISTS evita multiplicación por períodos. Ignorar cobertura puede alterar numeradores y tiempo en riesgo.

## Actividad 9: candidatos para verificar en ATHENA

Datos locales: no acreditan búsqueda interactiva en ATHENA. Hijos directos usan min_levels=1 y descendientes excluyen el propio concepto. Una jerarquía vacía no prueba ausencia de hijos.

| condition_concept_id | concept_name | vocabulary_id | domain_id | standard_concept | hijos_directos | descendientes | codigo_origen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4281516 | Gingivitis | SNOMED | Condition | S | 35 | 76 | 66383009 |
| 40481087 | Viral sinusitis | SNOMED | Condition | S | 1 | 1 | 444814009 |
| 4309238 | Social isolation | SNOMED | Condition | S | 6 | 6 | 422650009 |

## Actividad 10: referencia

No se solicitó referencia; no se reutilizó una comparación anterior.

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

Cero discrepancias no acredita completitud semántica: sin vocabulario parte
de la validación terminológica es vacua. La transición del informe se prueba con
vocabulario artificial aislado, no con ATHENA real.

## Evaluación de las diez actividades

| Actividad | Evaluación |
| --- | --- |
| 1 | Ruta y compatibilidad documentadas |
| 2 | Conversión ejecutada; conteos actuales arriba |
| 3 | Carga e inventario verificables arriba; pendiente solo si CONCEPT vacía |
| 4 | Diagrama y comparación 5.4 conservados; subconjunto docente |
| 5 | Porcentajes y causas cuantificados por tabla destino y dominio fuente; revisión científica pendiente |
| 6 | Consultas ejecutadas; nombres ausentes no se inventan |
| 7 | Conteos y relaciones verificados arriba; interpretación científica por validar |
| 8 | Efecto cuantificado; ventana pendiente de validación científica |
| 9 | Conceptos, códigos y jerarquías locales verificados; contraste interactivo pendiente |
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
