# Predicción de readmisión hospitalaria a 30 días en adultos con cáncer

## Estado actual y preservación del estudio

### Publicación del 18 de noviembre de 2026

Se publica el estado actual de 02.4 solicitado por el autor, con las tablas y
figuras guardadas de SHAP y calibración. La revisión de publicación no ejecuta
celdas, no reentrena modelos y no recalcula métricas. El SHA-256 de referencia es
`3fca2c3a910740c43a7dabac795c17227180247f789db736c95a01eb2dc5c7be`.
La celda SHAP conserva salidas aunque su contador de ejecución es nulo; no se
interpreta ese contador como prueba de una nueva ejecución. El informe
`docs/publication_audit.json` registra la integridad del archivo y sus salidas.

El estado publicado es posterior a los hashes de las auditorías del 15–16 de
noviembre. Aquellos informes son registros históricos, no una descripción del
contenido actualizado. La copia inicial de 02.4 sigue sin estar disponible para
una comparación exacta. Esta publicación no declara resuelta esa limitación ni
completa la migración OMOP: la carga persistente total y DQD siguen pendientes.

La versión actual local es [02.4_readmission_modeling.ipynb](notebooks/02.4_readmission_modeling.ipynb).
Utiliza **655 pacientes de entrenamiento y 76 eventos**, con corte temporal
`2022-11-27 07:16:42`: de 659 pacientes anteriores al corte, cuatro se excluyen
porque su seguimiento de 30 días cruza ese instante. Los 165 pacientes posteriores
permanecen reservados en ese notebook. La cohorte general sigue siendo de 824.

Esta migración no escribe ni ejecuta 02.4 ni
[02.3](notebooks/Otros/02.3_readmission_modeling.ipynb), y conserva las otras versiones
en `notebooks/Otros/`. Los apartados históricos siguientes describen otra versión
del análisis; sus particiones y métricas no deben atribuirse a 02.4. El antiguo
notebook 02 se encuentra ahora localmente en
[Otros/02_readmission_modeling.ipynb](notebooks/Otros/02_readmission_modeling.ipynb);
esa reubicación ya existía antes de esta tarea.

La [migración independiente](../omop_cdm/README.md) no modifica este estudio ni
recalcula sus modelos. La comparación de datos y de las tres variables derivadas
se ejecuta mediante un script separado. Sus [resultados y limitaciones](../omop_cdm/docs/validation.md)
incluyen el cambio del recuento de diagnósticos al aplicar dominios OMOP.

Las rutas `final_project/data/omop_minimal.duckdb` y
`lab10/data/clinical.duckdb` permanecen operativas; ninguna de sus tablas ni
identificadores se modifica. Las instrucciones de ejecución que siguen son
históricas y no constituyen el procedimiento de esta migración.

El control final detectó que 02.4 cambió durante la sesión, sin que los comandos
de migración lo escribieran. Se conservó su estado local y se documentaron los
dos hashes en el informe; no se afirma igualdad byte por byte con la captura
inicial. Los otros notebooks protegidos y las bases originales sí coinciden.

## Pregunta y alcance

¿La historia clínica de los 180 días anteriores a una hospitalización mejora la predicción de readmisión a 30 días después del alta, por encima de edad, sexo y hospitalizaciones previas? El análisis es **predictivo y exploratorio**, no causal ni apto para uso clínico.

La cohorte y las seis variables están definidas en `sql/` y documentadas en `docs/`. `notebooks/Otros/02_readmission_modeling.ipynb` cuenta la historia completa: lectura de la tabla analítica, controles de calidad, modelos M0/M1/M2, validación cruzada en entrenamiento, búsqueda ligera de Optuna para XGBoost, evaluación final, calibración exploratoria e interpretación SHAP. El notebook de referencia visual se utilizó únicamente para orientar la presentación.

Los datos proceden de **Synthea** y están representados mediante una capa OMOP mínima; no se afirma un mapeo completo a los vocabularios OMOP. El archivo local `final_project/data/omop_minimal.duckdb` debe existir previamente y contener `results.analytic_dataset`. Se abre en modo de solo lectura. Los datos y bases locales no se versionan.

## Entorno y ejecución

El notebook está configurado y ejecutado con **machine_learning_env**, Python **3.14.2**.
Activa el entorno existente:

```bash
conda activate machine_learning_env
python -c "import sys; print(sys.executable)"
```

El ejecutable utilizado es `/home/luis-enrique/miniconda3/envs/machine_learning_env/bin/python`.
En VS Code/Jupyter abre `final_project/notebooks/Otros/02_readmission_modeling.ipynb`, selecciona
**machine_learning_env**, reinicia el kernel y ejecuta todas las celdas. Su identificador de
kernel también es `machine_learning_env`; ya está registrado localmente. No se usa el entorno de `lab02`.

