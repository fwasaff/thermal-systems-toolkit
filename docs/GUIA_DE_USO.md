# Guía de uso — Thermal Systems Toolkit

> Para Nilton (y para mí mismo dentro de un año, cuando se me haya olvidado por qué escribí esto así).

## 1. Para qué sirve

Cuando hicimos el proyecto de recuperación de calor juntos, resolvimos todo a mano
con las ecuaciones clásicas de mecánica de fluidos: continuidad, Bernoulli/ecuación
general de energía, pérdidas de carga, factor de fricción — las mismas que yo
enseñaba en los cursos de mecánica de fluidos en el instituto, del libro de
Robert Mott. Este toolkit es **esas mismas ecuaciones, ya escritas, probadas y
listas para reutilizar** — no hay que volver a plantear las fórmulas desde cero
cada vez que llega un proyecto parecido.

## 2. Qué nos permite hacer

Cuatro cosas concretas, cada una en su propio módulo:

| Pregunta que responde | Módulo | Función principal |
|---|---|---|
| "¿Qué diámetro de tubería necesito, y cuánto se pierde de presión?" | `fluid_flow` | `pipe_design_summary()` |
| "¿Qué bomba necesito para vencer la altura y las pérdidas del sistema?" | `pumps` | funciones de altura dinámica |
| "¿Qué tan grande tiene que ser el intercambiador de calor?" | `heat_exchangers` | `effectiveness_ntu_counterflow()`, dimensionamiento LMTD |
| "¿Qué tamaño de estanque necesito para el acumulador térmico?" | `storage_tanks` | dimensionamiento de estanque |

Es una calculadora de ingeniería reutilizable, no un simulador — resuelve el
mismo tipo de cálculo puntual que haríamos a mano o en una planilla, pero
verificado y sin que cada quien lo reescriba desde cero.

## 3. La teoría detrás de cada módulo

### `fluid_flow.py` — mecánica de fluidos clásica

- **Continuidad**: $Q = A \cdot v$ — de ahí sale el diámetro óptimo de tubería
  dada una velocidad objetivo (`optimal_pipe_diameter`).
- **Número de Reynolds**: $Re = \rho v D / \mu$ — determina si el flujo es
  laminar, transicional o turbulento.
- **Factor de fricción**:
  - Laminar ($Re < 2300$): $f = 64/Re$ — resultado exacto (Hagen-Poiseuille),
    no una aproximación.
  - Turbulento ($Re > 4000$): Swamee-Jain (explícita) o Colebrook-White
    (implícita, se resuelve por iteración de punto fijo).
  - Transicional ($2300 \le Re \le 4000$): el factor de fricción es
    físicamente inestable en este rango — el código no finge precisión ahí,
    devuelve una advertencia y usa el valor conservador de Colebrook-White en
    $Re=4000$ como cota superior segura.
- **Darcy-Weisbach**: $\Delta P = f \cdot (L/D) \cdot (\rho v^2/2)$ — la
  ecuación central de pérdida de carga por fricción.
- **Pérdidas menores**: $\Delta P = K \cdot (\rho v^2/2)$ por cada accesorio
  (codos, válvulas, entradas/salidas), con los coeficientes $K$ estándar de
  la literatura.

### `heat_exchangers.py` — dimensionamiento de intercambiadores

- **LMTD** (diferencia de temperatura media logarítmica) para contraflujo.
- **Método ε-NTU**: la efectividad $\varepsilon$ como función del número de
  unidades de transferencia $NTU = UA/C_{min}$ y la razón de capacidades
  $C_r = C_{min}/C_{max}$:
  $$\varepsilon = \frac{1 - e^{-NTU(1-C_r)}}{1 - C_r \, e^{-NTU(1-C_r)}}$$
  con el caso especial $C_r=1 \Rightarrow \varepsilon = NTU/(1+NTU)$.

### `heat_transfer.py`, `pumps.py`, `storage_tanks.py`

Balances de energía y de altura estándar (ecuación general de energía con
pérdidas, dimensionamiento de estanque por capacidad térmica) — la misma
familia de ecuaciones, aplicadas a cada equipo.

## 4. Cómo se usa — ejemplo completo

```bash
git clone https://github.com/fwasaff/thermal-systems-toolkit.git
cd thermal-systems-toolkit
pip install -r requirements.txt
pip install -e .
```

```python
from thermal_toolkit.fluid_flow import pipe_design_summary

# Ejemplo genérico: dimensionar la tubería de un sistema de recuperación
# de calor con 3 codos de 90° y una válvula de compuerta abierta
resultado = pipe_design_summary(
    flow_rate_m3h=10.0,
    length=15.0,
    fittings={'90_elbow': 3, 'gate_valve_open': 1},
    material='commercial_steel',
)

print(f"Diámetro nominal: DN{resultado['DN']}")
print(f"Velocidad real: {resultado['velocity_m_s']:.2f} m/s")
print(f"Régimen: {resultado['flow_regime']}")
print(f"Caída de presión total: {resultado['pressure_drop_total_kPa']:.2f} kPa")
```

Salida real (corrida al escribir esta guía):

