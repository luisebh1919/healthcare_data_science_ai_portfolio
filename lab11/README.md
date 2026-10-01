# Lab 11 — SQL Avanzado: Actividades 1 a 10

Completadas únicamente las Actividades 1 a 10. SQL en `sql/analitica_longitudinal.sql`; fuente de las comparaciones iniciales: `../lab10/sql/consultas.sql`. Verificado el 2026-10-01 con DuckDB 1.5.6 y `../lab10/data/clinical.duckdb` abierta mediante `duckdb.connect(..., read_only=True)`. No se modificó Lab 10 ni se realizaron commit, push o merge.

## Actividad 1 — De anidado a legible

Se conservaron literalmente las dos consultas originales, incluidos sus comentarios, y se añadieron versiones compactas con CTEs descriptivas. A transforma una subconsulta en FROM, sin CTEs en el original, en una CTE descriptiva. B conserva la comparación larga usada en la Actividad 2; su original ya tenía CTEs y la mejora extrae las subconsultas restantes.

### A. Actividad 5, auditoría 1: IDs de paciente repetidos

Pregunta de calidad clínica: ¿cuántos identificadores de paciente aparecen en más de un registro de `patients`? Esta auditoría detecta registros repetidos que podrían distorsionar conteos de pacientes.

Se sustituyó diabetes sin HbA1c por una consulta real de Lab 10 sin CTEs: agrupa por `id` y filtra con `HAVING COUNT(*) > 1` dentro de una subconsulta en `FROM`; el SELECT externo cuenta los grupos. La reescritura mueve exactamente esa subconsulta a `duplicated_patient_ids`, manteniendo el conteo final y el nombre de la columna.

Ahora existe una transformación real de consulta anidada a CTE. El nombre del bloque hace explícito qué se cuenta y separa la detección de IDs repetidos del conteo final. Para inspeccionar el resultado intermedio, sustituir el SELECT final por `SELECT id FROM duplicated_patient_ids;`. La mejora de legibilidad es modesta porque la original ya es corta; aporta un nombre descriptivo, separación de pasos y acceso al resultado intermedio. No se afirma una mejora de rendimiento.

### B. Actividad 7: el JOIN que multiplica

Pregunta clínica: ¿cuántos encuentros tienen al menos un diagnóstico y cuál es su costo medio registrado? ¿Cómo cambia el resultado al unir todas sus condiciones directamente?

La original es la más larga de las dos y contiene un `EXISTS` correlacionado más seis subconsultas escalares en el resultado. La reescritura explicita los encuentros con diagnóstico (`diagnosed_encounters`), selecciona encuentros mediante `SEMI JOIN`, conserva el JOIN multiplicador y su deduplicación, y calcula las tres parejas de métricas en CTEs de resumen. El resultado combina tres agregados de una fila mediante `CROSS JOIN`.

Mejora la legibilidad al dar nombres a la selección y los resúmenes; separa selección, multiplicación, deduplicación y agregación. Permite inspeccionar tanto las filas clínicas como sus métricas sin editar subconsultas dentro del resultado final. Añade bloques, por lo que no necesariamente reduce longitud ni mejora rendimiento; no se afirma una ventaja de velocidad.

### Verificación de equivalencia exacta

Se ejecutaron ambas originales y ambas reescrituras en la misma conexión de solo lectura. Se compararon los nombres, orden y tipos de columnas y las filas completas mediante igualdad exacta, sin tolerancias. Además, `EXCEPT ALL` en ambos sentidos devolvió cero filas para cada pareja, verificando también multiplicidades y nulos. Ambas consultas producen una sola fila, por lo que no hay ambigüedad de orden.

| Consulta / columna | Original | CTE |
| --- | ---: | ---: |
| A: `patient_ids_duplicados` | 0 | 0 |
| B: `correct_rows` | 532652 | 532652 |
| B: `inflated_rows` | 830799 | 830799 |
| B: `corrected_rows` | 532652 | 532652 |
| B: `correct_avg` | 2378.07 | 2378.07 |
| B: `inflated_avg` | 2171.18 | 2171.18 |
| B: `corrected_avg` | 2378.07 | 2378.07 |

