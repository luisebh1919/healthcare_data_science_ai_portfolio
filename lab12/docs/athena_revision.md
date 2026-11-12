# Actividad 9 — verificación con ATHENA descargado

Ejecución final: `c5f4d42e-004f-4fb1-ab25-c056bd999276`; consulta UTC: 2026-11-09T03:10:54.787790+00:00.
Fuente: las tres tablas principales de los dos paquetes reales ATHENA, identificados por SHA256 en resultados/resultados.json. No son datos de fixtures ni de Eunomia.

| concept_id y enlace | concept_name | vocabulary_id | domain_id | estándar | hijos directos | descendientes | código SNOMED fuente |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [4281516](https://athena.ohdsi.org/search-terms/terms/4281516) | Gingivitis | SNOMED | Condition | S | 35 | 76 | 66383009 |
| [40481087](https://athena.ohdsi.org/search-terms/terms/40481087) | Viral sinusitis | SNOMED | Condition | S | 1 | 1 | 444814009 |
| [4309238](https://athena.ohdsi.org/search-terms/terms/4309238) | Social isolation | SNOMED | Condition | S | 6 | 6 | 422650009 |

Hijos directos: min_levels_of_separation=1. Descendientes: min_levels_of_separation>0, excluyendo el propio concepto. Sus Maps to vigentes, fechas y nombres de origen/destino se incluyen en mapping_audit.relaciones_top. Las FK de la jerarquía no tienen huérfanos.

La comprobación interactiva del portal no se realizó: en el intento registrado no había navegador conectado y el lector web no devolvió contenido legible. La misión autorizó usar el paquete real descargado y registrar esta limitación. No se presenta una visita web como realizada ni se trata como requisito técnico bloqueante bajo esa instrucción.

Las relaciones se refieren a la descarga v5.0 29-AUG-26. Una versión posterior del portal puede diferir; no sustituir valores sin documentar la actualización.
