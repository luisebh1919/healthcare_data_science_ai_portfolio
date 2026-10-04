import pandas as pd
import pytest

from clinlab.data_quality import (
    classify_clinical_value,
    find_implausible_values,
    find_temporal_inconsistencies,
    memory_mb,
    merge_with_cardinality,
    non_numeric_fraction,
)


def test_memory_mb_returns_positive_value():
    # Un DataFrame con datos debe ocupar una cantidad positiva de memoria.
    df = pd.DataFrame({"age": [45, 60, 72]})

    result = memory_mb(df)

    assert result > 0


def test_non_numeric_fraction_detects_text():
    # Simula una columna clínica donde un valor de texto se coló entre mediciones.
    values = pd.Series(["10", "20.5", "No", None])

    result = non_numeric_fraction(values)

    # "No" debe detectarse como dato no numérico; None se trata como faltante.
    assert result == pytest.approx(1 / 3)


def test_find_temporal_inconsistencies_respects_death_day_resolution():
    # Cada fila representa a una persona con nacimiento y una fecha de defuncion registrada solo por dia.
    patients = pd.DataFrame(
        {
            "patient_id": [1],
            "birth_date": ["1980-01-01 00:00"],
            "death_date": ["2020-05-10 00:00"],
        }
    )
    # La visita nocturna del dia de defuncion es valida; la siguiente ya es temporalmente imposible.
    encounters = pd.DataFrame(
        {
            "patient_id": [1, 1, 1],
            "encounter_date": [
                "1979-12-31 12:00",
                "2020-05-10 23:59",
                "2020-05-11 00:00",
            ],
        }
    )

    inconsistencies = find_temporal_inconsistencies(patients, encounters)

    # Evita conservar visitas previas al nacimiento o posteriores al dia registrado de defuncion.
    assert inconsistencies["issue"].tolist() == ["before_birth", "after_death"]


def test_merge_with_cardinality_allows_many_encounters_per_patient():
    # Varias visitas pueden pertenecer a una persona, mientras el catalogo de pacientes tiene una fila por clave.
    encounters = pd.DataFrame({"patient_id": [1, 1, 2], "encounter_id": [10, 11, 12]})
    patients = pd.DataFrame({"patient_id": [1, 2], "sex": ["F", "M"]})

    merged = merge_with_cardinality(encounters, patients, on="patient_id")

    # Confirma que el merge replica atributos del paciente sin perder ninguna visita.
    assert merged["sex"].tolist() == ["F", "F", "M"]


def test_merge_with_cardinality_rejects_duplicate_right_keys():
    # Dos fichas para la misma persona harian ambiguo que atributo clinico corresponde a la visita.
    encounters = pd.DataFrame({"patient_id": [1], "encounter_id": [10]})
    patients = pd.DataFrame({"patient_id": [1, 1], "sex": ["F", "M"]})

    # validate="many_to_one" previene duplicar encuentros por un catalogo de pacientes defectuoso.
    with pytest.raises(pd.errors.MergeError, match="not a many-to-one merge"):
        merge_with_cardinality(encounters, patients, on="patient_id")


def test_find_implausible_values_uses_supplied_clinical_limits():
    # Estas mediciones mezclan valores esperables, extremos y un faltante que no debe inventarse como anomalia.
    measurements = pd.DataFrame(
        {
            "heart_rate": [72.0, 300.0, None],
            "temperature_c": [36.8, 33.0, 42.1],
        }
    )
    # Los rangos vienen del contexto clinico, no de numeros escondidos dentro de la funcion.
    limits = {"heart_rate": (30.0, 220.0), "temperature_c": (34.0, 42.0)}

    implausible = find_implausible_values(measurements, limits)

    # Las mascaras booleanas localizan extremos sin alterar las mediciones originales.
    assert implausible["heart_rate"].tolist() == [False, True, False]
    assert implausible["temperature_c"].tolist() == [False, True, True]


@pytest.fixture
def malicious_clinical_data() -> dict[str, pd.DataFrame]:
    """Provide a compact dataset with mistakes common in clinical extracts."""

    # El catalogo combina una ficha normal con faltantes, una clave repetida y mediciones que requieren revision.
    patients = pd.DataFrame(
        {
            "person_id": [1, 2, 3, 4, 5, 5, 6],
            "birth_date": [
                "1980-01-01",
                "1975-06-01",
                "2000-01-01",
                "1940-03-15",
                "1990-04-20",
                "1990-04-20",
                "1985-08-30",
            ],
            "death_date": [None, None, None, "2020-05-10", None, None, None],
            "heart_rate": [72.0, None, 80.0, 65.0, 70.0, -999.0, 500.0],
        }
    )
    # Estas visitas permiten comprobar que la validacion temporal detecta solo los eventos imposibles.
    encounters = pd.DataFrame(
        {
            "person_id": [1, 3, 4],
            "encounter_date": ["2024-01-01", "1999-12-31", "2020-05-11"],
        }
    )

    return {"patients": patients, "encounters": encounters}


def test_non_numeric_fraction_returns_zero_for_all_missing_values():
    # Una columna completamente vacia no contiene texto contaminante y no debe producir una division por cero.
    values = pd.Series([None, float("nan")])

    result = non_numeric_fraction(values)

    assert result == pytest.approx(0.0)


def test_find_temporal_inconsistencies_handles_empty_dataframes():
    # Un extracto vacio puede aparecer antes de que llegue una carga; validarlo no debe romper el pipeline.
    patients = pd.DataFrame(columns=["patient_id", "birth_date", "death_date"])
    encounters = pd.DataFrame(columns=["patient_id", "encounter_date"])

    inconsistencies = find_temporal_inconsistencies(patients, encounters)

    # El resultado conserva su forma de reporte, pero no inventa alertas clinicas.
    assert inconsistencies.empty
    assert inconsistencies.columns.tolist() == ["patient_id", "encounter_date", "issue"]


