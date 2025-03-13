document.addEventListener("DOMContentLoaded", function () {
    const wardrobeBtn = document.getElementById("wardrobe-button");
    const dashboardBtn = document.getElementById("dashboard-button");
    const manualBtn = document.getElementById("manual-add");
    const closeBtn = document.getElementById("close-form");
    const addDevice = document.getElementById("add-device");
    wardrobeBtn.addEventListener("click", () => {
        window.location.href = "/wardrobe";
    });

    dashboardBtn.addEventListener("click", () => {
        window.location.href = "/dashboard";
    });

    manualBtn.addEventListener("click", () => {
        document.getElementById("manual-add-container").style.display = "block";
        document.getElementById("overlay").style.display = "block"; 
    });

    closeBtn.addEventListener("click", () => {
        document.getElementById("manual-add-container").style.display = "none";
        document.getElementById("overlay").style.display = "none"; 
    });

    addDevice.addEventListener("click", () => {

    });

    loadUserInfo();
    document.getElementById("update-user-form").addEventListener("submit", function (event) {
        event.preventDefault();
        updateUserInfo();
    });
    getUserId();
});

// function to manually add device


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
            document.getElementById("email").value = data.email;
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
                // Create the device card
                const card = document.createElement("div");
                card.classList.add("device-card");

                // Create container for label + input (flexbox)
                const detailsContainer = document.createElement("div");
                detailsContainer.classList.add("device-details");

                // Name Label & Input
                const nameLabel = document.createElement("label");
                nameLabel.textContent = "Device Name:";
                const nameInput = document.createElement("input");
                nameInput.type = "text";
                nameInput.value = device.name;
                nameInput.disabled = true;

                // MAC Address Label & Input
                const macLabel = document.createElement("label");
                macLabel.textContent = "MAC Address:";
                const macInput = document.createElement("input");
                macInput.type = "text";
                macInput.value = device.mac_address;
                macInput.disabled = true;

                // Edit button
                const editButton = document.createElement("button");
                editButton.classList.add("edit-button", "device-card-button");
                editButton.textContent = "Edit";

                // Save button (Initially Hidden)
                const saveButton = document.createElement("button");
                saveButton.classList.add("save-button", "device-card-button", "save-btn");
                saveButton.textContent = "Save";
                saveButton.style.display = "none"; // Hidden by default

                // Remove button
                const removeButton = document.createElement("button");
                removeButton.classList.add("remove-button", "device-card-button", "remove-btn");
                removeButton.textContent = "Remove";

                // Edit Button Functionality
                editButton.addEventListener("click", () => {
                    nameInput.disabled = false;
                    macInput.disabled = false;
                    editButton.style.display = "none"; // Hide Edit button
                    saveButton.style.display = "inline-block"; // Show Save button
                });

                // Save Button Functionality
                saveButton.addEventListener("click", () => {
                    fetch(`/api/update_device`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            "id": device.device_id,
                            "mac_address": macInput.value,
                            "name": nameInput.value
                        })
                    })
                    .then(response => response.json())
                    .then(() => {
                        nameInput.disabled = true;
                        macInput.disabled = true;
                        editButton.style.display = "inline-block"; // Show Edit button
                        saveButton.style.display = "none"; // Hide Save button
                    })
                    .catch(error => console.error("Error updating device:", error));
                });

                // Remove Button Functionality
                removeButton.addEventListener("click", () => {
                    fetch(`/api/remove_device`, {
                        method: "DELETE",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ "id": device.device_id, "mac_address": device.mac_address })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            card.remove(); // Remove the device from UI
                        } else {
                            alert("Error removing device.");
                        }
                    })
                    .catch(error => {
                        console.error("Error:", error);
                        alert("Failed to remove device.");
                    });
                });

                // Append label and input pairs
                detailsContainer.appendChild(nameLabel);
                detailsContainer.appendChild(nameInput);
                detailsContainer.appendChild(macLabel);
                detailsContainer.appendChild(macInput);

                // Button Container (Edit & Remove buttons on the same line)
                const buttonContainer = document.createElement("div");
                buttonContainer.classList.add("button-container");
                buttonContainer.appendChild(editButton);
                buttonContainer.appendChild(saveButton);
                buttonContainer.appendChild(removeButton);

                // Append elements to the card
                card.appendChild(detailsContainer);
                card.appendChild(buttonContainer);
                deviceList.appendChild(card);
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
                addButton.id = "add-button";
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