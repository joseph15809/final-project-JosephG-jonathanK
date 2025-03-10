document.addEventListener("DOMContentLoaded", function(){
    const sensor  = "temperature";
    let deviceIds = [];

    

    fetchDevices(userId).then(devices => {
        deviceIds = devices;  // Store device IDs
        deviceIds.forEach(deviceId => {
            fetchSensorData(sensor, deviceId, userId);
        });
    });
    document.getElementById("wardrobe").addEventListener("click", function(event){
        event.preventDefault();
        window.location.href = `/wardrobe/${userId}`;
    });

});


// Function to fetch devices for a user
function fetchDevices(userId) {
    fetch(`/api/devices/${userId}`)
        .then(response => response.json())
        .then(data => {
            if (!data.devices || data.devices.length === 0) {
                console.warn(`No devices found for user ${userId}`);
                return [];
            }
            return data.devices.map(device => device.device_id);  //Extract device IDs
        })
        .catch(error => {
            console.error(`Error fetching devices for user ${userId}:`, error);
            return [];
        });
}

function fetchSensorData(sensorType, deviceId, userId){
    fetch(`/api/${sensorType}/${userId}/${deviceId}`)
        .then(response => response.json())
        .then(data => {
            const timestamps = data.map(entry => entry.timestamp);
            const values = data.map(entry => entry.value);

            createChart(sensorType, timestamps, values);
        })
        .catch (error => console.error(`error fetching ${sensorType} data:`, error));
}

function createChart(sensorType, labels, data){
    const ctx = document.getElementById(`${sensorType}Chart`).getContext("2d");

    new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: `${sensorType} over time`,
                data: data,
                borderColor: "rgb(156, 175, 136)",
                backgroundColor: "rgba(156, 175, 136, 0.2)",
                fill: false
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {title: {display: true, text: "Timestamp"}},
                y: {title: {display: true, text: "Value"}}
            }
        }
    });
}



