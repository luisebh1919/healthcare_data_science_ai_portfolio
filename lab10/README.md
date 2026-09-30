# Lab 10 — SQL Fundamentals

Este documento cubre las diez actividades del laboratorio.

## Reproducción completa

Con `synthea-with-dependencies.jar` disponible en `lab02/`, los datos y la base
se pueden reconstruir desde cero con:

```bash
cd lab02
java -jar synthea-with-dependencies.jar \
  -p 20000 \
  --exporter.csv.export=true \
  --exporter.fhir.export=false \
  --exporter.baseDirectory=output
cd ..
python3 lab10/build_db.py
```

El último comando puede repetirse: elimina y vuelve a crear las cinco tablas,
imprime sus conteos y deja la base local en `lab10/data/clinical.duckdb`. El
notebook de la Actividad 10 puede abrirse después desde
`lab10/notebooks/sql_vs_pandas.ipynb`.

## Actividad 1. Datos clínicos sintéticos

Se reutilizan directamente los datos Synthea generados en el Lab 02, ubicados
en `lab02/output/csv/`. Los CSV originales no se copian ni se modifican. Se
inspeccionaron sus encabezados y algunas filas mediante lectura limitada, sin
cargar `observations.csv` completo en pandas.

| Archivo | Filas de datos |
|---|---:|
| `patients.csv` | 22,851 |
| `encounters.csv` | 1,353,311 |
| `conditions.csv` | 830,799 |
| `medications.csv` | 1,158,763 |
| `observations.csv` | 17,340,070 |

El comando original de generación está documentado en el README del Lab 02:

```bash
java -jar synthea-with-dependencies.jar \
  -p 20000 \
  --exporter.csv.export=true \
  --exporter.fhir.export=false \
  --exporter.baseDirectory=output
```

Los encabezados revisados corresponden a las cinco entidades solicitadas. En
particular, `observations.VALUE` contiene tanto números como texto (por ejemplo,
respuestas como `No` o descripciones clínicas), por lo que no puede tratarse
como una columna exclusivamente numérica.

## Actividad 2. Motor de base de datos

Se eligió DuckDB porque este laboratorio se ejecuta localmente y por una sola
persona. Está orientado a consultas analíticas y puede trabajar eficientemente
con los millones de filas de Synthea. Además, crea una base en un solo archivo
sin que sea necesario instalar, configurar o administrar un servidor.

## Actividad 3. Construcción de la base

Desde la raíz del repositorio, la carga completa se reproduce con:

```bash
python3 lab10/build_db.py
```

El script crea `lab10/data/clinical.duckdb`, cambia internamente a `lab10/` para
resolver las rutas de los CSV y ejecuta `lab10/sql/carga.sql`. La carpeta
`lab10/data/` está ignorada por Git, de modo que el archivo grande de la base no
se agrega al repositorio. La carga elimina primero las tablas existentes y las
vuelve a crear; por ello, el mismo comando se puede ejecutar varias veces.

Conteos obtenidos de la base construida y validados después de una segunda
ejecución completa:

| Tabla | Filas cargadas |
|---|---:|
| `patients` | 22,851 |
| `encounters` | 1,353,311 |
| `conditions` | 830,799 |
| `medications` | 1,158,763 |
| `observations` | 17,340,070 |

### Decisiones de tipos

- Los identificadores de pacientes, encuentros y otras entidades usan `UUID`.
- Las fechas sin hora usan `DATE`; los instantes de encuentros, medicamentos y
  observaciones usan `TIMESTAMP`.
- Los importes se almacenan como `DECIMAL(18, 2)`, las coordenadas como
  `DOUBLE`, los conteos como `INTEGER` y el ingreso como `BIGINT`.
- Códigos, FIPS y códigos postales se conservan como `VARCHAR` para no perder
  ceros iniciales ni asumir que todos los sistemas de codificación son
  exclusivamente numéricos.
- Los CSV se leen inicialmente como texto y cada campo se convierte de forma
  explícita. `NULLIF(..., '')` transforma strings vacíos en `NULL`.
