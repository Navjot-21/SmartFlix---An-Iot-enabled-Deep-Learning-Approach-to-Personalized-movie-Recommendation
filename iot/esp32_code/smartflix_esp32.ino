#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// OLED Display (SH1106)
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SH1106G display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Hardware Pins
#define BUTTON_PIN 4

// WiFi Credentials
const char* ssid = "wifi name";
const char* password = "wifi password";

// Server Configuration
const char* serverURL = "http://pc' s ip address"; // Change to your PC IP

// MPU6050 I2C address
const int MPU6050_ADDR = 0x68;

// System Variables
bool lastButtonState = HIGH;
bool buttonState = HIGH;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

// Tilt detection
float tiltThreshold = 1.5;
float lastTiltX = 0, lastTiltY = 0;
unsigned long lastTiltTime = 0;

void setup() {
  Serial.begin(115200);

  // Initialize I2C and Display
  Wire.begin(21, 22);
  initializeOLED();
  initializeMPU6050();
  initializePins();

  // Connect to WiFi
  connectToWiFi();

  // Welcome Screen
  displayWelcome();

  Serial.println("SmartFlix ESP32 Ready!");
  Serial.println("Press button or tilt for recommendations!");
}

void loop() {
  readButton();
  readTiltSensor();
  delay(100);
}

void initializeOLED() {
  if (!display.begin(0x3C, true)) {
    Serial.println("OLED initialization failed!");
    for(;;);
  }
  display.clearDisplay();
  display.setTextColor(SH110X_WHITE);
  display.setTextSize(1);
  display.setCursor(0, 10);
  display.println("OLED Initialized!");
  display.display();
  Serial.println("OLED initialized");
  delay(1000);
}

void initializeMPU6050() {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x6B); // Power management register
  Wire.write(0);    // Wake up MPU6050
  Wire.endTransmission(true);
  Serial.println("MPU6050 initialized");
}

void initializePins() {
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  Serial.println("Button initialized");
}

void connectToWiFi() {
  display.clearDisplay();
  display.setCursor(0,0);
  display.println("Connecting to WiFi...");
  display.display();

  WiFi.begin(ssid, password);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  display.clearDisplay();
  display.setCursor(0,0);
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    display.println("WiFi Connected!");
    display.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi Failed!");
    display.println("WiFi Failed!");
  }
  display.display();
  delay(2000);
}

void displayWelcome() {
  display.clearDisplay();
  display.setCursor(0,0);
  display.println("SmartFlix");
  display.println("IoT System");
  display.println("Ready!");
  display.println("Btn/Tilt for recs");
  display.display();
}

void readButton() {
  bool reading = digitalRead(BUTTON_PIN);
  if (reading != lastButtonState) lastDebounceTime = millis();

  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != buttonState) {
      buttonState = reading;
      if (buttonState == LOW) onButtonPress();
    }
  }
  lastButtonState = reading;
}

void readTiltSensor() {
  int16_t accelX, accelY, accelZ;
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU6050_ADDR, 6, true);

  accelX = Wire.read() << 8 | Wire.read();
  accelY = Wire.read() << 8 | Wire.read();
  accelZ = Wire.read() << 8 | Wire.read();

  float tiltX = (float)accelX / 16384.0;
  float tiltY = (float)accelY / 16384.0;

  if ((abs(tiltX - lastTiltX) > tiltThreshold || abs(tiltY - lastTiltY) > tiltThreshold)
      && (millis() - lastTiltTime > 1000)) {
    onTiltDetected(tiltX, tiltY);
    lastTiltTime = millis();
  }

  lastTiltX = tiltX;
  lastTiltY = tiltY;
}

void onButtonPress() {
  Serial.println("Button Pressed - Getting recommendations...");
  String response = sendAPIRequest("button", "");

  display.clearDisplay();
  display.setCursor(0,0);
  display.println("Button Pressed");
  display.println("Getting movies...");
  display.display();
  delay(1000);
}

void onTiltDetected(float tiltX, float tiltY) {
  Serial.printf("Tilt Detected: X=%.2f, Y=%.2f\n", tiltX, tiltY);
  String tiltData = String(tiltX) + "," + String(tiltY);
  String response = sendAPIRequest("tilt", tiltData);

  display.clearDisplay();
  display.setCursor(0,0);
  display.println("Tilt Gesture");
  display.println("Navigating...");
  display.display();
  delay(1000);
}

String sendAPIRequest(String interactionType, String data) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(serverURL) + "/api/interact";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");

    DynamicJsonDocument doc(200);
    doc["type"] = interactionType;
    doc["data"] = data;
    doc["device"] = "esp32";

    String jsonPayload;
    serializeJson(doc, jsonPayload);

    Serial.println("Sending to: " + url);
    Serial.println("Payload: " + jsonPayload);

    int httpResponseCode = http.POST(jsonPayload);
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("API Response: " + response);
      displayRecommendations(response);
      return response;
    } else {
      Serial.println("API Error: " + String(httpResponseCode));
      displayError("API Error");
      return "Error";
    }
    http.end();
  } else {
    Serial.println("WiFi Not Connected");
    displayError("WiFi Disconnected");
    return "Offline";
  }
}

void displayRecommendations(String response) {
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, response);
  if (error) {
    Serial.print("JSON parse failed: ");
    Serial.println(error.c_str());
    displayDemoRecommendations();
    return;
  }

  if (doc.containsKey("recommendations")) {
    JsonArray movies = doc["recommendations"];
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("Top 3 Movies");
    display.println("---------------");

    int displayCount = (movies.size() < 3) ? movies.size() : 3;
    for (int i = 0; i < displayCount; i++) {
      String title = movies[i]["title"];
      float score = movies[i]["score"];

      if (title.length() > 15)
        title = title.substring(0, 15) + "...";

      display.setCursor(0, 16 + (i * 16));
      display.print(i + 1);
      display.print(". ");
      display.println(title);
      display.setCursor(20, 24 + (i * 16));
      display.print("⭐");
      display.println(score, 1);
    }
    display.display();
  } else {
    displayDemoRecommendations();
  }
}

void displayDemoRecommendations() {
  display.clearDisplay();
  display.setCursor(0,0);
  display.println("Top 3 Movies");
  display.println("---------------");
  display.setCursor(0, 16);
  display.println("1. Toy Story");
  display.setCursor(20, 24);
  display.println("⭐4.8");
  display.setCursor(0, 32);
  display.println("2. Godfather");
  display.setCursor(20, 40);
  display.println("⭐4.7");
  display.setCursor(0, 48);
  display.println("3. Inception");
  display.setCursor(20, 56);
  display.println("⭐4.9");
  display.display();
}

void displayError(String error) {
  display.clearDisplay();
  display.setCursor(0,0);
  display.println("Error:");
  display.println(error);
  display.display();
}
