"""Sistema de gestión de batería (BMS) de un dron de inspección.

Módulo de ejemplo para el taller de Integración Continua y V&V.
Cada regla de negocio está etiquetada con el requisito que implementa
(ver ``requisitos.yml``), para que la trazabilidad sea explícita.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# ---------------------------------------------------------------------------
# Parámetros de diseño (unidades: V, °C, A, %)
# ---------------------------------------------------------------------------
V_CELDA_VACIA = 3.0          # V  -> 0 % de carga                 (REQ-01)
V_CELDA_LLENA = 4.2          # V  -> 100 % de carga               (REQ-01)

V_MIN_FISICA = 0.0           # V  rango físico admisible          (REQ-02)
V_MAX_FISICA = 5.0           # V
T_MIN_FISICA = -40.0         # °C
T_MAX_FISICA = 125.0         # °C

T_MAX_OPERACION = 60.0       # °C sobretemperatura -> FAULT       (REQ-03)
V_MIN_CELDA = 3.0            # V  subtensión de celda -> FAULT    (REQ-04)
SOC_RETORNO = 20.0           # %  por debajo -> RETURN_TO_HOME    (REQ-05)
DESEQUILIBRIO_MAX = 0.10     # V  diferencia máx. entre celdas    (REQ-06)


class Modo(str, Enum):
    """Modo de operación que el BMS comunica al controlador de vuelo."""

    NORMAL = "NORMAL"
    RETURN_TO_HOME = "RETURN_TO_HOME"
    FAULT = "FAULT"


@dataclass(frozen=True)
class Lectura:
    """Lectura instantánea de los sensores de la batería.

    Atributos:
        tensiones_celda: tensión de cada celda, en voltios (V).
        temperatura: temperatura del pack, en grados Celsius (°C).
        corriente: corriente de descarga, en amperios (A).
    """

    tensiones_celda: tuple[float, ...]
    temperatura: float
    corriente: float = 0.0


@dataclass(frozen=True)
class Estado:
    """Resultado de evaluar una lectura."""

    modo: Modo
    soc: float                       # %
    balanceo: bool
    motivos: tuple[str, ...] = field(default_factory=tuple)


def estado_de_carga(tensiones_celda: tuple[float, ...]) -> float:
    """Calcula el estado de carga (SoC, %) a partir de la tensión media de celda.

    REQ-01: interpolación lineal entre V_CELDA_VACIA (0 %) y V_CELDA_LLENA
    (100 %), saturada al intervalo [0, 100].
    """
    media = sum(tensiones_celda) / len(tensiones_celda)
    soc = (media - V_CELDA_VACIA) / (V_CELDA_LLENA - V_CELDA_VACIA) * 100.0
    return max(0.0, min(100.0, soc))


def validar(lectura: Lectura) -> None:
    """Rechaza lecturas físicamente imposibles (REQ-02).

    Lanza ValueError si no hay celdas, si alguna tensión está fuera de
    [V_MIN_FISICA, V_MAX_FISICA] V o si la temperatura está fuera de
    [T_MIN_FISICA, T_MAX_FISICA] °C.
    """
    if not lectura.tensiones_celda:
        raise ValueError("La lectura no contiene celdas")
    for v in lectura.tensiones_celda:
        if not V_MIN_FISICA <= v <= V_MAX_FISICA:
            raise ValueError(f"Tensión fuera de rango físico: {v} V")
    if not T_MIN_FISICA <= lectura.temperatura <= T_MAX_FISICA:
        raise ValueError(f"Temperatura fuera de rango físico: {lectura.temperatura} °C")


def evaluar(lectura: Lectura) -> Estado:
    """Evalúa una lectura y decide el modo de operación del dron.

    Prioridad: FAULT > RETURN_TO_HOME > NORMAL.
    """
    validar(lectura)                                            # REQ-02

    soc = estado_de_carga(lectura.tensiones_celda)              # REQ-01
    motivos: list[str] = []

    if lectura.temperatura > T_MAX_OPERACION:                   # REQ-03
        motivos.append("SOBRETEMPERATURA")

    if min(lectura.tensiones_celda) < V_MIN_CELDA:              # REQ-04
        motivos.append("SUBTENSION")

    # REQ-07 (sobrecorriente) -> pendiente de implementar en el taller

    diferencia = max(lectura.tensiones_celda) - min(lectura.tensiones_celda)
    balanceo = diferencia > DESEQUILIBRIO_MAX                   # REQ-06

    if motivos:
        modo = Modo.FAULT
    elif soc < SOC_RETORNO:                                     # REQ-05
        modo = Modo.RETURN_TO_HOME
        motivos.append("BATERIA_BAJA")
    else:
        modo = Modo.NORMAL

    return Estado(modo=modo, soc=round(soc, 1), balanceo=balanceo, motivos=tuple(motivos))
