const sensor  = "temperature";
document.addEventListener("DOMContentLoaded", function(){
    const wardrobeBtn = document.getElementById("wardrobe-button");
    const profileBtn = document.getElementById("profile-button");

    wardrobeBtn.addEventListener("click", () => {
        window.location.href = "/wardrobe";
    });

    profileBtn.addEventListener("click", () => {
        window.location.href = "/profile";
    });

    fetch(`/api/getId`)
        .then(response => response.json())
        .then(data => {
            userId = data.user_id;
            getWeather(userId)
            fetchDevices(userId).then(devices =>{
                const chartContainer = document.getElementById("charts-container");
                chartContainer.innerHTML = "";

                devices.forEach(device => {
                    const { device_id, mac_address } = device;
                    console.log(mac_address);

                    // new chart canvas for each device
                    const chartWrapper = document.createElement("div");
                    chartWrapper.innerHTML = `
                        <h3>Device ${device_id} Temperature</h3>
                        <canvas id=${device_id}></canvas>
                    `;
                    chartContainer.appendChild(chartWrapper);

                    fetchSensorData(mac_address, device_id); // fetch and plot sensor data
                });
            });
        })
    .catch(error => console.error("Error getting User ID:", error))
});

// Function to get weather from api
function getWeather(userId) {
    fetch(`/api/location/${userId}`)
    .then(response => response.json())
    .then(async data => {
        // fetch city coordinates from OpenStreetMap
        let geoResponse = await fetch(`https://nominatim.openstreetmap.org/search?q=${data.location}&format=json`);
        let geoData = await geoResponse.json

        // cgecks if valid city
        if(geoData.length == 0){
            alert("city not found");
            return;
        }
        let lat = geoData[0].lat;
        let lon = geoData[0].lon;

        // fetch weather API from National Weather Service
        let weatherResponse = await fetch(`https://api.weather.gov/points/${lat},${lon}`);
        let weatherData = await weatherResponse.json();

        // get forecast URL
        const forecastUrl = weatherData.properties.forecast;
        let forecastResponse = await fetch(forecastUrl);
        let forecastData = await forecastResponse.json();

        let weather = forecastData.properties.periods[0]; // gets current weather info

        // updates weather results info 
        document.getElementById("location").textContent = "Location:" + geoData[0].display_name;
        document.getElementById("condition").textContent = "Weather Condition(s):" + weather.shortForecast;
        document.getElementById("temperature").textContent = "Temperature:" + weather.temperature + "°F";
    })
}


// Function to fetch devices for a user
function fetchDevices(userId) {
    return fetch(`/api/devices/${userId}`)
        .then(response => response.json())
        .then(data => {
            if (!data.devices || data.devices.length === 0) {
                console.warn(`No devices found for user ${userId}`);
                return [];
            }
            return data.devices
        })
        .catch(error => {
            console.error(`Error fetching devices for user ${userId}:`, error);
            return [];
        });
}

function fetchSensorData(mac_address, deviceId){
    fetch(`/api/temperature/${mac_address}`)
        .then(response => response.json())
        .then(data => {
            const timestamps = data.map(entry => entry.timestamp);
            const values = data.map(entry => entry.value);

            createChart(`${deviceId}`, timestamps, values);
        })
        .catch (error => console.error(`error fetching ${sensor} data:`, error));
}

function createChart(chartId, labels, data){
    const canvas = document.getElementById(chartId);
    // Ensure the canvas exists before creating a chart
    if (!canvas) {
        console.error(`Canvas with id ${chartId} not found!`);
        return;
    }
    const ctx = canvas.getContext("2d");

    new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: `Temperature over time`,
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
                y: {title: {display: true, text: "Temperature (°C)"}}
            }
        }
    });
}
