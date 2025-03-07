#include "ECE140_WIFI.h"
#include "ECE140_MQTT.h"
#include <Adafruit_BMP085.h>

// WiFi credentials
const char* ucsdUsername = UCSD_USERNAME;
const char* ucsdPassword = UCSD_PASSWORD;
const char* wifiSsid = WIFI_SSID;
const char* nonEnterpriseWifiPassword = NON_ENTERPRISE_WIFI_PASSWORD;
// MQTT client - using descriptive client ID and topic
const char* clientId = CLIENT_ID;
const char* topicPrefix = TOPIC_PREFIX;

Adafruit_BMP085 bmp;
ECE140_MQTT mqtt(clientId, topicPrefix);
ECE140_WIFI wifi;

void setup() {
    Serial.begin(115200);
    


    // Connect to BMP085 Sensor
    if (!bmp.begin()) {
        Serial.println("[Main] Could not find a valid BMP085 sensor");
    }

    // Connect to MQTT Broker
    if (!mqtt.connectToBroker()) {
        Serial.println("[Main] Failed to connect to MQTT broker");
    }

    // Connect to WiFi
    // wifi.connectToWPAEnterprise(wifiSsid, ucsdUsername, ucsdPassword);
    wifi.connectToWiFi(wifiSsid, nonEnterpriseWifiPassword);

}

void loop() {
    mqtt.loop();
    float tempValue = bmp.readTemperature();
    float pressureValue = bmp.readPressure();

    String macAddress = wifi.macAddress();

    String payload = "{";
    payload += "\"temperature\":" + String(tempValue) + ",";
    payload += "\"mac_address\":" + macAddress;
    payload += "}";

    mqtt.publishMessage("readings", payload);

    // Delay for 2 seconds
    delay(2000); 
}
