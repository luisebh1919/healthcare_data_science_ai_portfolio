# Lab 02 · Large-Scale Clinical Data Processing

**Memory-efficient processing, data-quality validation, and performance benchmarking on 17.3M synthetic EHR observations.**

`Python` · `pandas` · `Polars` · `PySpark` · `PyArrow` · `Synthea`

---

## Highlights

| Metric | Result |
|---|---:|
| Patients | **22,851** |
| Encounters | **1.35M** |
| Clinical observations | **17.34M** |
| Generated CSV data | **~16 GB** |
| Initial `observations.csv` memory | **9.96 GB** |
| Optimized memory | **704.18 MB** |
| Memory reduction | **92.93%** |

---

## What This Lab Demonstrates

- Explicit dtype design and memory profiling
- Clinical data-quality auditing
- Temporal consistency validation
- Safe `many_to_one` joins
- Longitudinal EHR analysis
- Long-to-wide clinical transformations
- Processing under a fixed memory budget
- pandas vs Polars vs PySpark benchmarking

---

## Dataset

Synthetic electronic health record data were generated with **Synthea** using a target population of 20,000 patients and CSV export.

```bash
java -jar synthea-with-dependencies.jar \
  -p 20000 \
  --exporter.csv.export=true \
  --exporter.fhir.export=false \
  --exporter.baseDirectory=output
```

Main datasets:

| File | Rows |
|---|---:|
| `patients.csv` | 22,851 |
| `encounters.csv` | 1,353,311 |
| `observations.csv` | 17,340,070 |

Large generated files are excluded from the repository and can be reproduced using the command above.

---

## Memory Optimization

The initial pandas representation of `observations.csv` required approximately **9.96 GB of memory**.

By selecting more appropriate data representations:

- repeated values → `category`
- temporal fields → `datetime`
- mixed textual values → `string[pyarrow]`

memory usage was reduced to **704.18 MB**.

| Dataset | Initial Memory | Optimized Memory | Reduction |
|---|---:|---:|---:|
| Patients | 26.80 MB | 15.20 MB | 43.27% |
| Encounters | 1,046.21 MB | 601.45 MB | 42.51% |
| Observations | 9,960.77 MB | **704.18 MB** | **92.93%** |

### Main Result

**9.96 GB → 704.18 MB**

**92.93% reduction in memory usage**

---

## Data Quality Audit

The datasets were evaluated for missing values, duplicate identifiers, mixed clinical values, and temporal inconsistencies.

| Quality Check | Result |
|---|---:|
| Duplicate patient IDs | **0** |
| Observations without encounter reference | **3.60%** |
| Missing units | **27.27%** |
| Non-numeric `VALUE` | **36.80%** |
| Encounters before birth | **0** |
| Encounters after recorded death date | **2,734** |

Non-numeric values were not automatically treated as errors.

Examples included valid clinical responses such as:

- `No`
- `Unsure`
- `Never smoked tobacco`

This illustrates why clinical data quality requires semantic interpretation rather than automatic numerical coercion.

### Temporal Consistency

An initial timestamp comparison identified **3,161 encounters after death**.

However, `DEATHDATE` contains day-level information and was interpreted as midnight. Encounters later on the same calendar day could therefore be incorrectly flagged.

After comparing calendar dates instead of full timestamps:

**2,734 encounters remained genuinely later than the recorded death date.**

This prevented **427 same-day encounters** from being incorrectly classified as inconsistencies.

---

## Join Validation

The main analytical relationship was:

```text
observations → encounters → patients
```

Both joins were expected to follow a `many_to_one` relationship and were explicitly validated using:

```python
validate="many_to_one"
indicator=True
```

### Observations → Encounters

| Metric | Rows |
|---|---:|
| Before merge | 17,340,070 |
| After merge | 17,340,070 |
| Matched | 16,715,962 |
| Without encounter match | 624,108 |

Approximately **3.60%** of observations did not contain a valid encounter reference.

### Observations / Encounters → Patients

| Metric | Rows |
|---|---:|
| Before merge | 17,340,070 |
| After merge | 17,340,070 |
| Matched to patient | 17,340,070 |
| Without patient match | 0 |

The stable row count confirmed that the joins did not introduce unintended row multiplication.

---

## Clinical Analysis

### Encounters per Patient

| Metric | Result |
|---|---:|
| Mean | **59.22** |
| Median | **36** |

The difference between the mean and median indicates that some patients have substantially more encounters than the typical patient.

### Most Frequent Clinical Observations

