# Laboratorio 02 — Análisis de un dataset de pacientes con presupuesto de memoria

## Curso

Ciencia de Datos Aplicada en Biomedicina y en la Industria Farmacéutica/de la Salud: De la Academia a la Industria. Universidad Nacional Autónoma de México (UNAM), Doctorado en Ciencias Biomédicas, semestre 2027-1.

## Datos

Los datos fueron generados con **Synthea** utilizando una población de 20,000 pacientes sintéticos y exportación en formato CSV.

```bash
java -jar synthea-with-dependencies.jar \
  -p 20000 \
  --exporter.csv.export=true \
  --exporter.fhir.export=false \
  --exporter.baseDirectory=output
```

Los principales archivos utilizados fueron:

* `patients.csv`
* `encounters.csv`
* `observations.csv`

El archivo `observations.csv` contiene aproximadamente **17.3 millones de filas**.

## Reproducción

El análisis completo se encuentra en:

`analisis_pacientes.ipynb`

El notebook incluye carga y optimización de tipos, auditoría de calidad, validación de cardinalidades, análisis clínico, formato ancho, procesamiento por lotes y comparación entre pandas, Polars y PySpark.

## Optimización de memoria

La carga inicial de `observations.csv` ocupó aproximadamente **9960.77 MB**. Mediante tipos categóricos, fechas explícitas y almacenamiento `string[pyarrow]`, el consumo se redujo a **704.18 MB**, equivalente a una reducción de **92.93%**.

## Comparación de herramientas

| Herramienta | Tiempo pipeline completo (s) | Memoria muestra 1M filas (MB) | Resultado clínico | Principal dificultad        |
| ----------- | ---------------------------: | ----------------------------: | ----------------- | --------------------------- |
| pandas      |                        18.69 |                        189.27 | Coincide          | Mayor consumo de memoria    |
| Polars      |                         4.77 |                         49.08 | Coincide          | API diferente a pandas      |
| PySpark     |                         7.74 |    No comparable directamente | Coincide          | Inicialización de Spark/JVM |

Los tres motores reprodujeron una media de **59.22 encuentros por paciente**, una mediana de **36** y **22,793 pacientes** con al menos tres mediciones de presión sistólica.

## Conclusión

Para este volumen y una computadora individual, **Polars fue la opción más eficiente**. pandas continúa siendo práctico para análisis pequeños o medianos, mientras que PySpark cobra mayor sentido cuando los datos o el procesamiento necesitan distribuirse entre varias máquinas.