Versiones verificadas: DuckDB 2.0.0, NumPy 2.4.3, pandas 2.3.3, scikit-learn 1.8.0,
XGBoost 3.1.2, Optuna 4.6.0, SHAP 0.50.0 y Matplotlib 3.10.8. La primera tabla del notebook
registra las versiones efectivamente cargadas. La versión de XGBoost se consulta en el módulo
importado, sin exigir que la distribución instalada se llame `xgboost-cpu`.

`requirements.txt` conserva la referencia del entorno anterior con Python 3.13.5; **no describe
machine_learning_env**. No se instalaron ni actualizaron paquetes para esta corrección. Los
resultados siguientes corresponden a la ejecución actual; cambiar versiones de XGBoost u Optuna
puede cambiar el modelo seleccionado y sus métricas, aun conservando la semilla.

Para ejecutar y guardar desde la raíz del repositorio, con el entorno activado:

```bash
python - <<'PYTHON'
from pathlib import Path
import nbformat
from nbclient import NotebookClient

path = Path("final_project/notebooks/Otros/02_readmission_modeling.ipynb").resolve()
notebook = nbformat.read(path, as_version=4)
NotebookClient(
    notebook,
    kernel_name="machine_learning_env",
    timeout=300,
    allow_errors=False,
    record_timing=False,
    resources={"metadata": {"path": str(path.parent)}},
).execute()
nbformat.write(notebook, path)
PYTHON
```

Validación del 26 de octubre de 2026: **17 celdas de código ejecutadas sin errores**, cuatro
figuras guardadas y comprobaciones de cohorte/modelado superadas. La base DuckDB se abrió
en modo de solo lectura y su SHA-256 permaneció intacto. Se corrigieron únicamente la consulta
de versión, la selección del kernel y los textos que conservaban resultados del entorno anterior;
no cambiaron la cohorte, los seis predictores, las particiones ni los modelos.

## Diseño del análisis

Hay **824 pacientes y 85 eventos**. La partición estratificada 80/20 con semilla 42 deja **659 pacientes y 68 eventos en entrenamiento** y **165 pacientes y 17 eventos en prueba**. Todas las variables longitudinales utilizan `[index_admission - 180 días, index_admission)`; la readmisión comienza después de `index_discharge` y dentro de los 30 días siguientes.

- **M0:** regresión logística con edad, sexo y hospitalizaciones previas.
- **M1:** regresión logística con esas tres variables más diagnósticos, medicamentos y mediciones durante los 180 días anteriores.
- **M2 inicial:** XGBoost con las mismas seis variables, 100 árboles, profundidad 2 y parámetros conservadores fijados antes de evaluar prueba.
- **M2 ajustado:** el mismo XGBoost con cinco parámetros elegidos en 20 ensayos de Optuna, optimizando la AUPRC media de cinco pliegues estratificados de entrenamiento.

Cada pipeline ajusta el escalado y la codificación de sexo solo con su subconjunto de ajuste. Los tres modelos iniciales comparten cinco pliegues en entrenamiento. La puntuación de validación del M2 ajustado está afectada por la selección de hiperparámetros sobre esos mismos pliegues; no se presenta como validación independiente. La prueba no interviene en selección, parada temprana ni recalibración.

## Resultados de prueba

| Modelo | AUROC ↑ | AUPRC (precisión media) ↑ | Brier ↓ |
|---|---:|---:|---:|
| M0 | 0.6862 | 0.2142 | **0.0873** |
| M1 | **0.6888** | **0.2615** | 0.0878 |
| M2 inicial | 0.6484 | 0.1658 | 0.0895 |
| M2 ajustado | 0.6494 | 0.2102 | 0.0890 |

En esta ejecución, Optuna seleccionó el ensayo 7: 80 árboles, profundidad 2, tasa de aprendizaje 0,02, `min_child_weight=7` y `reg_lambda=5`. La AUPRC media de selección fue 0,2481 frente a 0,2436 del M2 inicial. M2 ajustado mejoró la AUPRC de prueba y redujo ligeramente el Brier respecto al M2 inicial, pero ambos XGBoost quedaron por debajo de las regresiones logísticas en AUROC y AUPRC. M1 obtiene la mayor discriminación observada y M0 el menor Brier. El notebook contiene las tablas de validación, curvas ROC y precisión–sensibilidad, calibración exploratoria y dos gráficos SHAP de M2 ajustado con sus interpretaciones.

Solo hay **17 eventos de prueba**. No se estimaron intervalos de confianza ni significancias y no existe validación externa. La calibración agrupa pocos eventos y SHAP explica predicciones del modelo, no efectos causales. Los resultados en datos sintéticos no demuestran utilidad clínica.

## Declaración de uso de IA

Se utilizaron asistentes de IA para apoyar programación, documentación y revisión. Las decisiones metodológicas, la interpretación, la validación y la responsabilidad final corresponden al autor.