Los conteos tienen tipo `BIGINT`; los promedios, `DOUBLE`, igual que en las originales.

## Actividad 2 — Depurar por partes

Se eligió B por ser la reescritura más larga. Cada CTE se ejecutó individualmente sustituyendo el resultado final por `SELECT COUNT(*) FROM nombre_del_bloque`, conservando el `WITH` y sus dependencias. El SQL también incluye una consulta ejecutable que reproduce juntos los siete conteos mediante `UNION ALL`, con columnas explícitas y orden de bloques.

| Bloque | Filas | Qué representa clínicamente |
| --- | ---: | --- |
| `diagnosed_encounters` | 532652 | Identificadores distintos de encuentro referidos por las condiciones; referencia previa a comprobar su coincidencia con encounters. |
| `correct_encounters` | 532652 | Registros de encuentros con al menos un diagnóstico, conservando su costo una vez por fila de encounters. |
| `inflated_join` | 830799 | Pares encuentro–condición; un encuentro con varios diagnósticos repite su costo. |
| `corrected_join` | 532652 | Pares distintos de identificador de encuentro y costo tras eliminar la multiplicación. |
| `correct_summary` | 1 | Conteo y costo medio de los encuentros seleccionados correctamente. |
| `inflated_summary` | 1 | Conteo y costo medio sobre los pares encuentro–condición, ponderados por cantidad de condiciones. |
| `corrected_summary` | 1 | Conteo y costo medio tras la deduplicación del JOIN. |

Los resúmenes tienen una fila porque son agregados sin `GROUP BY`; esa fila contiene métricas, no un paciente o encuentro. En esta base, la deduplicación recupera el mismo conteo y promedio del conjunto correcto.

Para inspeccionar valores intermedios, reutilizar el `WITH` de B y sustituir su resultado final, por ejemplo, por `SELECT encounter_id, total_claim_cost FROM corrected_join ORDER BY encounter_id LIMIT 10;`. Para `diagnosed_encounters`, proyectar `encounter_id`; para los resúmenes, proyectar sus dos métricas. No se usa `SELECT *` como resultado final; solo se utilizó temporalmente en la comprobación de diferencias.

## Actividad 3 — Primera y última visita

Pregunta clínica: ¿cuál fue la primera y última visita de cada paciente y cuántas visitas tuvo? Se consideran todos los encuentros, sin filtrar por clase. El resultado incluye pacientes con encuentros registrados.

El SQL conserva dos soluciones con CTEs descriptivas: `grouped_visits` usa `MIN(start_at)`, `MAX(start_at)` y `COUNT(*)` agrupando por paciente; `window_visits` usa `FIRST_VALUE`, `LAST_VALUE`, `COUNT(*) OVER` y `ROW_NUMBER`. `patient_visit_summary` selecciona la fila con `visit_order = 1` para obtener una sola fila por paciente. El orden `start_at, id` resuelve empates de fecha de manera determinista.

Con una ventana ordenada, el frame predeterminado termina en la fila actual y sus pares de orden, no al final de toda la partición. Por eso `LAST_VALUE` podría devolver la visita actual en vez de la última visita del paciente. El frame explícito `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` hace que ambas funciones consulten la historia completa del paciente.

Para este problema, **GROUP BY es más simple**: produce directamente una fila por paciente con tres agregados, sin repetir métricas por visita ni necesitar `ROW_NUMBER` para seleccionar una fila. Las ventanas serían útiles si además se necesitaran conservar detalles de cada visita.

| Validación ejecutada | Resultado |
| --- | ---: |
| `grouped_rows` | 22851 |
| `window_rows` | 22851 |
| Diferencias GROUP BY → ventana (`EXCEPT ALL`) | 0 |
| Diferencias ventana → GROUP BY (`EXCEPT ALL`) | 0 |

