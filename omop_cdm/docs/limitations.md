# Limitaciones y tareas pendientes

1. **Almacenamiento:** ejecutar la carga persistente completa únicamente con una
   salida nueva y espacio suficiente según preflight. No se ha medido el tamaño
   final, rendimiento ni comportamiento a escala de esa carga. La prueba en
   memoria valida la fuente completa de condiciones; las otras cinco fuentes
   tienen auditoría de códigos completa, pero solo pruebas pequeñas de ETL.
2. **Vocabularios:** las descargas originales no contienen Gender, Race,
   Ethnicity ni CVX. Todos los conceptos demográficos no disponibles quedan en
   cero. La cobertura CVX es cero para 329 742 inmunizaciones. Solicitar paquetes
   Athena compatibles con el mismo snapshot y licencias; no sustituirlos por
   conceptos inventados ni mezclar versiones silenciosamente.
3. **Sistema de observaciones:** el CSV no tiene SYSTEM. El flujo declara LOINC
   como sistema de referencia del exportador. Algunos códigos parecen proceder
   de otro sistema y otros son internos de Synthea (QALY, DALY, QOLS, X9999, etc.).
   No se recodifican por su apariencia. Se requiere revisar el código/módulos de
   la revisión exacta del generador para documentar sistemas alternativos. La
   cobertura publicada es condicional a ese sistema declarado, no absoluta.
4. **Dominios aún no implementados:** 1055 observaciones tienen un destino Note
   según los vocabularios disponibles. La ETL los registra en cuarentena con
   motivo explícito. Antes de completar la migración hay que validar la
   representación de su texto, clase, idioma y codificación. Otros dominios
   inesperados también se ponen en cuarentena y no se reclasifican clínicamente.
5. **Otras fuentes:** allergies (incluidas reacciones/severidad), careplans,
   supplies, imaging_studies, claims, claims_transactions, payer_transitions y
   payers permanecen originales. No tienen una transformación validada en esta
   entrega. No inferir procedimientos realizados de planes, causas de muerte de
   diagnósticos, ni cantidades de tratamiento a partir de costos. Ampliar el
   manifiesto de conciliación por fuente al implementar esos flujos.
6. **Tablas derivadas:** condition_era, drug_era, dose_era y episode existen pero
   quedan vacías hasta validar las reglas OHDSI de derivación y sus requisitos de
   información. Igual ocurre con NOTE, NOTE_NLP, SPECIMEN y COST; no se confunde
   existencia física con disponibilidad o completitud de datos.
7. **Visitas:** se conservan encuentros uno a uno. No se implementó la fusión de
   encuentros hospitalarios solapados ni la construcción jerárquica de
   VISIT_DETAIL. Revisarlo con ETL-Synthea/THEMIS antes de certificar semántica de
   visitas. La comparación actual retiene las hospitalizaciones fuente originales.
8. **Observabilidad:** un período por persona se deriva del mínimo inicio/máximo
   fin de encuentro, como en el estudio original. No prueba captura continua ni
   afiliación. Se informan eventos fuera del período; no se corrigen fechas para
   hacerlos desaparecer. Evaluar afiliación y lagunas en un análisis separado.
9. **Predictores:** contar solo conceptos del dominio Condition redefine el
   predictor de diagnósticos del estudio original. La comparación preserva todos
   los códigos fuente mediante linaje y documenta ambas variantes. Las reglas
   regex de las tres variables derivadas se extraen de 02.4 únicamente para
   verificar equivalencia; son reglas históricas aproximadas, no mappings OMOP
   ni nuevas clasificaciones clínicas. No se cambian ni se proponen como estándar.
10. **Validación OHDSI:** instalar DQD/DatabaseConnector/SqlRender y dependencias
    en un entorno con espacio, ejecutar sobre una copia de la salida completa,
    inspeccionar sus errores y umbrales, y conservar la versión y reporte JSON.
    No hay resultado DQD en esta entrega. Tampoco se ha hecho comparación integral
    evento a evento con la salida oficial de ETL-Synthea para esta revisión Synthea.

La migración no queda certificada como completa. La falta de espacio y de
vocabularios se registra como bloqueo reproducible, sin alterar el estudio para
eludirlo. No se ejecutó ningún notebook ni se reestimó ningún resultado predictivo.
