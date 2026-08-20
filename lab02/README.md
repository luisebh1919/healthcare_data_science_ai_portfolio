# Lab 02 · Large-Scale Clinical Data Processing

**Memory-efficient EHR processing, clinical data-quality validation, and performance benchmarking across pandas, Polars, and PySpark.**

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
| Chunk-processing memory budget | **200 MB** |

This project explores how data representation, validation strategy, and processing engine affect the analysis of large synthetic electronic health records.

---

## Objectives

The lab evaluates:

- explicit dtype selection and memory usage
- ≥70% memory reduction on `observations.csv`
- clinical data-quality auditing
- temporal consistency
- validated table cardinalities
- patient-level clinical analysis
- long-to-wide transformations
- physiological plausibility checks
- full-file processing under a fixed memory budget
- equivalent implementations in pandas, Polars, and PySpark

The complete implementation and methodological discussion are available in:

### [`analisis_pacientes.ipynb`](./analisis_pacientes.ipynb)

---

## Dataset

Data were generated with **Synthea**, a synthetic longitudinal EHR generator.

The dataset was created locally using:

```bash
java -jar synthea-with-dependencies.jar \
  -p 20000 \
  --exporter.csv.export=true \
  --exporter.fhir.export=false \
  --exporter.baseDirectory=output
```

Main files used:

| File | Description | Rows |
|---|---|---:|
| `patients.csv` | Patient demographics | 22,851 |
| `encounters.csv` | Clinical encounters | 1,353,311 |
| `observations.csv` | Laboratory and clinical measurements | 17,340,070 |

The complete generated CSV output occupies approximately **16 GB**.

Large generated files are excluded from GitHub and can be recreated using the command above.

---

## Memory Optimization

The datasets were first loaded using pandas with inferred data types and then reloaded using explicit representations.

| Dataset | Initial Memory | Optimized Memory | Reduction |
|---|---:|---:|---:|
| Patients | 26.80 MB | 15.20 MB | 43.27% |
| Encounters | 1,046.21 MB | 601.45 MB | 42.51% |
| Observations | 9,960.77 MB | **704.18 MB** | **92.93%** |

For `observations.csv`, the main optimizations were:

- repeated string values → `category`
- temporal fields → `datetime`
- mixed textual values → `string[pyarrow]`

### Column-Level Memory Decisions

| Column | Before | After | MB Before | MB After | Trade-off |
|---|---|---|---:|---:|---|
| CATEGORY | object | category | 942.69 | 16.54 | Less flexible when adding new categories |
| CODE | object | category | 916.87 | 33.10 | Text manipulation becomes less direct |
| DATE | object | datetime64 | 1,141.04 | 132.29 | Requires valid temporal interpretation |
| DESCRIPTION | object | category | 1,518.73 | 33.11 | Less flexible for arbitrary string edits |
| ENCOUNTER | object | category | 1,374.08 | 141.50 | New identifiers require category expansion |
| PATIENT | object | category | 1,405.63 | 35.43 | New identifiers require category expansion |
| TYPE | object | category | 907.08 | 16.54 | Less flexible for unseen values |
| UNITS | object | category | 797.52 | 16.54 | New units require category expansion |
| VALUE | object | string[pyarrow] | 957.14 | 279.13 | Some string operations may require conversion |

**Final reduction: 92.93%**, exceeding the required 70%.

---

## Data Quality Audit

The three datasets were audited before clinical analysis.

| Check | Result |
|---|---:|
| Duplicate patient IDs | **0** |
| Missing `ENCOUNTER` in observations | **3.60%** |
| Missing `UNITS` | **27.27%** |
| Non-numeric `VALUE` | **36.80%** |
| Encounters before birth | **0** |
| Encounters after recorded death date | **2,734** |

The non-numeric values were not automatically considered errors. Examples included valid clinical responses such as:

- `No`
- `Unsure`
- `Never smoked tobacco`

This is important because blindly coercing the entire `VALUE` column to numeric would destroy valid categorical clinical information.

### Temporal Consistency

A timestamp-level comparison initially detected **3,161 encounters after death**.

Because `DEATHDATE` contains day-level information, same-day encounters could be incorrectly classified as post-death events.

After comparing calendar dates instead of timestamps:

**2,734 encounters remained on dates after the recorded death date.**

This removed **427 false positives** caused by temporal granularity.

---

## Join Validation

The analytical relationship was:

```text
observations → encounters → patients
```

Both joins were expected to be `many_to_one`.

Each merge used:

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

### Observations / Encounters → Patients

| Metric | Rows |
|---|---:|
| Before merge | 17,340,070 |
| After merge | 17,340,070 |
| Matched to patient | 17,340,070 |
| Without patient match | 0 |

The stable row counts confirmed that the joins did not introduce unintended row multiplication.

---

## Clinical Analysis

### Patients by Ethnicity and Sex

| Ethnicity | Sex | Patients |
|---|---|---:|
| nonhispanic | M | 10,225 |
| nonhispanic | F | 10,192 |
| hispanic | F | 1,254 |
| hispanic | M | 1,180 |

