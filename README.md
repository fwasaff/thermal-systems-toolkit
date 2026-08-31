# Thermal Systems Toolkit

Python toolkit for the classical (non-CFD) fluid mechanics and heat transfer
calculations used to design industrial heat recovery systems: pipe sizing,
pump selection, heat exchanger sizing, and thermal storage tank design.

## Contexto — qué es esto realmente

**Este es un registro histórico de lo que sabía hacer *antes* de empezar el
Magíster en Simulación Computacional**, no una demostración de mi nivel
actual. La base física (continuidad, Bernoulli/ecuación general de energía,
Darcy-Weisbach, ε-NTU) es mecánica de fluidos e ingeniería térmica clásica
de pregrado — la misma que enseñaba en los cursos de termofluidos del
instituto. Referencia: Robert L. Mott, *Applied Fluid Mechanics*.

Dos cosas se agregaron *durante* el magíster, y esas sí reflejan lo que
estoy aprendiendo ahora: las **pruebas de verificación** (que encontraron
un bug real de convergencia, corregido con bisección — pensamiento de
Métodos Numéricos aplicado a código viejo) y las **propiedades de fluido
dependientes de temperatura vía CoolProp**. El resto es anterior.

Nació de un proyecto real de consultoría de recuperación de calor
industrial. Los detalles del cliente y las cifras financieras de ese
proyecto **no están incluidos aquí** — este repositorio contiene solo los
métodos de cálculo de propósito general, reutilizables para cualquier
proyecto similar.

## Capacidades — para qué sirve, cuándo usarlo, cuándo no

**Sirve para** diseñar el lado "clásico" de un sistema de recuperación de
calor con líquido:

| Pregunta de ingeniería | Módulo |
|---|---|
| ¿Qué diámetro de tubería, y cuánto se pierde de presión? | `fluid_flow.py` |
| ¿Qué bomba, con qué potencia? | `pumps.py` |
| ¿Qué tan grande el intercambiador de calor? | `heat_exchangers.py` |
| ¿Cuánto calor hay realmente, dado el caudal disponible? | `heat_transfer.py` |
| ¿Qué tamaño de estanque de acumulación? | `storage_tanks.py` |

Ver `examples/ejemplo_recuperacion_calor_generico.py` para los 5 módulos
encadenados en un caso ilustrativo completo (números inventados).

**Úsalo cuando**: necesitas un pre-dimensionamiento rápido y confiable de
un sistema de líquido monofásico, con física de texto verificada, no una
simulación detallada del campo de flujo.

**No lo uses cuando**: necesitas ver qué pasa DENTRO del flujo (perfiles
de velocidad, zonas de recirculación, turbulencia resuelta) — para eso
hace falta CFD de verdad, que es el trabajo en el resto de mi
[portafolio](https://github.com/fwasaff), no este toolkit.

### Límites explícitos (no es letra chica, es lo que hay que saber antes de usarlo)

- Solo flujo **monofásico líquido incompresible** (agua/agua-glicol) en
  tuberías — no gas, no multifásico.
- El régimen transicional (2300 < Re < 4000) es físicamente inestable —
  la física no es exacta ahí: el toolkit avisa con un warning en vez de
  fingir precisión que no tiene.
- Correlaciones de fricción turbulenta válidas para 4000 < Re < 10⁸ y
  10⁻⁶ < rugosidad relativa < 10⁻².
- Estado estacionario — no transientes, no golpe de ariete.
- Geometrías simples (codos, válvulas estándar) — no geometrías 3D
  complejas donde el campo de flujo interno importa.

## Temperature-dependent fluid properties (optional)

Por defecto, cada cálculo usa propiedades fijas del agua (`WATER_RHO`,
`WATER_MU` en `fluid_flow.py`), válidas cerca de 20°C. Un lazo real de
recuperación de calor recorre un rango mucho más amplio — la viscosidad
del agua sola cae más de 4x entre 10°C y 95°C, lo que entra directo en el
número de Reynolds y el factor de fricción. Cuando eso importa, pasa
`temperature_celsius` y las propiedades se buscan en
[CoolProp](http://www.coolprop.org/):

```python
from thermal_toolkit.fluid_flow import pipe_design_summary

d_cold = pipe_design_summary(flow, length, fittings, temperature_celsius=20.0)
d_hot  = pipe_design_summary(flow, length, fittings, temperature_celsius=85.0)
# misma tubería, mismo caudal -- distinta caída de presión, solo por la temperatura
```

Requiere `pip install CoolProp` (ya en `requirements.txt`). Sin ese
argumento, se mantiene el comportamiento original sin dependencia nueva.

## Ejemplo integrado

```bash
python3 examples/ejemplo_recuperacion_calor_generico.py
```

Encadena los 5 módulos para un caso ilustrativo: balance de calor →
intercambiador → tubería (con propiedades reales a la temperatura de
operación) → bomba → estanque de acumulación. Los números son inventados
a propósito — cámbialos por los de tu propio caso.

## Verification

`tests/` verifica la física, no solo que el código corra: límites
analíticos exactos (p. ej. `f = 64/Re` en laminar), acuerdo entre métodos
independientes (Swamee-Jain vs. Colebrook-White), consistencia de la
función inversa (NTU → efectividad → NTU), y que el ejemplo integrado
efectivamente encadena los 5 módulos. Correr esta suite durante un curso
de métodos numéricos del magíster encontró un bug real: el solver de
NTU-desde-efectividad usaba un paso fijo que asumía una pendiente
equivocada cerca de `C_ratio → 1`, devolviendo NTU con ~9% de error en
silencio. Se reemplazó por bisección (convergencia garantizada para una
función monótona) — ver el historial de git para el detalle.

```bash
pip install -r requirements.txt
pip install pytest
pytest tests/ -v   # 15/15 deben pasar
```

## Installation

```bash
pip install -e .
```

## Author

Felipe Wasaff — felipe.wasaff@uchile.cl