Ambas consultas se ejecutaron y la consulta de validación incluida en el SQL confirma igualdad en ambos sentidos, incluidas multiplicidades.

## Actividad 4 — Días entre visitas

Pregunta clínica: ¿cuál es la mediana de días entre visitas consecutivas de un paciente? `visits_with_previous` calcula `LAG(start_at) OVER (PARTITION BY patient_id ORDER BY start_at, id)`; `visit_intervals` calcula `DATE_DIFF('day', previous_visit, start_at)`.

| Resultado ejecutado | Valor |
| --- | ---: |
| `total_visits` | 1353311 |
| `first_visits` con `previous_visit IS NULL` | 22851 |
| `median_days` | 14 |

La primera visita tiene `previous_visit = NULL` porque no existe una visita previa; su intervalo también es `NULL`. **No se convierten esos NULL a 0**: hacerlo introduciría intervalos ficticios. `MEDIAN` excluye los valores nulos para responder sobre intervalos observados. Los intervalos reales de cero días se conservan. `DATE_DIFF('day', ...)` cuenta cambios de día calendario, no bloques completos de 24 horas.

## Actividad 5 — Readmisión a 30 días

Pregunta clínica: ¿qué proporción de altas de hospitalizaciones inpatient tiene una siguiente admisión inpatient entre 1 y 30 días después del alta?

La definición final usa únicamente `encounter_class = 'inpatient'`. `inpatient_stays` conserva admisión y alta (`stop_at`); `stays_with_next_admission` obtiene la siguiente admisión del mismo paciente mediante `LEAD(start_at)`, ordenando por `start_at, encounter_id`. La función se aplica después de seleccionar inpatient, por lo que visitas de otras clases no interrumpen la secuencia de hospitalizaciones.

`eligible_discharges` incluye cada alta registrada con `discharge_at >= start_at`, aunque no exista una admisión posterior. En esta base hay 21602 hospitalizaciones inpatient, ninguna con alta nula ni anterior a la admisión, por lo que todas entran en el denominador. `readmission_summary` cuenta como readmisión la siguiente admisión cuando `next_admission_at > discharge_at` y `DATE_DIFF('day', discharge_at, next_admission_at) BETWEEN 1 AND 30`. El día 30 está incluido; una admisión en el mismo día calendario no cumple el intervalo mínimo de 1 día. Se usa la misma unidad de días calendario que en la Actividad 4.

Se cuentan **todas las readmisiones elegibles**, no solo la primera de cada paciente: cada alta aporta una oportunidad. Las altas sin siguiente admisión permanecen en el denominador y no se cuentan en el numerador. No se añade un requisito de seguimiento completo de 30 días ni un filtro oncológico.

| Resultado ejecutado | Valor |
| --- | ---: |
| `eligible_discharges` | 21602 |
| `readmissions_30d` | 3177 |
| `readmission_rate` | 14.71% |

La tasa es `ROUND(100.0 * readmissions_30d / NULLIF(eligible_discharges, 0), 2)`. La formulación preliminar con `LAG` (13786 transiciones, 3177 readmisiones, 23.05%) se descartó porque su denominador eran transiciones entre hospitalizaciones, no todas las altas elegibles. No se incluye como consulta final.

**Esta definición corresponde al Lab 11 y todavía no es la cohorte oncológica final del proyecto.** Los resultados de las Actividades 3, 4 y 5 coinciden con todos los números previamente validados; no se encontraron diferencias. Las Actividades 1 y 2 y los siete conteos de la consulta larga se conservaron.

## Actividad 6 — Gaps-and-islands de exposiciones a medicamentos

Pregunta clínica: ¿cómo se agrupan las exposiciones a `sodium fluoride 0.0272 MG/MG Oral Gel` en episodios cuando se permiten gaps de 30, 60 o 90 días?

