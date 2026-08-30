# Lab 05 — clinlab

## 1. Esqueleto del paquete

### 1.1 Objetivo

Esta actividad inicia la conversión del análisis de Lab02 en un paquete Python
instalable llamado `clinlab`. Por ahora solo se prepara la estructura mínima:
un layout `src/`, metadatos del proyecto y herramientas de verificación.

La meta de esta fase es demostrar que el paquete puede instalarse en modo
editable y que Python lo puede importar desde el repositorio y desde otra ruta
del sistema.

### 1.2 Estructura

La estructura creada para esta actividad es:

```text
lab05/
├── README.md
└── clinlab/
    ├── pyproject.toml
    ├── src/
    │   └── clinlab/
    │       └── __init__.py
    ├── tests/
    └── notebooks/
```

El archivo `pyproject.toml` declara el paquete, la versión, la dependencia
principal (`pandas`) y las dependencias de desarrollo. El directorio `src/`
ayuda a comprobar que el código instalado es el que se importa, en lugar de
depender accidentalmente del directorio de trabajo.

### 1.3 Instalación editable

La instalación editable permite desarrollar el paquete sin reinstalarlo después
de cada cambio. En esta fase se usa además el extra `dev` para instalar las
herramientas que se usarán en pruebas, estilo y tipado.

Comando:

```bash
cd lab05/clinlab
python -m pip install -e ".[dev]"
```

Resultado:

```text
Successfully installed clinlab-0.1.0
```

Interpretación:

La instalación editable quedó activa. Las dependencias principales y de
desarrollo quedaron disponibles en el entorno usado para el laboratorio.

### 1.4 Verificación de importación

Primero se verifica el import desde el proyecto. Esto confirma que el paquete
queda visible para Python después de la instalación editable.

Comando:

```bash
python -c "import clinlab; print(clinlab.__version__)"
```

Resultado:

```text
0.1.0
```

Interpretación:

El paquete se importó correctamente desde el proyecto y expuso la versión
definida en `clinlab.__version__`.

También se verifica desde `/tmp`, fuera del repositorio. Esta comprobación es
importante porque reduce el riesgo de que el import funcione solo por estar
parados dentro de la carpeta del código fuente.

Comando:

```bash
cd /tmp
python -c "import clinlab; print(clinlab.__version__)"
```

Resultado:

```text
0.1.0
```

Interpretación:

El import también funcionó fuera del repositorio. Esto confirma que Python está
resolviendo el paquete instalado, no solo una carpeta local del directorio de
trabajo.

### 1.5 Revisión con ruff

`ruff` se usará para revisar estilo y errores estáticos simples en el código
del paquete y en las pruebas. En esta actividad todavía no hay tests clínicos,
pero se deja incluido `tests/` para mantener el flujo del paquete completo.

Comando:

```bash
cd lab05/clinlab
ruff check src tests
```

Resultado:

```text
All checks passed!
```

Interpretación:

La estructura inicial no presenta problemas detectados por `ruff`.

### 1.6 Revisión con mypy

`mypy` se usará para revisar tipos estáticos en el código de `src/`. En esta
fase solo existe el módulo inicial del paquete, así que la verificación sirve
como línea base para el resto del laboratorio.

Comando:

```bash
cd lab05/clinlab
mypy src
```

Resultado:

```text
Success: no issues found in 1 source file
```

Interpretación:

La línea base del paquete pasa la revisión de tipos.

### 1.7 Pruebas con pytest

`pytest` se usará en fases posteriores para comprobar el comportamiento de las
funciones extraídas del análisis original.

Comando previsto:

```bash
cd lab05/clinlab
pytest
```

Evidencia:

Pendiente.

### 1.8 Cobertura

La cobertura se revisará cuando existan pruebas reales sobre la lógica clínica.

Comando previsto:

```bash
cd lab05/clinlab
pytest --cov=clinlab
```

Evidencia:

Pendiente.

### 1.9 Pre-commit

`pre-commit` se configurará más adelante para ejecutar verificaciones antes de
aceptar un commit.

Evidencia de commit rechazado por pre-commit:

Pendiente.

### 1.10 CI

La integración continua se configurará en una fase posterior para ejecutar las
verificaciones en GitHub Actions.

Evidencia de CI en verde:

Pendiente.

## 2. Extracción de lógica del notebook

### 2.1 Criterio de extracción

Se revisó `lab02/analisis_pacientes.ipynb` buscando operaciones que no dependan
directamente de archivos ni de la sesión de Jupyter. La lógica seleccionada
recibe `DataFrame`, `Series` o valores explícitos y devuelve resultados que
pueden probarse con datos pequeños.

