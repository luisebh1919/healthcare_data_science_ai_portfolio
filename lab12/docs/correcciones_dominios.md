> Registro histórico de una etapa anterior. Para el estado definitivo usar ../README.md y ../reporte_calidad.md; Visit fue corregido posteriormente.

# Correcciones de sexo, dominios y auditoría de gingivitis

Se conservó intacta omop_athena.duckdb como antes. Se copió a omop_corregido.duckdb
y se aplicaron dos migraciones transaccionales: integrar destinos estándar ya
verificados y luego reubicar conceptos sin estándar en su dominio fuente conocido.
No se repitió la carga de los CSV ni el ETL completo. Ambas bases son locales e
ignoradas por Git. El proyecto final permanece intacto, sin merge.

## Gender: correspondencia documentada, no imputación

M se asignó a 8507 (MALE), F a 8532 (FEMALE), únicamente tras importar sus registros
CONCEPT canónicos desde [OHDSI EunomiaDatasets/GiBleed_5.3](https://github.com/OHDSI/EunomiaDatasets/blob/main/datasets/GiBleed/GiBleed_5.3.zip).
También se conservó la fila VOCABULARY de Gender y sus metadatos disponibles.
Los dos registros son suplemento oficial histórico, no parte del paquete ATHENA
2026 original; URL y SHA256 se registran en el manifiesto de migración.
La identidad de los conceptos se contrastó con [OHDSI OMOP-Queries](https://github.com/OHDSI/OMOP-Queries/blob/master/md/Person.md)
y la documentación oficial [Capr](https://ohdsi.github.io/Capr/reference/genderConcepts.html).
No se crearon fechas, IDs ni nombres arbitrarios. F: 11446; M: 11405; desconocidos: 0.
Se preservan los valores fuente; no se infiere identidad de género ni se rellenan
categorías desconocidas. El total CONCEPT aumenta en dos conceptos estándar.

## Integración y denominadores

| Campo de tabla | Antes: sin mapear / denominador | Después: sin mapear / denominador |
| --- | --- | --- |
| gender_concept_id | 22851/22851 (100%) | 0/22851 (0%) |
| condition_concept_id | 11435/399864 (2.8597223%) | 2497/390926 (0.6387398%) |
| observation_concept_id | Tabla no cargada; porcentaje no estimable | 8938/439868 (2.0319732%) |
| measurement_concept_id | Tabla no cargada; porcentaje no estimable | 0/5 (0%) |
| visit_concept_id | 77229/1353311 (5.7066705%) | 77229/1353311 (5.7066705%) |

Los denominadores clínicos son filas de cada tabla, no pacientes. Gender usa
personas (una fila por person_id). Un denominador inexistente no equivale a cero
sin mapear. Visit no se corrigió en esta tarea.

Se integraron los 430930 Observation y cinco Measurement ya mapeados en staging.
Adicionalmente se trasladaron 8938 registros de dominio fuente Observation que
antes estaban en CONDITION con concepto cero. Mantienen observation_concept_id=0
y su concepto/código fuente; conocer el dominio no autoriza asignar un estándar.
La reducción del porcentaje de ceros de CONDITION refleja sobre todo un cambio
de denominador y dominio, no nuevos mapeos clínicos. Los 11435 eventos sin estándar
siguen siendo 11435, ahora distribuidos en sus tablas correspondientes.

La suma es exacta: 390926 CONDITION + 439868 OBSERVATION + 5 MEASUREMENT = 830799
filas fuente. clinical_lineage enlaza cada origen con su tabla e ID de destino;
no hay fuentes sin destino, trazas duplicadas ni descartes pendientes. Se conserva
rejected_domain como archivo histórico: no se debe sumar a las tablas clínicas.
Los cinco Measurement corresponden a 4178483 (Toxoplasma gondii antibody detected),
código fuente SNOMED 428915008, en cinco personas. El concepto expresa detección;
no hay concentración ni unidad en conditions.csv y no se inventaron esos campos.

No se perdieron filas fuente; persisten limitaciones semánticas: 2393 eventos con
dos conceptos inválidos D, 104 con conceptos Condition vigentes sin Maps to y
8938 con conceptos Observation vigentes sin Maps to. Los valores y fechas STOP
que no tienen campo directo en esas tablas se conservan en staging y se recuperan
por la trazabilidad. Los tipos/procedencia permanecen cero. La fecha de medición se
toma de START del hallazgo fuente, no se afirma que sea la toma de muestra.

## Gingivitis: frecuencia histórica, no prevalencia puntual

4281516 (Gingivitis), SNOMED 66383009, tiene Maps to vigente a sí mismo. El código
fuente contribuye a un único estándar; no hay expansión uno-a-varios en estos datos.
Se verificaron 61993 filas fuente y 61993 transformadas, con 18515 personas en la
fuente. Dentro de OBSERVATION_PERIOD: 61962 eventos y 18512 personas distintas.
El denominador es toda la población sintética: 22851 personas, incluidas fallecidas
y de múltiples edades y períodos. La proporción es 18512/22851 = 81.0117719%.
No se presenta como prevalencia puntual, riesgo de incidencia ni prevalencia real.

Pruebas agregadas: cero grupos duplicados exactos fuente y destino; cero grupos
con igual paciente/inicio o paciente/encuentro; cero eventos con solapamiento
estricto de intervalos en el mismo paciente. Fechas adyacentes no se clasifican
como solapamiento. Las múltiples filas por paciente no multiplican el numerador:
todas las consultas epidemiológicas usan COUNT(DISTINCT person_id).

Se inspeccionó el JAR local. wellness_encounters.json contiene una transición con
probabilidad 0.25 hacia Gingivitis cuando se alcanza Refer to Dentist, después de
la rama para mayores de seis años. Es probabilidad condicional de una transición,
no prevalencia de la población ni probabilidad universal por visita. El módulo
dental contempla resolución de la condición; la repetición a lo largo de historias
extensas puede explicar una frecuencia acumulada elevada. Es una inferencia, no
una demostración causal del 81%. La evidencia y hashes del JAR/módulos están en
gingivitis_generador.json. No se conoce la semilla ni se demostró que este JAR
exacto generara los CSV disponibles. Lo verificable es que la frecuencia alta ya
estaba en los datos fuente y no fue creada por el mapeo o los joins.

## Reproducción incremental

Para una salida nueva, sin sobrescribir la original:

```bash
python3 lab12/corregir_dominios.py --source lab12/local/omop_athena.duckdb --output lab12/local/otra_copia.duckdb --gender-reference /tmp/lab12-eunomia/datasets/GiBleed/GiBleed_5.3.zip
python3 lab12/reubicar_no_mapeados.py --db lab12/local/otra_copia.duckdb
python3 lab12/generar_reporte.py --db lab12/local/otra_copia.duckdb --reference lab12/resultados/referencia_resultados.json
LAB12_DB=lab12/local/otra_copia.duckdb python3 -m unittest discover -s lab12/tests -v
```

El ZIP de la referencia es oficial, debe verificarse con la huella del manifiesto
y no subirse a Git. La base actual ya está corregida: para consultar su estado
usar directamente omop_corregido.duckdb. Los scripts rechazan migraciones repetidas.
Las seis tablas clínicas se contrastaron con las columnas del DDL oficial 5.4.0.
No se afirma conformidad completa con todo OMOP ni se inventó una migración a CDM 6.

## Pendientes científicos

Validar interpretación de las situaciones/hallazgos y del gran acumulado de
gingivitis; continuidad de observación, huecos y censura; procedencia y significado
temporal de los cinco hallazgos categóricos; raza/etnia y tipos cero. Continúan sin
mapeo cinco clases de visita. Falta contraste interactivo de los tres conceptos
principales en ATHENA, por el bloqueo de navegador documentado previamente.
