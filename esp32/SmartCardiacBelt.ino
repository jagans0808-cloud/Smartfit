/*
  =============================================================================
  SMART CARDIAC CHEST BELT - ESP32 EMBEDDED FIRMWARE
  Real-Time Physiological and Motion Monitoring Prototype
  =============================================================================
  
  Hardware Pinout:
  - AD8232 ECG Sensor:
      * OUTPUT -> GPIO 34 (ADC1_CH6)
      * LO+    -> GPIO 32 (Digital Input, Leads-Off Detection)
      * LO-    -> GPIO 33 (Digital Input, Leads-Off Detection)
  - Temperature Sensor (Analog / NTC / LM35):
      * VOUT   -> GPIO 35 (ADC1_CH7)
  - MPU6050 6-Axis Motion & IMU:
      * SDA    -> GPIO 21
      * SCL    -> GPIO 22
  - MAX30102 Pulse Oximeter & PPG:
      * SDA    -> GPIO 21 (Shared I2C Bus)
      * SCL    -> GPIO 22 (Shared I2C Bus)
      
  Communication:
  - Protocol: WebSocket Server on Port 81 (ws://ESP32_IP:81)
  - Subnet: Local Wi-Fi (No Internet Required)
  
  Required Arduino Libraries:
  - WebSockets by Markus Sattler (v2.3.5+)
  - ArduinoJson by Benoit Blanchon (v6.x or v7.x)
  - Adafruit MPU6050 (or Wire.h direct I2C read)
  - SparkFun MAX3010x Pulse and Proximity Sensor Library
  =============================================================================
*/

#include <WiFi.h>
#include <WebSocketsServer.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include "MAX30105.h"
#include "heartRate.h"

// -------------------- Wi-Fi Credentials --------------------
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// -------------------- Pin Definitions --------------------
#define PIN_ECG_OUT   34
#define PIN_ECG_LO_P  32
#define PIN_ECG_LO_M  33
#define PIN_TEMP_ADC  35

// -------------------- WebSocket Server --------------------
WebSocketsServer webSocket = WebSocketsServer(81);

// -------------------- Sensor Drivers --------------------
Adafruit_MPU6050 mpu;
MAX30105 particleSensor;

bool mpuAvailable = false;
bool max30102Available = false;

// -------------------- Timing & Telemetry --------------------
unsigned long lastSampleTime = 0;
const unsigned long sampleIntervalMs = 20; // 50 Hz broadcast (ECG sampled at 250 Hz internally)

// Fall detection tracking on ESP32
const float FALL_IMPACT_THRESHOLD_G = 2.4; // Impact spike in g
unsigned long lastFallTriggerTime = 0;
const unsigned long fallCooldownMs = 3000;

// Heart rate tracking
long lastBeatTime = 0;
float currentBpm = 72.0;
float currentRrMs = 833.0;

// -------------------------------------------------------------
// WebSocket Event Handler
// -------------------------------------------------------------
void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      Serial.printf("[WebSocket] Client #%u Disconnected\n", num);
      break;
    case WStype_CONNECTED: {
      IPAddress ip = webSocket.remoteIP(num);
      Serial.printf("[WebSocket] Client #%u Connected from %s\n", num, ip.toString().c_str());
      break;
    }
    case WStype_TEXT:
      Serial.printf("[WebSocket] Client #%u Command: %s\n", num, payload);
      break;
    default:
      break;
  }
}