- `observations.value` se conserva como `VARCHAR` porque combina valores
  numéricos y categóricos. Cuando una consulta necesite el componente numérico,
  puede usar `TRY_CAST(value AS DOUBLE)` sin descartar el texto original.

## Actividad 4. Modelo relacional

El modelo contiene cinco tablas clínicas. La siguiente síntesis usa los nombres
y tipos comprobados directamente en `clinical.duckdb`:

| Tabla | Filas | Columnas y tipos principales | PK lógica |
|---|---:|---|---|
| `patients` | 22,851 | `id UUID`, `birth_date DATE`, `death_date DATE`, datos demográficos `VARCHAR`, `healthcare_expenses DECIMAL(18,2)`, `healthcare_coverage DECIMAL(18,2)`, `income BIGINT` | `id` |
| `encounters` | 1,353,311 | `id UUID`, `patient_id UUID`, `start_at TIMESTAMP`, `stop_at TIMESTAMP`, `encounter_class VARCHAR`, `code VARCHAR`, costos `DECIMAL(18,2)` | `id` |
| `conditions` | 830,799 | `patient_id UUID`, `encounter_id UUID`, `start_date DATE`, `stop_date DATE`, `code VARCHAR`, `description VARCHAR` | No tiene una columna identificadora propia |
| `medications` | 1,158,763 | `patient_id UUID`, `encounter_id UUID`, `start_at TIMESTAMP`, `stop_at TIMESTAMP`, `code VARCHAR`, costos `DECIMAL(18,2)`, `dispenses INTEGER` | No tiene una columna identificadora propia |
| `observations` | 17,340,070 | `patient_id UUID`, `encounter_id UUID`, `observed_at TIMESTAMP`, `category VARCHAR`, `code VARCHAR`, `value VARCHAR`, `units VARCHAR`, `observation_type VARCHAR` | No tiene una columna identificadora propia |

`patients.id` y `encounters.id` son claves primarias **lógicas**: en la
validación realizada ambas tuvieron cero duplicados. Las relaciones o claves
foráneas lógicas son:

- `patients.id` → `encounters.patient_id`
- `patients.id` → `conditions.patient_id`
- `patients.id` → `medications.patient_id`
- `patients.id` → `observations.patient_id`
- `encounters.id` → `conditions.encounter_id`
- `encounters.id` → `medications.encounter_id`
- `encounters.id` → `observations.encounter_id`

Estas claves describen la estructura semántica de los datos, pero **no son
constraints físicos declarados**. `carga.sql` no define `PRIMARY KEY`,
`FOREIGN KEY`, `UNIQUE` ni `NOT NULL`; por eso DuckDB muestra `key=None` en
`DESCRIBE`. Tampoco se crean claves artificiales para `conditions`,
`medications` u `observations`, ya que los CSV fuente no proporcionan un ID
propio para esas tablas.

El diagrama entidad-relación completo está en
[`docs/er_diagram.md`](docs/er_diagram.md).

## Actividad 5. Auditoría de calidad

Las consultas de auditoría están en `sql/consultas.sql` y se ejecutaron contra
`data/clinical.duckdb`. Los resultados obtenidos fueron:

| Comprobación | Resultado |
|---|---:|
| IDs duplicados en `patients.id` | 0 |
| Encuentros anteriores al nacimiento | 0 |
| Filas con `observations.value` nulo o vacío | 0 de 17,340,070 |
| Porcentaje de `observations.value` nulo o vacío | 0.0000% |
| Encuentros sin paciente existente | 0 |

Un `patients.id` duplicado impediría identificar de forma unívoca al paciente y
podría multiplicar filas al relacionar tablas. Una visita anterior a
`patients.birth_date` es temporalmente imposible y señalaría un error en las
fechas o en la asociación del paciente.

Los valores nulos o vacíos en `observations.value` representarían mediciones
sin resultado disponible; no deben interpretarse como cero y podrían afectar
análisis de completitud o cálculos clínicos. En esta carga no se encontraron
casos. La consulta considera tanto `NULL` como strings formados solo por
espacios mediante `TRIM(value) = ''`.