El medicamento fue seleccionado empíricamente porque tiene suficientes pacientes y exposiciones y permite observar el efecto del parámetro de gap, no por una relevancia clínica particular.

Gaps-and-islands identifica grupos de intervalos conectados (episodios o islas), separados por huecos superiores al umbral. `valid_exposures` excluye `stop_at IS NULL` porque no se conoce el fin y no se imputa una duración; también excluye `stop_at < start_at` porque forma un intervalo inválido. Las exposiciones de duración cero son válidas y se conservan.

`exposure_history` usa `MAX(stop_at)` sobre todas las filas anteriores del paciente, ordenadas por `start_at, stop_at`, con `ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING`. Se usa `max_prior_stop` en lugar de simplemente `LAG(stop_at)` porque una exposición anterior larga puede cubrir exposiciones posteriores más cortas: el fin de la fila inmediatamente anterior no necesariamente es el máximo fin alcanzado.

`episode_boundaries` marca la primera exposición y cada inicio estrictamente posterior a `max_prior_stop + INTERVAL '30 days'`. Exactamente 30 días conserva el episodio. `numbered_exposures` crea `episode_id` mediante suma acumulada de esa marca con `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. `medication_episodes` agrega por paciente y episodio. Los empates exactos de inicio y fin no cambian los límites ni los conteos del episodio: la primera fila del empate puede abrirlo y las restantes permanecen en él.

La tabla de gap 30 contiene `patient_id`, `episode_id`, `episode_start`, `episode_end`, `duration_days` y `exposure_count`. La duración usa `DATE_DIFF('day', episode_start, episode_end)`: días calendario entre extremos, incluidos gaps internos, no días efectivos de tratamiento. Cada exposición se cuenta una vez, sin deduplicar registros.

| Gap (días) | SUM(exposure_count) | Pacientes distintos | Episodios |
| --- | ---: | ---: | ---: |
| 30 | 62462 | 19279 | 61159 |
| 60 | 62462 | 19279 | 58501 |
| 90 | 62462 | 19279 | 56506 |

Al aumentar el gap de 30 a 60 y 90 días se unen episodios separados por huecos que ahora están permitidos. Por eso disminuyen los episodios sin cambiar las exposiciones ni los pacientes. Las tres validaciones coinciden exactamente con el screening.

Resumen de duración para los 61159 episodios de gap 30:

| Medida | Días |
| --- | ---: |
| Mínimo | 0 |
| Mediana | 0 |
| Percentil 90 | 0 |
| Percentil 95 | 0 |
| Percentil 99 | 28 |
| Máximo | 112 |

El [notebook ejecutado](notebooks/analitica_longitudinal.ipynb) reutiliza las cuatro sentencias de la Actividad 6 del SQL y abre la base en solo lectura. Incluye validaciones con assertions y un histograma de todas las duraciones de gap 30, con ejes y título descriptivos, sin recortes ni transformación de datos. Los percentiles complementan el histograma.

## Actividad 7 — Última medición sistólica por paciente

Pregunta clínica: ¿cuál es la última medición registrada de presión arterial sistólica (LOINC `8480-6`) de cada paciente?

`ranked_systolic_measurements` filtra el analito y calcula `ROW_NUMBER() OVER (PARTITION BY patient_id ORDER BY observed_at DESC, encounter_id DESC) AS rn`. `latest_systolic_measurements` conserva únicamente `rn = 1`; la salida final muestra explícitamente `patient_id`, `observed_at`, `value` y `units`. Se conservan los valores y unidades originales, sin añadir filtros de conversión numérica o unidad.

No se puede filtrar `rn = 1` en el `WHERE` del mismo SELECT donde se calcula `ROW_NUMBER`: las funciones de ventana se evalúan después de `WHERE`. El CTE posterior permite filtrar el número de fila ya calculado.

`ORDER BY observed_at DESC` coloca primero la medición más reciente. `encounter_id DESC` es el criterio determinista de desempate entre encuentros cuando coinciden las fechas. Si varias mediciones comparten exactamente fecha y encuentro, estos dos campos no distinguen esas filas; se conserva el orden solicitado sin añadir criterios adicionales.

| Validación ejecutada en solo lectura | Resultado |
| --- | ---: |
| `measurements_before` | 327659 |
| `patients` distintos | 22851 |
| `measurements_after` | 22851 |

La salida contiene exactamente una fila por paciente y los tres conteos coinciden con los resultados validados. Las consultas de las Actividades 1–6 se conservaron.

## Actividad 8 — Promedio acumulado y media móvil sistólica

Pregunta clínica: ¿cómo difieren el promedio acumulado de presión arterial sistólica y la media móvil de las últimas tres observaciones de un paciente?

`numeric_systolic_measurements` selecciona LOINC `8480-6` y conserva únicamente valores convertibles mediante `TRY_CAST(value AS DOUBLE)`. `selected_patient` agrupa por `patient_id`, exige `HAVING COUNT(*) >= 5` y selecciona con `ORDER BY COUNT(*) DESC, patient_id LIMIT 1`. Se obtiene reproduciblemente el paciente `911d9cb5-f9ba-6f80-fe4f-90b2ad03655b`; no se fija su UUID como filtro. `patient_systolic_history` recupera su secuencia y `systolic_window_means` calcula ambas ventanas, ordenadas por `observed_at, encounter_id`.

El promedio acumulado usa todas las mediciones desde la primera hasta la actual, con `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. La media móvil usa como máximo la actual y las dos anteriores, con `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW`. Las primeras tres filas pueden coincidir porque todavía no hay más de tres observaciones; en esta ejecución coinciden. Desde la cuarta fila normalmente divergen porque la media móvil empieza a excluir observaciones antiguas, aunque pueden coincidir si sus valores producen la misma media.