| LOINC Code | Observation | Frequency |
|---|---|---:|
| 72514-3 | Pain severity | 563,044 |
| 8480-6 | Systolic Blood Pressure | 327,659 |
| 8462-4 | Diastolic Blood Pressure | 327,659 |
| 29463-7 | Body Weight | 313,604 |
| 9279-1 | Respiratory rate | 305,989 |
| 8867-4 | Heart rate | 305,989 |
| 8302-2 | Body Height | 299,890 |
| 72166-2 | Tobacco smoking status | 298,812 |
| 39156-5 | BMI | 277,810 |
| 33914-3 | Glomerular filtration rate | 233,209 |

---

## Clinical Example · Systolic Blood Pressure

Systolic blood pressure (`LOINC 8480-6`) was selected for longitudinal analysis.

| Metric | Result |
|---|---:|
| Measurements | **327,659** |
| Mean | **117.08 mmHg** |
| Median | **118 mmHg** |
| Minimum | **36 mmHg** |
| Maximum | **186 mmHg** |
| Patients with ≥3 measurements | **22,793** |

The high number of repeated measurements provides a dense longitudinal signal for patient-level analysis.

---

## Long-to-Wide Transformation

Six frequently measured clinical variables were transformed into patient-date wide format:

- systolic blood pressure
- diastolic blood pressure
- heart rate
- respiratory rate
- BMI
- body weight

The resulting table contained:

**334,269 patient-date rows**

Before aggregation, repeated measurements were explicitly audited.

| Metric | Result |
|---|---:|
| Patient/date/analyte combinations with multiple measurements | **2,349** |
| Maximum measurements in one combination | **3** |

This check is important because `pivot_table()` can silently aggregate repeated measurements.

For this workflow, the aggregation function was explicitly defined as the mean.

---

## Processing Under a Memory Constraint

The complete `observations.csv` dataset was also processed without loading the entire file into memory.

```python
chunksize = 100_000
```

| Metric | Result |
|---|---:|
| Artificial memory budget | **200 MB** |
| Measured peak with `tracemalloc` | **12.79 MB** |
| Budget satisfied | **Yes** |

Each chunk generated partial counts and sums by clinical code.

The final means were calculated using:

```text
total sum / total count
```

instead of averaging chunk-level means, avoiding a **mean-of-means error**.

---

## pandas vs Polars vs PySpark

The same analytical workflow was reproduced using three processing engines.

### Full Pipeline

| Engine | Runtime | Clinical Result | Main Consideration |
|---|---:|---|---|
| pandas | 18.69 s | Equivalent | Higher memory usage |
| **Polars** | **4.77 s** | Equivalent | Different API |
| PySpark | 7.74 s | Equivalent | Spark/JVM initialization overhead |

All three engines reproduced:

- mean encounters per patient: **59.22**
- median encounters per patient: **36**
- patients with ≥3 systolic measurements: **22,793**

### Controlled 1M-Row Memory Comparison

| Engine | Time | Memory |
|---|---:|---:|
| pandas | 0.76 s | 189.27 MB |
| **Polars** | **0.05 s** | **49.08 MB** |
| PySpark | 5.15 s | JVM-managed |

For this workload on a single machine, **Polars provided the best balance between execution speed and memory efficiency**.

PySpark becomes more attractive when the workload requires distributed computation across multiple machines.

---

## Key Takeaways

- Explicit dtype selection can dramatically reduce memory usage.
- Clinical data quality requires semantic interpretation.
- Join cardinalities should be validated explicitly.
- Mixed clinical values should not be blindly converted to numeric data.
- Wide transformations can hide repeated measurements through aggregation.
- Chunk-based processing allows large datasets to remain within strict memory constraints.
- Runtime and memory should be measured rather than assumed.
- Tool selection should depend on dataset scale and execution environment.

---

## Notebook

The complete implementation, outputs, validation steps, and methodological discussion are available in:

### [`analisis_pacientes.ipynb`](./analisis_pacientes.ipynb)

---

## Academic Context

Developed for the graduate course:

**Applied Data Science in Biomedicine and the Pharmaceutical/Healthcare Industry: From Academia to Industry**

**Universidad Nacional Autónoma de México (UNAM)**  
Biomedical Sciences PhD Program · Semester 2027-1

---

## Portfolio Context

This lab is part of the **Healthcare Data Science & AI Engineering Portfolio**, a growing collection of projects covering clinical analytics, data engineering, SQL, OMOP CDM, machine learning, cloud computing, APIs, Docker, LLM applications, and healthcare AI workflows.

[← Back to Healthcare Data Science & AI Engineering Portfolio](../README.md)