Finalmente, el `LEFT JOIN` conserva todos los encuentros y `WHERE p.id IS NULL`
selecciona aquellos para los que no se encontró un paciente correspondiente.
Este anti-join detectaría encuentros huérfanos; el resultado actual fue cero.

## Actividad 6. Quince preguntas SQL

Las quince consultas completas están en `sql/consultas.sql` y se ejecutaron sin
errores contra `data/clinical.duckdb`. Las consultas que generan muchas filas se
resumen aquí; el resultado detallado se obtiene ejecutando el SQL.

| # | Pregunta | Resultado principal |
|---:|---|---|
| 1 | Total de pacientes y pacientes vivos | 22,851 totales; 20,000 vivos |
| 2 | Distribución por sexo | F: 11,446 (50.09%); M: 11,405 (49.91%) |
| 3 | Diez condiciones más frecuentes | Primera: `Medication review due (situation)` (`314529007`), 163,616 registros y 22,851 pacientes |
| 4 | Pacientes nacidos antes de 1960 | 4,745 |
| 5 | Encuentros por año | 112 años entre 1915–2026; 1,353,311 encuentros. Máximo: 2021, con 117,682 |
| 6 | Media y mediana de encuentros por paciente | Media: 59.22; mediana: 36.0 |
| 7 | Edad al primer diagnóstico elegido | 5,182 pacientes; media: 42.40 años |
| 8 | Condiciones con más de 50 pacientes distintos | 231 condiciones |
| 9 | Distribución del analito elegido | 327,659 mediciones; media 117.08, mediana 118.00, p10 97.00 y p90 137.00 mmHg |
| 10 | Pacientes por grupo etario y sexo | 0–17: 4,347; 18–39: 6,245; 40–64: 8,014; 65+: 4,245 |
| 11 | Pacientes con diabetes e hipertensión | 1,012 |
| 12 | Pacientes con diabetes sin ninguna HbA1c | 0 |
| 13 | Primer y último encuentro por paciente | 22,851 filas, una por paciente; ninguno sin encuentros |
| 14 | Medicamento más frecuente en la cohorte elegida | Sodium fluoride 0.0272 MG/MG Oral Gel (`1535362`): 4,969 pacientes distintos |
| 15 | Encuentros de urgencias sin diagnóstico | 17,121 |

### Definiciones y decisiones

- **Pregunta 3:** la frecuencia es el número de filas de `conditions` por
  combinación de código y descripción. También se devuelve el número de
  pacientes distintos, ya que Synthea incluye en esta tabla trastornos,
  hallazgos y situaciones clínicas.
- **Pregunta 7:** se eligió hipertensión esencial, SNOMED `59621000`
  (`Essential hypertension (disorder)`), por ser frecuente y clínicamente
  interpretable. Primero se obtiene `MIN(start_date)` por paciente y después se
  calcula la edad; así, los diagnósticos repetidos no pesan varias veces.
- **Pregunta 9:** se eligió presión arterial sistólica, LOINC `8480-6`, limitada
  a unidades `mm[Hg]`. Se usa `TRY_CAST(value AS DOUBLE)` y se descartan los
  valores no convertibles antes de calcular media, mediana, p10 y p90.
- **Pregunta 10:** los grupos son 0–17, 18–39, 40–64 y 65+ años, que separan
  menores, adultos jóvenes, adultos y adultos mayores. Para pacientes vivos la
  edad se calcula al 29 de septiembre de 2026; para fallecidos, a la fecha de
  muerte. Por sexo, los conteos son F/M: 2,248/2,099; 3,182/3,063;
  4,015/3,999; y 2,001/2,244, respectivamente.
- **Preguntas 11–12:** diabetes se identifica con SNOMED `44054006`
  (`Diabetes mellitus type 2 (disorder)`), hipertensión con `59621000` y HbA1c
  con LOINC `4548-4` (`Hemoglobin A1c/Hemoglobin.total in Blood`). Se forman
  cohortes de pacientes distintos; la ausencia de HbA1c se evalúa con
  `NOT EXISTS`.