`ROWS` define posiciones físicas dentro de la secuencia ordenada, no días calendario: tres observaciones pueden estar separadas por intervalos temporales diferentes. Las medias se calculan sobre los valores DOUBLE sin redondeo previo y se redondean a dos decimales únicamente en la salida final, que muestra `patient_id`, `observed_at`, `systolic`, `cumulative_mean` y `moving_mean_3`.

| Fila en la secuencia | systolic | cumulative_mean | moving_mean_3 |
| --- | ---: | ---: | ---: |
| 4 | 115 | 118.25 | 117.33 |
| 20 | — | 102.90 | 99.33 |

Ambas ventanas se ejecutaron contra la base en solo lectura. Se verificaron el UUID seleccionado, la coincidencia de las primeras tres medias y los ejemplos de las filas 4 y 20. Las consultas de las Actividades 1–7 se conservaron.

## Actividad 9 — Observación cercana al índice y política de leakage

Pregunta clínica: ¿qué medición sistólica (LOINC `8480-6`) está más cerca del alta de la primera hospitalización inpatient y qué medición puede utilizarse como predictor sin información futura?

`ranked_inpatient_stays` selecciona la primera hospitalización con `ROW_NUMBER() OVER (PARTITION BY patient_id ORDER BY start_at, id)`. `index_discharges` usa su `stop_at` como `index_date`, conservando el TIMESTAMP y la hora del alta; excluye índices sin alta. No sustituye una primera hospitalización sin alta por otra posterior. `numeric_systolic_measurements` conserva únicamente valores convertibles a DOUBLE mediante `TRY_CAST`, aunque la salida muestra el `value` original.

### A. Comparación exploratoria ±90 días

`ranked_nearby_measurements` busca entre `index_date - INTERVAL '90 days'` e `index_date + INTERVAL '90 days'`, con extremos incluidos. Ordena por `ABS(DATE_DIFF('day', index_date, observed_at))`, preferencia por `observed_at <= index_date`, `observed_at DESC` y `encounter_id DESC`. `closest_measurements` conserva `rn = 1`. La distancia solicitada cuenta días calendario, pero la clasificación pre/post compara los instantes completos para detectar también futuro dentro del mismo día.