def test_find_temporal_inconsistencies_flags_encounter_before_birth(
    malicious_clinical_data: dict[str, pd.DataFrame],
):
    # Renombramos la clave de la fixture para ejercitar la funcion con el contrato de paciente y encuentro.
    patients = malicious_clinical_data["patients"].rename(columns={"person_id": "patient_id"})
    encounters = malicious_clinical_data["encounters"].rename(columns={"person_id": "patient_id"})
    # La clave duplicada no participa en esta comprobacion temporal, asi que conservamos una ficha por persona.
    patients = patients.drop_duplicates(subset="patient_id", keep="first")

    inconsistencies = find_temporal_inconsistencies(patients, encounters)

    # Impide aceptar una visita de 1999 para una persona cuyo nacimiento registrado es en 2000.
    assert "before_birth" in inconsistencies["issue"].tolist()


def test_merge_with_cardinality_rejects_duplicate_person_id(
    malicious_clinical_data: dict[str, pd.DataFrame],
):
    # La tabla derecha simula un maestro de pacientes con dos filas para person_id 5.
    patients = malicious_clinical_data["patients"][["person_id", "heart_rate"]]
    encounters = malicious_clinical_data["encounters"]

    # La validacion many-to-one evita que una visita se replique contra ambas fichas del mismo paciente.
    with pytest.raises(pd.errors.MergeError, match="not a many-to-one merge"):
        merge_with_cardinality(encounters, patients, on="person_id")


def test_find_implausible_values_flags_sentinel_value(
    malicious_clinical_data: dict[str, pd.DataFrame],
):
    # -999 es un sentinela de sistema, no una frecuencia cardiaca fisiologicamente posible.
    measurements = malicious_clinical_data["patients"][["heart_rate"]]
    limits = {"heart_rate": (30.0, 220.0)}

    implausible = find_implausible_values(measurements, limits)

    # La mascara permite localizar el sentinela sin modificar la tabla clinica original.
    assert implausible.loc[measurements["heart_rate"] == -999.0, "heart_rate"].all()


@pytest.mark.parametrize(
    ("column", "value", "limits", "expected"),
    [
        ("heart_rate", 72.0, {"heart_rate": (30.0, 220.0)}, False),
        ("heart_rate", 29.0, {"heart_rate": (30.0, 220.0)}, True),
        ("heart_rate", 220.0, {"heart_rate": (30.0, 220.0)}, False),
        ("heart_rate", 221.0, {"heart_rate": (30.0, 220.0)}, True),
        ("heart_rate", -999.0, {"heart_rate": (30.0, 220.0)}, True),
        ("temperature_c", 36.8, {"temperature_c": (34.0, 42.0)}, False),
        ("temperature_c", 33.0, {"temperature_c": (34.0, 42.0)}, True),
        ("temperature_c", 42.1, {"temperature_c": (34.0, 42.0)}, True),
    ],
)
def test_find_implausible_values_respects_external_clinical_limits(
    column: str,
    value: float,
    limits: dict[str, tuple[float, float]],
    expected: bool,
):
    # Cada caso representa una medicion aislada para comprobar los bordes sin codificar el rango en la funcion.
    measurements = pd.DataFrame({column: [value]})

    implausible = find_implausible_values(measurements, limits)

    # Las comparaciones conservan como validos los limites exactos y marcan solo valores fuera del intervalo.
    assert bool(implausible.loc[0, column]) is expected


@pytest.fixture
def teaching_classification_limits() -> dict[str, dict[str, object]]:
    """Provide an external scheme used only to exercise classification boundaries."""

    # Referencias externas pendientes: sustituir estos valores didacticos por una politica clinica aprobada.
    return {
        "heart_rate": {
            "implausible_low": 0.0,
            "very_low": (0.0, 29.0),
            "low": (30.0, 59.0),
            "normal": (60.0, 99.0),
            "high": (100.0, 129.0),
            "very_high": (130.0, 220.0),
            "implausible_high": 220.0,
            "urgent_categories": {"very_low", "very_high"},
        }
    }


@pytest.mark.parametrize(
    ("value", "expected_category", "expected_plausible", "expected_urgent"),
    [
        (-1.0, "implausible", False, False),
        (0.0, "very_low", True, True),
        (29.0, "very_low", True, True),
        (30.0, "low", True, False),
        (59.0, "low", True, False),
        (60.0, "normal", True, False),
        (99.0, "normal", True, False),
        (100.0, "high", True, False),
        (129.0, "high", True, False),
        (130.0, "very_high", True, True),
        (220.0, "very_high", True, True),
        (221.0, "implausible", False, False),
        (float("nan"), "missing", None, False),
    ],
)
def test_classify_clinical_value_separates_plausibility_severity_and_urgency(
    value: float,
    expected_category: str,
    expected_plausible: bool | None,
    expected_urgent: bool,
    teaching_classification_limits: dict[str, dict[str, object]],
):
    # Cada valor cae en un borde o justo a un lado del borde para prevenir errores de comparacion inclusiva.
    classification = classify_clinical_value(value, "heart_rate", teaching_classification_limits)

    # Una categoria extrema puede ser plausible y urgente; implausible solo describe calidad del dato.
    assert classification["category"] == expected_category
    assert classification["is_plausible"] is expected_plausible
    assert classification["is_urgent"] is expected_urgent
