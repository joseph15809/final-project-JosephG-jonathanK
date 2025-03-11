document.addEventListener("DOMContentLoaded", function () {
    loadUserInfo();
    document.getElementById("update-user-form").addEventListener("submit", function (event) {
        event.preventDefault();
        updateUserInfo();
    });
    getUserId();
});

// Fetch user id
function getUserId() {
    fetch(`/api/getId`)
        .then(response => response.json())
        .then(data => {
            userId = data.user_id;
            loadAvailableDevices(userId);
            loadUserDevices(userId);
        })
    .catch(error => console.error("Error getting User ID:", error))
}

// Fetch user info
function loadUserInfo() {

    fetch(`/api/userInfo`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error("Error fetching user info:", data.error);
                return;
            }

            document.getElementById("name").value = data.name;
            document.getElementById("email").value = data.email;  // Email stays uneditable
            document.getElementById("location").value = data.location;
        })
        .catch(error => console.error("Error loading user info:", error));
}

// Update user info
function updateUserInfo() {
    const name = document.getElementById("name").value;
    const location = document.getElementById("location").value;
    const currentPassword = document.getElementById("current_password").value;
    const newPassword = document.getElementById("new_password").value;
    const confirmPassword = document.getElementById("confirm_password").value;

    const requestData = { name, location };

    // Only include password fields if user wants to update their password
    if (currentPassword && newPassword && confirmPassword) {
        requestData.current_password = currentPassword;
        requestData.new_password = newPassword;
        requestData.confirm_password = confirmPassword;
    }

    fetch(`/api/updateUser`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        const message = document.getElementById("updateMessage");
        if (data.success) {
            message.textContent = "User info updated successfully!";
            message.style.color = "green";
        } else {
            message.textContent = "Error: " + data.detail;
            message.style.color = "red";
        }
    })
    .catch(error => console.error("Error updating user info:", error));
}


// Fetch devices already linked to the user
function loadUserDevices(userId) {
    fetch(`/api/devices/${userId}`)
        .then(response => response.json())
        .then(data => {
            const deviceList = document.getElementById("device-list");
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
function loadAvailableDevices(userId) {
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
                listItem.innerHTML = `Device ID: ${device.device_id}, MAC: ${device.mac_address} `;
                
                const addButton = document.createElement("button");  // Create a button element
                addButton.textContent = "Add Device";  
                addButton.dataset.deviceId = device.device_id;  // Store device_id in dataset
                addButton.addEventListener("click", function(event){
                    event.preventDefault();
                    addDeviceToProfile(userId, device.device_id)
                });

                listItem.appendChild(addButton);  // Append button to list item
                availableDevices.appendChild(listItem);
            });
        })
        .catch(error => console.error("Error loading available devices:", error));
}

function addDeviceToProfile(userId, deviceId) {
    fetch(`/api/add_device`, {
        method: "POST",
        headers: {"Content-Type": "application/json" },
        body: JSON.stringify({"user_id": userId, "device_id": deviceId })
    })
    .then(response => response.json())
    .then(data => {
        loadAvailableDevices(userId);
        loadUserDevices(userId);
    })
    .catch(error => console.error("Error adding device to profile:", error));
}