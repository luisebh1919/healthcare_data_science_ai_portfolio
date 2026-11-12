> Evidencia histórica de la ubicación anterior. Para resultados actuales usar ../reporte_calidad.md.

# Informe de calidad — Lab 12

Estado: **INCOMPLETO**, ejecución provisional sin vocabularios ATHENA. Las diez
actividades se evaluaron contra el README; no se certifica un CDM completo.
Resultados agregados reales; no hay registros de pacientes en este informe.

## Actividades 1–3: ruta, conversión y vocabularios

Ruta manual mínima autorizada, después de revisar OHDSI y documentar sus
dependencias y límites en README.md. Se ejecutó conversión con Python 3.13.5,
DuckDB 1.5.6. R disponible: 4.6.2. No se ejecutó ETLSyntheaBuilder.
Los CSV sí existen en el portafolio vecino; se verificaron encabezados y lectura
completa de patients, encounters y conditions. Los restantes dominios quedan fuera
del alcance mínimo permitido; no se consideran registros clínicos inexistentes.
Conteos, bytes y SHA256 fuente: resultados.json.

| tabla | filas |
| --- | --- |
| person | 22851 |
| visit_occurrence | 1353311 |
| condition_occurrence | 830799 |
| observation_period | 22851 |
| concept | 0 |
| concept_relationship | 0 |
| concept_ancestor | 0 |
| rejected_domain | 0 |

CONCEPT, CONCEPT_RELATIONSHIP y CONCEPT_ANCESTOR están vacías. Cero conceptos
estándar cargados. La carga ATHENA está implementada, pero no se ha ejecutado con
una descarga real: actividad 3 bloqueada. No se sustituyó ATHENA por Eunomia.

## Actividad 4: ER frente a CDM 5.4

Véase diagrama_er.md. La comparación ejecutada contra DDL oficial v5.4.0 encontró
cero columnas faltantes o adicionales en las cuatro tablas clínicas. No prueba
igualdad de tipos, constraints ni semántica. Dos diferencias documentadas:
subconjunto de tablas (simplificación docente legítima) y tipos/procedencia,
raza/etnia y terminología incompletos (limitaciones para corregir).

## Actividad 5: ceros y completitud

| dominio | eventos | sin_mapear | porcentaje |
| --- | --- | --- | --- |
| Condition | 830799 | 830799 | 100.0 |
| Visit | 1353311 | 1353311 | 100.0 |
| Gender | 22851 | 22851 | 100.0 |

Todos los dominios implementados empatan en 100% de conceptos cero porque no
hay vocabulario. Esto impide evaluar qué dominio tiene peor mapeo real. No es
evidencia de que todos los códigos clínicos fuente sean inválidos.
Faltantes de código fuente en conditions: **0**; faltantes de paciente fuente:
**0**. Por tanto los 830799 conceptos cero corresponden a ausencia de mapeo
disponible, no a ausencia de código fuente. Sexo y visita conservan valores de
origen en tablas locales. El ETL no está semánticamente completo.
No se calculan tasas de no mapeo para Drug o Measurement: no se convirtieron.

## Actividad 6 y 10: mismas consultas en base propia y referencia

La referencia es EunomiaDatasets/Synthea27NjParquet_5.4, una muestra **sintética**
de 28 personas, no una población clínica real. El vocabulario reducido tiene
2294 conceptos, 2178 estándar, pero le faltan nombres para conceptos de sexo y
CONCEPT_ANCESTOR está vacío. Sus ceros de jerarquía no prueban ausencia de hijos.
No se inventaron nombres para suplirlos.

| metrica | propia | referencia |
| --- | --- | --- |
| personas | 22851 | 28 |
| mediana días observados inclusivos | 10564.0 | 8700.0 |
| media visitas por persona | 59.22327250448558 | 63.964285714285715 |

La escala, período histórico, muestra y estado del mapeo difieren; no se infiere representatividad ni equivalencia epidemiológica de medias similares. El top propio se agrupa en cero y no es interpretable como diagnóstico.

### sexo

Propia:

| gender_concept_id | concept_name | personas |
| --- | --- | --- |
| 0 | No disponible | 22851 |

Referencia:

| gender_concept_id | concept_name | personas |
| --- | --- | --- |
| 8507 | No disponible | 15 |
| 8532 | No disponible | 13 |

### nacimiento

Propia:

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

Referencia:

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

### diagnosticos

Propia:

| condition_concept_id | concept_name | eventos | personas |
| --- | --- | --- | --- |
| 0 | No disponible | 825373 | 22834 |

Referencia:

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

### tipos_visita

Propia:

| visit_concept_id | concept_name | visitas | personas | media_por_persona |
| --- | --- | --- | --- | --- |
| 0 | No disponible | 1353311 | 22851 | 59.22327250448558 |

Referencia:

| visit_concept_id | concept_name | visitas | personas | media_por_persona |
| --- | --- | --- | --- | --- |
| 9201 | Inpatient Visit | 13 | 7 | 0.4642857142857143 |
| 9202 | Outpatient Visit | 1722 | 28 | 61.5 |
| 9203 | Emergency Room Visit | 56 | 21 | 2.0 |

## Actividad 7: estándar frente a origen

