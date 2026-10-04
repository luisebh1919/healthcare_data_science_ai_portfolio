-- Lab 10, actividad 3: carga reproducible de los CSV de Synthea en DuckDB.
-- Este archivo se ejecuta desde lab10/ (build_db.py fija ese directorio).
-- Todos los campos se leen primero como VARCHAR para controlar de forma
-- explícita los valores vacíos, las fechas y las columnas de tipo mixto.

DROP TABLE IF EXISTS observations;
DROP TABLE IF EXISTS medications;
DROP TABLE IF EXISTS conditions;
DROP TABLE IF EXISTS encounters;
DROP TABLE IF EXISTS patients;

CREATE TABLE patients (
    id UUID,
    birth_date DATE,
    death_date DATE,
    ssn VARCHAR,
    drivers_license VARCHAR,
    passport VARCHAR,
    prefix VARCHAR,
    first_name VARCHAR,
    middle_name VARCHAR,
    last_name VARCHAR,
    suffix VARCHAR,
    maiden_name VARCHAR,
    marital_status VARCHAR,
    race VARCHAR,
    ethnicity VARCHAR,
    gender VARCHAR,
    birthplace VARCHAR,
    address VARCHAR,
    city VARCHAR,
    state VARCHAR,
    county VARCHAR,
    fips VARCHAR,
    zip VARCHAR,
    latitude DOUBLE,
    longitude DOUBLE,
    healthcare_expenses DECIMAL(18, 2),
    healthcare_coverage DECIMAL(18, 2),
    income BIGINT
);

INSERT INTO patients
SELECT
    CAST(NULLIF(Id, '') AS UUID),
    CAST(NULLIF(BIRTHDATE, '') AS DATE),
    CAST(NULLIF(DEATHDATE, '') AS DATE),
    NULLIF(SSN, ''),
    NULLIF(DRIVERS, ''),
    NULLIF(PASSPORT, ''),
    NULLIF(PREFIX, ''),
    NULLIF(FIRST, ''),
    NULLIF(MIDDLE, ''),
    NULLIF(LAST, ''),
    NULLIF(SUFFIX, ''),
    NULLIF(MAIDEN, ''),
    NULLIF(MARITAL, ''),
    NULLIF(RACE, ''),
    NULLIF(ETHNICITY, ''),
    NULLIF(GENDER, ''),
    NULLIF(BIRTHPLACE, ''),
    NULLIF(ADDRESS, ''),
    NULLIF(CITY, ''),
    NULLIF(STATE, ''),
    NULLIF(COUNTY, ''),
    NULLIF(FIPS, ''),
    NULLIF(ZIP, ''),
    CAST(NULLIF(LAT, '') AS DOUBLE),
    CAST(NULLIF(LON, '') AS DOUBLE),
    CAST(NULLIF(HEALTHCARE_EXPENSES, '') AS DECIMAL(18, 2)),
    CAST(NULLIF(HEALTHCARE_COVERAGE, '') AS DECIMAL(18, 2)),
    CAST(NULLIF(INCOME, '') AS BIGINT)
FROM read_csv(
    '../lab02/output/csv/patients.csv',
    header = true,
    all_varchar = true,
    null_padding = true
);

CREATE TABLE encounters (
    id UUID,
    start_at TIMESTAMP,
    stop_at TIMESTAMP,
    patient_id UUID,
    organization_id UUID,
    provider_id UUID,
    payer_id UUID,
    encounter_class VARCHAR,
    code VARCHAR,
    description VARCHAR,
    base_encounter_cost DECIMAL(18, 2),
    total_claim_cost DECIMAL(18, 2),
    payer_coverage DECIMAL(18, 2),
    reason_code VARCHAR,
    reason_description VARCHAR
);

