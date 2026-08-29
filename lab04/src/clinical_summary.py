"""Funciones de apoyo para resumir y validar datos clinicos."""


def validate_required_columns(df, required_columns):
    """Valida que un DataFrame contenga todas las columnas requeridas.

    Args:
        df: DataFrame de pandas que se desea revisar.
        required_columns: Coleccion con los nombres de columnas esperadas.

    Raises:
        ValueError: Si una o mas columnas requeridas no estan presentes.
    """
    missing_columns = [column for column in required_columns if column not in df.columns]

    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(f"Faltan columnas requeridas: {missing_text}")
