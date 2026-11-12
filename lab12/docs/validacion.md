# Validación final

Base: local/omop_corregido.duckdb. Ejecución: `c5f4d42e-004f-4fb1-ab25-c056bd999276`.
Python 3.13.5; DuckDB 1.5.6, instalado en lab12/local/.venv con requirements fijados.

| Suite o comprobación | Resultado real |
| --- | --- |
| Lab 12 (unittest, base real y fixtures) | 22 aprobadas |
| Lab 04 | 7 aprobadas |
| Lab 05 | 32 aprobadas |
| Lab 06 | 32 aprobadas |
| Total de pruebas distintas | 93 aprobadas |
| Comprobaciones de la base final | 69, cero discrepancias |
| Repetición analítica | Dos conexiones independientes, resultados iguales |
| Insumos cotejados por SHA256 | 17 archivos, todos coinciden |
| Referencia | Mismo SQL confirmado por SHA256 |
| DDL oficial | Seis tablas sin columnas faltantes ni adicionales |

Las suites clinlab se ejecutaron por separado para evitar colisiones de módulos.
Las fixtures temporales son artificiales y no se exportan a resultados reales.
Se probaron rollback, repetición de migraciones, conceptos inexistentes/invalidos/U,
destinos de otro dominio, Gender, valores no inventados, Visit/hospice y la ausencia
de trazabilidad interna en la referencia externa.

Los controles de la base cubren PK, FK de persona/visita, conceptos y dominios,
relaciones y jerarquías, diccionarios y auxiliares, fuente/origen/destino, duplicados
exactos, fechas y cobertura. Los 69 ceros son discrepancias estructurales,
no una afirmación de mapeo total ni de observación continua. Véase el reporte para
los 11435 eventos sin estándar y los huecos de cobertura.

La evidencia de reproducibilidad se limita a los insumos identificados y a las
consultas: no afirma una segunda generación Synthea ni un ETL completo repetido
durante el cierre. El flujo completo reproducible está en README y sus migraciones
sí se ejecutaron sobre los datos reales durante el desarrollo.

Inspección Git: solo lab12/ en la entrega, sin cambios en final_project/ u otros
laboratorios; local/, entornos, bases y CSV excluidos. Publicación autorizada solo
de feat/lab12-omop-cdm y PR a main, sin merge.