| Resultado | Validación previa indicada | Ejecutado, conservando hora |
| --- | ---: | ---: |
| `patients_with_measurement` | 2245 | 2245 |
| `closest_pre_or_index` | 1337 | 1336 |
| `closest_post_index` | 908 | 909 |

Se encontró una diferencia explicable de un paciente: `9750c3e2-4f4a-f503-dbe9-9d2d4015aa85` tiene alta índice `2020-09-11 00:07:54` y observación seleccionada `2020-09-11 23:52:54`. Es posterior al alta, aunque `DATE_DIFF('day', index_date, observed_at) = 0`. La validación SQL incluye ambas clasificaciones: por días calendario reproduce 1337 pre/en el mismo día y 908 en días posteriores; por instantes completos son 1336 pre/en índice y 909 posteriores.

Los 908 pacientes del resultado indicado tendrían una medición de un día posterior si se utilizara ingenuamente la ventana simétrica; además, el caso del mismo día eleva a 909 las mediciones realmente futuras respecto del instante del alta. No se cambió la política para forzar los conteos anteriores.

### B. Política final predictiva: solo pre-index/en índice

**No se permiten observaciones posteriores al índice.** `ranked_preindex_measurements` limita `observed_at BETWEEN index_date - INTERVAL '90 days' AND index_date` y ordena por `observed_at DESC, encounter_id DESC`. `latest_preindex_measurements` conserva la medición más reciente disponible con `rn = 1`. La salida final contiene explícitamente `patient_id`, `index_date`, `observed_at`, `value` y `days_before_index`.

| Validación ejecutada | Resultado |
| --- | ---: |
| `patients_with_preindex_measurement` | 1621 |
| `min_days_before` | 0 |
| `median_days_before` | 30 |
| `max_days_before` | 90 |

Los 1621 no contradicen los 1337 indicados para la comparación simétrica (1336 al comparar instantes): ese conteo corresponde a pacientes cuya medición **más cercana** resultó pre-index/en índice. Algunos otros pacientes también tenían una medición pre-index válida, pero la simétrica seleccionaba una futura todavía más cercana. Al prohibir el futuro se recuperan 1621 pacientes con alguna medición válida disponible hasta el índice. Se verificó una fila por paciente y que ninguna observación seleccionada supera el instante índice.

Permitir post-index puede introducir **data leakage** en un modelo predictivo, porque incorpora información que no estaba disponible en el momento de predicción. La política final utiliza únicamente información disponible hasta `index_date`, incluido ese instante. Esta definición pertenece al Lab 11 y no sustituye todavía toda la definición de cohorte del proyecto final. Las consultas se ejecutaron en solo lectura y las Actividades 1–8 se conservaron.

## Actividad 10 — LAG frente a self-join sin ventanas

Pregunta clínica: ¿cómo reproducir el intervalo entre visitas consecutivas de cada paciente sin usar funciones de ventana, y cómo se comportan las dos implementaciones?

Ambas consultas usan exactamente `selected_patients`: los primeros 100 `patient_id` distintos de `encounters`, ordenados por UUID ascendente. `selected_visits` contiene sus 6079 visitas. Este conjunto se comprobó antes y después del benchmark y fue idéntico; no se limita a las primeras 6079 filas arbitrarias ni se cambia la muestra entre métodos.

`lag_previous_visits` calcula `LAG(start_at)` en el orden `start_at, id`. `self_join_previous_visits` usa un `LEFT JOIN` sobre ese mismo subconjunto con todas las visitas anteriores del paciente: `prev.start_at < curr.start_at OR (prev.start_at = curr.start_at AND prev.id < curr.id)`. `MAX(prev.start_at)`, agrupado por la visita actual, recupera el inicio de la visita anterior; la primera visita queda con `NULL`. No hay funciones de ventana en la versión self-join. Ambos resúmenes usan `MEDIAN(DATE_DIFF('day', previous_visit, start_at))`, excluyendo los intervalos nulos como en la Actividad 4.

