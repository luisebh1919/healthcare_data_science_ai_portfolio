# ER final y contraste con OMOP CDM v5.4

Diagrama de las seis tablas clínicas y las doce tablas de vocabulario cargadas.
Se muestran llaves principales; las columnas completas se verifican en
comparacion_esquema.json contra el DDL oficial CommonDataModel v5.4.0.
Las llaves clínicas son **lógicas y auditadas**, no constraints físicos declarados
para todas las tablas. Concepto cero es la excepción reservada para dato sin mapeo.

```mermaid
erDiagram
  person ||--o{ observation_period : person_id
  person ||--o{ visit_occurrence : person_id
  person ||--o{ condition_occurrence : person_id
  person ||--o{ observation : person_id
  person ||--o{ measurement : person_id
  visit_occurrence o|--o{ condition_occurrence : visit_occurrence_id
  visit_occurrence o|--o{ observation : visit_occurrence_id
  visit_occurrence o|--o{ measurement : visit_occurrence_id
  concept ||--o{ person : gender_concept_id
  concept ||--o{ visit_occurrence : visit_concept_id
  concept ||--o{ condition_occurrence : condition_concept_id
  concept ||--o{ observation : observation_concept_id
  concept ||--o{ measurement : measurement_concept_id
  vocabulary ||--o{ concept : vocabulary_id
  domain ||--o{ concept : domain_id
  concept_class ||--o{ concept : concept_class_id
  concept ||--o{ concept_relationship : concept_id_1_y_2
  relationship ||--o{ concept_relationship : relationship_id
  concept ||--o{ concept_ancestor : ancestor_y_descendant
  concept ||--o{ concept_synonym : concept_id_y_language
  concept ||--o{ drug_strength : drug_ingredient_unit
  concept ||--o{ pack_content : pack_y_drug
  concept ||--o{ concept_metadata : concept_id
  concept ||--o{ concept_relationship_metadata : concept_id_1_y_2
  person {
    bigint person_id PK
    integer gender_concept_id FK
    timestamp birth_datetime
    varchar person_source_value
  }
  observation_period {
    bigint observation_period_id PK
    bigint person_id FK
    date observation_period_start_date
    date observation_period_end_date
  }
  visit_occurrence {
    bigint visit_occurrence_id PK
    bigint person_id FK
    integer visit_concept_id FK
    date visit_start_date
    date visit_end_date
  }
  condition_occurrence {
    bigint condition_occurrence_id PK
    bigint person_id FK
    integer condition_concept_id FK
    bigint visit_occurrence_id FK
    varchar condition_source_value
  }
  observation {
    integer observation_id PK
    integer person_id FK
    integer observation_concept_id FK
    integer visit_occurrence_id FK
    varchar observation_source_value
  }
  measurement {
    integer measurement_id PK
    integer person_id FK
    integer measurement_concept_id FK
    integer visit_occurrence_id FK
    varchar measurement_source_value
  }
  concept {
    bigint concept_id PK
    varchar concept_name
    varchar domain_id FK
    varchar vocabulary_id FK
    varchar concept_class_id FK
  }
  concept_relationship {
    bigint concept_id_1 FK
    bigint concept_id_2 FK
    varchar relationship_id FK
  }
  concept_ancestor {
    bigint ancestor_concept_id FK
    bigint descendant_concept_id FK
    integer min_levels_of_separation
    integer max_levels_of_separation
  }
```

Las claves de diccionarios son vocabulary_id, domain_id, concept_class_id y
relationship_id. CONCEPT_RELATIONSHIP tiene clave lógica compuesta
(concept_id_1, concept_id_2, relationship_id); CONCEPT_ANCESTOR,
(ancestor_concept_id, descendant_concept_id). La unión ATHENA verificó conflictos
para esas claves. Metadatos y sinónimos pueden tener varias filas por concepto.
Las referencias a conceptos de vocabulario/dominio/clase se auditan también.

## Trazabilidad adicional al CDM

```mermaid
erDiagram
  src_conditions ||--o{ clinical_lineage : source_row
  clinical_lineage }o--|| condition_occurrence : destino_condition
  clinical_lineage }o--|| observation : destino_observation
  clinical_lineage }o--|| measurement : destino_measurement
```

Las tres flechas de destino son **alternativas** según event_table, no tres FKs
simultáneas. clinical_lineage registra source_row, event_table, event_id y
concepto destino. Se comprueba que cada traza tenga origen y destino correctos y
que ninguna fila fuente quede sin traza. rejected_domain conserva el archivo de
los 430935 destinos inicialmente separados: ya no son descartes pendientes.
Otras tablas de trabajo son src_patients, src_encounters, mapping, mapped,
condition_lineage, migration_relocated, visit_mapping_audit y lab12_run. No son
parte normativa del CDM y sus datos permanecen locales.

## Comparación y dos diferencias clasificadas

[Especificación oficial v5.4](https://ohdsi.github.io/CommonDataModel/cdm54.html).
La comparación ejecutada no encontró columnas faltantes ni adicionales en las
seis tablas clínicas, incluidas Observation y Measurement tomadas del DDL oficial.
Esto no demuestra igualdad de constraints o semántica de todas las columnas.

1. **Subconjunto de tablas y campos incompletos.** No se instancian todas las
   tablas del CDM, ni se convierten todos los CSV Synthea. Raza, etnia y algunos
   tipos/procedencia quedan en cero. El subconjunto es una simplificación docente
   legítima según la ruta manual del enunciado; no es conformidad completa ni
   suficiencia para una investigación clínica sin más trabajo.
2. **Constraints y observación aproximada.** Las llaves se verifican con consultas
   en lugar de declararse físicamente en todo el modelo; el período procede de
   primera/última visita. Es una decisión técnica explícita para la carga analítica,
   pero no certifica integridad automática futura ni cobertura asistencial continua.
   Su falta de fidelidad clínica sería un error si se presentara como seguimiento
   completo: por eso se cuantifican huecos y eventos externos.

PACK_CONTENT y las tablas *_METADATA vienen de la descarga moderna ATHENA y se
conservan como auxiliares, sin afirmar que sean tablas clínicas normativas 5.4.
La fila de diccionario denominada CDM v6.0.0 no convierte este esquema a CDM 6.
