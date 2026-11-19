"""Recoge qué requisito verifica cada prueba y su resultado.

Al terminar la sesión escribe reports/evidencias.json, que tools/vcrm.py
convierte en la matriz VCRM (Verification Cross-Reference Matrix).
"""

import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
_evidencias: dict[str, dict] = {}


def pytest_configure(config):
    config.addinivalue_line("markers", "req(id): requisito que verifica la prueba")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    resultado = yield
    informe = resultado.get_result()
    # Fase "call" = ejecución de la prueba; si falla el setup también cuenta como fallo
    if informe.when == "call" or (informe.when == "setup" and informe.outcome != "passed"):
        _evidencias[item.nodeid] = {
            "requisitos": [m.args[0] for m in item.iter_markers(name="req")],
            "resultado": informe.outcome,  # passed | failed | skipped
        }


def pytest_sessionfinish(session, exitstatus):
    salida = RAIZ / "reports"
    salida.mkdir(exist_ok=True)
    (salida / "evidencias.json").write_text(
        json.dumps(_evidencias, indent=2, ensure_ascii=False), encoding="utf-8"
    )