### Equivalencia ejecutada

| Resultado | LAG | Self-join |
| --- | ---: | ---: |
| `total_visits` | 6079 | 6079 |
| `first_visits` | 100 | 100 |
| `median_days` | 14 | 14 |

Se compararon también las 6079 filas completas con `patient_id`, `id`, `start_at` y `previous_visit`, no solo las tres métricas agregadas. Las filas coinciden exactamente. `EXCEPT ALL` en ambos sentidos devolvió cero diferencias y `results_equal = TRUE`; la consulta de validación queda en el SQL.

### Benchmark tras warm-up

DuckDB 1.5.6, 16 threads, misma conexión de solo lectura. Se ejecutó un warm-up completo de cada consulta; después cinco repeticiones por método. En las repeticiones impares se ejecutó primero LAG y en las pares primero self-join, reduciendo el sesgo por orden fijo. Se midió con `time.perf_counter()` desde `execute` hasta terminar `fetchall`, incluyendo selección del subconjunto, cálculo y recuperación del resumen. El warm-up, las validaciones y `EXPLAIN ANALYZE` no forman parte de estos cinco tiempos. Son mediciones con caché calentada, no un benchmark de lectura en frío.

| Repetición | LAG (s) | Self-join (s) |
| --- | ---: | ---: |
| 1 | 0.010079 | 0.045246 |
| 2 | 0.010591 | 0.040966 |
| 3 | 0.009970 | 0.042324 |
| 4 | 0.012559 | 0.040697 |
| 5 | 0.010027 | 0.044150 |
| **Mediana** | **0.010079** | **0.042324** |

El primer benchmark observado fue LAG = 0.1568 s y self-join = 0.0443 s: en aquella ejecución pequeña el self-join fue más rápido. La nueva serie tiene los tiempos indicados arriba; no cambia el resultado de aquel primer benchmark ni demuestra superioridad universal de un método. Con 100 pacientes el self-join puede ser igual o incluso más rápido, según las condiciones de ejecución y las historias seleccionadas.

Para repetir únicamente este benchmark desde la raíz del repositorio, manteniendo la restricción del subconjunto:

```python
from pathlib import Path
import statistics
import time
import duckdb

activity10 = Path("lab11/sql/analitica_longitudinal.sql").read_text().split("-- ACTIVIDAD 10", 1)[1]
with duckdb.connect("lab10/data/clinical.duckdb", read_only=True) as con:
    statements = con.extract_statements("-- ACTIVIDAD 10" + activity10)
    assert len(statements) == 3
    queries = statements[:2]  # LAG y self-join, ambos sobre 100 pacientes
    for query in queries:
        assert con.execute(query).fetchone() == (6079, 100, 14.0)
    times = [[], []]
    for repetition in range(5):
        for method in ([0, 1] if repetition % 2 == 0 else [1, 0]):
            started = time.perf_counter()
            result = con.execute(queries[method]).fetchall()
            times[method].append(time.perf_counter() - started)
            assert result == [(6079, 100, 14.0)]
    for name, values in zip(["LAG", "self-join"], times):
        print(name, values, "mediana:", statistics.median(values))
```

### Planes completos y operadores observados

Se ejecutó `EXPLAIN ANALYZE` sobre las dos mismas consultas resumidas después de las repeticiones. Los planes completos, sin recortar ni sustituir operadores, están en [explain_activity10_lag.txt](docs/explain_activity10_lag.txt) y [explain_activity10_self_join.txt](docs/explain_activity10_self_join.txt).

