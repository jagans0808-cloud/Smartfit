/*
  =============================================================================
  SMARTFIT - SMART KNEE BAND EMBEDDED FIRMWARE
  Real-Time Biomechanical Kinematics & Biofeedback
  Hardware (strictly from Biomedfinix2 SIH26213):
  - ESP32 Node
  - MPU6050 x2/3 (Thigh IMU: 0x68, Shin IMU: 0x69)
  - Flex Sensor (Anatomical joint bending: GPIO 36)
  - FSR x2/4 (Heel pressure: GPIO 39, Forefoot pressure: GPIO 34)
  - Vibration Motor (Tactile form cue: GPIO 26)
  - 3.7V Li-ion Battery
  
  Communication:
  - ESP-NOW Peer-to-Peer Link to Chest Belt Gateway (Cable-Free)
  =============================================================================
*/

#include <esp_now.h>
#include <WiFi.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// Pin Definitions strictly adhering to ADC1 rules
#define PIN_FLEX_SENSOR   36  // ADC1_CH0 (Flex Sensor)
#define PIN_FSR_HEEL      39  // ADC1_CH3 (Plantar Heel FSR)
#define PIN_FSR_FOREFOOT  34  // ADC1_CH6 (Plantar Forefoot FSR)
#define PIN_BATTERY_ADC   35  // ADC1_CH7 (Li-ion battery voltage)
#define PIN_VIBRATION     26  // Digital output to NPN transistor / Haptic motor

Adafruit_MPU6050 mpuThigh;
Adafruit_MPU6050 mpuShin;

bool thighImuFound = false;
bool shinImuFound = false;

// Peer MAC Address of Chest Belt ESP32 (Gateway)
uint8_t chestBeltMac[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF}; // Broadcast or paired MAC

// Structured telemetry packet for ESP-NOW
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

KneeTelemetryPacket kneeData;

void onDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  // Feedback callback for ESP-NOW delivery
}

void onDataRecv(const uint8_t * mac, const uint8_t *incomingData, int len) {
  // Received vibration motor command from gateway
  if (len == 1 && incomingData[0] == 0xAA) {
    digitalWrite(PIN_VIBRATION, HIGH);
    delay(400);
    digitalWrite(PIN_VIBRATION, LOW);
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_VIBRATION, OUTPUT);
  digitalWrite(PIN_VIBRATION, LOW);

  Wire.begin(21, 22);

  // Initialize Thigh IMU (Address 0x68)
  if (mpuThigh.begin(0x68)) {
    thighImuFound = true;
    mpuThigh.setAccelerometerRange(MPU6050_RANGE_4_G);
  }

  // Initialize Shin IMU (Address 0x69 via AD0 pulled HIGH)
  if (mpuShin.begin(0x69)) {
    shinImuFound = true;
    mpuShin.setAccelerometerRange(MPU6050_RANGE_4_G);
  }

  // Initialize Wi-Fi in Station Mode for ESP-NOW (No router/Internet required)
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  if (esp_now_init() == ESP_OK) {
    Serial.println("[ESP-NOW] Initialized successfully");
    esp_now_register_send_cb(onDataSent);
    esp_now_register_recv_cb(onDataRecv);

    esp_now_peer_info_t peerInfo = {};
    memcpy(peerInfo.peer_addr, chestBeltMac, 6);
    peerInfo.channel = 0;
    peerInfo.encrypt = false;
    esp_now_add_peer(&peerInfo);
  }
}

void loop() {
  // 1. Read Flex Sensor & convert ADC to degrees (180 deg = straight, 90 deg = bent)
  int flexRaw = analogRead(PIN_FLEX_SENSOR);
  float flexDeg = map(flexRaw, 1200, 3200, 0, 90);

  // 2. Read Plantar Pressure (FSR)
  int heelRaw = analogRead(PIN_FSR_HEEL);
  int forefootRaw = analogRead(PIN_FSR_FOREFOOT);
  float heelP = (heelRaw / 4095.0) * 100.0;
  float forefootP = (forefootRaw / 4095.0) * 100.0;

  // 3. Read IMU Kinematics
  sensors_event_t aT, gT, tempT;
  sensors_event_t aS, gS, tempS;
  float thighPitch = 0.0, shinPitch = 0.0;

  if (thighImuFound) {
    mpuThigh.getEvent(&aT, &gT, &tempT);
    thighPitch = atan2(aT.acceleration.y, aT.acceleration.z) * 180.0 / PI;
  }
  if (shinImuFound) {
    mpuShin.getEvent(&aS, &gS, &tempS);
    shinPitch = atan2(aS.acceleration.y, aS.acceleration.z) * 180.0 / PI;
  }

  // Relative Joint Angle
  float kneeAngle = 180.0 - abs(thighPitch - shinPitch);

  // Populate Telemetry
  kneeData.timestamp = millis();
  kneeData.knee_angle = kneeAngle;
  kneeData.flex_deg = flexDeg;
  kneeData.heel_pressure = heelP;
  kneeData.forefoot_pressure = forefootP;
  kneeData.thigh_ax = aT.acceleration.x;
  kneeData.thigh_ay = aT.acceleration.y;
  kneeData.thigh_az = aT.acceleration.z;
  kneeData.shin_ax = aS.acceleration.x;
  kneeData.shin_ay = aS.acceleration.y;
  kneeData.shin_az = aS.acceleration.z;
  kneeData.battery_pct = 95;

  // Transmit wirelessly over ESP-NOW to Chest Belt Node
  esp_now_send(chestBeltMac, (uint8_t *) &kneeData, sizeof(kneeData));

  delay(40); // 25 Hz sampling rate
}
