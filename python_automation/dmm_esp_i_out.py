import pyvisa
import serial
import time
import csv

# ------------------------- Configuration -------------------------
samples_per_duty = 10
settling_time = 0.5  # seconds after ESP sets PWM
duty_cycle_range = range(1, 100)  # 1% to 99%
output_csv = r"F:\1 siemens\Design a current source\Data\Final_measurements\nucleo_dmm_idc.csv"

esp_serial_port = 'COM14'  # Update if needed
esp_baudrate = 9600

# ------------------------- Connect to ESP -------------------------
esp = serial.Serial(esp_serial_port, esp_baudrate, timeout=2)
time.sleep(3)  # Let ESP boot and send READY
esp.reset_input_buffer()

input("🔌 Please ensure ESP is connected and ready. Press Enter to continue...")

# ------------------------- Connect to DMM -------------------------
rm = pyvisa.ResourceManager()
print("Available VISA devices:", rm.list_resources())

dmm = rm.open_resource('USB0::0x2A8D::0x0301::MY57503989::INSTR')  # Keysight 34465A
print("DMM:", dmm.query("*IDN?").strip())

# ------------------------- DMM Setup -------------------------
dmm.write("*RST")
dmm.write("SYST:BEEP:STAT OFF")
dmm.write("CONF:CURR:DC")         # DC current mode
dmm.write("SAMP:COUN 1")          # One sample at a time
dmm.write("INIT:CONT ON")         # Continuous mode
dmm.write("TRIG:SOUR IMM")        # Immediate trigger

# ------------------------- Measurement Loop -------------------------
results = []

for duty in duty_cycle_range:
    print(f"\n===> Sending {duty}% duty to ESP...")
    esp.write(f"{duty}\n".encode())

    # Wait for "OK" response from ESP
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

    if not confirmed:
        continue  # Skip this duty cycle

    print(f"Waiting {settling_time}s for signal to stabilize...")
    time.sleep(settling_time)

    # Measure DC current
    idc_values = []
    for _ in range(samples_per_duty):
        try:
            idc = float(dmm.query("READ?"))  # in Amps
        except:
            idc = float('nan')
        idc_values.append(idc)
        time.sleep(0.01)

    idc_avg = sum(idc_values) / len(idc_values)
    print(f"   DC Current Avg: {idc_avg:.9f} A  ({idc_avg * 1e6:.2f} µA)")

    results.append([duty, idc_avg * 1e6])  # Store in µA

# ------------------------- Cleanup -------------------------
dmm.close()
esp.close()
rm.close()

# ------------------------- Save CSV -------------------------
with open(output_csv, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["DutyCycle_Input(%)", "IDC_DMM(µA)"])
    writer.writerows(results)

print(f"\n✅ Measurement complete. Results saved to:\n{output_csv}")