- **Pregunta 14:** la cohorte vuelve a ser hipertensión esencial (`59621000`).
  “Más frecuente” significa el medicamento con mayor número de pacientes
  distintos expuestos; se deduplican primero las combinaciones paciente y
  medicamento para que dispensaciones repetidas no inflen el conteo.
- **Pregunta 15:** se consideran urgencias los encuentros con
  `encounter_class = 'emergency'`. El `LEFT JOIN` con `conditions` y la prueba
  `c.encounter_id IS NULL` identifican encuentros sin una condición asociada.

### Hallazgos breves

- La distribución por sexo está prácticamente equilibrada: 50.09% F y 49.91% M.
- La media de encuentros (59.22) supera ampliamente la mediana (36.0), lo que
  sugiere una distribución sesgada por pacientes con muchos encuentros.
- La presión sistólica central es 118 mmHg y el 80% central de las mediciones se
  encuentra aproximadamente entre 97 y 137 mmHg.
- De los pacientes con diagnóstico explícito de diabetes tipo 2, todos tienen
  al menos una observación de HbA1c; 1,012 también tienen hipertensión esencial.
- Se encontraron 17,121 encuentros de clase `emergency` sin una condición
  enlazada mediante `conditions.encounter_id`.

## Actividad 7. El JOIN que multiplica

El experimento compara tres versiones del mismo análisis sobre encuentros que
tienen al menos una condición. La versión correcta usa `EXISTS`, el `JOIN`
directo muestra la multiplicación y la versión corregida deduplica por
`encounter_id` y `total_claim_cost` antes de agregar.

| Medida | Correcta (`EXISTS`) | Inflada (`JOIN`) | Corregida (`DISTINCT`) |
|---|---:|---:|---:|
| Filas | 532,652 | 830,799 | 532,652 |
| Promedio de `total_claim_cost` | 2,378.07 | 2,171.18 | 2,378.07 |

La multiplicación ocurre porque un encuentro puede tener varias filas en
`conditions`. Al unir ambas tablas directamente, los datos del encuentro —entre
ellos `total_claim_cost`— aparecen una vez por cada condición asociada. Por eso
el resultado creció en 298,147 filas, aproximadamente un 56%.

El promedio inflado cambió de 2,378.07 a 2,171.18 porque los encuentros con más
condiciones recibieron más peso. El valor incorrecto seguía siendo plausible y
podría pasar inadvertido si solo se revisara su magnitud. Después de recuperar
una sola combinación de encuentro y costo con `DISTINCT`, tanto el conteo como
el promedio vuelven exactamente a sus valores correctos: 532,652 y 2,378.07.

## Actividad 8. La trampa del LEFT JOIN

El experimento usa el código SNOMED `59621000` de hipertensión esencial. Antes
del `JOIN`, `conditions` se deduplica por `encounter_id` y `code` para estudiar
solo el efecto de la ubicación del filtro, sin repetir la multiplicación de
filas de la Actividad 7.

| Ubicación del filtro `c.code = '59621000'` | Filas obtenidas |
|---|---:|
| En `WHERE` | 5,182 |
| Dentro de `ON` | 1,353,311 |

Un `LEFT JOIN` conserva inicialmente todos los encuentros. Cuando no encuentra
una condición coincidente, las columnas de la tabla derecha quedan en `NULL`.
Si después se coloca `c.code = '59621000'` en `WHERE`, esas filas no cumplen la
condición porque una comparación con `NULL` no es verdadera. Solo permanecen
los encuentros que sí tienen hipertensión esencial, por lo que para ese filtro
el resultado se comporta como un `INNER JOIN`.

Al mover el filtro a `ON`, este determina qué filas de `conditions` pueden
coincidir, pero no elimina filas de `encounters`. Los encuentros sin esa
condición siguen presentes y reciben `NULL` en las columnas de la derecha. Por
eso se conservan los 1,353,311 encuentros originales.

## Actividad 9. Medición de rendimiento

Se compararon dos formas de responder la pregunta 12: pacientes con diabetes
tipo 2 (`44054006`) sin mediciones de HbA1c (`4548-4`). Ambas devolvieron el
mismo resultado clínico: **0 pacientes**.