```
Diámetro nominal: DN40
Velocidad real: 2.11 m/s
Régimen: turbulent
Caída de presión total: 26.14 kPa
```

Cada función tiene ejemplos ejecutables en su propio docstring (`help(pipe_design_summary)`).

## 5. Verificación — ¿realmente funciona?

No basta con que el código corra sin error — hay que comprobar que la física
es correcta. `tests/test_verification.py` hace exactamente eso:

- **Casos límite exactos**: $f_{laminar} = 64/Re$ debe cumplirse a precisión
  de máquina (es un resultado analítico, no una aproximación).
- **Acuerdo entre métodos independientes**: Swamee-Jain y Colebrook-White son
  dos formulaciones distintas de la misma física — si difieren más de un 2%,
  algo está mal en una de las dos. Verificado: concuerdan.
- **Conservación de masa**: el diámetro que devuelve `optimal_pipe_diameter`
  debe satisfacer $Q = A \cdot v$ exactamente.
- **Consistencia de la función inversa**: NTU → efectividad → NTU debe
  devolver el NTU original.

**Este último test encontró un bug real.** La función que calcula NTU a
partir de la efectividad usaba una actualización de paso fijo
(`NTU = NTU - error * 0.5`) que asume una pendiente constante — funciona
bien cuando $C_r$ es chico, pero cerca de $C_r \to 1$ la curva de
efectividad es más plana de lo que ese paso fijo asume, y el resultado
quedaba ~9% errado sin ningún aviso. Se reemplazó por **bisección**, que no
depende de la pendiente local y converge siempre que la función sea
monótona (que lo es: más área de transferencia nunca puede *reducir* el
calor transferido).

```bash
pytest tests/ -v   # 9/9 deben pasar
```

### Convergencia del Colebrook-White (iteración de punto fijo)

El código itera hasta 10 veces, deteniéndose antes si el cambio es menor a
$10^{-6}$. Se probó el número real de iteraciones necesarias en distintos
escenarios:

| Caso | Iteraciones para converger |
|---|---|
| $Re=4000$ (borde turbulento), acero comercial | 5 |
| $Re=10^5$, acero comercial | 3 |
| $Re=10^8$ (límite superior de validez), acero comercial | 2 |
| $Re=10^5$, concreto (muy rugoso) | 3 |
| $Re=10^5$, PVC (muy liso), tubería grande | 4 |

El peor caso (5 iteraciones) queda muy por debajo del límite de 10 — margen
razonable, no es un límite ajustado que pueda fallar en un caso límite no
probado.

## 6. Cruce con lo que hemos visto en el magíster

Esto lo agrego porque tiene sentido revisarlo con el mismo rigor que
estamos aprendiendo ahora, no solo con lo que sabíamos antes:

**Métodos Numéricos (Barrientos, referencia Burden & Faires)**: el
Colebrook-White es literalmente el tipo de ecuación implícita que se resuelve
por iteración de punto fijo — la tabla de arriba es exactamente el tipo de
análisis de convergencia del curso. El bug del NTU y su arreglo con
bisección es un ejemplo real (no de libro) de por qué un método con garantía
de convergencia (bisección, para una función monótona) es preferible a un
método ad-hoc sin análisis de estabilidad detrás.

**Modelación Matemática (Donoso/Rojas)**: la metodología del curso —
plantear el modelo desde leyes de conservación y balances antes de resolver
— es la misma que sigue este toolkit (continuidad, balance de energía). Con
un límite honesto: este toolkit se queda en el nivel algebraico/EDO (fórmulas
cerradas, correlaciones empíricas), no resuelve EDPs — no hay campo de
velocidades ni discretización espacial. Para eso está el CFD que estoy
aprendiendo ahora en Mecánica de Fluidos Computacional (Galarce), que es un
proyecto aparte.

**Programación Avanzada (Pizarro)**: el toolkit sigue buenas prácticas
básicas — type hints, docstrings estilo NumPy con ejemplos ejecutables,
separación modular por dominio físico. **Punto honesto que falta**: las
funciones trabajan con un valor a la vez (`float`), no con arreglos —
justo el anti-patrón que el curso de Pizarro señala explícitamente
("no podemos darnos el lujo de escribir `for i in range(N)`"). Para el uso
real (dimensionar UNA tubería, UN intercambiador a la vez) esto no es un
problema — no hay miles de puntos que vectorizar. Si algún día lo usamos
para barrer muchos escenarios a la vez (ej. sensibilidad sobre 1000
combinaciones de diámetro/caudal), ahí sí valdría la pena vectorizar con
NumPy en vez de hacer un loop de Python por fuera.

## 7. Alcance — cuándo usarlo y cuándo no

**Sirve para**: flujo de líquido monofásico incompresible (agua, agua-glicol),
en régimen permanente, en tuberías — dimensionamiento de sistemas de
recuperación de calor industrial similares al que hicimos juntos.

**No sirve para**: flujo de gas, multifásico, geometrías 3D complejas,
transientes (golpe de ariete), o cualquier caso donde importe el campo de
velocidades interno, no solo la caída de presión global. Para eso hace falta
CFD de verdad — otra herramienta, no esta.
