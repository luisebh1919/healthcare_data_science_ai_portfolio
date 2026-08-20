# Lab 02 — Large-Scale Clinical Data Processing

Large-scale analysis of synthetic electronic health record data with emphasis on **memory optimization, data quality, reproducibility, clinical analytics, and computational performance**.

## Academic Context

Developed for the graduate course **Applied Data Science in Biomedicine and the Pharmaceutical/Healthcare Industry: From Academia to Industry**, Universidad Nacional Autónoma de México (UNAM), Biomedical Sciences PhD Program, semester 2027-1.

## Objective

Process and analyze a large synthetic EHR dataset while explicitly addressing:

- data types and memory usage
- clinical data quality
- temporal consistency
- join cardinality validation
- longitudinal clinical measurements
- wide-format transformation
- processing under a fixed memory budget
- comparison of pandas, Polars, and PySpark

## Dataset

Data were generated with **Synthea** using a target population of 20,000 synthetic patients and CSV export.

```bash
java -jar synthea-with-dependencies.jar \
  -p 20000 \
  --exporter.csv.export=true \
  --exporter.fhir.export=false \
  --exporter.baseDirectory=output
