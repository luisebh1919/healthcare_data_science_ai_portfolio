> Registro histórico: para el estado final usar ../README.md.

# Lab 12 — Introducción a OMOP CDM (provisional)

Repositorio de destino: `luisebh1919/healthcare_data_science_ai_portfolio`.
Rama: `feat/lab12-omop-cdm`. Se reutilizó la implementación previa del repositorio
del curso: no se reconstruyó desde cero. Solo se incorporaron archivos bajo lab12/.
El proyecto final y los laboratorios anteriores permanecen sin modificaciones.
No se hizo commit, push ni merge. Los CSV y bases están ignorados por Git.

Enunciados revisados: [Lab 12](https://github.com/insomnium098/curso-ciencia-datos-2027-1/blob/main/labs/s12-omop-cdm-introduccion/README.md)
y sesiones 10–11, además de los resultados locales del portafolio.
La base actual tiene **ATHENA cargado, pendiente de validación científica**; no es un CDM completo.


## Estado actual: copia corregida

La base activa es **local/omop_corregido.duckdb**. El antes se conserva en
local/omop_athena.duckdb. Gender está corregido con un suplemento oficial
identificado; Observation y Measurement están cargadas. Se reubicaron también
8938 Observation sin estándar manteniendo concepto cero. Véanse
docs/correcciones_dominios.md y reporte_calidad.md para antes/después y denominadores.

```bash
python3 lab12/generar_reporte.py --db lab12/local/omop_corregido.duckdb --reference lab12/resultados/referencia_resultados.json
LAB12_DB=lab12/local/omop_corregido.duckdb python3 -m unittest discover -s lab12/tests -v
```

Los apartados de reanudación con ATHENA y los comandos de base inicial que siguen
documentan estados anteriores. No ejecutarlos para regenerar el informe actual.
La reproducción de las migraciones está en docs/correcciones_dominios.md.

## Estado de la reanudación con ATHENA

Se conserva `local/omop_athena.duckdb` (run_id 976e8ad6-69eb-4b7d-9308-92383369ea1e).
No ejecutar el ETL para consultar estos resultados. Actualizar únicamente con:

```bash
python3 lab12/generar_reporte.py --db lab12/local/omop_athena.duckdb --reference lab12/resultados/referencia_resultados.json
LAB12_DB=lab12/local/omop_athena.duckdb python3 -m unittest discover -s lab12/tests -v
```

`preparar_vocabularios.py` documenta la unión de las dos descargas; los ZIP y CSV
permanecen fuera de Git. Actividades 3, 5 y 7 tienen resultados actuales; actividad
9 está verificada localmente y requiere contraste interactivo del portal.
Véanse docs/auditoria_athena.md y docs/athena_revision.md. Los comandos posteriores
sin vocabulario se conservan para reproducir el estado inicial, no el estado actual.
Faltan Gender, ampliar las clases Visit y destinos Observation/Measurement, y la
validación científica. No se modificó el ETL clínico ejecutado durante la reanudación.

## Archivos

- pipeline.py: conversión, carga de vocabularios y construcción en DuckDB.
- sql/consultas_omop.sql: doce consultas comentadas, sin multiplicar pacientes.
- generar_reporte.py: informe desde la base elegida en modo de solo lectura.
- tests/: regresiones de integridad y transición a vocabularios artificiales.
- docs/: ER, comparación oficial y reporte inicial conservado como evidencia histórica.
- resultados/: agregados verificables actuales y referencia independiente.
- local/: bases y extracción de referencia, excluidas de Git.
- etl_ohdsi.R: alternativa OHDSI preparada, no ejecutada.

## Ejecución desde la raíz del portafolio

```bash
python3 -m pip install -r lab12/requirements.txt
python3 lab12/pipeline.py --csv '../Labs - Clase - Tareas/lab02/output/csv' --allow-unmapped
python3 lab12/generar_reporte.py --db lab12/local/omop.duckdb --reference lab12/resultados/referencia_resultados.json
python3 -m unittest discover -s lab12/tests -v
LAB12_DB=lab12/local/omop.duckdb python3 -m unittest discover -s lab12/tests -v
```

Los CSV existen en el worktree original vecino; no se copiaron. En otra máquina,
usar --csv con la ruta real. El pipeline rechaza una base de salida existente:
para repetir, usar --db lab12/local/otra_ejecucion.duckdb. No sobrescribe datos.
Las pruebas predeterminadas son autocontenidas y usan fixtures temporales; la
variable LAB12_DB añade la validación de la base construida sin cambiarla.

Cada construcción registra run_id, fecha UTC, versiones y huellas SHA256 de los
CSV y vocabularios en lab12_run. El informe exige --db y recalcula cada consulta
desde esa base; no carga el JSON de la ejecución previa. La referencia se incluye
solo si se solicita con --reference y conserva la identidad de su ZIP.
Una base sin manifiesto o inconsistente provoca error; no reutilizar un reporte
previo como si correspondiera a una ejecución fallida.

## Completar ATHENA: actividades 3, 7 y 9

1. Crear/iniciar tu cuenta en [ATHENA](https://athena.ohdsi.org/) y verificarla.
   Seleccionar SNOMED, ICD10CM, RxNorm, LOINC y ATC, conservando vocabularios
   estándar y administrativos preseleccionados/dependencias, incluidos Gender y
   Visit para este ETL. Si ATHENA solicita licencias o acuerdos, resolverlos con
   tu cuenta; no compartir contraseñas. [Instrucciones oficiales OHDSI](https://ohdsi.github.io/TheBookOfOhdsi/StandardizedVocabularies.html#access-to-the-standardized-vocabularies).
2. Solicitar el paquete, esperar a que esté disponible y descargar/descomprimir
   el ZIP fuera de Git. Facilitar **solo la ruta local**. Debe contener los archivos
   tabulados CONCEPT.csv, CONCEPT_RELATIONSHIP.csv y CONCEPT_ANCESTOR.csv, sin
   renombrarlos. Conservar además VOCABULARY.csv y los metadatos de la descarga
   para documentar su versión/fecha; no versionar estos archivos.
3. El agente puede ejecutar los comandos siguientes al recibir la ruta. Si los
   ejecutas tú, sustituir /ruta/athena por la carpeta real y usar una salida nueva:

```bash
python3 lab12/pipeline.py --csv '../Labs - Clase - Tareas/lab02/output/csv' --vocab /ruta/athena --db lab12/local/omop_athena.duckdb
LAB12_DB=lab12/local/omop_athena.duckdb python3 -m unittest discover -s lab12/tests -v
python3 lab12/generar_reporte.py --db lab12/local/omop_athena.duckdb --reference lab12/resultados/referencia_resultados.json
```

**Actividad 3:** confirmar las tres tablas cargadas, cinco vocabularios presentes,
total de conceptos y estándar, y registrar versión/fecha de descarga. El pipeline
comprueba presencia de los cinco vocabularios y conserva huellas de los tres CSV.
La carga real sigue pendiente; las pruebas con vocabulario artificial no la sustituyen.

**Actividad 7:** revisar la sección estándar/origen del informe nuevo. Aprobar una
condición clínicamente interpretable y explicar la igualdad/diferencia real entre
personas por código fuente y por cada destino estándar. Si el código más frecuente
no tiene destino Condition, revisar el dominio y elegir justificadamente otra
condición en la consulta estandar_origen; no contar concept_id=0 como enfermedad.
Los destinos fuera de Condition están en rejected_domain, no son no mapeados.
No sumar conteos por destinos que pueden incluir a las mismas personas.

**Actividad 9:** tomar los tres candidatos de la sección athena del JSON/informe
nuevo y buscar cada ID en ATHENA. Registrar fecha y enlace, concept_id con
concept_name, vocabulario, dominio, estándar, hijos directos y al menos un código
fuente que mapea al destino. Contrastar hijos directos con min_levels=1 y no
confundirlos con todos los descendientes ni con el propio concepto.
Completar docs/athena_revision.md; los espacios pendientes no son resultados.

La continuidad de observación, clasificación de situaciones fuente, condición
elegida y explicaciones clínicas requieren tu validación. Los tipos/procedencia,
raza y etnia cero siguen como limitaciones explícitas del ETL mínimo.

## Compatibilidad y elección de ruta (actividades 1–2)


Se prefirió inicialmente [OHDSI ETL-Synthea](https://ohdsi.github.io/ETL-Synthea/),
revisado en commit `9ee6eb1b933c70af7b80711332aa92327af1f7c5`.
Soporta CDM 5.4 y versiones Synthea 2.7.0–3.3.0 enumeradas en su código.
`CreateCDMIndexAndConstraintScripts.r` enumera motores y no incluye DuckDB;
esto no demuestra imposibilidad de adaptar SqlRender, pero tampoco soporte probado.
La ruta documentada es PostgreSQL mediante DatabaseConnector/JDBC.

R 4.6.2 está instalado; ETLSyntheaBuilder y Eunomia no lo están. El JAR local tiene
Build-Version `7e08387`, fecha 2026-07-22, Gradle 9.2.1 y JDK 17.0.20.
Esto no identifica una versión compatible certificada ni prueba que esos CSV
procedan exactamente de ese JAR. No se fingió ejecutar OHDSI ni se regeneraron
los datos para acomodarlos al ETL. Las huellas reales están en `resultados/resultados.json`.

Se eligió la ruta manual de cuatro tablas autorizada por el enunciado, con DuckDB
1.5.6 y Python 3.13.5, para aprovechar los CSV verificados y ejecutar auditorías
locales reproducibles. No equivale a portar íntegramente el paquete OHDSI.
`etl_ohdsi.R` preserva la alternativa oficial, **preparada pero no ejecutada**:
requiere PostgreSQL, controlador JDBC, paquetes R, vocabularios y una versión
Synthea comprobada. Usa esquemas nuevos precreados, nunca credenciales embebidas.

Para instalar esa alternativa tras resolver compatibilidad:

```r
install.packages('remotes')
remotes::install_github('OHDSI/ETL-Synthea@9ee6eb1b933c70af7b80711332aa92327af1f7c5')
```

Configurar las variables enumeradas al inicio de `etl_ohdsi.R` y ejecutarlo con
`Rscript lab12/etl_ohdsi.R`.


## Referencia y especificación

Se conserva EunomiaDatasets/Synthea27NjParquet_5.4, sin usar la versión por defecto.
Para descargar nuevamente la evidencia externa:

```bash
git clone --depth 1 --filter=blob:none --no-checkout https://github.com/OHDSI/EunomiaDatasets.git /tmp/lab12-eunomia
git -C /tmp/lab12-eunomia checkout HEAD -- datasets/Synthea27NjParquet/Synthea27NjParquet_5.4.zip
python3 lab12/referencia.py /tmp/lab12-eunomia/datasets/Synthea27NjParquet/Synthea27NjParquet_5.4.zip
curl -fsSL https://raw.githubusercontent.com/OHDSI/CommonDataModel/v5.4.0/inst/ddl/5.4/postgresql/OMOPCDM_postgresql_5.4_ddl.sql -o /tmp/lab12-official.sql
python3 lab12/comparar_esquema.py /tmp/lab12-official.sql
```

Omitir clone si ya existe. El ZIP se identifica por SHA256 en resultados/
referencia_resultados.json. Se ejecuta el mismo SQL en ambas bases. Eunomia es
una muestra sintética pequeña; sus vocabularios reducidos no sustituyen ATHENA.
El diagrama Mermaid y dos diferencias con el estándar están en docs/diagrama_er.md.

## Evidencia y límites

Las diez actividades se evalúan en reporte_calidad.md. El informe histórico de
docs/reporte_inicial_provisional.md se conserva íntegro para trazabilidad; contiene
rutas y comandos de la ubicación anterior, no debe usarse para ejecutar este lab.
Las incidencias iniciales de CREATE VIEW y del número de consultas se corrigieron
en el trabajo previo. Las limitaciones del aislamiento bwrap requirieron ejecutar
las verificaciones con autorización fuera del aislamiento.
