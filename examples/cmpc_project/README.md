# CMPC Heat Recovery System Design

## Project Overview

**Client**: Papeles Cordillera S.A. (CMPC Puente Alto)  
**Consultant**: Leycero SpA  
**Equipment Supplier**: Kaeser Compresores de Chile  
**Date**: December 2024

## Problem Statement

Design a complete heat recovery system to capture waste heat from 6 industrial 
air compressors and use it to preheat industrial process water.

### System Requirements

**Thermal Power Available**: 622 kW (normal operation)  
**Water Flow Rate**: 21.72 m³/h  
**Temperature Rise**: 25 K  

### Design Challenges

1. **Piping Network**: Determine optimal pipe diameters and layout
2. **Pumping System**: Select pump configuration (central vs. distributed)
3. **Thermal Storage**: Size accumulator tank for load balancing
4. **Heat Transfer**: Design intermediate heat exchanger to isolate circuits
5. **System Integration**: Ensure compatibility with existing industrial water system

## Project Structure
```
cmpc_project/
├── 01_system_analysis.py       # Operating scenarios analysis
├── 02_piping_design.py         # Pipe sizing and pressure drop
├── 03_pump_selection.py        # Pump specification
├── 04_storage_design.py        # Accumulator tank design
├── 05_heat_exchanger.py        # Intermediate heat exchanger
├── 06_system_integration.py    # Complete system validation
└── data/
    ├── compressor_specs.json   # Equipment specifications
    └── operating_scenarios.json # Plant operation modes
```

## Key Technical Decisions

- [ ] Pump configuration: Central vs. distributed
- [ ] Piping material and insulation
- [ ] Accumulator tank volume and dimensions
- [ ] Heat exchanger type: Plate vs. shell-and-tube
- [ ] Control strategy for variable operation

## Results Summary

*(To be completed as project progresses)*

---

**Author**: Felipe Wasaff  
**Contact**: felipe.wasaff@uchile.cl  
**Repository**: [thermal-systems-toolkit](https://github.com/fwasaff/thermal-systems-toolkit)