INSERT INTO encounters
SELECT
    CAST(NULLIF(Id, '') AS UUID),
    CAST(NULLIF(START, '') AS TIMESTAMP),
    CAST(NULLIF(STOP, '') AS TIMESTAMP),
    CAST(NULLIF(PATIENT, '') AS UUID),
    CAST(NULLIF(ORGANIZATION, '') AS UUID),
    CAST(NULLIF(PROVIDER, '') AS UUID),
    CAST(NULLIF(PAYER, '') AS UUID),
    NULLIF(ENCOUNTERCLASS, ''),
    NULLIF(CODE, ''),
    NULLIF(DESCRIPTION, ''),
    CAST(NULLIF(BASE_ENCOUNTER_COST, '') AS DECIMAL(18, 2)),
    CAST(NULLIF(TOTAL_CLAIM_COST, '') AS DECIMAL(18, 2)),
    CAST(NULLIF(PAYER_COVERAGE, '') AS DECIMAL(18, 2)),
    NULLIF(REASONCODE, ''),
    NULLIF(REASONDESCRIPTION, '')
FROM read_csv(
    '../lab02/output/csv/encounters.csv',
    header = true,
    all_varchar = true,
    null_padding = true
);

CREATE TABLE conditions (
    start_date DATE,
    stop_date DATE,
    patient_id UUID,
    encounter_id UUID,
    system VARCHAR,
    code VARCHAR,
    description VARCHAR
);

INSERT INTO conditions
SELECT
    CAST(NULLIF(START, '') AS DATE),
    CAST(NULLIF(STOP, '') AS DATE),
    CAST(NULLIF(PATIENT, '') AS UUID),
    CAST(NULLIF(ENCOUNTER, '') AS UUID),
    NULLIF(SYSTEM, ''),
    NULLIF(CODE, ''),
    NULLIF(DESCRIPTION, '')
FROM read_csv(
    '../lab02/output/csv/conditions.csv',
    header = true,
    all_varchar = true,
    null_padding = true
);

CREATE TABLE medications (
    start_at TIMESTAMP,
    stop_at TIMESTAMP,
    patient_id UUID,
    payer_id UUID,
    encounter_id UUID,
    code VARCHAR,
    description VARCHAR,
    base_cost DECIMAL(18, 2),
    payer_coverage DECIMAL(18, 2),
    dispenses INTEGER,
    total_cost DECIMAL(18, 2),
    reason_code VARCHAR,
    reason_description VARCHAR
);

INSERT INTO medications
SELECT
    CAST(NULLIF(START, '') AS TIMESTAMP),
    CAST(NULLIF(STOP, '') AS TIMESTAMP),
    CAST(NULLIF(PATIENT, '') AS UUID),
    CAST(NULLIF(PAYER, '') AS UUID),
    CAST(NULLIF(ENCOUNTER, '') AS UUID),
    NULLIF(CODE, ''),
    NULLIF(DESCRIPTION, ''),
    CAST(NULLIF(BASE_COST, '') AS DECIMAL(18, 2)),
    CAST(NULLIF(PAYER_COVERAGE, '') AS DECIMAL(18, 2)),
    CAST(NULLIF(DISPENSES, '') AS INTEGER),
    CAST(NULLIF(TOTALCOST, '') AS DECIMAL(18, 2)),
    NULLIF(REASONCODE, ''),
    NULLIF(REASONDESCRIPTION, '')
FROM read_csv(
    '../lab02/output/csv/medications.csv',
    header = true,
    all_varchar = true,
    null_padding = true
);

CREATE TABLE observations (
    observed_at TIMESTAMP,
    patient_id UUID,
    encounter_id UUID,
    category VARCHAR,
    code VARCHAR,
    description VARCHAR,
    value VARCHAR,
    units VARCHAR,
    observation_type VARCHAR
);

INSERT INTO observations
SELECT
    CAST(NULLIF(DATE, '') AS TIMESTAMP),
    CAST(NULLIF(PATIENT, '') AS UUID),
    CAST(NULLIF(ENCOUNTER, '') AS UUID),
    NULLIF(CATEGORY, ''),
    NULLIF(CODE, ''),
    NULLIF(DESCRIPTION, ''),
    NULLIF(VALUE, ''),
    NULLIF(UNITS, ''),
    NULLIF(TYPE, '')
FROM read_csv(
    '../lab02/output/csv/observations.csv',
    header = true,
    all_varchar = true,
    null_padding = true
);
