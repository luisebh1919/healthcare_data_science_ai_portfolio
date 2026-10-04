# Diagrama entidad-relación — Lab 10

Este diagrama representa las relaciones **lógicas** de los CSV de Synthea
cargados en DuckDB. Una barra doble junto a la entidad padre y el símbolo de
“cero o muchos” junto a la entidad hija expresan una relación lógica 1:N: un
paciente o encuentro puede no tener registros hijos o puede tener varios.

```mermaid
erDiagram
    PATIENTS ||--o{ ENCOUNTERS : "tiene"
    PATIENTS ||--o{ CONDITIONS : "presenta"
    PATIENTS ||--o{ MEDICATIONS : "recibe"
    PATIENTS ||--o{ OBSERVATIONS : "genera"
    ENCOUNTERS ||--o{ CONDITIONS : "registra"
    ENCOUNTERS ||--o{ MEDICATIONS : "prescribe"
    ENCOUNTERS ||--o{ OBSERVATIONS : "incluye"

    PATIENTS {
        UUID id "PK lógica"
        DATE birth_date
        DATE death_date
        VARCHAR gender
        VARCHAR race
        VARCHAR ethnicity
        VARCHAR city
        VARCHAR state
        DECIMAL healthcare_expenses "18,2"
        DECIMAL healthcare_coverage "18,2"
        BIGINT income
    }

    ENCOUNTERS {
        UUID id "PK lógica"
        UUID patient_id "FK lógica a patients.id"
        TIMESTAMP start_at
        TIMESTAMP stop_at
        VARCHAR encounter_class
        VARCHAR code
        VARCHAR description
        DECIMAL base_encounter_cost "18,2"
        DECIMAL total_claim_cost "18,2"
        DECIMAL payer_coverage "18,2"
        VARCHAR reason_code
    }

    CONDITIONS {
        UUID patient_id "FK lógica a patients.id"
        UUID encounter_id "FK lógica a encounters.id"
        DATE start_date
        DATE stop_date
        VARCHAR system
        VARCHAR code
        VARCHAR description
    }

    MEDICATIONS {
        UUID patient_id "FK lógica a patients.id"
        UUID encounter_id "FK lógica a encounters.id"
        UUID payer_id
        TIMESTAMP start_at
        TIMESTAMP stop_at
        VARCHAR code
        VARCHAR description
        DECIMAL base_cost "18,2"
        DECIMAL payer_coverage "18,2"
        INTEGER dispenses
        DECIMAL total_cost "18,2"
        VARCHAR reason_code
    }

    OBSERVATIONS {
        UUID patient_id "FK lógica a patients.id"
        UUID encounter_id "FK lógica a encounters.id"
        TIMESTAMP observed_at
        VARCHAR category
        VARCHAR code
        VARCHAR description
        VARCHAR value "numérico o texto"
        VARCHAR units
        VARCHAR observation_type
    }
```

## Interpretación de claves

- `patients.id` y `encounters.id` son PK lógicas porque se verificó que no
  contienen duplicados.
- Los campos `patient_id` y `encounter_id` indicados arriba son FK lógicas por
  su significado en Synthea y por las relaciones establecidas para este lab.
- `conditions`, `medications` y `observations` no contienen un ID propio en los
  archivos fuente; no se les asigna una PK artificial.
- El diagrama no implica constraints físicos. En la base actual todas las
  columnas muestran `key=None` porque `carga.sql` no declara `PRIMARY KEY` ni
  `FOREIGN KEY`.
