import pyvisa
import serial
import time
import csv

# ------------------------- Configuration -------------------------
samples_per_duty = 10
settling_time = 0.5  # seconds after ESP sets PWM
duty_cycle_range = range(1, 101)  # 1% to 100%
output_csv = r"F:\1 siemens\Design a current source\Data\Final_measurements\dmm_nucleo_vdc.csv"

esp_serial_port = 'COM14'  # Update if needed
esp_baudrate = 9600

# ------------------------- Connect to ESP -------------------------
esp = serial.Serial(esp_serial_port, esp_baudrate, timeout=2)
time.sleep(3)  # Let ESP boot
esp.reset_input_buffer()

input("🔌 Please ensure ESP is connected and ready. Press Enter to continue...")

# ------------------------- Connect to DMM -------------------------
rm = pyvisa.ResourceManager()
print("Available VISA devices:", rm.list_resources())

dmm = rm.open_resource('USB0::0x2A8D::0x0301::MY57503989::INSTR')  # Update as needed
print("DMM:", dmm.query("*IDN?").strip())

# ------------------------- DMM Setup -------------------------
dmm.write("*RST")
dmm.write("SYST:BEEP:STAT OFF")
dmm.write("CONF:VOLT:DC")
dmm.write("SAMP:COUN 1")
dmm.write("INIT:CONT ON")
dmm.write("TRIG:SOUR IMM")

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

    # Take multiple voltage samples
    vdc_values = []
    for i in range(samples_per_duty):
        try:
            vdc = float(dmm.query("READ?"))
        except:
            vdc = float('nan')
        vdc_values.append(vdc)
        time.sleep(0.1)

    vdc_avg = sum(vdc_values) / len(vdc_values)
    print(f"   VDC Avg at {duty}%: {vdc_avg:.6f} V")

    results.append([duty, vdc_avg])

# ------------------------- Cleanup -------------------------
dmm.close()
esp.close()
rm.close()

# ------------------------- Save to CSV -------------------------
with open(output_csv, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["DutyCycle_Input(%)", "VDC_DMM(V)"])
    writer.writerows(results)

print(f"\n✅ Measurement complete. Results saved to:\n{output_csv}")