The original Synthea categories were preserved rather than creating artificial demographic groups.

### Encounters per Patient

| Metric | Result |
|---|---:|
| Mean | **59.22** |
| Median | **36** |

### Most Frequent Observations

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

### Longitudinal Example · Systolic Blood Pressure

LOINC `8480-6`

| Metric | Result |
|---|---:|
| Measurements | **327,659** |
| Mean | **117.08 mmHg** |
| Median | **118 mmHg** |
| Minimum | **36 mmHg** |
| Maximum | **186 mmHg** |
| Patients with ≥3 measurements | **22,793** |

The analysis operates directly on the individual observations rather than averaging patient-level averages, avoiding a mean-of-means error.

---

## Long-to-Wide Transformation

Six frequently measured variables were transformed into patient-date wide format:

- systolic blood pressure
- diastolic blood pressure
- heart rate
- respiratory rate
- BMI
- body weight

The resulting table contained:

**334,269 patient-date rows**

Before aggregation:

| Check | Result |
|---|---:|
| Patient/date/analyte combinations with multiple measurements | **2,349** |
| Maximum measurements in one combination | **3** |

This audit was performed because `pivot_table()` can silently aggregate multiple observations for the same patient, date, and analyte.

Physiologically implausible values were flagged for review rather than automatically removed. The notebook contains the complete detection logic and the references used to justify the selected limits.

---

## Processing Under a Memory Budget

The complete `observations.csv` file was processed incrementally under an artificial memory constraint.

```python
chunksize = 100_000
```

| Metric | Result |
|---|---:|
| Memory budget | **200 MB** |
| Measured peak with `tracemalloc` | **12.79 MB** |
| Budget satisfied | **Yes** |

Each chunk generated partial counts and sums by clinical observation code.

Global means were calculated as:

```text
total sum / total count
```

rather than averaging chunk-level means.

---

## pandas vs Polars vs PySpark

The clinical pipeline from Activity 5 was reproduced in all three engines and checked for equivalent analytical results.

All implementations reproduced:

- mean encounters per patient: **59.22**
- median encounters per patient: **36**
- patients with ≥3 systolic measurements: **22,793**
- equivalent demographic and observation-frequency results

### Required Engine Comparison

| Tool | Lines of Code | Time (s) | Peak Memory (MB) | Hardest Part |
|---|---:|---:|---:|---|
| pandas | **TBD** | 18.69 | **TBD** | Higher memory consumption |
| Polars | **TBD** | 4.77 | **TBD** | Adapting grouping and expression syntax |
| PySpark | **TBD** | 7.74 | **TBD** | Spark/JVM initialization and distributed API |

> `TBD` values should be replaced with the final measured LOC and peak-memory values from the notebook before submission. The course specification requires measured values rather than estimates.

### Controlled 1M-Row Memory Experiment

A secondary experiment was also performed on the same 1M-row subset:

| Engine | Time | DataFrame Memory |
|---|---:|---:|
| pandas | 0.76 s | 189.27 MB |
| Polars | **0.05 s** | **49.08 MB** |
| PySpark | 5.15 s | JVM-managed |

This secondary table is useful for portfolio comparison, but it does **not replace the required peak-memory measurements above**.

---

## Recommendation

For this dataset — approximately **17.3 million observations** and a workload dominated by filtering, grouping, aggregation, and clinical transformations on a single machine — **Polars provided the best balance of speed and memory efficiency**.

pandas remains highly practical for smaller and medium-scale analyses because of its mature ecosystem and straightforward API.

PySpark introduces additional overhead in local execution and becomes more compelling when the workload grows beyond the memory or computational capacity of a single machine and can benefit from distributed execution.

---

## Reproducibility

Repository structure:

```text
lab02/
├── analisis_pacientes.ipynb
├── README.md
└── .gitignore
```

Large Synthea outputs and local environments are excluded from version control.

To reproduce the analysis:

1. Install the required Python packages:
   `pandas`, `numpy`, `pyarrow`, `polars`, and `pyspark`.
2. Generate the Synthea CSV files using the command shown above.
3. Place the generated files under `output/csv/`.
4. Open `analisis_pacientes.ipynb`.
5. Run the notebook from a clean kernel using **Restart & Run All**.

The implementation avoids `iterrows()` and `inplace=True`.

---

## Academic Context

Developed for the graduate course:

**Applied Data Science in Biomedicine and the Pharmaceutical/Healthcare Industry: From Academia to Industry**

Universidad Nacional Autónoma de México (UNAM)  
Biomedical Sciences PhD Program · Semester 2027-1

---

## Portfolio Context

This project is part of the **Healthcare Data Science & AI Engineering Portfolio**, a growing collection of hands-on projects in clinical analytics, data engineering, SQL, OMOP CDM, machine learning, cloud computing, APIs, deployment, and applied AI.

[← Back to Healthcare Data Science & AI Engineering Portfolio](../README.md)
