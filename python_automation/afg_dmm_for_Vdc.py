import pyvisa
import time
import csv
import os

# Custom CSV path
output_csv = r"F:\1 siemens\Design a current source\data\afg_dmm_Vdc_avg_results.csv"

# Connect to VISA instruments
rm = pyvisa.ResourceManager()
afg = rm.open_resource("USB0::0x0699::0x0345::C021866::INSTR")  # Tek AFG
dmm = rm.open_resource("USB0::0x2A8D::0x0301::MY57503989::INSTR")  # Keysight 34465A

# ID checks
print("AFG ID:", afg.query("*IDN?"))
print("DMM ID:", dmm.query("*IDN?"))

# Configure AFG
afg.write("FUNC PULS")
afg.write("FREQ 1000")
afg.write("VOLT:HIGH 3.3")
afg.write("VOLT:LOW 0")
afg.write("OUTP ON")

# Configure DMM
dmm.write("*RST")
dmm.write("CONF:VOLT:DC")
dmm.write("VOLT:DC:NPLC 1")

# Write data
with open(output_csv, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["DutyCycle (%)", "Avg DC Voltage (V)"])

    for duty_cycle in range(1, 101):
        afg.write(f"PULS:DCYC {duty_cycle}")
        time.sleep(3) # RC settle time

        voltages = []
        for _ in range(10):
            voltages.append(float(dmm.query("READ?")))
            time.sleep(0.1)

        avg_voltage = sum(voltages) / len(voltages)
        writer.writerow([duty_cycle, avg_voltage])
        print(f"Duty Cycle: {duty_cycle}% => Avg V: {avg_voltage:.6f} V")

afg.write("OUTP OFF")

print(f"\n Sweep complete. Results saved to:\n{os.path.abspath(output_csv)}")
