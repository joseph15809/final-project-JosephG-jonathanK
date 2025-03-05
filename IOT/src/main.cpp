#include "ECE140_WIFI.h"
#include "ECE140_MQTT.h"
#include <Adafruit_BMP085.h>

// WiFi credentials
const char* ucsdUsername = UCSD_USERNAME;
const char* ucsdPassword = UCSD_PASSWORD;
const char* wifiSsid = WIFI_SSID;
const char* nonEnterpriseWifiPassword = NON_ENTERPRISE_WIFI_PASSWORD;
const char* clientId = CLIENT_ID;
const char* topicPrefix = TOPIC_PREFIX;

Adafruit_BMP085 bmp;

ECE140_MQTT mqtt(clientId, topicPrefix);
ECE140_WIFI wifiManager;

void setup() {
    Serial.begin(115200);
    
    if (!bmp.begin()) {
        Serial.println("Could not find a valid BMP085 sensor, check wiring!");
        while (1) {}
      }

    wifiManager.connectToWPAEnterprise(wifiSsid, ucsdUsername, ucsdPassword);
    // wifiManager.connectToWiFi(wifiSsid, nonEnterpriseWifiPassword);

    // Connect to MQTT Broker
    if (mqtt.connectToBroker()) {
        Serial.println("[ESP32] MQTT Connection Successful!");
    } else {
        Serial.println("[ESP32] MQTT Connection Failed!");
    }
    
}

void loop() {
    float tempValue = bmp.readTemperature();
    float pressureValue = bmp.readPressure();
    unsigned long timestamp = millis();

    String message = "{";
    message += "\"temperature\":" + String(tempValue) + ",";
    message += "\"pressure\":" + String(pressureValue);
    message += "}";

    if (mqtt.publishMessage("readings", message)) {
        Serial.println("[ESP32] Sensor data published successfully: " + message);
    } 
    else {
        Serial.println("[ESP32] Failed to publish sensor data");
    }
    mqtt.loop();
    delay(5000);

    
}