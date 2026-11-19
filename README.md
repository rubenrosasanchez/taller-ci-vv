# Taller: Integración Continua como verificación continua

Sistema de ejemplo: el **BMS (Battery Management System) de un dron de inspección**.
Cada vez que subáis código, GitHub Actions instalará el proyecto, ejecutará las pruebas
y generará automáticamente la **matriz VCRM** que relaciona requisitos y evidencias.

## Qué necesitáis

1. Una cuenta de GitHub (gratuita).
2. Un navegador. `git` y Python 3.10+ son opcionales.

## Estructura del repositorio

| Ruta | Qué es | Equivalente en V&V |
|---|---|---|
| `requisitos.yml` | Requisitos del BMS y método de verificación previsto | Especificación + columna "método" de la VCRM |
| `src/bms/battery.py` | Implementación del BMS | Elemento del sistema a verificar |
| `tests/test_bms.py` | Pruebas, cada una marcada con `@pytest.mark.req("REQ-xx")` | Acciones de verificación |
| `tests/conftest.py` | Recoge qué requisito cubre cada prueba y su resultado | Registro de evidencias |
| `tools/vcrm.py` | Genera `reports/vcrm.md` | Matriz VCRM |
| `.github/workflows/ci.yml` | El pipeline de integración continua | Procedimiento de verificación automatizado |

## Paso 1 — Subir el repositorio a GitHub y ver el primer pipeline (15 min)

1. En GitHub: **+ → New repository**, nombre `taller-ci-vv`, **público**, sin README ni .gitignore.
2. Subid el **contenido** de esta carpeta (no la carpeta en sí):
   - Con git: `git init -b main && git add . && git commit -m "Repositorio de partida"`,
     después `git remote add origin https://github.com/USUARIO/taller-ci-vv.git` y `git push -u origin main`.
   - Solo navegador: enlace **uploading an existing file**, arrastrad todo el contenido y **Commit changes**.
     En macOS la carpeta `.github` está oculta (`Cmd + Mayús + .` en Finder para verla).
3. Comprobad que en GitHub aparece `.github/workflows/ci.yml`. Si no: **Add file → Create new file**,
   nombre `.github/workflows/ci.yml` y pegad su contenido.
4. Id a la pestaña **Actions**. Veréis una ejecución en marcha: espera ~30 s.
5. Abrid la ejecución. En la página de resumen aparece la **Matriz de verificación (VCRM)**.
6. Responded: ¿cuántos requisitos están verificados? ¿Por qué REQ-07 dice `SIN EVIDENCIA`? ¿Y REQ-08?

## Paso 2 — Romper el sistema a propósito (10 min)

1. Abrid `src/bms/battery.py` y pulsad el lápiz para editar (o la tecla `.` para abrir el editor web).
2. Cambiad `T_MAX_OPERACION = 60.0` por `T_MAX_OPERACION = 70.0`.
3. Haced **Commit changes** directamente en `main`.
4. Id a **Actions**: el pipeline sale en **rojo**. Abrid la VCRM.
5. Responded: ¿qué requisitos fallan? ¿Por qué un solo cambio rompe **dos** requisitos?
6. Deshaced el cambio y comprobad que vuelve a verde.

## Paso 3 — Añadir un requisito con pruebas primero (20 min)

REQ-07: *si la corriente de descarga supera 30 A en valor absoluto, el BMS pasará a modo FAULT.*

1. **Primero la prueba.** Al final de `tests/test_bms.py` añadid al menos dos pruebas marcadas con
   `@pytest.mark.req("REQ-07")`: una con 31 A (debe dar `Modo.FAULT` y el motivo `"SOBRECORRIENTE"`)
   y otra en el límite, 30 A (no debe ser FAULT). Usad la función auxiliar `lectura(corriente=...)`.
2. Haced commit. El pipeline debe salir **rojo**: la prueba describe algo que el sistema aún no hace.
3. **Después la implementación.** En `battery.py` añadid la constante `I_MAX_DESCARGA = 30.0` y la
   comprobación en `evaluar()` donde está el comentario de REQ-07.
4. Haced commit. Pipeline **verde** y REQ-07 `VERIFICADO` en la VCRM.

## Paso 4 — Que nadie pueda romper `main` (15 min)

1. **Settings → Branches → Add branch ruleset** (o *Add rule*) sobre `main`:
   activad *Require a pull request before merging* y *Require status checks to pass*,
   seleccionando el check **Pruebas y matriz VCRM**.
2. Cread una rama, introducid un fallo y abrid una **pull request**.
3. Comprobad que GitHub no deja hacer *merge* mientras el check esté en rojo.

## Paso 5 — Verificar no es validar (debate, 10 min)

Todas las pruebas pasan: el BMS cumple su especificación. Pero pensad en este escenario:

> El dron está a 3 km de la base, con viento en contra de 40 km/h y a 2 °C. El BMS ordena volver a casa al 20 %.

- ¿Llegará? ¿Algún test del repositorio puede responder a esto?
- ¿Es un problema de **verificación** (el sistema no cumple el requisito) o de **validación** (el requisito no responde a la necesidad)?
- Proponed **una actividad de validación** (simulación operacional, prueba de campo, revisión con operadores…) y añadidla a `requisitos.yml` como un nuevo requisito con método `Demostracion` o `Analisis`.

## Retos extra

- Ejecutad la VCRM en **modo estricto** (`python tools/vcrm.py --strict`) en el pipeline: ¿qué pasa con REQ-08?
- Añadid una **matriz** de versiones de Python (3.10, 3.12, 3.13) con `strategy.matrix`.
- Medid la **cobertura** con `pytest-cov` y publicadla en el resumen.
- Añadid el *badge* del pipeline al principio de este README:
  `![CI](https://github.com/<usuario>/<repo>/actions/workflows/ci.yml/badge.svg)`

## Trabajar en local (opcional)

```bash
pip install -r requirements.txt
pytest                      # ejecuta las pruebas
python tools/vcrm.py        # genera reports/vcrm.md
```
