import pyvisa
import time
import csv

# ------------------------- Configuration -------------------------
duty_start = 1
duty_end = 99
samples_per_duty = 10
settling_time = 5  # seconds after setting duty
output_csv = r"F:\1 siemens\Design a current source\Data\afg_dmm_vref_final_output_idc.csv"

# ------------------------- VISA Setup -------------------------
rm = pyvisa.ResourceManager()
print("Available devices:", rm.list_resources())

# Replace with your actual VISA addresses
afg = rm.open_resource('USB0::0x0699::0x0345::C021866::INSTR')  # Tektronix AFG3252
dmm = rm.open_resource('USB0::0x2A8D::0x0301::MY57503989::INSTR')  # Keysight DMM34465A

print("AFG:", afg.query("*IDN?").strip())
print("DMM:", dmm.query("*IDN?").strip())

# ------------------------- AFG Setup -------------------------
afg.write("*RST")
afg.write("SOURce1:FUNCtion PULSe")
afg.write("SOURce1:FREQuency 1000")  # 1 kHz

#  Correct Hi-Z setting
afg.write("OUTPut1:IMPedance INF")  # Hi-Z

# Set correct amplitude and offset for 0V–3.3V pulse
afg.write("SOURce1:VOLTage:AMPLitude 3.3")
afg.write("SOURce1:VOLTage:OFFSet 1.65")

# Fast rise/fall times
afg.write("SOURce1:PULSe:TRANsition:LEADing 5E-9")
afg.write("SOURce1:PULSe:TRANsition:TRAiling 5E-9")

afg.write("OUTPut1 ON")

# ------------------------- DMM Setup -------------------------
dmm.write("*RST")
dmm.write("SYST:BEEP:STAT OFF")
dmm.write("CONF:CURR:DC")
dmm.write("SAMP:COUN 1")
dmm.write("INIT:CONT ON")
dmm.write("TRIG:SOUR IMM")

# ------------------------- Measurement Loop -------------------------
results = []

for duty in range(duty_start, duty_end + 1):
    print(f"\n→ Setting AFG duty cycle to {duty}%")
    afg.write(f"PULSe:DCYCle {duty}")
    time.sleep(settling_time)

    vdc_values = []

    for i in range(samples_per_duty):
        try:
            vdc = float(dmm.query("READ?"))
        except:
            vdc = float('nan')
        vdc_values.append(vdc)
        time.sleep(0.2)

    vdc_avg = sum(vdc_values) / len(vdc_values)
    print(f"   DC Current Avg: {vdc_avg:.9f} A  ({vdc_avg*1e6:.2f} µA)")

    results.append([duty, vdc_avg * 1e6])  # Store in µA


# ------------------------- Cleanup and Save -------------------------
afg.close()
dmm.close()
rm.close()

with open(output_csv, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["DutyCycle_Input(%)", "IDC_DMM(µA)"])
    writer.writerows(results)

print(f"\n Measurement complete. Results saved to:\n{output_csv}")
