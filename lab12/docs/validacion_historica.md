> Registro histórico; estado final en validacion.md.

# Validación de la integración

## Estado actual: correcciones de dominios y Gender

Esta sección prevalece sobre los registros históricos inferiores. La base activa
es local/omop_corregido.duckdb, con el antes conservado en omop_athena.duckdb.
Se aplicaron migraciones incrementales sobre copia, sin repetir el ETL completo.

- **19 pruebas de Lab 12 aprobadas** sobre la base corregida (última serie: 7.808 s),
  incluidas seis pruebas nuevas de migración: Gender canónico, sexo desconocido,
  Observation, Measurement sin valores inventados, reubicación con concepto cero,
  repetición rechazada y rollback ante destino inválido (varios aspectos por prueba).
- **71 pruebas anteriores aprobadas**: Lab 04, 7; Lab 05, 32; Lab 06, 32.
- **38 comprobaciones** de integridad/reconciliación en la base corregida: cero
  discrepancias; cero fuentes sin destino y cero pendientes de otro dominio.
- Las seis tablas clínicas se compararon con las columnas oficiales CDM 5.4.0:
  ninguna faltante ni adicional. Las claves siguen siendo lógicas auditadas.
- Gingivitis: cero expansión del mapeo, duplicados exactos, grupos con mismo
  inicio/encuentro y solapamientos estrictos. Se registró evidencia del generador,
  sin afirmar conocer la semilla ni la procedencia exacta de los CSV.
- Estados antes/después en resultados/antes_correcciones.json y resultados/resultados.json.
  Denominadores y límites científicos en correcciones_dominios.md.
- Git solo muestra incorporaciones bajo lab12/; proyecto final intacto, datos y
  bases ignorados; sin commit, push ni merge.

## Actualización posterior: auditoría de ATHENA sin repetir ETL

Esta actualización prevalece sobre los conteos de pruebas de la integración
inicial que se conservan abajo como registro histórico. La base ATHENA existente
se reutilizó con el mismo run_id; no se creó omop_athena_v2.duckdb.

- Lab 12: **13 pruebas aprobadas** en 5.254 s, incluyendo la base real ATHENA y
  fixtures temporales para inexistentes, inválidos D, actualizados/obsoletos U,
  separación por dominio y bloqueo del informe ante relaciones huérfanas.
- Lab 04: 7 aprobadas; Lab 05: 32 aprobadas; Lab 06: 32 aprobadas.
- 19 comprobaciones estructurales sin discrepancias; cuatro extremos de FK de
  vocabularios sin huérfanos; cero filas fuente sin traza; cero eventos clínicos
  estándar sin relación Maps to válida.
- El informe y resultados.json se recalcularon desde la base en solo lectura.
  Las tablas temporales de las pruebas no se incorporaron a los resultados reales.
- Proyecto final sin diferencias respecto de main; datos, vocabularios y bases
  siguen ignorados. No hubo commit, push ni merge.

Auditoría científica y técnica: auditoria_athena.md. Verificación de conceptos:
athena_revision.md. El contraste interactivo del portal ATHENA permanece bloqueado
por falta de navegador conectado y páginas no legibles mediante el lector web.

## Registro de la integración inicial

Repositorio: `https://github.com/luisebh1919/healthcare_data_science_ai_portfolio.git`.
Rama verificada: `feat/lab12-omop-cdm`. HEAD y main permanecen en
`1163cee71c7105235f3f8058faf565d7c9574688`; no hubo commit, push ni merge.
Solo `lab12/` aparece como incorporación en git status. La comparación
`git diff --exit-code main -- final_project` no mostró cambios.

Se reutilizó el trabajo anterior, reorganizando SQL en sql/, pruebas en tests/,
diagrama y comparación en docs/, y agregados en resultados/. Las bases se
construyeron únicamente en local/, ignorado por Git. El archivo de informe
inicial se conserva como histórico con una advertencia de su ubicación anterior.

## Ejecuciones reales en el worktree de destino

Python 3.13.5 y DuckDB 1.5.6. R y ruta OHDSI conservados de la revisión previa,
sin simular ejecución. El manifiesto de la nueva carga registra run_id y fecha UTC
en resultados/resultados.json y en la tabla local lab12_run.

| Verificación | Resultado |
| --- | --- |
| `python3 -m unittest discover -s lab12/tests -v` | 8 pruebas aprobadas, fixtures aisladas |
| `LAB12_DB=lab12/local/omop.duckdb python3 -m unittest discover -s lab12/tests -v` | 8 aprobadas, incluye base real provisional |
| Lab 04, `python3 -m pytest -q -p no:cacheprovider lab04/tests` | 7 aprobadas |
| Lab 05, PYTHONPATH=lab05/clinlab/src, pytest sobre sus tests | 32 aprobadas |
| Lab 06, PYTHONPATH=lab06/clinlab/src, pytest sobre sus tests | 32 aprobadas |
| Validaciones de la carga provisional | 19 comprobaciones, cero discrepancias |
| Consultas SQL sobre base propia y Eunomia | Las 12 se ejecutaron en ambas |
| Comparación con DDL oficial 5.4.0 | Ninguna columna faltante/adicional en las cuatro tablas |
| Datos locales visibles para Git | local/ y cachés ignorados; ningún CSV o base entre entregables |

Se ejecutaron todas las suites Python identificadas en este worktree por separado
para evitar conflictos entre los dos paquetes llamados clinlab. No se ejecutaron
entrenamientos de modelos ni se abrió/modificó ninguna base del proyecto final.

## Regresión del generador de informes

La versión anterior contenía cifras/conclusiones fijas de la ejecución inicial y
rechazaba datos nuevos. Ahora exige una base identificada y recalcula todas las
consultas en modo read_only. Los JSON previos no intervienen. La referencia es
opcional y explícita; sin --reference no se arrastra la comparación anterior.

La prueba de transición construye dos bases **artificiales** en un directorio
temporal: una sin vocabularios y otra con diez conceptos de prueba, un destino
Condition, otro Observation y un código conocido sin mapeo. Verifica:

- Identificadores de ejecución distintos y conteos nuevos en el informe.
- Eliminación de texto anterior deliberadamente obsoleto y tolerancia a un JSON
  anterior inválido, porque no se lee como fuente.
- Conservación del concepto fuente incluso cuando no tiene destino estándar.
- Separación del destino Observation en rejected_domain.
- Rechazo de una base ausente o de vocabulario inconsistente con el manifiesto.

Estas fixtures nunca se exportan a resultados/ ni representan una descarga ATHENA.
La carga con el paquete real aún requiere la cuenta y los archivos del estudiante.

## Pendientes

No se certifican las actividades 3, 7 y 9 ni completitud semántica. Sigue en cero
el 100% de los conceptos de Condition, Visit y Gender por ausencia de vocabularios,
frente a cero códigos fuente ausentes en conditions. El efecto temporal observado
es 5426 eventos externos (0.6531062267%). La ventana, situaciones fuente, condición
elegida, interpretación estándar/origen y comparación de poblaciones requieren
validación científica. Raza, etnia y tipos/procedencia cero requieren desarrollo
adicional para uso científico. Pasos exactos y comandos: ../README.md.
