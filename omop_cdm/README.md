# Synthea → OMOP CDM 5.4.2 independiente

Publicación del 18 de noviembre de 2026: se versionan esquema, ETL, pruebas e
informes históricos. **La carga persistente completa y DataQualityDashboard
siguen pendientes**; no se declara una migración integralmente validada. Las
cifras de espacio y hashes de los informes del 15–16 de noviembre corresponden
a aquellas inspecciones y no se presentan como mediciones de la publicación.

## Estado de finalización — 16 de noviembre de 2026

La migración continúa **incompleta**. La [revisión de cierre](docs/completion_status.md)
documenta dos bloqueos: falta el contenido inicial de 02.4 para comparar sus
cambios científicos, y el último control registró 72.8 MiB libres frente a una
reserva estimada de 20.60 GiB. No se modificó el notebook ni se inició otra carga.

Se verificaron por SQL los 824 pacientes, 655 de entrenamiento y 165 de prueba,
sin diferencias en los seis predictores originales; las tres variables FE
coinciden para los 655 de entrenamiento. La explicación de los 418 casos ya está
desglosada [por código, dominio y registro](docs/diagnosis_domain_audit.md).

La base OMOP persistente tiene las **39 tablas vacías**; las matrices de auditoría
están en otra base y no se presentan como un CDM poblado. DQD admite 5.4 y DuckDB,
pero faltan sus paquetes R y la base completa: no se ejecutó. Las 13 pruebas
locales se aprobaron nuevamente y no equivalen a DQD.

Para reproducir solo las comprobaciones, sin ejecutar notebooks ni escribir bases:

```bash
.venv/bin/python tools/verify_omop_completion.py notebook
.venv/bin/python tools/verify_omop_completion.py storage
.venv/bin/python tools/verify_omop_completion.py persistence
.venv/bin/python tools/verify_omop_completion.py semantic
```

Los comandos guardan informes; `semantic` conserva los conteos por paciente
únicamente en `results/`, ignorado por Git. No desbloquean automáticamente la
implementación ni certifican como segura una diferencia no comprobable de 02.4.

El esquema completo de **39 tablas y 432 campos** se deriva del DDL oficial.
La ETL y sus pruebas son independientes de los laboratorios históricos. **La
carga persistente completa no se ha ejecutado:** al iniciar había 184 MiB libres.
La base local `local/omop54_schema_only.duckdb` contiene el esquema, sin registros
clínicos. Las validaciones clínicas de esta entrega se ejecutaron en memoria.
No se afirma cumplimiento integral de OMOP ni aprobación por DQD.

La auditoría reproduce la cohorte de 824 pacientes y el entrenamiento de 655
pacientes de 02.4 con la definición original. Compara los seis predictores y las
tres variables derivadas, sin ejecutar notebooks, modelos ni métricas predictivas.
Véanse [validación](docs/validation.md) y [resultados agregados](docs/data_audit.json).

## Diseño y fuentes oficiales

