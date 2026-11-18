"""Pruebas con archivos sintéticos diminutos y conceptos oficiales conocidos.

Las fechas de vigencia son controles de prueba; no son una exportación Athena.
No se distribuyen pacientes ni vocabularios clínicos licenciados.
"""

import csv
import sys
from datetime import date
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import etl
from schema import create_schema, validate_schema


def write_csv(path, header, rows, delimiter=","):
    with path.open("w", newline="") as f:
        w = csv.writer(f, delimiter=delimiter)
        w.writerow(header)
        w.writerows(rows)


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "csv"
    root.mkdir()
    write_csv(
        root / "patients.csv",
        ["Id", "BIRTHDATE", "DEATHDATE", "GENDER", "RACE", "ETHNICITY"],
        [["p1", "1980-01-01", "", "F", "unknown", "unknown"]],
    )
    write_csv(
        root / "encounters.csv",
        [
            "Id",
            "PATIENT",
            "START",
            "STOP",
            "ENCOUNTERCLASS",
            "ORGANIZATION",
            "PROVIDER",
        ],
        [
            [
                "v1",
                "p1",
                "2020-01-01T12:00:00Z",
                "2020-01-02T12:00:00Z",
                "inpatient",
                "",
                "",
            ]
        ],
    )
    headers = ["START", "STOP", "PATIENT", "ENCOUNTER", "CODE", "DESCRIPTION"]
    for name in ["conditions", "medications", "procedures", "devices"]:
        write_csv(
            root / (name + ".csv"),
            headers,
            [["2020-01-01T12:00:00Z", "", "p1", "v1", "UNKNOWN", "Unknown source"]],
        )
    write_csv(
        root / "observations.csv",
        [
            "DATE",
            "PATIENT",
            "ENCOUNTER",
            "CODE",
            "DESCRIPTION",
            "VALUE",
            "UNITS",
            "TYPE",
        ],
        [
            [
                "2020-01-01T12:00:00Z",
                "p1",
                "v1",
                "8480-6",
                "Systolic blood pressure",
                "123.456789",
                "mm[Hg]",
                "numeric",
            ]
        ],
    )
    write_csv(
        root / "immunizations.csv",
        ["DATE", "PATIENT", "ENCOUNTER", "CODE", "DESCRIPTION"],
        [],
    )
    return root


def memory():
    c = duckdb.connect(":memory:")
    c.execute("SET threads=1")
    create_schema(c)
    etl.setup_audit(c)
    # Identificadores/códigos reales; los restantes metadatos se limitan al doble de prueba.
    for cid, name, domain, vocab, code in [
        (0, "No matching concept", "Metadata", "None", "No matching concept"),
        (8532, "FEMALE", "Gender", "Gender", "F"),
        (8507, "MALE", "Gender", "Gender", "M"),
        (9201, "Inpatient Visit", "Visit", "Visit", "IP"),
        (3004249, "Systolic blood pressure", "Measurement", "LOINC", "8480-6"),
    ]:
        c.execute(
            "INSERT INTO omop.concept VALUES (?,?,?,?,?,?,?,?,?,?)",
            [
                cid,
                name,
                domain,
                vocab,
                "Test fixture",
                "S",
                code,
                "1970-01-01",
                "2099-12-31",
                None,
            ],
        )
    c.execute(
        "INSERT INTO omop.domain SELECT DISTINCT domain_id,domain_id,0 FROM omop.concept"
    )
    c.execute(
        "INSERT INTO omop.vocabulary SELECT DISTINCT vocabulary_id,vocabulary_id,NULL,NULL,0 FROM omop.concept"
    )
    c.execute("INSERT INTO omop.concept_class VALUES ('Test fixture','Test fixture',0)")
    c.execute(
        "INSERT INTO omop.relationship VALUES ('Maps to','Maps to','0','0','Maps to',0)"
    )
    return c


def test_official_schema_and_types():
    with memory() as c:
        r = validate_schema(c)
        assert r["tables"] >= 39
        assert not r["errors"]


def test_source_reconciliation_precision_and_no_invented_concepts(source):
    with memory() as c:
        when = date(2026, 11, 15)
        etl.demographics(c, source, when)
        etl.visits(c, source, when)
        for name in etl.EVENT_FILES:
            etl.clinical_events(c, name, source, when)
        result = etl.validate(c)
        assert not result["schema"]["errors"]
        assert not any(result["errors"].values())
        assert c.execute("SELECT value_as_number FROM omop.measurement").fetchone()[
            0
        ] == pytest.approx(123.456789)
        assert c.execute(
            "SELECT condition_concept_id FROM omop.condition_occurrence"
        ).fetchall() == [(0,)]
        assert c.execute("SELECT count(*) FROM etl.lineage").fetchone()[0] == 5
        assert c.execute("SELECT count(*) FROM omop.visit_detail").fetchone()[0] == 0
        assert c.execute(
            "SELECT verbatim_end_date,drug_exposure_end_date FROM omop.drug_exposure"
        ).fetchone() == (None, date(2020, 1, 1))


