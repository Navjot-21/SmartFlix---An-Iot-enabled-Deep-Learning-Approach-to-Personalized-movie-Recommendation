import serial
import serial.tools.list_ports

ports = list(serial.tools.list_ports.comports())

if not ports:
    print("❌ No COM ports found.")
else:
    print("🔍 Available COM ports:")
    for p in ports:
        print(f"  {p.device} - {p.description}")

    for p in ports:
        try:
            print(f"\nTrying to open {p.device} ...")
            s = serial.Serial(p.device, 9600, timeout=1)
            s.close()
            print(f"✅ Successfully opened {p.device}")
        except Exception as e:
            print(f"❌ Could not open {p.device}: {e}")
