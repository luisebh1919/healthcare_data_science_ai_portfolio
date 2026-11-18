"""Prueba de regresión del conteo de hospitalizaciones previas."""

from pathlib import Path

import duckdb


def test_prior_inpatient_hospitalizations_180d():
    """Cuenta solo hospitalizaciones en [ingreso − 180 días, ingreso)."""
    sql_path = Path(__file__).resolve().parents[1] / "sql" / "05_features.sql"

    with duckdb.connect(":memory:") as con:
        # Datos sintéticos; no se abren ni modifican bases locales.
        con.execute("""
            CREATE SCHEMA omop;
            CREATE SCHEMA results;
            ATTACH ':memory:' AS raw;

            CREATE TABLE omop.person AS
            SELECT person_id, CAST(person_id AS VARCHAR) AS person_source_value,
                TIMESTAMP '1980-01-01' AS birth_datetime,
                'F' AS gender_source_value
            FROM (VALUES (1), (2), (3)) AS p(person_id);

            CREATE TABLE results.outcome_30d AS
            SELECT person_id, 100 + person_id AS index_visit_id,
                TIMESTAMP '2024-07-01' AS index_admission,
                TIMESTAMP '2024-07-02' AS index_discharge,
                0 AS readmission_30d
            FROM omop.person;

            CREATE TABLE omop.visit_occurrence AS
            SELECT visit_occurrence_id, person_id, visit_concept_id,
                TIMESTAMP '2024-07-01'
                    + horas * INTERVAL 1 HOUR AS visit_start_datetime
            FROM (VALUES
                (1, 1, 9201, -4320), -- Límite inferior incluido.
                (2, 1, 9201, -1),    -- Hospitalización previa incluida.
                (3, 1, 9201, -4321), -- Anterior a la ventana.
                (101, 1, 9201, 0),   -- Hospitalización índice excluida.
                (5, 1, 9201, 1),     -- Posterior al ingreso.
                (6, 1, 9202, -24),   -- Consulta ambulatoria.
                (7, 1, 9203, -24),   -- Urgencias.
                (8, 1, NULL, -24),   -- Clasificación ausente.
                (9, 2, 9202, -24),   -- Solo visitas no hospitalarias.
                (10, 99, 9201, -24)  -- Persona ajena a la cohorte.
            ) AS v(visit_occurrence_id, person_id, visit_concept_id, horas);

            CREATE TABLE omop.condition_occurrence (
                person_id BIGINT, condition_source_value VARCHAR,
                condition_start_date DATE
            );
            CREATE TABLE raw.main.medications (
                patient_id VARCHAR, code VARCHAR, start_at TIMESTAMP
            );
            CREATE TABLE raw.main.observations (
                patient_id VARCHAR, observed_at TIMESTAMP,
                observation_type VARCHAR, category VARCHAR
            );
        """)

        con.execute(sql_path.read_text(encoding="utf-8"))

        assert con.execute("""
            SELECT person_id, prior_inpatient_hospitalizations_180d
            FROM results.analytic_dataset
            ORDER BY person_id
        """).fetchall() == [(1, 2), (2, 0), (3, 0)]
