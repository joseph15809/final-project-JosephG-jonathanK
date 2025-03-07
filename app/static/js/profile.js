document.addEventListener("DOMContentLoaded", function () {
    const pathSegments = window.location.pathname.split("/");
    const userId = pathSegments[pathSegments.length - 1];  // Extract user_id from URL

    loadUserDevices(userId);
    loadAvailableDevices(userId);

    document.getElementById("add-device").addEventListener("click", function (event) {
        event.preventDefault();
        addDeviceToProfile(userId);
    });
});

// Fetch devices already linked to the user
function loadUserDevices(userId) {
    fetch(`/api/devices/${userId}`)
        .then(response => response.json())
        .then(data => {
            const deviceList = document.getElementById("deviceList");
            deviceList.innerHTML = ""; // Clear previous entries

            if (!data.devices || data.devices.length === 0) {
                deviceList.innerHTML = "<li>No devices registered under your account.</li>";
                return;
            }

            data.devices.forEach(device => {
                const listItem = document.createElement("li");
                listItem.textContent = `Device ID: ${device.device_id}, MAC: ${device.mac_address}, Name: ${device.name}`;
                deviceList.appendChild(listItem);
            });
        })
        .catch(error => console.error("Error loading user devices:", error));
}

// Fetch all available devices (devices not yet assigned to any user)
function loadAvailableDevices() {
    fetch(`/api/devices`)  // Endpoint to get unassigned ESP32 devices
        .then(response => response.json())
        .then(data => {
            const availableDevices = document.getElementById("available-devices");
            availableDevices.innerHTML = ""; // Clear previous entries

            if (!data.devices || data.devices.length === 0) {
                availableDevices.innerHTML = "<li>No available devices.</li>";
                return;
            }

            data.devices.forEach(device => {
                const listItem = document.createElement("li");
                listItem.innerHTML = `
                    Device ID: ${device.device_id}, MAC: ${device.mac_address}
                    <button onclick="addDeviceToProfile('${userId}', '${device.device_id}')">Add</button>
                `;
                availableDevices.appendChild(listItem);
            });
        })
        .catch(error => console.error("Error loading available devices:", error));
}

function addDeviceToProfile(userId, deviceId) {
    fetch(`/api/add_device/${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device_id: deviceId })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message); // Show success message
        loadUserDevices(userId); // Refresh the registered device list
        loadAvailableDevices(userId); // Refresh the available devices list
    })
    .catch(error => console.error("Error adding device to profile:", error));
}