Se eligió **5.4.2**, manteniendo la estructura CDM 5.4, por soporte explícito de
[ETL-Synthea](https://github.com/OHDSI/ETL-Synthea) y el ejemplo DuckDB de
[Tutorial-ETL](https://github.com/OHDSI/Tutorial-ETL/tree/master/etl/etl-synthea).
El tutorial necesita ajustes de esquemas para DuckDB; por ello no se ejecuta
ciegamente su script, que además elimina su salida previa.

[CDM 5.5](https://ohdsi.github.io/CommonDataModel/cdm55Changes.html) es una versión
oficial disponible: agrega campos opcionales y tres tablas de vocabulario. No es
una incompatibilidad intrínseca de DuckDB. Se pospone porque no aporta una
necesidad demostrada del estudio y ETL-Synthea sigue declarando soporte 5.3/5.4.
[DQD](https://github.com/OHDSI/DataQualityDashboard) contempla ambas versiones; la
elección no se basa en afirmar que 5.5 carezca de herramientas de calidad.

`sql/vendor/` conserva sin modificar DDL PostgreSQL y CSV de campos de
[CommonDataModel v5.4.2](https://github.com/OHDSI/CommonDataModel/tree/v5.4.2).
`src/schema.py` sustituye solo el nombre de esquema y `NUMERIC` por `DOUBLE`:
DuckDB interpreta NUMERIC sin escala como DECIMAL(18,3), que redondearía mediciones.
Los valores originales quedan en el linaje. Se contrastan tablas, columnas,
tipos y nulabilidad contra el CSV oficial; las claves se verifican mediante SQL.
No se confunde esa verificación estructural con cumplimiento semántico.

Los vocabularios proceden de las dos descargas locales de [Athena](https://athena.ohdsi.org/).
Se cargan sus nueve tablas de CDM 5.4, deduplicando solo filas exactamente iguales
y rechazando conflictos de clave. Los archivos adicionales de 5.5 se conservan
en origen. Las [reglas oficiales de vocabularios](https://github.com/OHDSI/Vocabulary-v5.0/wiki)
orientan el mapeo a conceptos estándar mediante `Maps to`, con vigencia y dominio.
El informe conserva las versiones reales: SNOMED 2026, RxNorm 20260601, LOINC 2.82
y versión general `v5.0 29-AUG-26`. La fecha `--vocabulary-date` es la **fecha de
evaluación de vigencia**, no una afirmación sobre la fecha de descarga.

## Entorno limpio

Desde la raíz del repositorio, con Python 3.13 y espacio suficiente:

```bash
python3 -m venv omop_cdm/local/venv
omop_cdm/local/venv/bin/python -m pip install -r omop_cdm/requirements.txt
omop_cdm/local/venv/bin/python -m pytest omop_cdm/tests -q
```

No se requieren pandas, scikit-learn, XGBoost ni el entorno de 02.4. Los datos
Synthea y vocabularios no están en Git: deben provisionarse localmente respetando
las licencias Athena. Las fuentes actuales se identifican por el metadato Synthea:
revisión `7e08387`, semilla `1786913600893`, 22 851 pacientes, Massachusetts,
fecha de referencia `2026-08-16` e historial exportado de diez años. No se supone
que esa revisión sea idéntica a Synthea 3.3.0, ni se afirma reproducción exacta
del generador sin sus módulos y propiedades originales.

Las dos carpetas locales `vocabulary_download_v5_*` son paquetes distintos y deben
pasarse explícitamente mediante sendos `--vocab`. Con variables de shell que
apunten a esas carpetas, el comando reproducible es:

```bash
python omop_cdm/src/etl.py \
  --csv lab02/output/csv \
  --vocab "$ATHENA_PRIMARY" --vocab "$ATHENA_SECONDARY" \
  --output omop_cdm/local/omop54.duckdb \
  --source-date 2026-08-16 --vocabulary-date 2026-11-15 --preflight
```

La inspección previa no crea la base y devuelve bytes de entrada, espacio libre
y una reserva conservadora para tablas, linaje, WAL y temporales. Esta reserva
es una estimación, no un tamaño medido de la base final. **Solo con espacio
suficiente**, repetir sin `--preflight` inicia la carga. No hay descargas
automáticas, borrado de salidas ni modificación de fuentes.

La ETL crea una salida `.building`, valida dentro de una transacción y publica
la salida con un enlace exclusivo. Una ejecución repetida con los mismos hashes,
código y parámetros devuelve el informe guardado sin escribir. Si las entradas
cambian o la salida es ajena, exige otro nombre. Un `.building` tras un fallo se
conserva para diagnóstico y no se reutiliza ni elimina automáticamente.

## Transformación y conservación

`patients`, `encounters`, `conditions`, `medications`, `observations`, `procedures`,
`immunizations` y `devices` son las fuentes requeridas por el flujo. Organizaciones
y proveedores son opcionales. Las seis fuentes de eventos se enrutan al dominio
oficial del concepto destino: Condition, Drug, Measurement, Observation, Procedure
o Device. Mapeos múltiples oficiales se mantienen. Sin destino estándar se usa
concepto cero y una razón; el archivo de origen determina únicamente la tabla
de respaldo, sin inventar una clasificación clínica estándar.

`etl.lineage` conserva archivo/fila, código, descripción, valor, unidad, fechas,
paciente/encuentro fuente y destino. `etl.rejected` conserva el motivo y la fila
completa de registros imposibles de representar con las reglas implementadas.
El manifiesto SHA-256 enlaza los datos originales. Las relaciones paciente-visita
se validan; se ponen en cuarentena referencias cruzadas o fechas inválidas.

No se crean subvisitas duplicando encuentros. `VISIT_DETAIL` queda vacío porque
este flujo conserva cada encuentro fuente como una visita y todavía no fusiona
hospitalizaciones solapadas. Esto se declara como limitación frente al tratamiento
de visitas de ETL-Synthea. No se inventan dosis, suministros, causas de muerte,
razas, especialidades ni episodios. Para medicamentos sin STOP se aplica
`coalesce(stop,start)`, como en el SQL oficial de ETL-Synthea; `verbatim_end_date`
y el linaje distinguen el fin fuente ausente. No expresa duración real conocida.
Para visitas sin alta no se imputa un alta: se registra la cuarentena.

Los textos largos se conservan; su incompatibilidad con longitudes declaradas
se informa, sin truncarlos silenciosamente. Las unidades solo se asignan por
correspondencia UCUM exacta y única; no se convierten valores numéricos. Los
valores categóricos no reciben conceptos por semejanza de texto.

## Auditoría sin recalcular el estudio

Con DuckDB disponible, desde la raíz y con las variables Athena definidas:

```bash
python omop_cdm/src/audit_data.py \
  --csv lab02/output/csv \
  --vocab "$ATHENA_PRIMARY" --vocab "$ATHENA_SECONDARY" \
  --vocabulary-date 2026-11-15 \
  --raw lab10/data/clinical.duckdb \
  --original final_project/data/omop_minimal.duckdb \
  --report omop_cdm/results/data_audit.json
```

La auditoría usa hasta 6 GB de memoria del motor, más sobrecarga de proceso, y
prohíbe derramar temporales a disco. Requiere RAM disponible; no reduce la fuente
para aparentar una validación completa. Las bases originales se adjuntan READ_ONLY
y se verifican por SHA-256. La cohorte y condiciones se reconstruyen en un CDM
nuevo en memoria; fármacos y mediciones para predictores se leen de los CSV fuente.
La cobertura de vocabularios se calcula sobre **todas** las filas de las seis
fuentes de eventos. Eso no equivale a haberlas cargado todas al CDM.

`--comparison-output` permite conservar en una base nueva y pequeña las tablas de
comparación de cohortes/entrenamiento. Esa base contiene resultados de auditoría,
no se presenta como la OMOP clínica completa. Todas las salidas por paciente
permanecen en `local/` o `results/`, ignoradas por Git.

## Calidad y trabajo pendiente

`src/run_dqd.R` prepara la ejecución de DQD sobre una copia nueva de la OMOP
poblada, con resultados en otro directorio. No instala dependencias ni toca las
bases originales. No pudo ejecutarse: faltan los paquetes R y la base completa
poblada; el disco tampoco permite instalarlos ahora. Los controles Python/SQL
no se etiquetan como un resultado oficial DQD.

La [validación](docs/validation.md) y el [plan de pendientes](docs/limitations.md)
detallan cobertura, diferencias científicas y límites. No se cambia la definición
del estudio, se rediseñan modelos ni se reemplaza su base por esta implementación.
