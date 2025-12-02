# CMPC Heat Recovery System - Complete Engineering Project

## Project Overview

**Client:** Papeles Cordillera S.A. (CMPC Puente Alto)  
**Location:** Región Metropolitana, Chile  
**Engineer:** Felipe Wasaff  
**Company:** Leycero SpA (Consultant)  
**Date:** December 2024

Complete industrial heat recovery system design capturing waste heat from 
6 air compressors (1,200 kW installed) to preheat industrial water.

## Key Results

- **Heat Recovered:** 622 kW (design capacity)
- **System Efficiency:** 96%
- **Annual Energy Saved:** 4,976 MWh/year
- **Investment:** $46.3M CLP
- **Payback Period:** 28 months
- **NPV (10 years):** $104.2M CLP
- **IRR:** 43%
- **CO2 Avoided:** 1,172 ton/year

## Project Structure
```
cmpc_project/
├── 01_compressor_analysis.py      # Heat source characterization
├── 02_piping_network_design.py    # Hydraulic network design
├── 03_pump_selection.py           # Circulation pump sizing
├── 04_storage_tank_design.py      # Thermal storage design
├── 05_heat_exchanger_design.py    # Heat transfer equipment
├── 06_system_integration.py       # Complete system integration
├── data/                          # Input data files
└── output/                        # Generated reports & diagrams
```

## Technical Highlights

### Heat Sources
- 6× Industrial air compressors
- Total capacity: 948 kW thermal
- Operating mode: 5 units + 1 backup
- Design point: 80% probability operation

### Piping Network
- Material: ASTM A53 Schedule 40 carbon steel
- Insulation: 50mm mineral wool + aluminum jacket
- Main header: DN80, 15m length
- Branch lines: DN25-DN40, 50m total
- Pressure drop: 15.2 kPa total

### Circulation Pumps
- Configuration: Distributed (1 per compressor)
- Manufacturer: Grundfos TPE3 series
- Total power: 2.18 kW active
- Design head: 7.1 m

### Thermal Storage
- Volume: 1.64 m³ (15 min storage)
- Dimensions: Ø920mm × H2,450mm
- Stratification: Ri = 26.7 (excellent)
- Heat loss: 146 W
- Energy capacity: 11.4 MJ

### Heat Exchanger
- Type: Gasketed plate heat exchanger
- Model: Alfa Laval CB30
- Area: 3.6 m² (12 plates)
- Duty: 622 kW
- Effectiveness: 78.6%
- U coefficient: 4,200 W/(m²·K)

## Methodology

This project demonstrates professional thermal system design methodology:

1. **Heat Source Analysis:** Detailed compressor characterization and operating scenarios
2. **Hydraulic Design:** Complete piping network with pressure drop calculations
3. **Equipment Selection:** Pump curves, NPSH verification, efficiency analysis
4. **Thermal Storage:** Stratification analysis, energy capacity, heat loss
5. **Heat Transfer:** HX sizing with LMTD method, effectiveness-NTU
6. **System Integration:** Energy balance, control strategy, ROI analysis

## Key Features

✅ **Modular Design:** Each component independently designed and validated  
✅ **Energy Balance:** Complete verification with <1% error  
✅ **Financial Analysis:** Detailed CAPEX/OPEX with NPV and IRR  
✅ **P&ID Diagram:** Professional system layout with instrumentation  
✅ **Operating Procedures:** Startup, normal operation, shutdown sequences  
✅ **Environmental Impact:** Carbon footprint reduction quantified  

## Implementation Recommendations

**Priority:** HIGH - Excellent payback (<3 years)

**Phased Approach:**
1. **Phase 1:** Install 3 pumps on units 1, 2, 4 (60% capacity)
2. **Phase 2:** Complete with remaining pumps (100% capacity)
3. **Phase 3:** Add VFDs for optimization (future enhancement)

**Risk Level:** LOW - Proven technology, standard components

## Technical Skills Demonstrated

- Thermal system design and integration
- Heat transfer calculations (conduction, convection, radiation)
- Fluid mechanics and hydraulic networks
- Pump selection and sizing
- Energy storage systems
- Heat exchanger design (LMTD, ε-NTU methods)
- Economic analysis (NPV, IRR, payback)
- Technical documentation and P&ID creation
- Python scientific computing (NumPy, Matplotlib, Pandas)
- Professional engineering report writing

## Tools & Libraries Used

- **Python 3.x** - Programming language
- **NumPy** - Numerical calculations
- **Matplotlib** - Technical diagrams and plots
- **Pandas** - Data analysis and reporting
- **Custom thermal_toolkit** - Specialized thermal calculations

## Validation

All calculations verified against:
- ASME codes for pressure vessels
- ASHRAE guidelines for thermal storage
- Pump manufacturer curves (Grundfos)
- Heat exchanger manufacturer data (Alfa Laval)
- Chilean energy costs and emissions factors

## Academic Application

This project demonstrates graduate-level competencies required for 
**Master's in Computational Simulation (PUCV)** including:

- Complex system modeling and integration
- Multi-physics simulation (thermal + fluid)
- Optimization and design methodology
- Professional technical communication
- Real industrial consulting experience

## Contact

**Felipe Wasaff**  
Coordinator of Physics Laboratories  
Universidad de Chile, Faculty of Sciences  
Email: felipe.wasaff@uchile.cl  
LinkedIn: felipewasaff  
GitHub: fwasaff/thermal-systems-toolkit

---

*This project represents professional-quality industrial engineering work 
suitable for portfolio presentation and graduate program applications.*