No se extrajo lectura de CSV, escritura de archivos ni visualización. Esas
partes pertenecen al flujo de I/O del notebook, no al núcleo reutilizable del
paquete.

### 2.2 Funciones extraídas

Las piezas identificadas en el notebook fueron:

1. Porcentaje de valores faltantes por columna.
   - Entrada: un `DataFrame`.
   - Devuelve: una `Series` con porcentajes redondeados.
   - Proviene de la auditoría de calidad donde se usa `isna().mean() * 100`.
   - Merece extraerse porque se repite como chequeo básico para varias tablas.

2. Conteo de IDs duplicados.
   - Entrada: una `Series` de identificadores.
   - Devuelve: un entero con duplicados después de la primera aparición.
   - Proviene de la revisión de `patients["Id"].duplicated().sum()`.
   - Merece extraerse porque valida unicidad antes de merges `many_to_one`.

3. Detección de valores no numéricos en `VALUE`.
   - Entrada: una `Series` con valores clínicos como texto.
   - Devuelve: una máscara booleana.
   - Proviene de `pd.to_numeric(..., errors="coerce")` sobre observaciones.
   - Merece extraerse porque separa valores categóricos válidos de mediciones numéricas.

4. Unión de encuentros con fechas de paciente.
   - Entrada: `encounters` y `patients`.
   - Devuelve: un `DataFrame` con `START`, `BIRTHDATE` y `DEATHDATE`.
   - Proviene del bloque de coherencia temporal.
   - Merece extraerse porque prepara una validación clínica clara sin depender de archivos.

5. Detección de encuentros antes del nacimiento o después del día de muerte.
   - Entrada: el `DataFrame` ya unido con fechas.
   - Devuelve: máscaras booleanas.
   - Proviene de las comparaciones temporales del notebook.
   - Merece extraerse porque evita mezclar la decisión clínica con `print` y permite probar el caso especial de `DEATHDATE` con precisión de día.

6. Joins `left` con validación de cardinalidad y auditoría.
   - Entrada: dos `DataFrame`, columnas de unión y cardinalidad esperada.
   - Devuelve: el resultado con columna `_merge`.
   - Proviene de las uniones `observations` -> `encounters` -> `patients`.
   - Merece extraerse porque la cardinalidad es parte de la calidad de datos, no un detalle accidental del notebook.

7. Transformaciones clínicas de observaciones.
   - Entrada: tablas de pacientes, encuentros u observaciones.
   - Devuelve: conteos, tablas resumidas, formato ancho o resumen de valores implausibles.
   - Proviene de las actividades de preguntas clínicas y formato ancho.
   - Merece extraerse porque esas operaciones son deterministas y se pueden validar con muestras pequeñas.

Funciones implementadas:

- `missing_percentages`
- `memory_reduction_percent`
- `left_join_with_audit`
- `merge_indicator_percent`
- `duplicated_id_count`
- `non_numeric_mask`
- `encounters_with_patient_dates`
- `before_birth_mask`
- `after_death_day_mask`
- `unique_patients_by_ethnicity_gender`
- `encounters_per_patient`
- `top_observation_codes`
- `systolic_blood_pressure_values`
- `patients_with_minimum_measurements`
- `observations_to_daily_wide`
- `repeated_daily_measurements`
- `implausible_value_summary`

### 2.3 Separación entre I/O y lógica

El notebook original mezcla lectura de archivos, limpieza, validación,
agregaciones y presentación de resultados. En el paquete, las funciones no leen
CSV, no escriben salidas y no imprimen. Cada función recibe datos ya cargados y
devuelve un resultado explícito.

Esta separación permite probar la lógica con tablas pequeñas creadas en memoria.
También deja al notebook como orquestador: carga datos, llama funciones y
presenta resultados.

### 2.4 Verificación estática

Comando:

```bash
cd lab05/clinlab
ruff check src
```

Resultado:

```text
All checks passed!
```

Comando:

```bash
cd lab05/clinlab
mypy src
```

Resultado:

```text
Success: no issues found in 4 source files
```

## 3. Primeras pruebas

### 3.1 Estrategia

Las primeras pruebas cubren funciones pequeñas y directamente derivadas del
notebook: porcentajes de faltantes, reducción de memoria, conteo de IDs
duplicados y detección de valores no numéricos en `VALUE`.

Los datos se construyen dentro de cada test para mantener la prueba enfocada en
la lógica. No se usan CSV, notebooks ni fixtures globales en esta fase.

### 3.2 Ciclo rojo → verde

