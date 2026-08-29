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
