# Lab 12 — OMOP CDM v5.4: entrega para revisión académica

Repositorio: `luisebh1919/healthcare_data_science_ai_portfolio`, rama
`feat/lab12-omop-cdm`. Solo se incorporan archivos bajo lab12/. El proyecto final,
los demás laboratorios y sus bases permanecen intactos. No se fusiona a main.

Las diez actividades tienen evidencia en [reporte_calidad.md](reporte_calidad.md)
y [docs/criterios_evaluacion.md](docs/criterios_evaluacion.md). La actividad 9 se
verificó con los vocabularios ATHENA descargados, como autorizó el estudiante;
no se afirma navegación interactiva en el portal.

## Alcance y decisión técnica

Se implementó la ruta manual permitida por el [enunciado oficial](https://github.com/insomnium098/curso-ciencia-datos-2027-1/blob/main/labs/s12-omop-cdm-introduccion/README.md):
person, observation_period, visit_occurrence y condition_occurrence, ampliadas a
observation y measurement para respetar los dominios reales de conditions.csv.
No equivale a un CDM completo ni convierte medications.csv u observations.csv
completos. Los 830799 eventos contabilizados proceden únicamente de conditions.csv.

Se examinó primero OHDSI ETL-Synthea en commit
`9ee6eb1b933c70af7b80711332aa92327af1f7c5`: admite CDM 5.4 y versiones explícitas de
Synthea hasta 3.3.0, con ejemplo PostgreSQL/JDBC. No se demostró soporte directo
de su flujo completo para DuckDB ni compatibilidad del JAR local por commit
`7e08387` con esas versiones. DuckDB 1.5.6 permitió convertir los CSV verificados
sin regenerarlos. etl_ohdsi.R conserva la alternativa oficial, **no ejecutada**.

## Estado final observado

- 22851 personas, 1353311 visitas y 22851 períodos aproximados.
- 390926 Condition + 439868 Observation + 5 Measurement = 830799 filas clínicas
  fuente, todas trazables. No hay filas sin destino ni duplicación de trazas.
- Sin estándar: Condition 2497/390926 (0.638740%); Observation 8938/439868
  (2.031973%); Measurement 0/5; Gender 0/22851; Visit 3166/1353311 (0.233945%).
- 2042800 conceptos, 846204 estándar: incluye dos conceptos Gender canónicos de
  un suplemento oficial histórico identificado. ATHENA original aportó 2042798 y
  846202 respectivamente. Relaciones y dependencias se conservan.
- 22 pruebas Lab 12 y 71 pruebas anteriores aprobadas; 69 comprobaciones sin discrepancias.
- Las 3166 visitas hospice no se fuerzan a un tipo: no se conoce su lugar de
  atención. home, virtual y snf tienen destinos explícitos; urgentcare se agrega
  a Emergency Room por convención OHDSI, conservando la clase fuente para no
  confundir esos registros con urgencias hospitalarias exclusivamente.

## Consultar y validar la base disponible

Desde la raíz del worktree:

```bash
python3 -m venv lab12/local/.venv
lab12/local/.venv/bin/python -m pip install -r lab12/requirements.txt
lab12/local/.venv/bin/python lab12/generar_reporte.py --db lab12/local/omop_corregido.duckdb --reference lab12/resultados/referencia_resultados.json
LAB12_DB=lab12/local/omop_corregido.duckdb lab12/local/.venv/bin/python -m unittest discover -s lab12/tests -v
```

No es necesario reconstruir la base ya disponible. Sin LAB12_DB, las pruebas usan
fixtures artificiales autocontenidas; nunca se publican como resultados reales.
El generador consulta la base identificada en read_only y no carga resultados
propios anteriores. Registra run_id, fecha, versiones y huellas del SQL.

## Reproducción en una salida nueva

Se necesitan los CSV propios patients/encounters/conditions y las dos descargas
ATHENA. Sus huellas están en resultados/resultados.json. Los CSV comprobados
residen en el worktree vecino `../Labs - Clase - Tareas/lab02/output/csv`.
Los scripts rechazan salidas existentes y migraciones repetidas para preservar
el antes. No ejecutar esta reconstrucción solo para consultar la base actual.

```bash
# Usar rutas reales, fuera de Git. Ejemplo de nombres de salida nuevos.
export LAB12_CSV='/ruta/synthea/csv'
export LAB12_ATHENA='lab12/local/athena_nuevo'
export LAB12_GENDER='/ruta/GiBleed_5.3.zip'
export LAB12_EUNOMIA='/ruta/Synthea27NjParquet_5.4.zip'
lab12/local/.venv/bin/python lab12/preparar_vocabularios.py --zip /ruta/paquete_1.zip --zip /ruta/paquete_2.zip --out "$LAB12_ATHENA"
lab12/local/.venv/bin/python lab12/pipeline.py --csv "$LAB12_CSV" --vocab "$LAB12_ATHENA" --db lab12/local/repro_base.duckdb --results lab12/local/repro_base.json
lab12/local/.venv/bin/python lab12/corregir_dominios.py --source lab12/local/repro_base.duckdb --output lab12/local/repro_final.duckdb --gender-reference "$LAB12_GENDER"
lab12/local/.venv/bin/python lab12/reubicar_no_mapeados.py --db lab12/local/repro_final.duckdb
lab12/local/.venv/bin/python lab12/finalizar_visitas.py --db lab12/local/repro_final.duckdb
lab12/local/.venv/bin/python lab12/referencia.py "$LAB12_EUNOMIA"
lab12/local/.venv/bin/python lab12/generar_reporte.py --db lab12/local/repro_final.duckdb --reference lab12/resultados/referencia_resultados.json
```

La unión ATHENA elimina solo filas idénticas, detecta conflictos y conserva las
tablas auxiliares completas. No se convirtió un concepto no estándar en estándar.
Se integraron 430930 Observation y cinco Measurement válidos; otros 8938 eventos
se reubicaron en Observation conservando concepto cero y su origen.

Los dos conceptos Gender se extraen del ZIP oficial
[GiBleed_5.3](https://github.com/OHDSI/EunomiaDatasets/blob/3d349dcdd79cc346b8e36eb837e49feffe7f7497/datasets/GiBleed/GiBleed_5.3.zip).
La referencia comparativa es [Synthea27NjParquet_5.4](https://github.com/OHDSI/EunomiaDatasets/blob/3d349dcdd79cc346b8e36eb837e49feffe7f7497/datasets/Synthea27NjParquet/Synthea27NjParquet_5.4.zip).
Se descargaron de OHDSI, no se copian sus pacientes ni los archivos al repositorio.
Los SHA256 identifican exactamente las versiones utilizadas; no usar el CDM por
defecto de Eunomia, que puede tener otra versión.

## Evidencia de reproducibilidad y pruebas

```bash
lab12/local/.venv/bin/python lab12/verificar_reproducibilidad.py --db lab12/local/omop_corregido.duckdb --csv '../Labs - Clase - Tareas/lab02/output/csv' --vocab lab12/local/athena_unificado --gender-reference /tmp/lab12-eunomia/datasets/GiBleed/GiBleed_5.3.zip --reference /tmp/lab12-eunomia/datasets/Synthea27NjParquet/Synthea27NjParquet_5.4.zip
```

Ese comando usa las rutas locales de esta sesión: ajustarlas en otra máquina.
Verifica 17 archivos y repite todas las consultas en conexiones independientes;
no afirma haber repetido una generación Synthea con semilla desconocida.
Para las suites anteriores se usó pytest disponible en el entorno original,
por separado para evitar colisiones entre dos paquetes llamados clinlab:

```bash
python3 -m pytest -q -p no:cacheprovider lab04/tests
PYTHONPATH=lab05/clinlab/src python3 -m pytest -q -p no:cacheprovider lab05/clinlab/tests
PYTHONPATH=lab06/clinlab/src python3 -m pytest -q -p no:cacheprovider lab06/clinlab/tests
```

## Modelo y archivos de entrega

- sql/consultas_omop.sql: las doce consultas principales, idénticas para Eunomia.
- sql/calidad_vocabularios.sql, consultas_ampliadas.sql y auditoria_final.sql:
  mapeo, denominadores, duplicación, trazabilidad y temporalidad.
- docs/diagrama_er.md: seis tablas clínicas, vocabularios y diferencias con 5.4.
- docs/comparacion_esquema.json: comprobación ejecutada de columnas de seis tablas.
- resultados/resultados.json y reproducibilidad.json: agregados, manifiestos y pruebas.
- resultados/antes_correcciones.json y docs/correcciones_dominios.md: antes/después.
- docs/athena_revision.md: tres conceptos, jerarquías, origen y limitación del portal.
- docs/validacion.md: validación final; documentos históricos se marcan como tales.

El DDL se contrastó con CommonDataModel v5.4.0. Para repetir la comparación:

```bash
curl -fsSL https://raw.githubusercontent.com/OHDSI/CommonDataModel/v5.4.0/inst/ddl/5.4/postgresql/OMOPCDM_postgresql_5.4_ddl.sql -o /tmp/lab12-official.sql
lab12/local/.venv/bin/python lab12/comparar_esquema.py /tmp/lab12-official.sql lab12/local/omop_corregido.duckdb
```

## Límites científicos

Es un subconjunto docente, no un CDM completo ni apto por sí solo para inferencia
clínica. Raza, etnia y tipos/procedencia tienen campos cero. Los períodos de primera
a última visita no prueban observación continua: 21165 personas tienen algún hueco
mayor de un año. Los eventos fuera de esos límites se conservan y se filtran con
EXISTS cuando el análisis exige cobertura; no se amplió la ventana para ocultarlos.

Los 11435 eventos sin estándar no se sustituyen por aproximaciones clínicas:
2393 tienen dos conceptos inválidos D; los demás son conceptos no estándar sin
Maps to vigente. Los 8938 Observation permanecen en su dominio. Los cinco
hallazgos categóricos de anticuerpos no reciben una concentración/unidad inventada.
Gingivitis aparece en 18512/22851 personas dentro del período (81.01%): es una
fracción histórica en datos sintéticos, no prevalencia puntual ni estimación real.
La frecuencia ya estaba en la fuente y no deriva de duplicaciones del ETL.

Ningún CSV, base, vocabulario descargado, credencial o entorno local se publica.
El portal ATHENA no pudo verificarse interactivamente; los tres conceptos y sus
relaciones sí se comprobaron en el paquete real descargado. Esta limitación está
permitida por la misión y no se presenta como navegación realizada.
