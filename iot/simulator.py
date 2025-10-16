import random
import time
import threading
from datetime import datetime

class IoTDevice:
    def __init__(self):
        self.recommendation_count = 0
        self.voice_commands = 0
        self.tilt_gestures = 0
        self.button_presses = 0
        self.multi_sensory = 0
        self.last_update = datetime.now()
        self.running = False
        self.thread = None
        
        # ESP32 Sensor Simulation
        self.sensors = {
            'mpu6050_tilt': {'x': 0.0, 'y': 0.0, 'z': 1.0},
            'microphone': {'listening': False, 'volume': 0},
            'button': {'pressed': False, 'press_count': 0},
            'oled': {'displaying': True, 'brightness': 100},
            'led': {'color': 'blue', 'blinking': False}
        }
        
        # System status
        self.system_status = "ready"
        self.temperature = 25.0
        self.memory_usage = 45.0
        
        print("📱 IoT Device (ESP32) Initialized")
    
    def start(self):
        """Start IoT device simulation"""
        self.running = True
        self.thread = threading.Thread(target=self._sensor_loop, daemon=True)
        self.thread.start()
        print("✅ IoT Device Started - Sensors Active")
        return True
    
    def stop(self):
        """Stop IoT device"""
        self.running = False
        print("🛑 IoT Device Stopped")
    
    def _sensor_loop(self):
        """Simulate sensor data updates"""
        while self.running:
            # Update tilt sensor data (simulate gentle movement)
            self.sensors['mpu6050_tilt'] = {
                'x': random.uniform(-0.5, 0.5),
                'y': random.uniform(-0.5, 0.5), 
                'z': random.uniform(0.8, 1.2)
            }
            
            # Update microphone volume
            self.sensors['microphone']['volume'] = random.uniform(0, 100)
            
            # Update system metrics
            self.temperature = random.uniform(20.0, 35.0)
            self.memory_usage = random.uniform(40.0, 75.0)
            
            time.sleep(2)  # Update every 2 seconds
    
    def get_status(self):
        """Get simple status - ADD THIS METHOD"""
        return {
            "status": "active",
            "sensors_online": 5,
            "interactions": self.get_total_interactions()
        }
    
    def record_interaction(self, interaction_type):
        """Record different IoT interactions"""
        self.last_update = datetime.now()
        
        if interaction_type == "voice_command":
            self.voice_commands += 1
            self.sensors['microphone']['listening'] = True
            print("🎤 Voice Command: 'Show me action movies'")
            time.sleep(1)
            self.sensors['microphone']['listening'] = False
            
        elif interaction_type == "tilt_gesture":
            self.tilt_gestures += 1
            print("📱 Tilt Gesture: Navigating through recommendations")
            # Simulate tilt data
            self.sensors['mpu6050_tilt'] = {
                'x': random.uniform(-1.0, 1.0),
                'y': random.uniform(-1.0, 1.0),
                'z': random.uniform(0.5, 1.5)
            }
            
        elif interaction_type == "button_press":
            self.button_presses += 1
            self.sensors['button']['press_count'] += 1
            self.sensors['button']['pressed'] = True
            print("🔘 Button Press: Refreshing recommendations")
            time.sleep(0.5)
            self.sensors['button']['pressed'] = False
            
        elif interaction_type == "multi_sensory":
            self.multi_sensory += 1
            print("🔄 Multi-Sensory: Voice + Tilt + Button combined")
            self.simulate_multi_sensory()
        
        self.recommendation_count += 1
    
    def simulate_multi_sensory(self):
        """Simulate combined sensor interaction"""
        print("   🎤 Listening for voice command...")
        self.sensors['microphone']['listening'] = True
        time.sleep(1)
        
        print("   📱 Detecting tilt gesture...")
        self.sensors['mpu6050_tilt'] = {'x': 0.8, 'y': -0.3, 'z': 1.1}
        time.sleep(1)
        
        print("   🔘 Button pressed for confirmation...")
        self.sensors['button']['pressed'] = True
        time.sleep(0.5)
        self.sensors['button']['pressed'] = False
        self.sensors['microphone']['listening'] = False
        
        print("   ✅ Multi-sensory interaction completed")
    
    def display_message(self, message):
        """Simulate OLED display"""
        print(f"📟 OLED Display: {message}")
        self.sensors['oled']['displaying'] = True
    
    def led_feedback(self, status):
        """Simulate LED feedback"""
        colors = {
            'success': '🟢 GREEN', 
            'processing': '🟡 YELLOW', 
            'error': '🔴 RED',
            'ready': '🔵 BLUE'
        }
        color = colors.get(status, '⚪ WHITE')
        self.sensors['led']['color'] = status
        print(f"💡 LED: {color} - {status.upper()}")
    
    def show_detailed_status(self):
        """Show detailed IoT status"""
        print("\n" + "="*60)
        print("📱 SMARTFLIX IOT DEVICE STATUS (ESP32 SIMULATION)")
        print("="*60)
        
        print(f"🕒 Last Update: {self.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 System Status: {self.system_status.upper()}")
        print(f"🌡️  Temperature: {self.temperature:.1f}°C")
        print(f"💾 Memory Usage: {self.memory_usage:.1f}%")
        
        print("\n🎯 INTERACTION STATISTICS:")
        print(f"   🎤 Voice Commands: {self.voice_commands}")
        print(f"   📱 Tilt Gestures: {self.tilt_gestures}")
        print(f"   🔘 Button Presses: {self.button_presses}")
        print(f"   🔄 Multi-Sensory: {self.multi_sensory}")
        print(f"   📈 Total Interactions: {self.get_total_interactions()}")
        print(f"   🎬 Recommendations Generated: {self.recommendation_count}")
        
        print("\n🔧 SENSOR STATUS:")
        tilt = self.sensors['mpu6050_tilt']
        print(f"   📱 MPU6050 Tilt: X:{tilt['x']:6.2f}, Y:{tilt['y']:6.2f}, Z:{tilt['z']:6.2f}")
        mic = self.sensors['microphone']
        print(f"   🎤 Microphone: {'🎤 LISTENING' if mic['listening'] else '🔇 IDLE'} (Vol: {mic['volume']:.0f}%)")
        btn = self.sensors['button']
        print(f"   🔘 Button: {'🔴 PRESSED' if btn['pressed'] else '🟢 READY'} (Total presses: {btn['press_count']})")
        oled = self.sensors['oled']
        print(f"   📟 OLED: {'📺 ACTIVE' if oled['displaying'] else '⚫ OFF'} (Brightness: {oled['brightness']}%)")
        led = self.sensors['led']
        print(f"   💡 LED: {led['color'].upper()} {'🔅 BLINKING' if led['blinking'] else '💤 STEADY'}")
        
        print("="*60)
    
    def get_sensor_status(self):
        """Get current sensor status"""
        return {
            'tilt_x': self.sensors['mpu6050_tilt']['x'],
            'tilt_y': self.sensors['mpu6050_tilt']['y'],
            'tilt_z': self.sensors['mpu6050_tilt']['z'],
            'mic_active': self.sensors['microphone']['listening'],
            'mic_volume': self.sensors['microphone']['volume'],
            'button_pressed': self.sensors['button']['pressed'],
            'oled_on': self.sensors['oled']['displaying'],
            'led_color': self.sensors['led']['color'],
            'temperature': self.temperature,
            'memory_usage': self.memory_usage
        }
    
    def get_total_interactions(self):
        return self.voice_commands + self.tilt_gestures + self.button_presses + self.multi_sensory
    
    def record_comparison(self):
        """Record model comparison activity"""
        self.recommendation_count += 1
        self.last_update = datetime.now()
        print("📊 AI Model Comparison Recorded")
    
    def simulate_voice_command(self, command):
        """Simulate specific voice command"""
        self.record_interaction("voice_command")
        print(f"🎤 Voice Command: '{command}'")
        return f"Processing: {command}"