- **En ambos:** `TABLE_SCAN` de tipo `Sequential Scan`; `HASH_GROUP_BY` para los pacientes distintos (22851 filas); `TOP_N` con Top 100; `HASH_JOIN` de tipo INNER por `patient_id` para recuperar 6079 visitas; `PROJECTION`; y `UNGROUPED_AGGREGATE` final con `count_star()`, conteo filtrado y `median`, que produce una fila. La selección de los pacientes distintos escanea los 1353311 encuentros, pero el cálculo temporal opera solo sobre 6079 visitas.
- **LAG:** aparece `WINDOW` con `LAG(start_at) OVER (PARTITION BY patient_id ORDER BY start_at ASC, id ASC)`, 6079 filas y 0.01 s mostrado. El plan informa `Total Time: 0.0114s`.
- **Self-join:** aparece `CTE` para `selected_visits`, dos `CTE_SCAN` de 6079 filas y `BLOCKWISE_NL_JOIN` de tipo LEFT con la condición temporal y el desempate por `id`. Este join produce 588789 filas y muestra 0.12 s. Un `HASH_GROUP_BY` posterior, con tres claves y `max(#3)`, reduce a 6079 filas y muestra 0.01 s. No aparece `WINDOW` en este plan. El plan informa `Total Time: 0.0421s`.

Los tiempos de operadores son los que muestra DuckDB, redondeados y con ejecución paralela; no deben sumarse para reconstruir el tiempo de pared total. Los tiempos de `EXPLAIN ANALYZE` corresponden a ejecuciones adicionales y se distinguen de las cinco repeticiones.

### Escalabilidad y desempates

LAG ya se ejecutó sobre las **1353311 visitas** completas en la Actividad 4. El intento previo del self-join equivalente full-table fue interrumpido manualmente por resultar computacionalmente prohibitivo, según lo reportado durante el laboratorio; no se dispone de un tiempo completo de ese intento. **No se volvió a ejecutar el self-join full-table** en esta actividad ni se guardó como consulta ejecutable sin el límite de pacientes.

La auditoría de empates, ejecutada mediante GROUP BY sin self-join temporal, confirmó **6313 grupos** de `patient_id/start_at` con **12655 encuentros**. No se puede eliminar el desempate por `id`: una visita puede tener como anterior otra con el mismo inicio y un UUID menor. Comparar solo fechas cambiaría los intervalos y las primeras visitas.

El self-join construye muchas parejas candidatas conforme crece la historia del paciente: una historia de n visitas puede aportar hasta n(n−1)/2 parejas anteriores antes de la agregación. El plan observado ya muestra 588789 filas del LEFT JOIN para 6079 visitas. LAG expresa directamente la visita anterior y es mucho más legible. El intento full-table interrumpido aporta evidencia práctica de peor escalabilidad para esta implementación del self-join, sin demostrar que cualquier self-join sea más lento en todas las muestras o motores.

## Estado para revisión

Las **Actividades 1–10 están completas**, con las consultas anteriores conservadas, el notebook ejecutado de la Actividad 6 y los dos planes de la Actividad 10 disponibles. Los resultados de las comparaciones se documentan en cada sección. La diferencia de un paciente por hora del alta en la Actividad 9 queda explícita para revisión; se mantiene la política final sin observaciones futuras. No se implementó ningún Lab 12. Lab 10 permanece intacto y no se hicieron commit, push ni merge.

## Decisiones para revisión manual

- A cuenta grupos de IDs repetidos, no todas sus filas ni las filas excedentes. Se conserva la agrupación original, incluido su tratamiento de IDs nulos.
- El costo medio corresponde a todos los encuentros con diagnóstico, sin restringir a una enfermedad ni atribuir el medicamento o costo a un diagnóstico específico. Se conserva `AVG` y su exclusión de costos nulos, así como el redondeo a dos decimales.
- Se utilizaron `SEMI JOIN` de DuckDB en B para expresar existencia sin multiplicar filas. Si se requiere portabilidad a otro motor, revisar estos operadores.
- A parte de una subconsulta sin CTEs; B conserva su original con CTEs y la depuración de la Actividad 2. A es una auditoría de calidad de datos clínicos y su mejora de legibilidad es modesta.

Laboratorio listo para revisión. No se avanzó a ningún Lab 12 ni se hicieron commit, push o merge.
