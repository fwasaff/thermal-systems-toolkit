"""
Ejemplo integrado: recuperación de calor residual de un compresor de aire
industrial (caso GENÉRICO/ilustrativo -- los números son inventados,
redondos, para mostrar el flujo de diseño completo, no un proyecto real).

Encadena los 5 módulos del toolkit en el orden en que se usarían de
verdad para dimensionar un sistema: cuánto calor hay que mover, con qué
intercambiador, por qué tubería, con qué bomba, y con qué estanque de
acumulación si la demanda no es constante.

Uso:
    python3 examples/ejemplo_recuperacion_calor_generico.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from thermal_toolkit.heat_transfer import calculate_heat_transfer_system
from thermal_toolkit.heat_exchangers import plate_heat_exchanger_design
from thermal_toolkit.fluid_flow import pipe_design_summary
from thermal_toolkit.pumps import total_dynamic_head, pump_power
from thermal_toolkit.storage_tanks import design_thermal_storage_tank


def main():
    print("=" * 70)
    print("EJEMPLO ILUSTRATIVO -- recuperación de calor de un compresor de aire")
    print("(números inventados, no corresponden a ningún proyecto real)")
    print("=" * 70)

    # --- 1. ¿Cuánto calor hay realmente, dado el caudal y el salto de T? ---
    calor = calculate_heat_transfer_system(
        Q_target=500e3,       # objetivo: 500 kW
        flow_rate_m3h=17.2,   # caudal disponible del lado caliente
        delta_T=25.0,         # salto de temperatura de diseño [K]
    )
    print(f"\n[1] Balance de calor")
    print(f"    Caudal másico: {calor['mass_flow_kg_s']:.3f} kg/s")
    print(f"    Calor real alcanzable: {calor['Q_actual_kW']:.1f} kW "
          f"(objetivo: {calor['Q_target_kW']:.1f} kW)")

    # --- 2. Dimensionar el intercambiador para ese calor ---
    Q = calor['Q_actual_W']
    m = calor['mass_flow_kg_s']
    hx = plate_heat_exchanger_design(
        Q=Q, m_hot=m, m_cold=m,
        T_hot_in=90.0, T_hot_out=65.0,   # lado caliente: compresor
        T_cold_in=40.0, T_cold_out=65.0,  # lado frío: agua de proceso
    )
    print(f"\n[2] Intercambiador de placas")
    print(f"    Área requerida: {hx['area_required_m2']:.2f} m²")
    print(f"    NTU: {hx['NTU']:.2f}  ·  Efectividad: {hx['effectiveness']:.3f}")

    # --- 3. Dimensionar la tubería que alimenta el intercambiador ---
    tuberia = pipe_design_summary(
        flow_rate_m3h=17.2, length=25.0,
        fittings={'90_elbow': 4, 'gate_valve_open': 2, 'check_valve': 1},
        material='commercial_steel',
        temperature_celsius=75.0,  # temperatura media del lado caliente
    )
    print(f"\n[3] Tubería (lado caliente, T≈75°C -- usa CoolProp, no la "
          f"constante fija de 20°C)")
    print(f"    Diámetro: DN{tuberia['DN']}  ·  Velocidad: {tuberia['velocity_m_s']:.2f} m/s")
    print(f"    Caída de presión: {tuberia['pressure_drop_total_kPa']:.2f} kPa "
          f"(Re={tuberia['Reynolds']:.0f}, {tuberia['flow_regime']})")

    # --- 4. Bomba: altura dinámica total y potencia ---
    tdh = total_dynamic_head(
        static_head=3.0, friction_loss=tuberia['pressure_drop_total_kPa'] * 1000 / (9810),
        minor_losses=0.5, equipment_losses=2.0,
    )
    potencia = pump_power(flow=17.2, head=tdh, efficiency=65.0)
    print(f"\n[4] Bomba")
    print(f"    Altura dinámica total (TDH): {tdh:.2f} m")
    print(f"    Potencia al eje: {potencia['shaft_power_kW']:.2f} kW "
          f"(eficiencia asumida 65%)")

    # --- 5. Estanque de acumulación (si la demanda no es constante) ---
    tanque = design_thermal_storage_tank(
        power=Q, storage_time_hours=0.5, delta_T=25.0,
    )
    print(f"\n[5] Estanque de acumulación (30 min de autonomía)")
    print(f"    Volumen: {tanque.volume:.2f} m³")
    print(f"    Dimensiones: {tanque.diameter:.2f} m x {tanque.height:.2f} m")

    print("\n" + "=" * 70)
    print("Los 5 módulos encadenados: calor -> intercambiador -> tubería "
          "-> bomba -> estanque. Cambia los números arriba para tu propio caso.")
    print("=" * 70)


if __name__ == "__main__":
    main()
