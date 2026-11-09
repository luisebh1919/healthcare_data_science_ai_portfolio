"""Extrae evidencia de reglas sintéticas, nunca registros clínicos."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from pipeline import ROOT

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("jar", type=Path)
    a = p.parse_args()
    result = {
        "jar_sha256": hashlib.sha256(a.jar.read_bytes()).hexdigest(),
        "limitacion": "No se demostró que este JAR y sus parámetros/semilla generaran los CSV disponibles.",
        "modules": {},
    }
    with zipfile.ZipFile(a.jar) as z:
        for name in [
            "modules/wellness_encounters.json",
            "modules/dental_and_oral_examination.json",
        ]:
            raw = z.read(name)
            d = json.loads(raw)
            states = {
                k: v
                for k, v in d["states"].items()
                if "66383009" in json.dumps(v)
                or "Gingivitis" in json.dumps(v)
                or k in ["Dental Referral?", "Refer to Dentist"]
            }
            result["modules"][name] = {
                "sha256": hashlib.sha256(raw).hexdigest(),
                "states": states,
            }
    (ROOT / "docs/gingivitis_generador.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    )
