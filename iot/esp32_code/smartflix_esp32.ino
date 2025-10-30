#include <Wire.h>
#include <Adafruit_SSD1306.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// OLED Display
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Hardware Pins
#define BUTTON_PIN 4

// WiFi Credentials
const char* ssid = "CGC_Block_1";
const char* password = "Reenu@5668";

// Server Configuration
const char* serverURL = "http://10.60.35.73:5000";

// System Variables
bool lastButtonState = HIGH;
bool buttonState = HIGH;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

// Device status
bool oledInitialized = false;

void setup() {
  Serial.begin(115200);
  Serial.println("🚀 Starting SmartFlix System...");
  
  // Initialize OLED FIRST with simple approach
  initializeOLED();
  
  // Then initialize other components
  initializePins();
  
  // Connect to WiFi
  connectToWiFi();
  
  // Display welcome message
  displayWelcome();
  
  Serial.println("✅ SmartFlix ESP32 Ready!");
  Serial.println("📝 Press button for recommendations!");
}

void loop() {
  // Read button only (skip MPU6050 for now)
  readButton();
  delay(100);
}

void initializeOLED() {
  Serial.println("🔧 Initializing OLED...");
  
  // Simple OLED initialization - just try the most common address
  if(display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("✅ OLED initialized successfully!");
    oledInitialized = true;
    
    // Basic display setup
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(0,0);
    display.display();
  } else {
    Serial.println("❌ OLED initialization failed!");
    oledInitialized = false;
  }
}

void initializePins() {
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  Serial.println("✅ Button initialized");
}

void connectToWiFi() {
  if (oledInitialized) {
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("Connecting WiFi");
    display.println(ssid);
    display.display();
  }
  
  Serial.println("📡 Connecting to WiFi: " + String(ssid));
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
    
    // Show progress on OLED
    if (oledInitialized && attempts % 4 == 0) {
      display.print(".");
      display.display();
    }
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected!");
    Serial.print("📱 IP Address: ");
    Serial.println(WiFi.localIP());
    
    if (oledInitialized) {
      display.clearDisplay();
      display.setCursor(0,0);
      display.println("WiFi Connected!");
      display.print("IP: ");
      display.println(WiFi.localIP());
      display.display();
      delay(2000);
    }
  } else {
    Serial.println("\n❌ WiFi Failed!");
    if (oledInitialized) {
      display.clearDisplay();
      display.setCursor(0,0);
      display.println("WiFi Failed!");
      display.display();
    }
  }
}

void displayWelcome() {
  if (oledInitialized) {
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("=== SmartFlix ===");
    display.println("IoT Movie System");
    display.println("----------------");
    display.println("Press Button for");
    display.println("Recommendations!");
    display.println("----------------");
    display.display();
    delay(1000);
  }
}

void readButton() {
  bool reading = digitalRead(BUTTON_PIN);
  
  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }
  
  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != buttonState) {
      buttonState = reading;
      
      if (buttonState == LOW) {
        Serial.println("🎯 Button Pressed!");
        onButtonPress();
      }
    }
  }
  
  lastButtonState = reading;
}

void onButtonPress() {
  if (oledInitialized) {
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("Button Pressed!");
    display.println("Getting movies...");
    display.display();
  }
  
  // Send button interaction to server
  String response = sendAPIRequest("button", "");
  
  // Show result for 3 seconds
  delay(3000);
  
  // Return to welcome screen
  displayWelcome();
}

String sendAPIRequest(String interactionType, String data) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    
    String url = String(serverURL) + "/api/interact";
    Serial.println("🌐 Sending to: " + url);
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    
    // Create JSON payload
    DynamicJsonDocument doc(200);
    doc["type"] = interactionType;
    doc["data"] = data;
    doc["device"] = "esp32";
    
    String jsonPayload;
    serializeJson(doc, jsonPayload);
    Serial.println("Payload: " + jsonPayload);
    
    int httpResponseCode = http.POST(jsonPayload);
    
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("✅ API Response Code: " + String(httpResponseCode));
      Serial.println("Response: " + response);
      
      // Display recommendations on OLED
      displayRecommendations(response);
      return response;
    } else {
      Serial.println("❌ API Error: " + String(httpResponseCode));
      if (oledInitialized) {
        display.clearDisplay();
        display.setCursor(0,0);
        display.println("API Error");
        display.println("Code: " + String(httpResponseCode));
        display.display();
      }
      return "Error";
    }
    
    http.end();
  } else {
    Serial.println("❌ WiFi Not Connected");
    if (oledInitialized) {
      display.clearDisplay();
      display.setCursor(0,0);
      display.println("WiFi Disconnected");
      display.display();
    }
    return "Offline";
  }
}

void displayRecommendations(String response) {
  if (!oledInitialized) return;
  
  // Try to parse JSON response
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, response);
  
  if (error) {
    Serial.print("❌ JSON parse failed: ");
    Serial.println(error.c_str());
    displayDemoRecommendations();
    return;
  }
  
  // Check if recommendations exist
  if (doc.containsKey("recommendations")) {
    JsonArray movies = doc["recommendations"];
    
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("=== Top Movies ===");
    
    int displayCount = (movies.size() < 3) ? movies.size() : 3;
    
    for (int i = 0; i < displayCount; i++) {
      String title = movies[i]["title"];
      float score = movies[i]["score"];
      
      // Shorten title for OLED
      if (title.length() > 16) {
        title = title.substring(0, 16);
      }
      
      display.setCursor(0, 10 + (i * 18));
      display.print(i + 1);
      display.print(". ");
      display.println(title);
      
      display.setCursor(100, 10 + (i * 18));
      display.print(score, 1);
    }
    
    display.display();
  } else {
    // Show demo data if no recommendations
    displayDemoRecommendations();
  }
}

void displayDemoRecommendations() {
  if (!oledInitialized) return;
  
  display.clearDisplay();
  display.setCursor(0,0);
  display.println("=== Top Movies ===");
  
  display.setCursor(0, 10);
  display.println("1. Inception");
  display.setCursor(100, 10);
  display.println("8.8");
  
  display.setCursor(0, 28);
  display.println("2. The Matrix");
  display.setCursor(100, 28);
  display.println("8.7");
  
  display.setCursor(0, 46);
  display.println("3. Interstellar");
  display.setCursor(100, 46);
  display.println("8.6");
  
  display.display();
}