| codigo | personas_origen | condition_concept_id | concept_name | personas_estandar |
| --- | --- | --- | --- | --- |
| 314529007 | 22851 | No disponible | No disponible | No disponible |

El código fuente elegido por frecuencia es SNOMED 314529007, descrito en Lab 10
como Medication review due (situation). No se validó como condición estándar:
Synthea incluye situaciones y hallazgos en conditions. El conteo fuente es real;
el conteo estándar queda **no disponible**, no cero y no el total de concept_id=0.
Con vocabulario, varios códigos fuente pueden confluir en un estándar o un código
puede tener varios destinos; esos cambios y la exclusión de otros dominios deben
cuantificarse antes de interpretar diferencias. No se presupone desigualdad.
En la referencia, el código fuente 444814009.0 corresponde a 40481087
(Viral sinusitis): ambos conteos dan 23 personas. Esto ilustra que pueden coincidir.

## Actividad 8: ventana de observación

| todos | dentro | porcentaje_fuera |
| --- | --- | --- |
| 830799 | 825373 | 0.6531062266565077 |

Hay **5426 eventos** fuera de la ventana aproximada (0.6531062267%). Se
cuentan eventos, no prevalencia; EXISTS impide duplicarlos por múltiples períodos.
Los límites son inclusivos. Ignorar la ventana puede añadir eventos de períodos
sin cobertura demostrada y alterar numeradores y tiempo en riesgo. Primera y
última visita no prueban seguimiento continuo; corresponde al estudiante validar
esta aproximación o definir reglas de huecos. No se amplió para absorber condiciones.

## Actividad 9: ATHENA

Bloqueada para la base propia: no hay tres conceptos estándar identificables.
La consulta prepara vocabulario, dominio, estándar, hijos directos, descendientes
sin el propio concepto y código fuente. Falta revisar los tres conceptos en
https://athena.ohdsi.org/ tras obtener la descarga; no se presentan los datos de
Eunomia como una exploración ATHENA realizada.

## Validación automática

19 comprobaciones de integridad y reconciliación: cero discrepancias. Cinco
pruebas unittest pasaron, incluyendo corrupción
deliberada de PK, FK y mapeo, y solapamiento de períodos con rollback. Las doce
consultas se ejecutaron sobre ambas bases. La ausencia de conceptos distintos de
cero hace vacua parte de la prueba terminológica: **no certifica mapeo completo**.
La prueba de completitud cuantifica 100% sin mapear y mantiene bloqueada la entrega.
El cargador ATHENA real y la ruta R necesitan validación posterior.

## Evaluación de las diez actividades y rúbrica

| Actividad | Estado y criterio |
| --- | --- |
| 1 Ruta | Evaluada y justificada; preferencia OHDSI revisada, alternativa manual elegida |
| 2 Conversión | Ejecutada y reproducible, cuatro tablas, conteos reales; provisional semánticamente |
| 3 Vocabularios | Bloqueada: cero conceptos; cargador preparado |
| 4 ER | Entregado y contrastado con v5.4, dos diferencias documentadas |
| 5 Ceros | Cuantificado por dominio implementado; diagnóstico causal limitado por vocabularios |
| 6 Población | Consultas ejecutadas; sexo, diagnósticos y tipos propios aún sin nombres estándar |
| 7 Estándar/origen | Fuente contado; estándar bloqueado; explicación y SQL entregados |
| 8 Observación | Cuantificada; regla provisional pendiente de validación científica |
| 9 ATHENA | Bloqueada por cuenta/descarga; consulta y campos preparados |
| 10 Referencia | Descargada CDM 5.4 y mismas consultas ejecutadas; limitaciones documentadas |

Rúbrica transversal: conteos epidemiológicos usan COUNT(DISTINCT person_id),
IDs de conceptos se acompañan de concept_name; nombres ausentes se muestran como
no disponibles. Las llaves son lógicas auditadas. No se afirma cumplimiento del
criterio de nombres legibles donde falta vocabulario. No se modificó el enunciado.

## Acciones exactas del estudiante

1. Crear/iniciar sesión en ATHENA, aceptar las licencias aplicables y solicitar
   SNOMED, ICD10CM, RxNorm, LOINC y ATC junto con sus dependencias. Descomprimir
   localmente; no compartir credenciales ni subir los archivos.
2. Proporcionar la ruta al directorio con los tres CSV oficiales. Ejecutar el
   comando con --vocab de README.md en una base nueva o entregar la ruta al agente
   para que complete la ejecución. El generador del informe bloquea datos nuevos
   hasta revisar su interpretación provisional; debe actualizarse tras el mapeo.
3. Validar científicamente ventana continua, clasificación de situaciones fuente,
   reglas de sexo/raza/etnia, condición elegida y diferencias entre poblaciones.
4. Revisar en ATHENA los tres conceptos identificados después del mapeo y registrar
   fecha, nombres, hijos y códigos. Resolver tipos/procedencia cero antes de uso
   científico. Si se exige ruta R, confirmar versión Synthea y facilitar PostgreSQL/JDBC.

No faltan los CSV fuente ni la referencia. Sí faltan vocabularios autorizados y
validación científica; el laboratorio permanece incompleto.
