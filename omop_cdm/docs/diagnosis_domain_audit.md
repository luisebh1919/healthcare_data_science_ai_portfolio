# Diferencias del predictor de diagnósticos por dominio

Se consultaron bases existentes READ_ONLY y las dos descargas Athena originales. No se modifican predictores ni modelos. Fecha de evaluación de vigencia: 2026-11-15.

## Códigos excluidos del recuento Condition

| Código SNOMED fuente | Destino OMOP | Registros fuente | Registros en lookback de entrenamiento | Pacientes de entrenamiento |
|---|---|---:|---:|---:|
| 1003755004 | Observation | 2 | 0 | 0 |
| 105531004 | Observation | 2784 | 0 | 0 |
| 10939881000119105 | Observation | 3806 | 7 | 7 |
| 1187604002 | Observation | 1029 | 0 | 0 |
| 160701002 | Observation | 13 | 0 | 0 |
| 160903007 | Observation | 59985 | 152 | 130 |
| 160904001 | Observation | 37497 | 99 | 90 |
| 161744009 | Observation | 4306 | 1 | 1 |
| 162573006 | Observation | 217 | 192 | 192 |
| 183996000 | Observation | 579 | 1 | 1 |
| 224295006 | Observation | 2111 | 0 | 0 |
| 224299000 | Observation | 10866 | 0 | 0 |
| 248595008 | Observation | 663 | 0 | 0 |
| 266934004 | Observation | 2220 | 0 | 0 |
| 266948004 | Observation | 4434 | 2 | 2 |
| 287185009 | Observation | 1 | 0 | 0 |
| 314529007 | Observation | 163616 | 388 | 223 |
| 315268008 | Observation | 382 | 9 | 9 |
| 32911000 | Observation | 416 | 0 | 0 |
| 384709000 | Observation | 3276 | 8 | 8 |
| 424393004 | Observation | 12206 | 35 | 34 |
| 428915008 | Measurement | 5 | 0 | 0 |
| 473461003 | Observation | 5432 | 0 | 0 |
| 48333001 | Observation | 875 | 1 | 1 |
| 698303004 | Observation | 55 | 3 | 3 |
| 698306007 | Observation | 775 | 0 | 0 |
| 706893006 | Observation | 14994 | 37 | 36 |
| 713458007 | Observation | 2210 | 0 | 0 |
| 73438004 | Observation | 8440 | 32 | 32 |
| 73595000 | Observation | 64815 | 169 | 145 |
| 741062008 | Observation | 20839 | 65 | 59 |
| 840544004 | Observation | 1932 | 4 | 4 |
| 876882001 | Observation | 154 | 0 | 0 |

Las descripciones fuente, conceptos destino, identificadores oficiales y evidencia de mapping por código están en `diagnosis_domain_audit.json`. Los pacientes por código se solapan: sus recuentos no deben sumarse como pacientes únicos.

## Interpretación

La definición original cuenta códigos distintos de conditions.csv en los 180 días previos, incluidos registros sociales y hallazgos. El recuento restringido a CONDITION_OCCURRENCE incluye conceptos de Condition y los códigos sin mapping mantenidos con concepto cero. Los códigos con destino oficial Observation/Measurement se representan en esas tablas y dejan de contribuir al recuento de Condition. La ausencia de un código de esa tabla no implica pérdida del registro.

Los destinos excluidos se verifican contra conceptos estándar vigentes y relaciones oficiales Maps to o identidad de concepto estándar. No se encontró evidencia de un mapping erróneo que explique los 418 pacientes; no se certifica con esto toda la validez clínica del ETL. Cambiar el predictor original para contar solo Condition sería un cambio científico y no se aplica.

La definición por dominio corresponde a las tablas OMOP; un predictor basado en códigos fuente históricos también puede reproducirse mediante linaje, pero debe etiquetarse como tal y no llamarse un recuento de enfermedades estándar.

## Recuentos y equivalencia

```json
{
  "population_deltas": {
    "training": {
      "patients": 655,
      "changed_patients": 418,
      "original_code_counts_sum": 2449,
      "standard_code_counts_sum": 1472,
      "removed_patient_code_pairs": 977,
      "removed_source_records": 1205
    },
    "cohort": {
      "patients": 824,
      "changed_patients": 515,
      "original_code_counts_sum": 3075,
      "standard_code_counts_sum": 1900,
      "removed_patient_code_pairs": 1175,
      "removed_source_records": 1447
    }
  },
  "delta_histogram_training": [
    {
      "removed_distinct_codes": 0,
      "patients": 237
    },
    {
      "removed_distinct_codes": 1,
      "patients": 164
    },
    {
      "removed_distinct_codes": 2,
      "patients": 90
    },
    {
      "removed_distinct_codes": 3,
      "patients": 86
    },
    {
      "removed_distinct_codes": 4,
      "patients": 40
    },
    {
      "removed_distinct_codes": 5,
      "patients": 22
    },
    {
      "removed_distinct_codes": 6,
      "patients": 8
    },
    {
      "removed_distinct_codes": 7,
      "patients": 7
    },
    {
      "removed_distinct_codes": 8,
      "patients": 1
    }
  ],
  "original_counts": {
    "cohort": 824,
    "events": 85,
    "training": 655,
    "temporal_test": 165,
    "overlap_excluded": 4
  },
  "persisted_training_counts_match_sql": {
    "original": 0,
    "standard": 0
  },
  "base_value_mismatches_all": {
    "age": 0,
    "sex": 0,
    "prior_inpatient_hospitalizations_180d": 0,
    "distinct_diagnoses_180d": 0,
    "distinct_medications_180d": 0,
    "measurement_count_180d": 0
  },
  "base_value_mismatches_test": {
    "age": 0,
    "sex": 0,
    "prior_inpatient_hospitalizations_180d": 0,
    "distinct_diagnoses_180d": 0,
    "distinct_medications_180d": 0,
    "measurement_count_180d": 0
  },
  "temporal_test_membership_differences_both_directions": [
    0,
    0
  ],
  "fe_mismatches_training": {
    "dx_cardiovascular": 0,
    "med_antihipertensivos": 0,
    "distinct_nononcological_diagnoses_180d": 0
  },
  "fe_temporal_test": "not_compared_no_original_fe_test_matrix; no_test_selection_performed"
}
```

La equivalencia utiliza las matrices de auditoría persistidas previamente, no una nueva OMOP clínica completa. Las tres variables FE se comparan para los 655 pacientes: no existe una matriz FE original de la prueba temporal en 02.4 que permita afirmar equivalencia de esas variables en los 165 reservados. No se generan resultados predictivos ni se usa la prueba para selección.
