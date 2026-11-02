# Healthcare Data Science & AI Engineering Portfolio

Portafolio técnico orientado a **analítica clínica, ingeniería de datos en salud, aprendizaje automático, informática clínica e inteligencia artificial aplicada**.

## Contexto académico y progresión

Este repositorio sigue progresivamente los laboratorios de [insomnium098/curso-ciencia-datos-2027-1](https://github.com/insomnium098/curso-ciencia-datos-2027-1). Cada carpeta reúne implementaciones, análisis y documentación propios vinculados con las actividades del curso. Se conserva la numeración de los laboratorios; la tabla siguiente enumera las carpetas disponibles, sin implicar que todos los laboratorios del curso estén presentes o completados.

Se incorporarán nuevos laboratorios conforme avance el desarrollo del portafolio.

## Navegación por laboratorios

| Laboratorio | Tema | Descripción breve | Carpeta |
| --- | --- | --- | --- |
| 02 | Procesamiento de datos clínicos a gran escala | Datos sintéticos Synthea, optimización de memoria, controles de calidad y comparación de pandas, Polars y PySpark. | [lab02](./lab02/) |
| 03 | Análisis exploratorio de datos clínicos | Cohorte adulta con diabetes tipo 2, datos faltantes, evolución de HbA1c, comorbilidades y visualización. | [lab03](./lab03/) |
| 04 | Validación de datos y pruebas | Validación de columnas requeridas en DataFrames clínicos y pruebas con pytest. | [lab04](./lab04/) |
| 05 | Empaquetado y calidad de software | Paquete `clinlab` con funciones reutilizables de calidad de datos, pruebas y herramientas de desarrollo. | [lab05](./lab05/) |
| 06 | Contenedores e integración continua | Imagen Docker de `clinlab`, pruebas en contenedor y flujo de GitHub Actions para publicación en GHCR. | [lab06](./lab06/) |
| 07 | Orquestación con Docker Compose | Entorno con PostgreSQL, Jupyter y Adminer opcional, inicialización SQL y bitácora de actividades. | [lab07](./lab07/) |
| 10 | Fundamentos de SQL | Carga de datos clínicos en DuckDB, modelo relacional, auditorías, consultas y comparación con pandas. | [lab10](./lab10/) |
| 11 | SQL avanzado y análisis longitudinal | CTEs, funciones de ventana, intervalos entre visitas, readmisiones y episodios de exposición a medicamentos. | [lab11](./lab11/) |

La tabla describe el contenido revisado en las carpetas. Esta revisión documental no verifica la ejecución integral de los laboratorios ni les asigna un estado de finalización.

## Proyecto independiente en desarrollo

[final_project](./final_project/) es un proyecto independiente en desarrollo sobre predicción de readmisión hospitalaria a 30 días en adultos con cáncer. Su alcance comprende la definición de una cohorte, una ventana de historia clínica de 180 días, seis predictores y la comparación prevista de modelos de regresión logística y XGBoost.

Utiliza datos sintéticos Synthea y una capa OMOP mínima; no constituye un OMOP CDM completo. Su alcance, protocolo y avances se documentan dentro de la carpeta del proyecto.

## Lab 02 — Resultados y benchmarks conservados

Análisis de datos clínicos longitudinales sintéticos generados con **Synthea**. Se conservan los resultados y benchmarks previamente documentados en este README; las mediciones no se repitieron durante esta revisión.

### Datos

* 22,851 pacientes
* 1.35M encuentros
* 17.34M observaciones clínicas
* ~16 GB de datos CSV generados

### Trabajo documentado

* selección explícita de tipos de datos
* medición y optimización de memoria
* auditoría de datos faltantes y duplicados
* comprobaciones de consistencia temporal
* uniones validadas como `many_to_one`
* análisis longitudinal de presión arterial
* transformaciones de formato largo a ancho
* procesamiento por bloques bajo un presupuesto de memoria
* comparación de pandas, Polars y PySpark

### Resultado principal

El uso de memoria de `observations.csv` se redujo de:

**9,960.77 MB → 704.18 MB**

Equivalente a una **reducción del 92.93%**.

### Benchmark de motores

| Motor   | Flujo completo |
| ------- | ------------: |
| pandas  |       18.69 s |
| Polars  |    **4.77 s** |
| PySpark |        7.74 s |

Los tres motores reprodujeron los mismos resultados: **59.22 encuentros por paciente en promedio, mediana de 36 y 22,793 pacientes con ≥3 mediciones de presión arterial sistólica**.

En una prueba controlada de 1M de filas, pandas utilizó **189.27 MB**, mientras que Polars utilizó **49.08 MB**.

## Áreas de interés técnico

El alcance formativo del portafolio incluye procesamiento de registros clínicos y análisis longitudinal; terminologías como LOINC, SNOMED CT, ICD-10 y RxNorm; aprendizaje automático, evaluación, calibración y SHAP; APIs, contenedores y despliegue; AWS S3, EC2, IAM y flujos de trabajo en la nube; y aplicaciones de modelos de lenguaje, NER biomédico, NL2SQL, embeddings y RAG. Estas áreas de interés no equivalen a entregables completados en las carpetas actuales.

`Python` · `pandas` · `Polars` · `PySpark` · `PyArrow` · `SQL` · `OMOP CDM` · `scikit-learn` · `XGBoost` · `LightGBM` · `SHAP` · `FastAPI` · `Docker` · `AWS` · `LLMs` · `RAG`

## Principios

El objetivo es construir flujos reproducibles que conecten el análisis biomédico con decisiones prácticas de ingeniería de datos orientadas a producción. Los proyectos priorizan:

* reproducibilidad
* controles explícitos de calidad de datos
* medición de tiempo de ejecución y memoria
* validación de uniones y transformaciones
* interpretación clínica
* documentación de decisiones técnicas y sus limitaciones

Los conjuntos de datos voluminosos no se almacenan directamente en GitHub; las instrucciones para obtenerlos o regenerarlos se consultan en cada laboratorio.

## Contacto

GitHub: [@luisebh1919](https://github.com/luisebh1919)
