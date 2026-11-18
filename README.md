# Healthcare Data Science & AI Engineering Portfolio

## Navegación y reproducibilidad

| Unidad | Contenido y entrada |
|---|---|
| [Lab 02](lab02/README.md) | Synthea y analítica; notebook en `notebooks/` y datos locales en `output/` |
| [Lab 03](lab03/README.md) | EDA; notebook en `notebooks/` y entregables en `figuras/` |
| [Lab 04](lab04/README.md) | Funciones en `src/` y pruebas en `tests/` |
| [Lab 05](lab05/README.md) | Paquete académico independiente `clinlab/` |
| [Lab 06](lab06/README.md) | Paquete `clinlab/`, contenedor y CI |
| [Lab 07](lab07/README.md) | Servicios y evidencias en `stack/` |
| [Lab 10](lab10/README.md) | SQL, notebooks y constructor en `src/`; se mantiene la entrada histórica |
| [Lab 11](lab11/README.md) | SQL longitudinal sobre la base de Lab 10, en solo lectura |
| [Proyecto final](final_project/README.md) | Estudio original; notebooks 02.3 y 02.4 preservados |
| [Nueva OMOP](omop_cdm/README.md) | Esquema 5.4.2, ETL independiente y auditoría científica |

La [auditoría y arquitectura](docs/reorganization.md) registra dependencias,
movimientos, árboles anterior/nuevo y problemas preexistentes. La nueva OMOP está
separada de los análisis históricos: su carga persistente completa está pendiente
por falta de espacio y su cumplimiento integral **no está certificado**.

Technical portfolio focused on **clinical analytics, healthcare data engineering, machine learning, clinical informatics, and applied AI**.

## Scope

The labs in this repository cover:

* EHR data processing and longitudinal analysis
* Memory-efficient analytics with pandas, Polars, and PySpark
* SQL and OMOP CDM
* LOINC, SNOMED CT, ICD-10, and RxNorm
* Machine learning with scikit-learn, XGBoost, and LightGBM
* Model evaluation, calibration, and SHAP
* FastAPI, Docker, testing, and deployment
* AWS S3, EC2, IAM, and cloud workflows
* LLMs, biomedical NER, NL2SQL, embeddings, and RAG

The objective is to build reproducible workflows that connect biomedical analysis with practical data engineering and production-oriented decisions.

## Labs

This repository will contain multiple progressively more advanced labs.

### [Lab 02 — Large-Scale Synthetic EHR Analytics](./lab02/)

Analysis of synthetic longitudinal EHR data generated with **Synthea**.

**Dataset**

* 22,851 patients
* 1.35M encounters
* 17.34M clinical observations
* ~16 GB of generated CSV data

**Work performed**

* explicit dtype selection
* memory profiling and optimization
* missing-data and duplicate auditing
* temporal consistency checks
* validated `many_to_one` joins
* longitudinal blood-pressure analysis
* long-to-wide transformations
* processing by chunks under a memory budget
* pandas vs Polars vs PySpark benchmarking

### Main result

`observations.csv` memory usage was reduced from:

**9,960.77 MB → 704.18 MB**

Equivalent to a **92.93% reduction**.

### Engine benchmark

| Engine  | Full pipeline |
| ------- | ------------: |
| pandas  |       18.69 s |
| Polars  |    **4.77 s** |
| PySpark |        7.74 s |

All three reproduced the same results: **59.22 mean encounters per patient, median 36, and 22,793 patients with ≥3 systolic blood-pressure measurements**.

For a controlled 1M-row test, pandas used **189.27 MB**, while Polars used **49.08 MB**.

## Technical Areas

`Python` · `pandas` · `Polars` · `PySpark` · `PyArrow` · `SQL` · `OMOP CDM` · `scikit-learn` · `XGBoost` · `LightGBM` · `SHAP` · `FastAPI` · `Docker` · `AWS` · `LLMs` · `RAG`

## Principles

Projects emphasize:

* reproducibility
* explicit data-quality checks
* measured runtime and memory
* validated joins and transformations
* clinical interpretation
* documented technical trade-offs

Large datasets are not stored directly in GitHub; each lab documents how to obtain or regenerate them.

## Contact

GitHub: [@luisebh1919](https://github.com/luisebh1919)

---

*Additional labs will be added as the portfolio develops.*
