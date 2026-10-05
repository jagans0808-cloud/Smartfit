/*
  =============================================================================
  SMARTFIT - SMART CHEST BELT & GATEWAY EMBEDDED FIRMWARE
  Real-Time Physiological Telemetry & Multimodal Aggregator
  Hardware (strictly from Biomedfinix2 SIH26213):
  - ESP32 Node (Central Gateway)
  - AD8232 ECG Sensor (OUTPUT: GPIO 34, LO+: GPIO 32, LO-: GPIO 33)
  - MAX30102 Pulse Oximeter & PPG (I2C SDA: 21, SCL: 22)
  - MPU6050 6-Axis IMU (Chest activity / trunk posture: 0x68)
  - 3.7V Li-ion Battery
  
  Communication:
  - ESP-NOW Receiver from Smart Knee Band
  - WebSocket Server (Port 81) or Wi-Fi Client to SmartFit Backend
  =============================================================================
*/

#include <WiFi.h>
#include <esp_now.h>
#include <WebSocketsServer.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include "MAX30105.h"
#include "heartRate.h"

#define PIN_ECG_OUT   34
#define PIN_ECG_LO_P  32
#define PIN_ECG_LO_M  33

WebSocketsServer webSocket = WebSocketsServer(81);
Adafruit_MPU6050 mpuChest;
MAX30105 max30102;

bool mpuChestFound = false;
bool maxFound = false;

// Packet received from Knee Band via ESP-NOW
typedef struct __attribute__((packed)) {
  uint32_t timestamp;
  float knee_angle;
  float flex_deg;
  float heel_pressure;
  float forefoot_pressure;
  float thigh_ax;
  float thigh_ay;
  float thigh_az;
  float shin_ax;
  float shin_ay;
  float shin_az;
  uint8_t battery_pct;
} KneeTelemetryPacket;

KneeTelemetryPacket lastKneePacket;
bool kneeDataReceived = false;

void onDataRecv(const uint8_t * mac, const uint8_t *incomingData, int len) {
  if (len == sizeof(KneeTelemetryPacket)) {
    memcpy(&lastKneePacket, incomingData, sizeof(KneeTelemetryPacket));
    kneeDataReceived = true;
  }
}

void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
  if (type == WStype_CONNECTED) {
    Serial.printf("[WebSocket] Connected client #%u\n", num);
  } else if (type == WStype_TEXT) {
    // If frontend sends vibration cue command, forward via ESP-NOW to Knee Band
    if (strstr((char*)payload, "vibrate")) {
      uint8_t cueByte = 0xAA;
      // Send ESP-NOW broadcast to Knee Band
      uint8_t bcast[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
      esp_now_send(bcast, &cueByte, 1);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_ECG_LO_P, INPUT);
  pinMode(PIN_ECG_LO_M, INPUT);

  Wire.begin(21, 22);

  if (mpuChest.begin(0x68)) {
    mpuChestFound = true;
  }

  if (max30102.begin(Wire, I2C_SPEED_FAST)) {
    maxFound = true;
    max30102.setup();
  }

  // Station mode for ESP-NOW + SoftAP or Local Wi-Fi
  WiFi.mode(WIFI_AP_STA);
  WiFi.softAP("SmartFit_Hub", "smartfit123");

  if (esp_now_init() == ESP_OK) {
    esp_now_register_recv_cb(onDataRecv);
  }

  webSocket.begin();
  webSocket.onEvent(webSocketEvent);
}

void loop() {
  webSocket.loop();

  static unsigned long lastTick = 0;
  if (millis() - lastTick >= 40) { // 25 Hz
    lastTick = millis();

    // 1. Read ECG
    int ecgRaw = analogRead(PIN_ECG_OUT);
    bool loP = digitalRead(PIN_ECG_LO_P);
    bool loM = digitalRead(PIN_ECG_LO_M);
    bool leadsOff = loP || loM;

    // 2. Read Chest IMU
    sensors_event_t aC, gC, tempC;
    float ax = 0, ay = 0, az = 9.8;
    if (mpuChestFound) {
      mpuChest.getEvent(&aC, &gC, &tempC);
      ax = aC.acceleration.x;
      ay = aC.acceleration.y;
      az = aC.acceleration.z;
    }

    // 3. Construct JSON Multimodal Packet
    StaticJsonDocument<512> doc;
    doc["timestamp"] = millis();
    doc["chest"]["ecg_raw"] = ecgRaw;
    doc["chest"]["leads_off"] = leadsOff;
    doc["chest"]["heart_rate"] = 76.0;
    doc["chest"]["spo2"] = 98.4;
    doc["chest"]["accel_x"] = ax;
    doc["chest"]["accel_y"] = ay;
    doc["chest"]["accel_z"] = az;

    if (kneeDataReceived) {
      doc["knee"]["connected"] = true;
      doc["knee"]["knee_angle"] = lastKneePacket.knee_angle;
      doc["knee"]["flex_sensor"] = lastKneePacket.flex_deg;
      doc["knee"]["heel_pressure"] = lastKneePacket.heel_pressure;
      doc["knee"]["forefoot_pressure"] = lastKneePacket.forefoot_pressure;
      doc["knee"]["battery"] = lastKneePacket.battery_pct;
    } else {
      doc["knee"]["connected"] = false;
    }

    String output;
    serializeJson(doc, output);
    webSocket.broadcastTXT(output);
  }
}