La prueba seleccionada fue
`test_non_numeric_mask_treats_blank_strings_as_missing`. El comportamiento
esperado es que cadenas vacías o formadas solo por espacios se traten como
faltantes, no como valores clínicos categóricos no numéricos.

Inicialmente falló porque `non_numeric_mask` usaba `values.notna()`: para pandas,
`""` y `"   "` no son nulos, así que quedaban marcados como valores no
numéricos. El cambio mínimo fue normalizar la serie como texto, aplicar
`str.strip()` y exigir contenido real antes de marcar un valor como no numérico.

Evidencia roja:

```text
evidence/pytest_red.txt
```

Evidencia verde:

```text
evidence/pytest_green.txt
```

### 3.3 Pruebas iniciales

Se agregaron pruebas para:

- `missing_percentages`: porcentajes por columna y `DataFrame` vacío.
- `memory_reduction_percent`: cálculo normal y error con línea base no positiva.
- `duplicated_id_count`: IDs repetidos y IDs únicos.
- `non_numeric_mask`: texto clínico no numérico, números, nulos y cadenas en blanco.

Comando:

```bash
cd lab05/clinlab
pytest -v
```

Resultado:

```text
8 passed
```

## 4. Fixture maliciosa

### 4.1 Diseño

Se agregó una fixture pequeña llamada `malicious_cohort` para probar reglas de
calidad sin depender de los CSV completos. El objetivo es tener un conjunto de
datos que se pueda leer visualmente en pocos segundos y que active casos límite
presentes en el análisis de Lab02.

Usar una tabla sintética permite aislar la lógica: cada prueba controla el dato
de entrada y verifica una sola intención. Los CSV completos sirven para análisis,
pero son demasiado grandes y ruidosos para explicar por qué falla una función.

### 4.2 Casos incluidos

La fixture contiene seis filas sintéticas con columnas alineadas con Lab02:
`Id`, `PATIENT`, `BIRTHDATE`, `DEATHDATE`, `START`, `DATE`, `CODE`,
`DESCRIPTION`, `VALUE` y `UNITS`. También incluye `person_id` como alias explícito
para probar duplicados de persona sin cambiar las funciones del paquete.

Casos cubiertos:

- un paciente adulto con presión sistólica plausible;
- un paciente menor de edad;
- un `person_id` duplicado;
- una visita anterior a `BIRTHDATE`;
- valores faltantes en `VALUE` y `UNITS`;
- una presión sistólica centinela de `0 mmHg`, fisiológicamente implausible.

### 4.3 Uso en pruebas

La fixture se usa en pruebas de validación y resumen clínico. Los tests llaman
funciones de `clinlab` para revisar duplicados, coherencia temporal, faltantes y
valores implausibles, sin leer archivos ni depender del notebook.

Comando usado para la suite inicial con la fixture:

```bash
cd lab05/clinlab
pytest -v
```

## 5. Validación clínica externa

### 5.1 Ecuación CKD-EPI 2021

Se agregó `calculate_egfr_2021` para estimar eGFR con la ecuación CKD-EPI 2021
basada en creatinina. La función usa creatinina sérica estandarizada en mg/dL,
edad en años y sexo (`female` o `male`). Devuelve eGFR en mL/min/1.73 m^2.

No se usa raza. Esto corresponde a la versión CKD-EPI 2021 recomendada para
estimar eGFR con creatinina sin variable racial.

### 5.2 Tabla parametrizada

No basta con probar que la función corre: una fórmula clínica puede ejecutarse y
aun así estar mal por constantes, exponentes, unidades o factores condicionales.
Por eso se agregó una tabla parametrizada con más de ocho combinaciones clínicas.

Los valores esperados se calcularon de forma independiente a partir de la
ecuación publicada por la National Kidney Foundation, no llamando a la función
del paquete.

### 5.3 Casos extremos

La tabla cubre mujeres y hombres, adultos jóvenes y mayores, creatinina baja,
valores alrededor de rangos habituales, creatinina alta, eGFR alto y función
renal muy reducida. Las comparaciones usan `pytest.approx` con tolerancia
relativa explícita para evitar comparar floats con igualdad exacta.

También se agregaron pruebas para entradas inválidas: creatinina igual a cero,
edad igual a cero y sexo fuera de `female`/`male`.

### 5.4 Referencia clínica

National Kidney Foundation.
CKD-EPI Creatinine Equation (2021).

## 6. Hallazgos de Lab02 como tests permanentes

### 6.1 DataFrame vacío

Lab02 calcula auditorías por tabla completa. Para una tabla vacía, el test fija
que `missing_percentages` devuelva una serie vacía en lugar de fallar o inventar
columnas.

