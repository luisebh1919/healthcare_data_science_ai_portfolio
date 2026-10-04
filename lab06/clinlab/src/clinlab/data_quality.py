from typing import Any, Literal

import pandas as pd


def non_numeric_fraction(values: pd.Series) -> float:
    """Calculate the fraction of present values that are not numeric."""

    # Convierte a número; texto no convertible pasa a NaN.
    numeric_values = pd.to_numeric(values, errors="coerce")

    # Identifica qué valores estaban presentes originalmente.
    present_values = values.notna()

    # Detecta valores presentes que no pudieron convertirse a número.
    non_numeric_values = numeric_values.isna() & present_values

    present_count = present_values.sum()

    # Sin datos presentes no hay texto invalido; devolvemos 0.0 y evitamos dividir entre cero.
    if present_count == 0:
        return 0.0

    return non_numeric_values.sum() / present_count


def memory_mb(df: pd.DataFrame) -> float:
    """Return DataFrame memory usage in megabytes."""

    # Calcula el uso total de memoria en bytes.
    bytes_used = df.memory_usage(deep=True).sum()

    # Convierte bytes a megabytes.
    return bytes_used / (1024**2)


def find_temporal_inconsistencies(patients: pd.DataFrame, encounters: pd.DataFrame) -> pd.DataFrame:
    """Return encounters that occur before birth or after the recorded death day."""

    # Conservamos solo las fechas necesarias del catalogo de pacientes antes de unirlo a las visitas.
    patient_dates = patients[["patient_id", "birth_date", "death_date"]].copy()

    # pd.to_datetime permite comparar texto, fechas y timestamps con una sola representacion temporal.
    patient_dates["birth_date"] = pd.to_datetime(patient_dates["birth_date"], errors="coerce").dt.normalize()
    patient_dates["death_date"] = pd.to_datetime(patient_dates["death_date"], errors="coerce").dt.normalize()

    # Cada encuentro recibe las fechas de su paciente; cada paciente debe aportar como maximo una ficha.
    dated_encounters = encounters.merge(patient_dates, on="patient_id", how="left", validate="many_to_one")

    # Comparamos por fecha y no por timestamp para no marcar una visita del mismo DEATHDATE como error.
    encounter_day = pd.to_datetime(dated_encounters["encounter_date"], errors="coerce").dt.normalize()

    # Estas mascaras booleanas dejan fuera los pacientes sin la fecha clinica necesaria para comparar.
    before_birth = (
        dated_encounters["birth_date"].notna()
        & encounter_day.notna()
        & (encounter_day < dated_encounters["birth_date"])
    )
    after_death = (
        dated_encounters["death_date"].notna()
        & encounter_day.notna()
        & (encounter_day > dated_encounters["death_date"])
    )

    # Seleccionamos solo las visitas problematicas para que puedan revisarse o corregirse aguas abajo.
    inconsistencies = dated_encounters.loc[before_birth | after_death, ["patient_id", "encounter_date"]].copy()
    inconsistencies["issue"] = "after_death"
    inconsistencies.loc[before_birth[before_birth].index, "issue"] = "before_birth"

    return inconsistencies


def merge_with_cardinality(
    left: pd.DataFrame,
    right: pd.DataFrame,
    on: str | list[str],
    how: Literal["left", "right", "inner", "outer"] = "left",
) -> pd.DataFrame:
    """Merge a table of records with one reference row per key on the right."""

    # validate hace que pandas falle antes de multiplicar filas si el catalogo derecho repite una clave.
    return left.merge(right, on=on, how=how, validate="many_to_one")


def find_implausible_values(df: pd.DataFrame, limits: dict[str, tuple[float, float]]) -> pd.DataFrame:
    """Return boolean masks for values outside caller-supplied plausibility limits."""

    implausible = pd.DataFrame(index=df.index)

    for column, (lower_limit, upper_limit) in limits.items():
        if lower_limit > upper_limit:
            raise ValueError("Each lower limit must be less than or equal to its upper limit.")

        # Convertimos la columna para comparar mediciones; texto no numerico queda como faltante aqui.
        numeric_values = pd.to_numeric(df[column], errors="coerce")

        # La mascara marca solo extremos y deja los faltantes como False para no inventar una anomalia.
        implausible[column] = (numeric_values < lower_limit) | (numeric_values > upper_limit)

    return implausible


def classify_clinical_value(
    value: float | None,
    measurement: str,
    limits: dict[str, dict[str, Any]],
) -> dict[str, str | bool | None]:
    """Classify one measurement using externally supplied clinical policy.

    "normal" describes clinical severity under the supplied policy.
    "urgent" is a separate attention flag that may apply to an extreme but plausible value.
    "implausible" means the value fails data-quality bounds and must not be interpreted clinically.

    External clinical references:
        Keep threshold values in the caller-provided policy. Add approved institutional or
        literature-backed references there before using this function for patient care.
    """

    # Un dato faltante no es una medicion extrema ni un error fisiologico; se conserva como faltante.
    if pd.isna(value):
        return {"category": "missing", "is_plausible": None, "is_urgent": False}

    measurement_limits = limits[measurement]
    implausible_low = measurement_limits["implausible_low"]
    implausible_high = measurement_limits["implausible_high"]

    # La plausibilidad se evalua primero para que sentinelas como -999 no reciban severidad clinica.
    if value < implausible_low or value > implausible_high:
        return {"category": "implausible", "is_plausible": False, "is_urgent": False}

    urgent_categories = measurement_limits.get("urgent_categories", set())

    # Los nombres de categorias son estables, pero sus intervalos y urgencia vienen de la configuracion externa.
    for category in ("very_low", "low", "normal", "high", "very_high"):
        lower_bound, upper_bound = measurement_limits[category]

        # Los limites inclusivos hacen que el borde pertenezca a una sola categoria predecible.
        if lower_bound <= value <= upper_bound:
            return {
                "category": category,
                "is_plausible": True,
                "is_urgent": category in urgent_categories,
            }

    # Un hueco entre rangos es un problema de configuracion, no una categoria clinica inventada.
    raise ValueError("Plausible value is not covered by the supplied clinical ranges.")
