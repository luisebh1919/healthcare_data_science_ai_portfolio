# Verificación individual del enunciado y su rúbrica

Se releyó el [README oficial de Lab 12](https://github.com/insomnium098/curso-ciencia-datos-2027-1/blob/main/labs/s12-omop-cdm-introduccion/README.md)
al cierre. No se modificó el enunciado. El alcance es la ruta manual docente.

| Actividad | Estado de entrega | Evidencia verificable |
| --- | --- | --- |
| 1 Elegir ruta | Completa | README: preferencia OHDSI investigada y alternativa manual justificada; DuckDB 1.5.6 / CDM 5.4 |
| 2 Convertir | Completa | pipeline.py y migraciones; comandos, incidentes, versiones, huellas y conteos por tabla |
| 3 Vocabularios | Completa | Cinco vocabularios, tres tablas principales y auxiliares cargadas; 2042800 conceptos / 846204 estándar, suplemento Gender explícito |
| 4 Modelo | Completa en alcance docente | ER final y comparación ejecutada de seis tablas con DDL 5.4.0; dos diferencias clasificadas |
| 5 Ceros | Completa | Tasas por tabla/dominio y global, denominadores, causas y antes/después; no se pretende mapeo total |
| 6 Población | Completa | Personas, sexo legible, años de nacimiento, mediana de días, top 20 y medias de visitas / tipo |
| 7 Estándar/origen | Completa | Gingivitis 18512 por ambos métodos dentro de observación; igualdad explicada y código verificado |
| 8 Observación | Completa con límite científico | 390926 condiciones vs 389254 dentro, diferencia 1672 / 0.427702%; huecos y aproximación explícitos |
| 9 ATHENA | Completa con paquete descargado según autorización | Tres conceptos, estándar/dominio/vocabulario, hijos/descendientes, Maps to y códigos de origen; consulta interactiva al portal no realizada |
| 10 Referencia | Completa | Eunomia Synthea27NjParquet_5.4, mismas consultas ejecutadas, huella SQL y ZIP, comparación tabulada y límites |

## Nueve criterios de evaluación

- [x] Conversión documentada y reproducible a partir de los insumos identificados.
- [x] Vocabularios cargados; conceptos totales y estándar reportados.
- [x] ER contrastado con especificación 5.4, sin afirmar conformidad completa.
- [x] Porcentaje de cero por dominio/tabla con diagnóstico y denominadores.
- [x] IDs de conceptos en resultados públicos acompañados de nombres; los nombres
  Gender de la referencia reducida se presentan con el diccionario canónico OHDSI,
  sin cambiar sus tablas ni conteos.
- [x] Conteos epidemiológicos con COUNT(DISTINCT person_id); COUNT(*) queda para filas.
- [x] Efecto de observation_period cuantificado y sin duplicación por joins.
- [x] Diferencia estándar/origen explicada; en estos datos la diferencia real es cero.
- [x] Hallazgos ATHENA documentados sobre la descarga real; no se simula visita web.

## Qué no se presenta como completado

No se realizó verificación interactiva del portal ni validación clínica externa.
No se regeneró Synthea con la semilla original (desconocida), no se ejecutó la ruta
R y no se instanciaron todas las tablas CDM. No se resolvieron mediante conjeturas
los conceptos sin Maps to ni el lugar de atención de hospice. Raza/etnia y algunos
campos de procedencia quedan en cero. Son límites explícitos del alcance docente,
no resultados inventados ni tareas pendientes ocultas. La revisión académica y
cualquier uso científico posterior corresponden al estudiante/docente.
