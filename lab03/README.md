# Lab 03 — Exploratory Data Analysis of a Type 2 Diabetes Cohort

## Objective

This laboratory performs a complete exploratory data analysis (EDA) of an adult cohort with type 2 diabetes mellitus (T2D) generated with Synthea.

The analysis follows a clinically oriented EDA workflow focused on:

- defining a reproducible cohort;
- evaluating data structure and missingness;
- exploring distributions and temporal patterns;
- identifying potential data-quality problems;
- describing major comorbidities;
- producing publication-quality figures;
- comparing visualization libraries;
- generating a baseline characteristics table.

The final goal is not only to summarize the dataset, but to identify patterns that could affect downstream statistical or predictive modeling.

---

## Cohort definition

The initial Synthea population contained **22,851 patients**.

Patients were included if they had an explicit diagnosis of type 2 diabetes mellitus:

- SNOMED CT: `44054006`
- Description: `Diabetes mellitus type 2 (disorder)`

This identified **1,671 patients**.

Because the analysis focuses on an adult T2D population, patients younger than 18 years at the first recorded diagnosis were excluded.

- Initial T2D cohort: **1,671**
- Patients <18 years excluded: **3**
- Final adult T2D cohort: **1,668**

The notebook includes a cohort-selection flow diagram documenting this process.

---

## EDA workflow

The exploratory analysis follows the sequence:

1. Dataset dimensions and data types
2. Duplicate records
3. Missing values and missingness patterns
4. Distribution of age at diagnosis by sex
5. Temporal distribution of HbA1c measurements
6. Evolution of HbA1c around T2D diagnosis
7. Most frequent clinical comorbidities
8. Graphically detectable data-quality problems
9. Publication-quality 2×2 summary figure
10. Comparison of Matplotlib, Seaborn and Plotly
11. Baseline characteristics table

---

## Missing data

Missingness was concentrated primarily in demographic and administrative variables.

Examples include:

- `SUFFIX`: name suffix such as Jr., Sr. or III
- `MAIDEN`: maiden name
- `MIDDLE`: middle name
- `FIPS`: geographic administrative code
- `DEATHDATE`: only available when a death date is recorded
- `MARITAL`: marital status

After ordering patients by their total number of missing values, no clearly separated subgroup with globally incomplete clinical information was observed.

Most missingness therefore appears to be related to the meaning or applicability of individual variables rather than generalized loss of patient information.

---

## Age at T2D diagnosis

The final cohort contained:

- **809 women**
- **859 men**

Age at diagnosis was broadly similar between sexes.

Women had a median age of approximately **48 years**, while men had a median age of approximately **46 years**.

The majority of diagnoses were concentrated approximately between **35 and 60 years of age**.

Both count-based and density-based histograms were used because they answer different questions:

- count shows the absolute number of patients in each age interval;
- density shows the relative shape of each sex-specific distribution independently of group size.

---

## HbA1c analysis

HbA1c was identified using:

- LOINC: `4548-4`
- `Hemoglobin A1c/Hemoglobin.total in Blood`

A total of **66,382 HbA1c measurements** were identified.

All **1,668 patients** had at least one measurement, corresponding to **100% cohort coverage**.

All measurements were reported in `%`.

### Temporal coverage

HbA1c observations extended from approximately:

- **3,346 days before diagnosis**
- to **27,153 days after diagnosis**

This extremely broad simulated follow-up makes a single global temporal visualization difficult to interpret.

The detailed analysis therefore focused on a window of approximately **±5 years around diagnosis**.

---

## HbA1c around diagnosis

Before the T2D diagnosis, HbA1c measurements were concentrated around approximately **6%** with relatively low dispersion.

Near the diagnostic date, the median HbA1c increased to approximately **7%**.

After diagnosis, HbA1c values showed substantially greater variability.

To summarize this pattern without assuming normality, measurements were grouped into six-month intervals and described using:

- median;
- first quartile;
- third quartile;
- interquartile range.

The temporal profile shows a clear change in the distribution of HbA1c around the diagnostic event.

---

## Comorbidities

An initial inspection of `conditions.csv` showed that the file contains more than clinical diseases.

Frequent categories included social, occupational and administrative concepts in addition to disorders.

For this reason, the final comorbidity analysis was restricted to descriptions explicitly identified as:

```text
(disorder)