def test_cross_patient_visit_is_quarantined(source):
    with memory() as c:
        when = date(2026, 11, 15)
        etl.demographics(c, source, when)
        etl.visits(c, source, when)
        c.execute("UPDATE omop.visit_occurrence SET person_id=999")
        etl.clinical_events(c, "conditions", source, when)
        assert (
            c.execute("SELECT count(*) FROM omop.condition_occurrence").fetchone()[0]
            == 0
        )
        assert (
            c.execute("SELECT reason FROM etl.rejected").fetchone()[0]
            == "missing_or_wrong_patient_visit"
        )


def test_existing_database_is_never_overwritten(source, tmp_path):
    p = tmp_path / "old.duckdb"
    p.write_bytes(b"protected")
    with pytest.raises(FileExistsError):
        etl.preflight(source, [], p)
    assert p.read_bytes() == b"protected"


def test_preflight_stops_before_creating_output(source, tmp_path, monkeypatch):
    from collections import namedtuple

    Usage = namedtuple("Usage", "total used free")
    monkeypatch.setattr(etl.shutil, "disk_usage", lambda p: Usage(100, 99, 1))
    output = tmp_path / "new.duckdb"
    with pytest.raises(OSError, match="Espacio insuficiente"):
        etl.build(source, [], output, date(2026, 8, 16), date(2026, 11, 15))
    assert not output.exists()


def test_identity_does_not_duplicate_maps_to(source):
    with memory() as c:
        when = date(2026, 11, 15)
        etl.demographics(c, source, when)
        etl.visits(c, source, when)
        # Añadir otra fuente al mismo destino real verifica multiplicación solo por Maps to.
        c.execute(
            "INSERT INTO omop.concept_relationship VALUES (3004249,3004249,'Maps to','1970-01-01','2099-12-31',NULL)"
        )
        etl.clinical_events(c, "observations", source, when)
        assert c.execute("SELECT count(*) FROM omop.measurement").fetchone()[0] == 1


def test_condition_source_is_routed_to_official_observation_domain(source):
    with memory() as c:
        when = date(2026, 11, 15)
        c.execute(
            "INSERT INTO omop.concept VALUES (4053118,'Full-time employment','Observation','SNOMED','Test fixture','S','160903007','1970-01-01','2099-12-31',NULL)"
        )
        write_csv(
            source / "conditions.csv",
            ["START", "STOP", "PATIENT", "ENCOUNTER", "CODE", "DESCRIPTION"],
            [["2020-01-01", "", "p1", "v1", "160903007", "Full-time employment"]],
        )
        etl.demographics(c, source, when)
        etl.visits(c, source, when)
        etl.clinical_events(c, "conditions", source, when)
        assert (
            c.execute("SELECT count(*) FROM omop.condition_occurrence").fetchone()[0]
            == 0
        )
        assert c.execute(
            "SELECT observation_concept_id,value_as_number,unit_concept_id FROM omop.observation"
        ).fetchone() == (4053118, None, 0)
        assert (
            c.execute("SELECT source_description FROM etl.lineage").fetchone()[0]
            == "Full-time employment"
        )


def test_end_to_end_replay_is_idempotent_and_source_drift_refused(
    source, tmp_path, monkeypatch
):
    # Generar el pequeño paquete de prueba a partir del doble en memoria.
    folder = tmp_path / "vocabulary"
    folder.mkdir()
    with memory() as c:
        for table in etl.VOCAB_TABLES:
            cols = [x[0] for x in c.execute(f"DESCRIBE omop.{table}").fetchall()]
            rows = c.execute(f"SELECT * FROM omop.{table}").fetchall()
            write_csv(folder / (table.upper() + ".csv"), cols, rows, delimiter="\t")
    monkeypatch.setattr(etl, "preflight", lambda *args: {"enough_space": True})
    output = tmp_path / "new.duckdb"
    when = date(2026, 11, 15)
    report = etl.build(source, [folder], output, date(2026, 8, 16), when)
    before = etl.digest(output)
    assert report["counts"]["person"] == 1
    assert (
        etl.build(source, [folder], output, date(2026, 8, 16), when)["replay"]
        == "identical_inputs_no_write"
    )
    assert etl.digest(output) == before
    with (source / "patients.csv").open("a") as f:
        f.write("\n")
    with pytest.raises(FileExistsError, match="cambiaron"):
        etl.build(source, [folder], output, date(2026, 8, 16), when)
    assert etl.digest(output) == before


def test_vocabulary_conflicts_fail(tmp_path):
    for i, name in enumerate(["a", "b"]):
        folder = tmp_path / name
        folder.mkdir()
        with memory() as c:
            for table in etl.VOCAB_TABLES:
                columns = [x[0] for x in c.execute(f"DESCRIBE omop.{table}").fetchall()]
                rows = []
                if table == "concept":
                    rows = [
                        [
                            8532,
                            "FEMALE" if i == 0 else "conflict",
                            "Gender",
                            "Gender",
                            "Gender",
                            "S",
                            "F",
                            "19700101",
                            "20991231",
                            "",
                        ]
                    ]
                write_csv(
                    folder / (table.upper() + ".csv"), columns, rows, delimiter="\t"
                )
    with memory() as c:
        c.execute("DELETE FROM omop.concept")
        with pytest.raises(ValueError, match="contradictorios"):
            etl.load_vocab(c, [tmp_path / "a", tmp_path / "b"])
