import pyvisa
import serial
import time
import csv

# ------------------------- Configuration -------------------------
samples_per_duty = 10
settling_time = 0.5  # seconds after ESP sets PWM
duty_cycle_range = range(1, 101)  # 1% to 100%
output_csv = r"F:\1 siemens\Design a current source\Data\Final_measurements\nucleo_pwm_at_vref_outputs.csv"

esp_serial_port = 'COM14'  # Update if needed
esp_baudrate = 9600

# ------------------------- Connect to ESP -------------------------
esp = serial.Serial(esp_serial_port, esp_baudrate, timeout=2)
time.sleep(3)  # Let ESP boot and send READY
esp.reset_input_buffer()

# ✅ Manually confirm ESP is ready
input("🔌 Please ensure ESP is connected and ready. Press Enter to continue...")


# ------------------------- Connect to DSO -------------------------
rm = pyvisa.ResourceManager()
print("Available VISA devices:", rm.list_resources())

dso = rm.open_resource('USB0::0x0699::0x0408::C024253::INSTR')  # Change if needed
print("DSO:", dso.query("*IDN?").strip())

# ------------------------- DSO Setup -------------------------
dso.write("SELect:CH1 ON")
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

for duty in duty_cycle_range:
    print(f"\n===> Sending {duty}% duty to ESP...")
    esp.write(f"{duty}\n".encode())

    # ✅ Wait for ESP confirmation
    confirmed = False
    while True:
        try:
            line = esp.readline().decode(errors='ignore').strip()
        except Exception as e:
            print("Error reading from ESP:", e)
            break

        if not line:
            continue

        print("ESP:", line)

        if line == "OK":
            confirmed = True
            break
        elif line == "ERR":
            print("⚠️ ESP reported error. Skipping duty cycle.")
            break
        # ignore "PWM_SET: xx%" messages

    if not confirmed:
        continue  # Skip this duty cycle if not confirmed

    print(f"Waiting {settling_time}s for signal to stabilize...")
    time.sleep(settling_time)

    # Take multiple DSO samples
    ch1_acc = {key: 0 for key in ["Amplitude (V)", "Frequency (Hz)", "Positive Width (s)", "Period (s)", "Duty Cycle (%)"]}

    for i in range(samples_per_duty):
        ch1 = get_dso_measurements(1)
        for key in ch1:
            ch1_acc[key] += ch1[key]
        time.sleep(0.2)

    # Average the results
    ch1_avg = {key: ch1_acc[key] / samples_per_duty for key in ch1_acc}

    print(f"CH1 Average at {duty}%:")
    for k, v in ch1_avg.items():
        print(f"  {k}: {v}")

    results.append([
        duty,
        ch1_avg["Amplitude (V)"], ch1_avg["Frequency (Hz)"],
        ch1_avg["Positive Width (s)"], ch1_avg["Period (s)"], ch1_avg["Duty Cycle (%)"]
    ])

# ------------------------- Cleanup -------------------------
dso.close()
rm.close()
esp.close()

# ------------------------- Save to CSV -------------------------
with open(output_csv, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        "DutyCycle_Input(%)",
        "CH1_Amplitude(V)", "CH1_Freq(Hz)", "CH1_PosWidth(s)", "CH1_Period(s)", "CH1_DutyCycle(%)"
    ])
    writer.writerows(results)

print(f"\n Measurement complete. Results saved to:\n{output_csv}")
