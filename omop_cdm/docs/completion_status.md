# Estado de finalización y decisiones pendientes

Revisión del 16 de noviembre de 2026. No se ha completado la migración clínica
persistente. Durante esta revisión no se modificó la implementación ETL ni se
ejecutaron notebooks, ajustes de modelos o métricas predictivas. Se realizaron
consultas de solo lectura y se guardaron informes de auditoría.

## 1. Protección de 02.4

La comparación exacta está bloqueada: el hash inicial
`15a515fb86bea687abe4809c75e94509d88163a05c65c7e68d1c38c39d30d3a3`
no corresponde al contenido actual
`c7e863db914575105c4b77a124297473d195c752f49489f9979e0c1c771fc93a`.
El actual sí coincide con el cierre anterior. Se inspeccionaron historial Git,
objetos Git no alcanzables y ubicaciones pertinentes de backups; no se encontró
el contenido inicial. 02.4 no está rastreado y no tiene commits propios.

Se inventariaron código, Markdown, imágenes/salidas y metadatos del estado actual.
La última celda contiene llamadas de ajuste e interpretación SHAP, pero no es
posible atribuir con exactitud qué cambió respecto del estado inicial. La
comparación suplementaria con 02.3 no sustituye la versión anterior de 02.4.
No se puede certificar que el cambio fue solo visual ni declarar que se
modificaron determinadas métricas sin esa evidencia.

**Se detiene la implementación y carga por precaución científica**, sin afirmar
que exista un error demostrado. Para desbloquearla se necesita una copia con el
hash inicial o una revisión explícita que autorice una nueva referencia. No se
restauró, sobrescribió ni ejecutó 02.4. Detalle en
[notebook_24_audit.md](notebook_24_audit.md) y su JSON verificable.

## 2. Almacenamiento y solución

El disco de 287.3 GiB está prácticamente lleno. El diagnóstico actualizado
[`storage_audit.json`](storage_audit.json) registra el espacio libre al ejecutar
la inspección, los archivos existentes y los hashes. Se observaron aproximadamente
72.8 MiB libres en el control final, insuficientes para una carga clínica
completa. El valor exacto más reciente queda en `review_final_integrity.json`;
el espacio puede variar por actividad de otros procesos.

| Elemento | Tamaño observado |
|---|---:|
| `clinical.duckdb` | 539 504 640 bytes, 514.5 MiB |
| `omop_minimal.duckdb` | 12 070 912 bytes, 11.5 MiB |
| CSV Synthea completos | 16 642 482 619 bytes, 15.50 GiB |
| CSV usados por el flujo clínico implementado | 4 798 776 434 bytes, 4.47 GiB |
| Dos paquetes Athena originales | 1 463 865 540 bytes, 1.36 GiB |
| Datos locales de la implementación antigua del otro worktree | 5 268 979 050 bytes, 4.91 GiB |
| Reserva estimada del flujo actual | 22 122 836 816 bytes, 20.60 GiB libres |

La reserva corresponde a cuatro veces los CSV seleccionados más dos veces los
vocabularios. Incluye una estimación de linaje, WAL y temporales; **no es el tamaño
medido del CDM final** ni garantiza por sí sola capacidad para DQD. Se recomienda
un volumen persistente con al menos **30 GiB libres iniciales**, y volver a medir
el espacio requerido para DQD una vez conocido el tamaño real de la nueva base.
`/tmp` comparte el sistema de archivos del repositorio y no resuelve el bloqueo.
`/dev/shm` es memoria volátil y no se considera una solución de persistencia.

La búsqueda en las rutas ETL no encontró WAL, archivos `.building` ni temporales
de derrame pendientes de este flujo. No se eliminó ningún archivo para liberar
espacio. Hay copias de vocabulario con equivalencia SHA-256, enumeradas en el
JSON; se conservan. Su mera existencia no autoriza borrarlas ni fusionarlas.

La solución recomendada es mantener todas las fuentes en su ubicación y escribir
solo la nueva base y sus temporales en otro volumen persistente. Para una futura
optimización, tras resolver la puerta científica:

1. Consultar las fuentes por lotes con proyección de las columnas necesarias y
   registrar un manifiesto de lote, filas origen, destinos y cuarentena. El flujo
   actual materializa fuentes completas por etapas; **todavía no implementa
   checkpoints incrementales por lote**. Repetirlo completo no debe describirse
   como carga incremental.
2. Reutilizar un vocabulario compartido en solo lectura, después de verificar sus
   hashes y versión. `vocabDatabaseSchema` de DQD permite indicar un esquema
   distinto. La ETL actual usa `omop.concept` y tablas locales: cambiarla para usar
   un almacén externo requiere una adaptación y pruebas que no se aplican con la
   puerta científica bloqueada.