### 6.2 Columna completa de NaN

Lab02 distingue valores faltantes de valores textuales no convertibles en
`VALUE`. El test fija que una columna completamente faltante no se marque como
no numérica.

### 6.3 Coherencia temporal

Lab02 revisa encuentros anteriores al nacimiento. El test fija que
`before_birth_mask` detecte una visita cuyo `START` precede `BIRTHDATE`.

### 6.4 IDs duplicados y cardinalidad

Lab02 valida IDs antes de merges `many_to_one`. El test fija que los duplicados
se cuenten y que un join con cardinalidad violada lance `MergeError` en lugar de
multiplicar filas silenciosamente.

### 6.5 Valores centinela

Lab02 revisa valores fisiológicamente implausibles con límites amplios. El test
fija que una presión sistólica de `0 mmHg` se detecte como valor centinela fuera
de rango.

## 7. Cobertura como diagnóstico

### 7.1 Cobertura inicial

La primera medición se ejecutó antes de agregar tests nuevos:

```bash
cd lab05/clinlab
pytest --cov=clinlab --cov-report=term-missing
```

Resultado registrado en `evidence/coverage_initial.txt`: cobertura total de
75%. La medición mostró que todavía había funciones reales sin prueba directa,
especialmente en resúmenes clínicos y validación temporal.

### 7.2 Líneas no cubiertas

El reporte inicial marcó estas líneas como no cubiertas:

- `src/clinlab/clinical.py`: 10, 20, 29, 44-50, 60-61, 94-95.
- `src/clinlab/data.py`: 56.
- `src/clinlab/validation.py`: 29-36, 56-61.

Esas líneas correspondían a comportamiento útil: conteos clínicos, conversión de
presión sistólica, conteo de mediciones, repetidos diarios, porcentaje de merge,
preparación de fechas y detección de encuentros después del día de muerte.

### 7.3 Tests añadidos

Se agregó `tests/test_clinical_summaries.py` para cubrir comportamientos reales
sin depender de CSV: conteos por etnia y sexo, encuentros por paciente, códigos
de observación frecuentes, presión sistólica, cobertura longitudinal,
mediciones repetidas, auditoría de merge y validación temporal.

No se añadieron asserts solo para tocar líneas. Cada test fija una decisión que
sale del análisis de Lab02 o de la forma en que esas funciones quedaron
extraídas en el paquete.

### 7.4 Cobertura final

La medición final quedó registrada en `evidence/coverage_final.txt`:

```text
TOTAL 87 statements, 0 missing, 100% coverage
```

La cobertura final supera el umbral de 80% definido para esta actividad.

### 7.5 Qué queda sin probar y por qué

- No quedan líneas de `src/clinlab` sin cubrir según el reporte final.
- Todavía no hay pruebas con CSV reales porque esta fase busca probar lógica pura
  con datos pequeños y controlados.
- En una versión posterior convendría agregar pruebas de integración sobre una
  muestra de archivos, separadas de los tests unitarios actuales.

## 8. Automatización con pre-commit

### 8.1 Hooks configurados

Se configuró `pre-commit` con tres hooks dentro de
`lab05/clinlab/.pre-commit-config.yaml`:

- `ruff`: revisa errores de lint en `src` y `tests`.
- `ruff-format`: verifica que el formato de `src` y `tests` sea consistente.
- `mypy`: ejecuta revisión de tipos sobre `src`.

Los hooks se ejecutan con las herramientas disponibles en el entorno del
proyecto para mantener la configuración simple y compatible con este laboratorio.

### 8.2 Instalación

El hook debe instalarse en cada clon del repositorio, porque vive en la carpeta
local `.git/hooks` y no se versiona como parte del historial.

Comando usado desde la raíz del repositorio:

```bash
pre-commit install --config lab05/clinlab/.pre-commit-config.yaml
```

### 8.3 Commit rechazado

Para demostrar el rechazo se agregó temporalmente un `import os` no utilizado en
`src/clinlab/clinical.py`. Ruff lo detectó como `F401` y el commit no entró al
historial.

La salida real del rechazo quedó guardada en:

```text
evidence/precommit_rejected.txt
```

### 8.4 Corrección y validación

Después del rechazo se eliminó únicamente el import deliberado. Se volvieron a
ejecutar Ruff, mypy y pytest, y luego `pre-commit run --all-files` con la misma
configuración.

La evidencia de pre-commit en verde quedó guardada en:

```text
evidence/precommit_passed.txt
```

Con el error corregido, el commit fue aceptado por los hooks.
