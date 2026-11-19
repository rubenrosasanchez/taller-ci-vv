"""Genera la matriz VCRM a partir de los requisitos y de las evidencias de prueba.

Uso:
    python tools/vcrm.py                 # escribe reports/vcrm.md
    python tools/vcrm.py --strict        # además falla si algún requisito "Test" no está verificado

Estados posibles de cada requisito:
    VERIFICADO        todas sus pruebas pasan
    FALLA             al menos una de sus pruebas falla
    SIN EVIDENCIA     método "Test" pero ninguna prueba lo referencia
    PENDIENTE (<m>)   método distinto de Test: requiere actividad manual (inspección, análisis...)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent


def construir_matriz(requisitos: list[dict], evidencias: dict) -> list[dict]:
    filas = []
    for req in requisitos:
        pruebas = {
            nodo: ev["resultado"]
            for nodo, ev in evidencias.items()
            if req["id"] in ev["requisitos"]
        }
        if req["metodo"] != "Test":
            estado = f"PENDIENTE ({req['metodo']})"
        elif not pruebas:
            estado = "SIN EVIDENCIA"
        elif any(r == "failed" for r in pruebas.values()):
            estado = "FALLA"
        else:
            estado = "VERIFICADO"
        filas.append({**req, "pruebas": pruebas, "estado": estado})
    return filas


def a_markdown(filas: list[dict]) -> str:
    total_test = [f for f in filas if f["metodo"] == "Test"]
    ok = sum(f["estado"] == "VERIFICADO" for f in total_test)
    lineas = [
        "## Matriz de verificación (VCRM)",
        "",
        f"**{ok} de {len(total_test)}** requisitos con método *Test* verificados automáticamente.",
        "",
        "| ID | Requisito | Método | Pruebas (pasan/total) | Estado |",
        "|---|---|---|---|---|",
    ]
    for f in filas:
        n = len(f["pruebas"])
        pasan = sum(r == "passed" for r in f["pruebas"].values())
        estado = f"**{f['estado']}**" if f["estado"] in ("FALLA", "SIN EVIDENCIA") else f["estado"]
        lineas.append(
            f"| {f['id']} | {f['texto']} | {f['metodo']} | {pasan}/{n} | {estado} |"
        )
    fallidas = [(f["id"], nodo) for f in filas for nodo, r in f["pruebas"].items() if r == "failed"]
    if fallidas:
        lineas += ["", "### Pruebas que fallan", ""]
        lineas += [f"- `{nodo}` &rarr; {rid}" for rid, nodo in fallidas]
    return "\n".join(lineas) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--requisitos", default=RAIZ / "requisitos.yml", type=Path)
    p.add_argument("--evidencias", default=RAIZ / "reports" / "evidencias.json", type=Path)
    p.add_argument("--out", default=RAIZ / "reports" / "vcrm.md", type=Path)
    p.add_argument("--strict", action="store_true", help="falla si algún requisito Test no está VERIFICADO")
    args = p.parse_args()

    requisitos = yaml.safe_load(args.requisitos.read_text(encoding="utf-8"))
    evidencias = json.loads(args.evidencias.read_text(encoding="utf-8")) if args.evidencias.exists() else {}

    filas = construir_matriz(requisitos, evidencias)
    md = a_markdown(filas)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(md, encoding="utf-8")
    print(md)

    if args.strict and any(f["metodo"] == "Test" and f["estado"] != "VERIFICADO" for f in filas):
        print("Modo estricto: hay requisitos sin verificar.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
