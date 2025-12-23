import pyvisa
import time
import csv

# ------------------------- Configuration -------------------------
duty_start = 1
duty_end = 99
samples_per_duty = 10
settling_time = 2  # seconds after setting duty
output_csv = r"F:\1 siemens\Design a current source\Data\afg_dso_PWM_at_dso_finallll.csv"

# ------------------------- VISA Setup -------------------------
rm = pyvisa.ResourceManager()
print("Available devices:", rm.list_resources())

# Replace with your actual VISA addresses
afg = rm.open_resource('USB0::0x0699::0x0345::C021866::INSTR')  # AFG3252
dso = rm.open_resource('USB0::0x0699::0x0408::C024253::INSTR')  # MDO3104


print("AFG:", afg.query("*IDN?").strip())
print("DSO:", dso.query("*IDN?").strip())

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


# ------------------------- DSO Setup -------------------------
dso.write("SELect:CH1 ON")
#dso.write("SELect:CH2 ON")
dso.write("AUTOSet EXECute")
time.sleep(3)

# ------------------------- Helper Function -------------------------
def get_dso_measurements(channel):
    dso.write(f"MEASU:IMM:SOU1 CH{channel}")
    result = {}

    for scpi_type, label in [
        ("AMPl", "Amplitude (V)"),
        ("FREQ", "Frequency (Hz)"),
        ("PWI", "Positive Width (s)"),
        ("PER", "Period (s)"),
        ("DUTY", "Duty Cycle (%)")
    ]:
        dso.write(f"MEASU:IMM:TYPE {scpi_type}")
        time.sleep(0.2)
        dso.write("MEASU:IMM:VAL?")
        try:
            val = float(dso.read())
        except:
            val = float('nan')
        result[label] = val

    return result

# ------------------------- Main Measurement Loop -------------------------
results = []

for duty in range(duty_start, duty_end + 1):
    print(f"\n→ Setting AFG duty cycle to {duty}%")
    afg.write(f"PULSe:DCYCle {duty}")
    time.sleep(settling_time)

    # Accumulators for CH1 and CH2
    ch1_acc = {key: 0 for key in ["Amplitude (V)", "Frequency (Hz)", "Positive Width (s)", "Period (s)", "Duty Cycle (%)"]}
   # ch2_acc = ch1_acc.copy()

    for i in range(samples_per_duty):
        ch1 = get_dso_measurements(1)
        #ch2 = get_dso_measurements(2)

        for key in ch1:
            ch1_acc[key] += ch1[key]
          #  ch2_acc[key] += ch2[key]

        time.sleep(0.5)

    # Compute averages
    ch1_avg = {key: ch1_acc[key] / samples_per_duty for key in ch1_acc}
    #ch2_avg = {key: ch2_acc[key] / samples_per_duty for key in ch2_acc}

    print(f"   CH1 Avg: {ch1_avg}")
  #  print(f"   CH2 Avg: {ch2_avg}")

    results.append([
        duty,
        ch1_avg["Amplitude (V)"], ch1_avg["Frequency (Hz)"], ch1_avg["Positive Width (s)"], ch1_avg["Period (s)"], ch1_avg["Duty Cycle (%)"],
       # ch2_avg["Amplitude (V)"], ch2_avg["Frequency (Hz)"], ch2_avg["Positive Width (s)"], ch2_avg["Period (s)"], ch2_avg["Duty Cycle (%)"]
    ])

# ------------------------- Cleanup and Save -------------------------
afg.close()
dso.close()
rm.close()

with open(output_csv, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        "DutyCycle_Input(%)",
        "CH1_Amplitude(V)", "CH1_Freq(Hz)", "CH1_PosWidth(s)", "CH1_Period(s)", "CH1_DutyCycle(%)"
        #"CH2_Amplitude(V)", "CH2_Freq(Hz)", "CH2_PosWidth(s)", "CH2_Period(s)", "CH2_DutyCycle(%)"
    ])
    writer.writerows(results)

print(f"\n Measurement complete. Results saved to:\n{output_csv}")
