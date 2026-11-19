"""Pruebas del BMS. Cada prueba declara qué requisito verifica con @pytest.mark.req."""

import pytest

from bms import Lectura, Modo, estado_de_carga, evaluar


def lectura(v=3.8, n=4, temperatura=25.0, corriente=5.0):
    """Construye una lectura con n celdas iguales a v voltios."""
    return Lectura(tensiones_celda=(v,) * n, temperatura=temperatura, corriente=corriente)


# --- REQ-01: estado de carga -------------------------------------------------

@pytest.mark.req("REQ-01")
@pytest.mark.parametrize(
    "v, soc_esperado",
    [(3.0, 0.0), (3.6, 50.0), (4.2, 100.0)],
)
def test_soc_interpolacion_lineal(v, soc_esperado):
    assert estado_de_carga((v, v, v, v)) == pytest.approx(soc_esperado)


@pytest.mark.req("REQ-01")
def test_soc_saturado_en_0_y_100():
    assert estado_de_carga((2.9,) * 4) == 0.0
    assert estado_de_carga((4.3,) * 4) == 100.0


# --- REQ-02: lecturas imposibles ---------------------------------------------

@pytest.mark.req("REQ-02")
@pytest.mark.parametrize(
    "l",
    [
        Lectura(tensiones_celda=(3.8, -0.1, 3.8), temperatura=25),
        Lectura(tensiones_celda=(3.8, 5.1, 3.8), temperatura=25),
        Lectura(tensiones_celda=(3.8, 3.8, 3.8), temperatura=130),
        Lectura(tensiones_celda=(), temperatura=25),
    ],
)
def test_rechaza_lecturas_fuera_de_rango(l):
    with pytest.raises(ValueError):
        evaluar(l)


# --- REQ-03: sobretemperatura ------------------------------------------------

@pytest.mark.req("REQ-03")
def test_sobretemperatura_provoca_fault():
    estado = evaluar(lectura(temperatura=61))
    assert estado.modo == Modo.FAULT
    assert "SOBRETEMPERATURA" in estado.motivos


@pytest.mark.req("REQ-03")
def test_temperatura_limite_no_es_fault():
    assert evaluar(lectura(temperatura=60)).modo == Modo.NORMAL


# --- REQ-04: subtensión ------------------------------------------------------

@pytest.mark.req("REQ-04")
def test_una_celda_baja_provoca_fault():
    l = Lectura(tensiones_celda=(3.8, 3.8, 2.95, 3.8), temperatura=25)
    estado = evaluar(l)
    assert estado.modo == Modo.FAULT
    assert "SUBTENSION" in estado.motivos


# --- REQ-05: retorno a casa --------------------------------------------------

@pytest.mark.req("REQ-05")
def test_bateria_baja_ordena_retorno():
    # 3.2 V -> SoC = 16,7 %
    assert evaluar(lectura(v=3.2)).modo == Modo.RETURN_TO_HOME


@pytest.mark.req("REQ-05")
def test_fallo_tiene_prioridad_sobre_retorno():
    assert evaluar(lectura(v=3.2, temperatura=70)).modo == Modo.FAULT


# --- REQ-06: balanceo --------------------------------------------------------

@pytest.mark.req("REQ-06")
def test_desequilibrio_activa_balanceo():
    l = Lectura(tensiones_celda=(3.80, 3.80, 3.65, 3.80), temperatura=25)
    assert evaluar(l).balanceo is True


@pytest.mark.req("REQ-06")
def test_celdas_equilibradas_no_balancean():
    l = Lectura(tensiones_celda=(3.80, 3.78, 3.75, 3.80), temperatura=25)
    assert evaluar(l).balanceo is False


# --- REQ-07: sobrecorriente -> lo escribís vosotros en el Paso 3 -------------