| Versión | Estrategia | Tiempo total |
|---|---|---:|
| Original | `NOT EXISTS` | 0.0245 s |
| Reescrita | CTE deduplicados + `LEFT JOIN` + `IS NULL` | 0.0202 s |

En la ejecución medida, la versión reescrita fue aproximadamente un 17.6% más
rápida. Esto no demuestra una mejora estable de 17.6%: ambos tiempos son muy
pequeños y proceden de una sola ejecución, por lo que pueden cambiar por caché,
carga del sistema y variación normal. La conclusión prudente es que la
reescritura fue ligeramente más rápida en esa ejecución y que ambas estrategias
son eficientes.

El plan original muestra que DuckDB ya transformó `NOT EXISTS` en un anti-join,
con operadores `RIGHT_DELIM_JOIN` y `RIGHT_ANTI`. Es decir, la forma declarativa
original no obliga al motor a ejecutar una subconsulta fila por fila. En ambos
planes se observa *predicate pushdown*: los filtros `code = '44054006'` y
`code = '4548-4'` se aplican dentro de los `TABLE_SCAN`, reduciendo los datos
antes de los joins y agregaciones.

DuckDB es un motor columnar orientado a análisis: en estos planes solo proyecta
`patient_id` y escanea de forma eficiente las columnas necesarias. Por ello, un
índice tradicional no necesariamente mejoraría esta consulta, especialmente
cuando el motor puede filtrar y procesar columnas en bloques.

Los árboles de operadores capturados están disponibles en:

- [`docs/explain_before.txt`](docs/explain_before.txt)
- [`docs/explain_after.txt`](docs/explain_after.txt)

Los archivos se regeneraron para conservar los planes reales y pueden mostrar
otra duración por la variación entre ejecuciones. La comparación porcentual de
esta actividad usa exclusivamente la ejecución manual emparejada de 0.0245 s y
0.0202 s indicada arriba.

## Actividad 10. SQL frente a pandas

Se compararon las consultas 1, 6 y 15 usando DuckDB y pandas. En los tres casos
los resultados coincidieron exactamente. Los DataFrames se cargaron antes de
iniciar el cronómetro, por lo que estos tiempos comparan únicamente la operación
analítica y **no** incluyen la lectura inicial desde DuckDB o desde los CSV.

| Consulta | Resultado en ambos métodos | Líneas SQL aprox. | Líneas pandas aprox. | SQL | pandas | Legibilidad |
|---|---|---:|---:|---:|---:|---|
| #1 Pacientes totales/vivos | `(22851, 20000)` | 5 | 4 | 0.001432 s | 0.003601 s | Ambas son directas; SQL reúne ambos conteos en una consulta. |
| #6 Media/mediana de encuentros | `(59.22327250448558, 36.0)` | 9 | 8 | 0.008418 s | 0.293975 s | SQL expresa directamente la relación; pandas requiere agrupar y reindexar. |
| #15 Urgencias sin diagnóstico | `17121` | 6 | 7 | 0.014573 s | 0.439359 s | El anti-join resulta más explícito y compacto en SQL. |

La diferencia de legibilidad es pequeña para el conteo sencillo de la consulta
1. En las consultas 6 y 15, SQL describe con mayor claridad la relación entre
tablas y la intención del anti-join. pandas necesita pasos intermedios útiles
para inspección, pero más verbosos para este tipo de operación relacional. En
las tres mediciones SQL fue más rápido, con una diferencia especialmente clara
en las dos consultas que relacionan tablas grandes. Son mediciones puntuales y
no sustituyen un benchmark con repeticiones y control de caché.

El notebook reproducible, que carga únicamente las columnas necesarias, mide
ambas implementaciones y verifica la igualdad con `assert`, está en
[`notebooks/sql_vs_pandas.ipynb`](notebooks/sql_vs_pandas.ipynb).

Para este volumen (~22,851 pacientes, 1.35 M encounters y hasta 17.3 M
observations), SQL/DuckDB es preferible para consultas relacionales,
agregaciones y filtros sobre tablas grandes.

pandas sigue siendo útil después de reducir el dataset a un subconjunto
analítico manejable para análisis estadístico, ML o visualización.
