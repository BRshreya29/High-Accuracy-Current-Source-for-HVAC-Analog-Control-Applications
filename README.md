# High-Accuracy Current Source for HVAC Analog Control Applications

The goal of this project was to design a **0–1 mA precision current source** with **10 µA steps** using a **PWM duty cycle** as the control input. Various current-source architectures were explored, after which a **comparator + voltage-regulated current source** was finalized and tested in hardware. Voltage fluctuations in the PWM input were found to affect current accuracy, so a **3.3 V regulator and comparator stage** were added to stabilize the control voltage. The **sense resistor (3.3 kΩ)** was selected with **0.1% tolerance** and **10 ppm** temp-co because it directly sets the output current. The **current-source op-amp** and **comparator op-amp** were chosen based on precision, rail-to-rail performance, and slew-rate requirements. RC filter values were chosen based on cutoff calculations, as they do not impact current accuracy. Python + PyVISA scripts were developed to automate AFG, DSO, and DMM measurements.

**Full detailed documentation is available in the repo:**  
**[Precision Current Source 0-1mA.pdf](./Precision%20Current%20Source%200-1mA.pdf)**

---

## Repository Structure

```
/ltspice/
    core_comparator_stage.asc
    Final_design.asc
    Testing_stage_file.asc
    plots/
        each stage Ltspice simulated plots

/python_automation/
    dmm, dso with input from afg and esp [microcontroller with 3.3V output] code files in python

/test_results/
    Final_circuit_testing_measurements.xlsx
    Monte-Carlo_Analysis.xlsx
    Worst_Case_Analysis.xlsx

/external_imported_library_models/
    libraries for components not available in ltspice

Precision Current Source 0-1mA.pdf - details documentation of project

readme.md
```

---

## ✅ Summary

This repository contains the **complete LTspice simulations**, **hardware validation**, **component analysis**, and **automated test scripts** for a high-accuracy 0–1 mA current source for HVAC analog control applications.