3. Usar Parquet solo cuando represente las mismas fuentes y exista procedencia
   verificable. Los Parquet de `local/referencia/` del otro worktree corresponden
   a un conjunto de referencia: no se sustituyen por los datos de los 22 851
   pacientes actuales para ahorrar espacio.
4. Mantener compresión DuckDB y evitar duplicar el staging y los datos de salida
   cuando un linaje por archivo/fila permita recuperar el original. No eliminar
   códigos, descripciones ni valores originales para reducir el tamaño.

### Procedimiento reproducible para terminar

**Primero debe resolverse la verificación de 02.4.** Después, con el volumen
disponible y las dependencias del README, desde la raíz del repositorio:

```bash
export SYNTHEA_CSV="$PWD/lab02/output/csv"
export ATHENA_PRIMARY="$PWD/vocabulary_download_v5_{20d4455f-c100-46dc-8821-8bc4895fa5ff}_1794189468751"
export ATHENA_SECONDARY="$PWD/vocabulary_download_v5_{6780bd73-b8a1-4136-ab04-d4d26c9188ca}_1794190792454"
# Sustituir por una ruta nueva en un volumen persistente con espacio suficiente.
export OMOP_OUTPUT='/ruta/al/volumen/omop54.duckdb'

.venv/bin/python omop_cdm/src/etl.py \
  --csv "$SYNTHEA_CSV" --vocab "$ATHENA_PRIMARY" --vocab "$ATHENA_SECONDARY" \
  --output "$OMOP_OUTPUT" --source-date 2026-08-16 \
  --vocabulary-date 2026-11-15 --preflight

# Solo si la verificación científica y el preflight son satisfactorios:
.venv/bin/python omop_cdm/src/etl.py \
  --csv "$SYNTHEA_CSV" --vocab "$ATHENA_PRIMARY" --vocab "$ATHENA_SECONDARY" \
  --output "$OMOP_OUTPUT" --source-date 2026-08-16 \
  --vocabulary-date 2026-11-15
```

La ruta de salida debe ser nueva. El esquema vacío local existente no se utiliza
como destino a sobrescribir. Este procedimiento ejecuta el alcance clínico
implementado y no resuelve automáticamente fuentes, vocabularios o dominios aún
pendientes que se enumeran en [limitations.md](limitations.md). Antes de declarar
OMOP completo se deben resolver esos puntos, validar la base resultante y ejecutar
DQD, además de repetir las comparaciones científicas contra esa base poblada.

## 3. Persistencia y estructura real

Se abrieron ambas bases nuevas en modo READ_ONLY y se contaron todas sus tablas:

- `local/omop54_schema_only.duckdb`: **39 tablas, 432 campos; las 39 tienen cero
  registros**. No hay tablas OMOP clínicas o de vocabulario pobladas en esa base.
- `local/cohort_comparison.duckdb`: siete tablas de resultados de auditoría. Hay
  824 filas en `cohort_rebuilt`, 655 en cada una de las tres matrices de
  entrenamiento y de las dos matrices FE, y un informe. **No es un CDM poblado.**

Los recuentos por nombre de tabla están en
[persistent_tables.json](persistent_tables.json). Las verificaciones de integridad
de tablas vacías no prueban calidad de una migración clínica completa. Los
recuentos clínicos del informe anterior describen únicamente el experimento en
memoria; no se trasladan a esta tabla de persistencia como si fueran filas
guardadas.

## 4. Discrepancias de los 418 pacientes

La auditoría independiente confirma 418 diferencias en entrenamiento y 515 en la
cohorte general. En entrenamiento, los recuentos de códigos distintos suman
**2449 con la definición original y 1472 con el recuento por tabla Condition**:
977 pares paciente–código, procedentes de 1205 registros fuente, dejan de
contribuir al predictor. Son registros representables como Observation, no
registros perdidos. En los 824 pacientes intervienen 1447 registros y 1175 pares.

Se identificaron 33 códigos de conditions.csv con destino ajeno a Condition:
32 de Observation y uno de Measurement. El único código Measurement no aparece
en el lookback de entrenamiento; por tanto no causa ninguno de los 418 casos.
Los códigos contribuyentes, sus conceptos oficiales, dominios, descripciones,
filas y pacientes por código están en
[diagnosis_domain_audit.md](diagnosis_domain_audit.md) y su JSON. Los conteos por
paciente se guardan solo en el directorio ignorado `results/`.

