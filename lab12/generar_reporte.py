"""Informe recalculado desde una base elegida, sin JSON propios anteriores."""

import argparse
import json
from pathlib import Path

import duckdb
from pipeline import ROOT, snapshot


def table(rows):
    if not rows:
        return "Sin filas disponibles; no equivale a ausencia clínica.\n"
    cols = list(rows[0])
    return (
        "\n".join(
            [
                "| " + " | ".join(cols) + " |",
                "| " + " | ".join(["---"] * len(cols)) + " |",
            ]
            + [
                "| "
                + " | ".join(
                    "No disponible" if r[c] is None else str(r[c]).replace("|", "/")
                    for c in cols
                )
                + " |"
                for r in rows
            ]
        )
        + "\n"
    )


def render(a, reference=None):
    q = a["queries"]
    vocab = a["counts"]["concept"] > 0
    w = q["ventana"][0]
    migrated = bool(a.get("migration"))
    parts = [
        f"""# Reporte de calidad — Lab 12

Estado de la ejecución: **{a["estado"]}**. Implementación docente con alcance y
limitaciones explícitos; no se certifica un CDM completo ni utilidad clínica.

Ejecución: `{a["run_id"]}`; construcción UTC: {a["created_at"]}.
Consulta UTC: {a["queried_at"]}. Python {a["python"]}; DuckDB {a["duckdb"]}.
Los agregados propios se recalcularon desde esta base, sin leer JSON anteriores.

## Actividades 1–4: conversión, vocabularios y modelo

Ruta manual inicialmente de cuatro tablas, ampliada por migración cuando corresponde, después de
revisar OHDSI. Compatibilidad y alternativa R en README.md. Huellas fuente y
vocabulario en resultados/resultados.json. Diagrama en docs/diagrama_er.md.
Comparación de columnas con DDL oficial v5.4.0 en docs/comparacion_esquema.json;
no certifica tipos, constraints físicos ni conformidad semántica completa.
""",
        table([{"tabla": k, "filas": v} for k, v in a["counts"].items()]),
        table(q["vocabularios"]),
    ]
    parts.append(
        "Vocabulario cargado en esta ejecución; revisar huellas y validación científica.\n"
        if vocab
        else "ATHENA ausente: vocabularios vacíos y mapeo provisional.\n"
    )
    final = a.get("final_audit", {})
    if final:
        parts += [
            "## Cierre técnico de las diez actividades\n",
            "Se cotejó de nuevo el README oficial. Las actividades 1–10 tienen evidencia y resultados en esta entrega; actividad 9 usa el paquete ATHENA real conforme a la instrucción del estudiante. No se afirma acceso interactivo al portal. La rúbrica detallada está en docs/criterios_evaluacion.md.\n",
            "### Corrección final de Visit\n",
            table(final["reglas_visita"]),
            f"Se mapearon {sum(r['changed_rows'] for r in final['reglas_visita'])} visitas, con denominador {a['counts']['visit_occurrence']}. Las clases aún sin mapear se detallan en la tabla Visit; hospice por sí sola no determina el lugar de atención. urgentcare se agrupa en Emergency Room según OHDSI ETL-Synthea: para estudiar urgencias hospitalarias hay que filtrar también la clase fuente. SNF se agrega al tipo institucional no hospitalario, perdiendo granularidad en el estándar pero conservando el origen.\n",
            "### Completitud global y denominadores\n",
            table(final["cobertura_fuente_global"]),
            f"Esta tasa global usa {final['cobertura_fuente_global'][0]['denominador_eventos_fuente']} filas originales de conditions.csv y comprueba si cada una tiene algún destino estándar. Hay {final['cobertura_fuente_global'][0]['sin_destino_estandar']} sin estándar: moverlas al dominio correcto no las convirtió artificialmente en mapeadas. Las tasas por tabla usan únicamente filas de esa tabla; Gender usa personas. Los dominios sin tabla en la ejecución inicial no tenían una tasa estimable.\n",
        ]
    parts += [
        "## Actividad 5: mapeo y fuente\n",
        table(q["ceros"]),
        table([a["missing_source"]]),
        "Cada porcentaje anterior usa filas de su propia tabla como denominador; Gender usa personas. Un código ausente es distinto de un código presente sin mapeo. rejected_domain conserva el archivo de destinos inicialmente separados. Drug no se convirtió.\n",
    ]
    if migrated:
        before = a["migration"]["before"]
        parts += [
            "## Antes y después de las correcciones\n",
            table(before["ceros"]),
            table(
                [
                    {
                        "tabla": t,
                        "antes": before["counts"].get(t, "No cargada"),
                        "despues": a["counts"][t],
                    }
                    for t in [
                        "person",
                        "condition_occurrence",
                        "observation",
                        "measurement",
                    ]
                ]
            ),
            "Gender se complementó con los registros canónicos 8507 (MALE) y 8532 (FEMALE) de la referencia oficial OHDSI EunomiaDatasets/GiBleed_5.3. Es un suplemento explícito e histórico, no parte de la descarga ATHENA original. Su URL y SHA256 están en el manifiesto de migración. Se usó M/F explícito; valores desconocidos permanecen en cero.\n",
            table(a["corrections"]["reconciliacion_clinica"]),
            "No hay pérdida de filas fuente ni rechazo clínico pendiente en esta migración. Se conserva la base anterior. Los eventos sin estándar se mantienen con concepto cero en el dominio conocido; no se inventa una correspondencia. Las tablas de trabajo y el archivo rejected_domain no se suman de nuevo a las tablas clínicas.\n",
            table(a["corrections"]["mediciones_categoricas"]),
            "Los cinco hallazgos de anticuerpos conservan su concepto de detección; no se infirió concentración, unidad ni un resultado adicional.\n",
            "### Auditoría de gingivitis\n",
            table(a["corrections"]["gingivitis"]),
            table(a["corrections"]["gingivitis_temporal"]),
            "### Observation conservadas sin estándar\n",
            table(a["corrections"]["observation_sin_correspondencia"]),
            "El denominador es toda la población sintética (personas distintas), y el numerador personas con un registro dentro de OBSERVATION_PERIOD. Es frecuencia histórica acumulada en datos sintéticos, no prevalencia puntual ni estimación poblacional real. Los eventos repetidos de un paciente no multiplican el numerador. La auditoría compara filas fuente, expansión por mapeo y duplicados exactos; explicación del módulo local y sus límites en docs/correcciones_dominios.md.\n",
        ]
    if not vocab:
        parts.append(
            "Los conceptos cero obedecen a vocabularios no disponibles; no permiten comparar calidad semántica entre dominios.\n"
        )
    audit = a.get("mapping_audit", {})
    if audit:
        parts += [
            "### Inventario de vocabularios cargados\n",
            table(audit["inventario"]),
        ]
        versions = a.get("athena_packages", {}).get("vocabularies", [])
        if versions:
            parts.append(
                table(
                    [
                        r
                        for r in versions
                        if r["vocabulary_id"]
                        in ["SNOMED", "ICD10CM", "RxNorm", "LOINC", "ATC", "None"]
                    ]
                )
            )
        observed = {r["motivo"]: r["eventos"] for r in audit["no_mapeados"]}
        parts.append(
            table(
                [
                    {"motivo": reason, "eventos": observed.get(reason, 0)}
                    for reason in [
                        "sin_codigo_fuente",
                        "codigo_no_presente_en_paquete",
                        "concepto_invalido_D",
                        "concepto_obsoleto_U",
                        "concepto_vigente_sin_destino_condition",
                    ]
                ]
            )
        )
        parts += [
            "### Causas verificadas de ausencia de mapeo\n",
            table(audit["no_mapeados"]),
            table(audit["detalle_no_mapeados"]),
            "La inexistencia se evalúa contra todos los conceptos del paquete, incluidos los inválidos: concept_source_id=0 no demuestra inexistencia. D indica concepto eliminado/inválido; U indica actualizado/obsoleto. No se inventan sustituciones ni se promueve un concepto no estándar a estándar.\n",
            "### Correspondencia con otros dominios y cobertura\n",
            table(audit["fuera_condition"]),
            table(audit["cobertura_otros_dominios"]),
            table(audit["reconciliacion"]),
            (
                "Los destinos separados ya están integrados en sus tablas clínicas. rejected_domain queda como archivo de trazabilidad, no como lista actual de descartes.\n"
                if migrated
                else "Los destinos separados se conservan en staging, pero todavía faltan sus tablas clínicas.\n"
            ),
            table(audit["detalle_exclusiones"]),
            "### Visitas y sexo\n",
            table(audit["visitas_no_mapeadas"]),
            table(audit["sexo_fuente"]),
            (
                "El sexo se corrigió con el suplemento canónico documentado; las clases de visita sin mapeo siguen siendo una limitación del CASE conservado.\n"
                if migrated
                else "Los valores fuente de sexo están presentes; conceptos Gender cero por falta de vocabulario no son datos ausentes. Las clases Visit sin mapeo siguen siendo una limitación del CASE.\n"
            ),
        ]
        parts += [
            "### Dominio del concepto fuente frente a tabla destino\n",
            table(audit["dominio_fuente_sin_mapeo"]),
            (
                "Los eventos de Observation sin Maps to se reubicaron con concepto cero en OBSERVATION. No se interpretan como diagnósticos.\n"
                if migrated
                else "Los eventos de Observation sin Maps to todavía quedan como cero en CONDITION: es una limitación del ETL inicial.\n"
            ),
            table(audit["mapeos_condition_sin_relacion"]),
        ]
    parts.append("## Actividad 6: caracterización actual\n")
    for name in [
        "personas",
        "sexo",
        "nacimiento",
        "observacion",
        "diagnosticos",
        "visitas",
        "tipos_visita",
    ]:
        parts += ["### " + name + "\n", table(q[name])]
    parts += [
        """## Actividad 7: estándar frente a origen

Se elige el código fuente más frecuente por personas distintas. Cada destino
se cuenta por separado: no sumar personas entre destinos. Varios códigos pueden
confluir en un estándar y un código puede tener varios destinos.
""",
        table(q["estandar_origen"]),
    ]
    mapped = [r for r in q["estandar_origen"] if r["condition_concept_id"] is not None]
    if mapped:
        parts += [
            "Diferencias actuales (estándar menos origen):\n",
            table(
                [
                    {
                        "condition_concept_id": r["condition_concept_id"],
                        "concept_name": r["concept_name"],
                        "diferencia_personas": r["personas_estandar"]
                        - r["personas_origen"],
                    }
                    for r in mapped
                ]
            ),
        ]
        parts.append(
            "La consulta usa eventos dentro de OBSERVATION_PERIOD. Si ambos conteos coinciden, no se fuerza una diferencia: se verifica qué códigos fuente contribuyen al mismo estándar.\n"
        )
        if audit:
            parts.append(table(audit["codigos_del_estandar"]))
    else:
        parts.append(
            "Comparación estándar bloqueada: no hay destino Condition disponible. No contar el grupo cero como enfermedad.\n"
        )
    parts += [
        "## Actividad 8: observación\n",
        table(q["ventana"]),
        f"Eventos fuera de ventana: **{w['todos'] - w['dentro']}**.\n",
        "Ventana aproximada inclusiva de primera visita a último fin de visita. No demuestra seguimiento continuo. EXISTS evita multiplicación por períodos. Ignorar cobertura puede alterar numeradores y tiempo en riesgo.\n",
        "## Actividad 9: candidatos para verificar en ATHENA\n",
        "Datos locales: no acreditan búsqueda interactiva en ATHENA. Hijos directos usan min_levels=1 y descendientes excluyen el propio concepto. Una jerarquía vacía no prueba ausencia de hijos.\n",
        table(q["athena"]),
        "## Actividad 10: referencia\n",
    ]
    if final:
        parts += [
            "### Auditoría temporal por dominio\n",
            table(final["fuera_periodo_por_tabla"]),
            table(final["huecos_observacion"]),
            f"La aritmética temporal es coherente, pero primera/última visita no prueba observación continua: {final['huecos_observacion'][0]['personas_hueco_mayor_365']} personas tienen al menos un hueco mayor de 365 días sin visitas registradas. No se usa esta aproximación como tiempo-persona clínicamente validado. Se preservan eventos externos y se excluyen mediante EXISTS en las consultas que requieren cobertura; no se amplió la ventana para ocultarlos.\n",
        ]
    if reference is None:
        parts.append(
            "No se solicitó referencia; no se reutilizó una comparación anterior.\n"
        )
    else:
        parts.append(
            f"Referencia independiente: {reference['dataset']}; ZIP SHA256 `{reference['sha256']}`.\n"
        )
        parts.append(
            "Eunomia es sintética con vocabulario reducido. Se usó el mismo SQL; interpretar diferencias por tamaño, período y vocabulario.\n"
        )
        parts.append(
            "La referencia tiene 28 personas; es demostración, no una población clínica real. Nombres Gender ausentes en su CONCEPT reducido se presentan con los nombres canónicos OHDSI 8507/8532, sin añadir conceptos ni cambiar conteos de esa referencia. Las versiones distintas de vocabulario pueden explicar diferencias de asignación de dominio.\n"
        )
        parts.append(
            table(
                [
                    {
                        "metrica": key,
                        "propia": q[name][0][key],
                        "referencia": reference["queries"][name][0][key],
                    }
                    for name, key in [
                        ("personas", "personas"),
                        ("observacion", "mediana_dias"),
                        ("visitas", "media_visitas"),
                    ]
                ]
            )
        )
        for name in ["sexo", "nacimiento", "diagnosticos", "tipos_visita"]:
            parts += [
                "### Referencia: " + name + "\n",
                table(reference["queries"][name]),
            ]
    if audit:
        parts += [
            "## Relaciones verificadas de los conceptos principales\n",
            table(audit["relaciones_top"]),
            "Verificación local sobre el paquete ATHENA identificado por huellas; enlaces y limitación de acceso web en docs/athena_revision.md. La búsqueda interactiva no pudo certificarse: no hay navegador conectado y el lector web no devuelve el contenido de los conceptos.\n",
            table(audit["dependencias"]),
        ]
    if final:
        parts += [
            "## Auditoría final de temporalidad, duplicación y relaciones\n",
            table(final["temporalidad"]),
            table(final["duplicados_y_traza"]),
            table(final["diccionarios"]),
            table(final["auxiliary_integrity"]),
            "La verificación reproducible de insumos y consultas repetidas está en resultados/reproducibilidad.json. Su alcance es repetición analítica e identidad de archivos, no una nueva generación Synthea con semilla desconocida.\n",
        ]
    parts += [
        "## Validación automática\n",
        table(
            [
                {"comprobacion": k, "discrepancias": v}
                for k, v in a["validation"].items()
            ]
        ),
        """Cero discrepancias no acredita completitud semántica: sin vocabulario parte
de la validación terminológica es vacua. La transición del informe se prueba con
vocabulario artificial aislado, no con ATHENA real.

## Evaluación de las diez actividades

| Actividad | Evaluación |
| --- | --- |
| 1 | Ruta y compatibilidad documentadas |
| 2 | Conversión ejecutada; conteos actuales arriba |
| 3 | Carga e inventario verificados; suplemento Gender identificado por separado |
| 4 | Diagrama y comparación 5.4 conservados; subconjunto docente |
| 5 | Porcentajes y causas cuantificados; límites y denominadores explícitos |
| 6 | Consultas ejecutadas; nombres ausentes no se inventan |
| 7 | Conteos, igualdad y relaciones explicados; frecuencia sintética no extrapolable |
| 8 | Efecto y huecos cuantificados; aproximación no certificada como seguimiento continuo |
| 9 | Verificada en ATHENA descargado; acceso al portal no realizado, limitación permitida |
| 10 | Referencia solo si se solicitó explícitamente |

## Pendientes científicos y técnicos

- Validar seguimiento continuo, huecos y censura; ausencia de registros no implica
  ausencia de enfermedad.
- Revisar situaciones/hallazgos de Synthea y destinos fuera de Condition; confirmar
  la condición frecuente elegida para comparar estándar y origen.
- Completar raza, etnia y tipos/procedencia actualmente cero; validar sexo y visita.
- Verificar jerarquías y tres conceptos en ATHENA, sin sustituir la descarga por Eunomia.
- Ruta R preparada pero no ejecutada; compatibilidad del JAR local no certificada.

Acciones exactas para actividades 3, 7 y 9: README.md. Sin merge a main.
""",
    ]
    return "\n".join(parts)


def generate(db, output, results, reference=None):
    if not db.is_file():
        raise FileNotFoundError(db)
    with duckdb.connect(str(db), read_only=True) as con:
        current = snapshot(con)
    if any(current["validation"].values()):
        raise ValueError("La base no supera validación")
    audit = current["mapping_audit"]
    if (
        any(r["huerfanos"] for r in audit["dependencias"])
        or audit["reconciliacion"][0]["fuente_sin_traza"]
        or audit["mapeos_condition_sin_relacion"][0]["eventos_sin_maps_to_valido"]
    ):
        raise ValueError("Fallo en dependencias, trazabilidad o relaciones de mapeo")
    external = json.loads(reference.read_text()) if reference else None
    content = render(current, external)
    output.parent.mkdir(parents=True, exist_ok=True)
    results.parent.mkdir(parents=True, exist_ok=True)
    results.write_text(json.dumps(current, indent=2, default=str) + "\n")
    output.write_text(content)
    return current


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--output", type=Path, default=ROOT / "reporte_calidad.md")
    p.add_argument("--results", type=Path, default=ROOT / "resultados/resultados.json")
    p.add_argument("--reference", type=Path)
    a = p.parse_args()
    generate(a.db, a.output, a.results, a.reference)
