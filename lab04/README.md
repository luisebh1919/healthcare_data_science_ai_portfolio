## 1. Issue #1 — Validación de DataFrames clínicos

### 1.1 Objetivo

Este avance agrega una validación básica para revisar que un DataFrame clínico tenga las columnas mínimas necesarias antes de continuar con análisis o resúmenes. El objetivo es detectar temprano errores de entrada, como archivos incompletos o columnas mal nombradas.

### 1.2 Implementación

La función `validate_required_columns(df, required_columns)` recibe un DataFrame de pandas y una colección de nombres de columnas requeridas. Si todas las columnas existen, la función termina sin lanzar errores. Si falta una o más columnas, lanza `ValueError` con un mensaje que lista claramente las columnas faltantes.

### 1.3 Pruebas

Las pruebas con `pytest` cubren tres casos:

1. Un DataFrame válido con todas las columnas requeridas.
2. Un DataFrame al que le falta una columna.
3. Un DataFrame al que le faltan varias columnas.

### 1.4 Evidencia Git

- Rama usada:
- Commit:
- PR:
- Issue cerrado con `fixes #1`:

## 2. Issue #3 — Resumen de cohorte

### 2.1 Edad mediana

Se agregó la función `median_age(df, age_column="edad")` para calcular la mediana de edad de una cohorte clínica. Antes de calcular, la función valida que exista la columna de edad usando `validate_required_columns()`. El resultado se devuelve como `float`, lo que facilita usarlo después en reportes o resúmenes numéricos.

Las pruebas cubren el cálculo correcto de la mediana y el error esperado cuando falta la columna de edad.
