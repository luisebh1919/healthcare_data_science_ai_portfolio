> Registro histórico de una etapa anterior. Para el estado definitivo usar ../README.md y ../reporte_calidad.md; Visit fue corregido posteriormente.

# Auditoría de ATHENA y reanudación

El worktree y remoto corresponden a healthcare_data_science_ai_portfolio, rama
feat/lab12-omop-cdm. git status muestra únicamente lab12/ sin seguimiento.

## Interrupción

El último comando cancelado contenía una edición Python de pipeline.py seguida de
un ETL hacia omop_athena_v2.duckdb. La inspección confirmó que no se aplicó la edición,
no existe esa segunda base y no quedó proceso pipeline en ejecución. Sí se había
creado calidad_vocabularios.sql mediante la operación previa. Se continuó desde
omop_athena.duckdb, sin repetir su construcción ni el ETL.

## Actividad 3: paquetes y relaciones

Las descargas son complementarias: el primer ZIP contiene SNOMED, RxNorm, LOINC y
ATC; el segundo ICD10CM. Se combinaron previamente todas las tablas por unión de
filas distintas, sin filtrar relaciones o dependencias, y sin conflictos de claves.
La base conservada tiene 2042798 conceptos (846202 estándar), 13945404 relaciones y
12073517 pares ancestro/descendiente. Se preservaron nueve tablas auxiliares.
Se comprobaron los cuatro extremos referenciales: cero huérfanos.

Versiones: OMOP Vocabulary v5.0 29-AUG-26; SNOMED International 2026-02-01,
US 2026-03-01 y UK 2026-04-08; ICD10CM FY2027; RxNorm 20260601; LOINC 2.82;
ATC 2026-02-01. La fila de vocabulario CDM v6.0.0 es una entrada terminológica,
no una conversión del esquema clínico de este laboratorio a CDM 6.

## Actividad 5: diagnóstico de mapeo

Campos de tablas destino: Condition 11435/399864 = 2.8597223%; Visit
77229/1353311 = 5.7066705%; Gender 22851/22851 = 100%. Gender no está incluido
en los paquetes aunque existen valores fuente F/M para todas las personas.
Visit conserva sin mapear home, hospice, snf, urgentcare y virtual: el CASE del ETL
es incompleto. No se aplicó la ampliación propuesta en el comando interrumpido.

De los 11435 eventos sin estándar: 2393 corresponden a dos conceptos inválidos D:
378001 (Concussion with no loss of consciousness, código 62106007; 1321 eventos)
y 4275756 (Dependent drug abuse, 6525002; 1072 eventos). No tienen Maps to ni
Concept replaced by vigentes en esta descarga; no se inventó reemplazo.
Los otros 9042 corresponden a 20 conceptos vigentes, no estándar y sin Maps to:
8938 eventos con dominio fuente Observation y 104 con dominio Condition
(metástasis a próstata y colon). La ausencia de Maps to es comprobable en el paquete;
su causa externa requiere revisión del vocabulario, no se atribuye sin evidencia.
Inexistentes en el paquete: 0. Actualizados/obsoletos U: 0. Códigos fuente ausentes: 0.

Por dominio declarado en CONCEPT fuente: Condition 2497/390926 = 0.6387398%;
Observation 8938/439868 = 2.0319732%; Measurement 0/5 = 0%. No confundir estas
tasas con el porcentaje de ceros de una tabla destino: hay Observation sin Maps to
que permanecen como cero en CONDITION por la lógica de fallback del ETL mínimo.

## Registros separados y pérdida de cobertura

Se reconciliaron 830799 filas fuente = 399864 en CONDITION + 430935 separadas,
sin filas sin traza. Las separadas representan 51.8699469% de conditions.csv.
430930 Observation tienen estándares vigentes: predominan revisión de medicación
(4199788, Medication review due; 163616 eventos), estrés, empleo y otras situaciones.
Los cinco Measurement son 4178483 (Toxoplasma gondii antibody detected), código
428915008: hallazgos positivos categóricos, no concentraciones numéricas ausentes.
No se debe inferir un valor numérico ni unidad a partir de esa descripción.

Excluirlos de CONDITION es coherente con el dominio OMOP. Mantenerlos solo en
rejected_domain es limitación del ETL docente: faltan OBSERVATION y MEASUREMENT
para consultarlos por mecanismos OMOP habituales. No se borró información fuente;
sí existe pérdida de cobertura analítica en las tablas clínicas estándar.
También quedan 8938 eventos Observation sin destino estándar en CONDITION. Estas
exclusiones no son ausencia clínica ni justifican ignorar información en un estudio.
La ampliación a esos dominios queda pendiente, sin reconstruir la base en esta tarea.

## Actividades 7 y 9

Gingivitis: 4281516 (Gingivitis), SNOMED 66383009, Maps to vigente a sí mismo.
Ambos conteos dan 18512 personas dentro de OBSERVATION_PERIOD, frente a 18515 sin
ese filtro. No hay diferencia estándar/origen porque solo ese código contribuye
a ese estándar en los datos. No se fuerza una discrepancia inexistente.
Los tres conceptos, jerarquías y códigos fuente se verificaron en el paquete local
y están documentados en athena_revision.md. Sigue pendiente el contraste interactivo
del portal por falta de navegador/contenido accesible, y la interpretación científica.

## Reproducción sin ETL

```bash
python3 lab12/generar_reporte.py --db lab12/local/omop_athena.duckdb --reference lab12/resultados/referencia_resultados.json
LAB12_DB=lab12/local/omop_athena.duckdb python3 -m unittest discover -s lab12/tests -v
```

Consultas completas: sql/calidad_vocabularios.sql. Se conservan huellas del SQL
actual en resultados.json, separadas de la identidad de la construcción original.
El generador consulta esta base y no reutiliza los agregados de una ejecución previa.
Las limitaciones científicas adicionales siguen siendo continuidad de observación,
censura, tipos/procedencia cero y el carácter sintético de las dos poblaciones.
No se certifica un CDM completo, ni se modificó el proyecto final o se fusionó a main.
