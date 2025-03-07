#include "ECE140_WIFI.h"

ECE140_WIFI::ECE140_WIFI() {
    Serial.println("[ECE140_WIFI] Initialized");
}

void ECE140_WIFI::connectToWiFi(String ssid, String password) {
  Serial.println("[WiFi] Connecting to WiFi...");
  WiFi.begin(ssid.c_str(), password.c_str());
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\n[WiFi] Connected to WiFi.");
  registerDevice();
}

void ECE140_WIFI::connectToWPAEnterprise(String ssid, String username, String password) {
  Serial.println("[WiFi] Connecting to WPA Enterprise...");

  WiFi.disconnect(true);  // Disconnect from any network
  WiFi.mode(WIFI_STA); // Set WiFi to Station Mode

  // Initialize the WPA2 Enterprise parameters
  esp_wifi_sta_wpa2_ent_set_identity((uint8_t *)username.c_str(), username.length());
  esp_wifi_sta_wpa2_ent_set_username((uint8_t *)username.c_str(), username.length());
  esp_wifi_sta_wpa2_ent_set_password((uint8_t *)password.c_str(), password.length());
  
  // Enable WPA2 Enterprise
  esp_wifi_sta_wpa2_ent_enable();

  WiFi.begin(ssid.c_str()); // Start connection attempt

  // Wait for connection result
  Serial.print("Waiting for connection...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[WiFi] Connected to WPA Enterprise successfully!");

  // Optional: Manually set DNS servers if DHCP does not work correctly
  ip_addr_t dnsserver;
  IP_ADDR4(&dnsserver, 8, 8, 8, 8);
  dns_setserver(0, &dnsserver);
}

void ECE140_WIFI::registerDevice() {
  HTTPClient http;
  String serverURL = "http://localhost:8000/api/register_device";

  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");

  uint8_t mac[6];  // Array to hold the MAC address
  WiFi.macAddress(mac);  // Get MAC address as a byte array

  char macStr[18];  // Buffer for formatted MAC address
  snprintf(macStr, sizeof(macStr), "%02X:%02X:%02X:%02X:%02X:%02X", 
           mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);


  String payload = "{\"mac_address\": \"" + String(macStr) + "\"}";

  int httpResponseCode = http.POST(payload);

  if (httpResponseCode == 200) {
      Serial.println("Device registered successfully!");
  } else {
      Serial.print("Error sending MAC to server: ");
      Serial.println(httpResponseCode);
  }

  http.end();
}


String ECE140_WIFI::macAddress() {
    uint8_t mac[6];  // Array to hold the MAC address
    WiFi.macAddress(mac);  // Get MAC address as a byte array

    char macStr[18];  // Buffer for formatted MAC address
    snprintf(macStr, sizeof(macStr), "%02X:%02X:%02X:%02X:%02X:%02X", 
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);

    return String(macStr);  // Return as a String
}

