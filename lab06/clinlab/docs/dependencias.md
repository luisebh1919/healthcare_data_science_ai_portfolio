# Dependencias y lockfile

El proyecto usa `uv.lock` para fijar versiones exactas y hacer reproducible el entorno.

## Dependencias transitivas

1. `numpy`
   - No está declarada directamente en `pyproject.toml`.
   - Se instala porque `pandas` depende de `numpy`.

2. `python-dateutil`
   - No está declarada directamente.
   - Se instala porque `pandas` depende de `python-dateutil`.

3. `coverage`
   - No está declarada directamente.
   - Se instala porque `pytest-cov` depende de `coverage`.

El árbol de dependencias se verificó con:

```bash
uv tree