No se encontró un destino Condition omitido por la regla de exclusión ni evidencia
de mappings erróneos entre estos códigos y sus dominios oficiales vigentes.
La definición original cuenta los códigos fuente de conditions.csv, incluso
hallazgos y situaciones sociales; la representación OMOP los distribuye por
dominio. Usar solamente CONDITION_OCCURRENCE redefine el predictor. **No se
aplica ninguna corrección a las variables existentes.**

## 5. Cobertura de vocabularios

La auditoría de códigos fuente completa anterior continúa disponible, con su
snapshot declarado, en `data_audit.json`:

| Fuente | Cobertura por filas |
|---|---:|
| conditions | 98.6236% |
| medications | 100.0000% |
| observations | 96.2065% |
| procedures | 99.3527% |
| immunizations | 0.0000% |
| devices | 80.6254% |

Son coberturas de mapping, no tasas de carga persistente. Faltan CVX y vocabularios
demográficos en las descargas originales. El sistema LOINC de observaciones sin
SYSTEM requiere confirmar excepciones del exportador. Las listas de códigos no
mapeados y razones están en el JSON; no se fabricaron conceptos.

## 6. Pruebas y DQD

Comando local ejecutado nuevamente:

```bash
pytest omop_cdm/tests lab04/tests final_project/tests -q
```

**13 pruebas aprobadas, cero fallidas**. No ejecutan el notebook científico ni
ajustan modelos. Son pruebas propias y no reemplazan DQD.

[DQD oficial admite CDM 5.4](https://ohdsi.github.io/DataQualityDashboard/reference/executeDqChecks.html)
y su [historial documenta pruebas DuckDB](https://github.com/OHDSI/DataQualityDashboard/blob/main/NEWS.md).
No se ha demostrado una incompatibilidad entre ellos. Los impedimentos locales
son concretos:

- `requireNamespace` devuelve FALSE para DataQualityDashboard, DatabaseConnector,
  SqlRender y duckdb en R. No se instalaron paquetes automáticamente.
- La nueva base tiene cero personas, cero vocabularios y CDM_SOURCE vacía.
- No hay almacenamiento para completar el CDM y reservar una copia para DQD.
- Sigue bloqueada la verificación del estado inicial de 02.4.

**DQD no se ejecutó.** Número de comprobaciones, superadas, fallidas y
advertencias: **no disponibles**, no ceros. No se presentan los controles SQL
anteriores como un resultado del dashboard. El runner existente
`src/run_dqd.R` opera sobre una copia nueva y debe verificarse con los paquetes y
drivers instalados, una vez poblada la base. No se certificó su ejecución local.

## 7. Equivalencia científica de los datos disponibles

| Comprobación SQL | Resultado |
|---|---|
| Cohorte original | 824 pacientes y 85 readmisiones |
| Entrenamiento | 655 pacientes; cuatro exclusiones temporales sobre el bloque de 659 |
| Prueba temporal | 165 pacientes; mismas pertenencias en ambos sentidos |
| Seis predictores originales | Cero diferencias por variable en 824 pacientes, incluidos los 165 reservados |
| Tres variables FE | Cero diferencias por variable para los 655 de entrenamiento |
| FE en prueba temporal | Sin matriz original disponible para afirmar equivalencia |
| Reestimación de modelos/métricas | Ninguna |

La igualdad corresponde a matrices de comparación ya persistidas y a consultas
de fuentes originales, **no a una carga nueva de OMOP completa**. No se usaron
resultados de prueba para elegir mappings, variables o modelos. Las bases
originales se verificaron por SHA-256 y no se alteraron sus identificadores.

## 8. Estado por componente

| Componente | Estado |
|---|---|
| DDL oficial y esquema DuckDB | Implementado y verificado estructuralmente |
| Auditoría de códigos/418 discrepancias | Verificada por SQL y Athena |
| ETL clínica | Parcialmente implementada; validación a escala incompleta |
| Carga persistente completa | Pendiente; bloqueada por almacenamiento y referencia de 02.4 |
| Comparación exacta inicial de 02.4 | Pendiente; falta el contenido inicial |
| Matrices de auditoría | Persistidas y comparadas |
| DQD | Compatible a nivel de herramienta; entorno local no preparado, sin ejecución |
| Incompatibilidad demostrada | Ninguna; no confundir falta de requisitos con «no compatible» |

No hay commit, push, eliminación de archivos, modificación de notebooks ni
sobrescritura de bases. La tarea permanece **incompleta** hasta resolver la
referencia científica, persistir los datos y realizar la validación pendiente.
