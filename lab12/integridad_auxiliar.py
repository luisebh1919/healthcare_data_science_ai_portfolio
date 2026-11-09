"""Comprueba referencias de diccionarios y extensiones realmente presentes."""


def audit(con):
    relations = {
        "concept_synonym": ["concept_id", "language_concept_id"],
        "drug_strength": [
            "drug_concept_id",
            "ingredient_concept_id",
            "amount_unit_concept_id",
            "numerator_unit_concept_id",
            "denominator_unit_concept_id",
        ],
        "pack_content": ["pack_concept_id", "drug_concept_id"],
        "concept_metadata": ["concept_id"],
        "concept_relationship_metadata": ["concept_id_1", "concept_id_2"],
        "vocabulary": ["vocabulary_concept_id"],
        "domain": ["domain_concept_id"],
        "concept_class": ["concept_class_concept_id"],
        "relationship": ["relationship_concept_id"],
    }
    rows = []
    tables = {
        r[0].lower()
        for r in con.execute(
            "SELECT table_name FROM information_schema.tables"
        ).fetchall()
    }
    for table, columns in relations.items():
        if table not in tables:
            continue
        actual = {r[0].lower() for r in con.execute(f"DESCRIBE {table}").fetchall()}
        for column in columns:
            if column not in actual:
                continue
            n = con.execute(
                f"SELECT count(*) FROM {table} r WHERE r.{column} IS NOT NULL AND NOT EXISTS (SELECT 1 FROM concept c WHERE c.concept_id=try_cast(r.{column} AS BIGINT))"
            ).fetchone()[0]
            rows.append({"control": table + "." + column + "_fk", "discrepancias": n})
    rows.append(
        {
            "control": "concept_pk",
            "discrepancias": con.execute(
                "SELECT count(*)-count(DISTINCT concept_id) FROM concept"
            ).fetchone()[0],
        }
    )
    return rows
