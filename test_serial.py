import serial.tools.list_ports

ports = list(serial.tools.list_ports.comports())
for port in ports:
    print(f"Found port: {port.device}")
    if "COM6" in port.device:
        print(f"✅ Found possible ESP32 at: {port.device}")
        try:
            ser = serial.Serial(port.device, 115200)
            print("✅ Successfully opened serial port!")
            ser.close()
        except Exception as e:
            print("❌ Error:", e)