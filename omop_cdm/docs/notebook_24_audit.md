# Verificación forense del notebook 02.4

Hash inicial: `15a515fb86bea687abe4809c75e94509d88163a05c65c7e68d1c38c39d30d3a3`; hash actual: `c7e863db914575105c4b77a124297473d195c752f49489f9979e0c1c771fc93a`.
Tamaño inicial: 1947610 bytes; actual: 2597958 bytes. El hash actual coincide con el cierre de la auditoría anterior.

## Límite de la comparación

02.4 es un archivo sin rastrear y no tiene historial propio en Git. Se buscaron copias en el repositorio, temporales accesibles, historial y Backups de VS Code, y en todos los objetos Git (incluidos no alcanzables). No se localizó una copia cuyo contenido corresponda al hash inicial.

Un hash no permite reconstruir el contenido. Quitar la última celda SHAP produce un candidato de 1947570 bytes y hash `da72e47e839f5edc9f60bc4f28d4d400c2bbf0a49ac13284e50cd287e30aa6f5`, que NO coincide con el inicial. No se utiliza ese candidato como versión anterior ni se escribe al disco.

| Categoría | Comparación exacta frente al estado inicial |
|---|---|
| Python | No determinable sin la copia inicial |
| Markdown | No determinable sin la copia inicial |
| Resultados y gráficos | No determinable sin la copia inicial |
| Metadatos Jupyter | No determinable sin la copia inicial |

## Inspección estática del estado actual

La última celda (índice 59) importa SHAP, clona los pipelines M1 + FE y M2 + FE, llama `.fit(X_shap, y_shap)` sobre 655 pacientes de entrenamiento y calcula explicaciones y comprobaciones de reconstrucción. Contiene tablas y figuras guardadas. No se ejecutó esa celda. Sin el estado inicial no puede probarse que esta sea la única adición ni descartarse otro cambio científico.

La referencia 02.3 se compara por ID de celda en `notebook_24_audit.json`; es otra versión del análisis, no el estado anterior de 02.4. Sus diferencias no demuestran cuándo ni quién modificó 02.4.

## Consecuencia y decisión

**Puerta científica bloqueada:** no se modifica la implementación ETL ni se inicia una carga mientras no pueda verificarse el contenido inicial de 02.4. Esto no demuestra un error científico; impide certificar su ausencia. Se necesita una copia de 02.4 con SHA-256 inicial `15a515...d3a3`, o una revisión explícita del cambio que establezca una nueva referencia autorizada.

El notebook se conserva sin restaurar, sobrescribir ni ejecutar. Las consultas de auditoría de datos y almacenamiento continúan de forma no destructiva.