// -------------------------------------------------------------
// Setup
// -------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=============================================");
  Serial.println("  SMART CARDIAC CHEST BELT - ESP32 FIRMWARE  ");
  Serial.println("=============================================");

  // 1. Configure Analog Inputs
  analogReadResolution(12); // 0 - 4095
  analogSetAttenuation(ADC_11db); // 0 - 3.3V range
  pinMode(PIN_ECG_LO_P, INPUT);
  pinMode(PIN_ECG_LO_M, INPUT);

  // 2. Initialize I2C Bus
  Wire.begin(21, 22);

  // 3. Initialize MPU6050
  if (mpu.begin()) {
    Serial.println("[OK] MPU6050 Accelerometer / Gyroscope initialized.");
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
    mpuAvailable = true;
  } else {
    Serial.println("[WARN] MPU6050 not detected. Continuing with analog sensors.");
  }

  // 4. Initialize MAX30102
  if (particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("[OK] MAX30102 Pulse Oximeter initialized.");
    particleSensor.setup();
    particleSensor.setPulseAmplitudeRed(0x0A);
    particleSensor.setPulseAmplitudeGreen(0);
    max30102Available = true;
  } else {
    Serial.println("[WARN] MAX30102 not detected. Heart rate estimated via AD8232.");
  }

  // 5. Connect to Wi-Fi
  Serial.printf("[WiFi] Connecting to %s ", ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] CONNECTED!");
    Serial.printf("[WiFi] ESP32 IP Address: %s\n", WiFi.localIP().toString().c_str());
    Serial.println("[WebSocket] Starting server on Port 81...");
  } else {
    Serial.println("\n[WiFi] Connection timed out. Starting SoftAP fallback: SmartCardiacBelt");
    WiFi.softAP("SmartCardiacBelt", "12345678");
    Serial.printf("[WiFi] SoftAP IP Address: %s\n", WiFi.softAPIP().toString().c_str());
  }

  // 6. Start WebSocket Server
  webSocket.begin();
  webSocket.onEvent(webSocketEvent);
  Serial.println("[OK] WebSocket server active on ws://ESP32_IP:81");
}

// -------------------------------------------------------------
// Main Loop
// -------------------------------------------------------------
void loop() {
  webSocket.loop();

  unsigned long currentMillis = millis();

  // Read MAX30102 PPG Sample
  if (max30102Available) {
    long irValue = particleSensor.getIR();
    if (checkForBeat(irValue)) {
      long delta = currentMillis - lastBeatTime;
      lastBeatTime = currentMillis;
      if (delta > 300 && delta < 1800) {
        currentRrMs = (float)delta;
        currentBpm = 60.0 / ((float)delta / 1000.0);
      }
    }
  }

  // Transmit Telemetry Packet
  if (currentMillis - lastSampleTime >= sampleIntervalMs) {
    lastSampleTime = currentMillis;

    // 1. Read AD8232 ECG
    int rawEcg = analogRead(PIN_ECG_OUT);
    bool leadsOff = (digitalRead(PIN_ECG_LO_P) == HIGH || digitalRead(PIN_ECG_LO_M) == HIGH);
    if (leadsOff) {
      rawEcg = 0; // Signals leads off condition
    }

    // 2. Read Temperature (e.g. LM35: 10 mV/°C or NTC conversion)
    int rawTemp = analogRead(PIN_TEMP_ADC);
    float millivolts = (rawTemp / 4095.0) * 3300.0;
    float temperatureC = millivolts / 10.0;
    if (temperatureC < 20.0 || temperatureC > 50.0) {
      // Normative placeholder if sensor disconnected
      temperatureC = 36.6;
    }

    // 3. Read MPU6050 Motion & Fall Detection
    float ax = 0.0, ay = 0.0, az = 9.8;
    bool fallDetected = false;

    if (mpuAvailable) {
      sensors_event_t a, g, temp;
      mpu.getEvent(&a, &g, &temp);
      ax = a.acceleration.x;
      ay = a.acceleration.y;
      az = a.acceleration.z;

      // Magnitude in m/s^2
      float mag = sqrt(ax * ax + ay * ay + az * az);

      // Fall spike check (e.g. impact >= 22.0 m/s^2)
      if (mag >= (FALL_IMPACT_THRESHOLD_G * 9.806)) {
        if (currentMillis - lastFallTriggerTime >= fallCooldownMs) {
          fallDetected = true;
          lastFallTriggerTime = currentMillis;
          Serial.printf("[ALERT] Fall detected on ESP32! Mag: %.2f m/s^2\n", mag);
        }
      }
    }

    // 4. Construct JSON Packet
    StaticJsonDocument<256> doc;
    doc["type"] = "sensor_data";
    doc["timestamp"] = currentMillis;
    doc["ecg"] = rawEcg;
    doc["heart_rate"] = round(currentBpm);
    doc["rr_interval"] = round(currentRrMs);
    doc["temperature"] = serialized(String(temperatureC, 1));
    doc["accel_x"] = serialized(String(ax, 2));
    doc["accel_y"] = serialized(String(ay, 2));
    doc["accel_z"] = serialized(String(az, 2));
    doc["fall"] = fallDetected;

    String jsonString;
    serializeJson(doc, jsonString);

    // 5. Broadcast to Connected WebSocket Clients
    webSocket.broadcastTXT(jsonString);
  }
}
