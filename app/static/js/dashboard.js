const sensor  = "temperature";
var temperature;
var condition;
var charts = {};

document.addEventListener("DOMContentLoaded", function(){
    const wardrobeBtn = document.getElementById("wardrobe-button");
    const profileBtn = document.getElementById("profile-button");
    const outfitBtn = document.getElementById("outfit-button");

    wardrobeBtn.addEventListener("click", () => {
        window.location.href = "/wardrobe";
    });

    profileBtn.addEventListener("click", () => {
        window.location.href = "/profile";
    });

    outfitBtn.addEventListener("click",() =>{
        generateOutfit()
    });

    fetch(`/api/getId`)
        .then(response => response.json())
        .then(data => {
            userId = data.user_id;
            getWeather(userId);
            fetchDevices(userId).then(devices => {
                const chartContainer = document.getElementById("charts-container");
                chartContainer.innerHTML = "";

                devices.forEach(device => {
                    const { device_id, mac_address } = device;
                    console.log(mac_address);

                    // Create a new chart canvas for each device
                    const chartWrapper = document.createElement("div");
                    chartWrapper.innerHTML = `
                        <h3>Device ${device_id} Temperature</h3>
                        <canvas id="chart-${device_id}"></canvas>
                    `;
                    chartContainer.appendChild(chartWrapper);

                    fetchSensorData(mac_address, device_id);

                    // Start periodic updates every 5 seconds
                    setInterval(() => {
                        updateChart(mac_address, device_id);
                    }, 5000);
                });
            });
        })
        .catch(error => console.error("Error getting User ID:", error));
});

// Function to get weather from api
function getWeather(userId) {
    fetch(`/api/location/${userId}`)
    .then(response => response.json())
    .then(async data => {
        // fetch city coordinates from OpenStreetMap
        let geoResponse = await fetch(`https://nominatim.openstreetmap.org/search?q=${data.location}&format=json`);
        let geoData = await geoResponse.json()

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
        temperature = weather.temperature
        condition = weather.shortForecast
        // updates weather results info 
        document.getElementById("location").textContent = "Location:" + geoData[0].name;
        document.getElementById("condition").textContent = "Weather Condition(s):" + condition;
        document.getElementById("wind-speed").textContent = "Wind Speed:" + weather.windSpeed;  
        document.getElementById("temperature").textContent = "Temperature:" + temperature + "°F";
    })
}

// Function to generate outfit for user
function generateOutfit() {
    const outfitTextElement = document.getElementById("outfit-text");
    const thinkingText = document.getElementById("thinking-text");

    // Show "Thinking..." text and clear previous outfit
    thinkingText.style.display = "block";
    outfitTextElement.textContent = "";
    fetch(`/api/generate-outfit/${temperature}/${condition}`)
        .then(response => response.json())
        .then(data => {
            thinkingText.style.display = "none";
            const outfitText = data.outfit;
            typeText("outfit-text", outfitText);
        })
        .catch(error => {
            thinkingText.style.display = "none"; // Hide thinking if error occurs
            outfitTextElement.textContent = "Failed to load outfit. Try again.";
            console.error("Error fetching outfit:", error);
        });
}

// Function for typing effect
function typeText(elementId, text, speed = 50) {
    let i = 0;
    const element = document.getElementById(elementId);
    element.innerHTML = "";

    // Convert **bold** and *italic* to proper HTML
    text = text
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>");

    let tempHTML = ""; // Temporary string to store formatted text

    function type() {
        if (i < text.length) {
            tempHTML += text.charAt(i);
            element.innerHTML = tempHTML; // Update innerHTML each step
            i++;
            setTimeout(type, speed);
        }
    }
    type();
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

function fetchSensorData(mac_address, deviceId) {
    fetch(`/api/temperature/${mac_address}`)
        .then(response => response.json())
        .then(data => {
            const timestamps = data.map(entry => entry.timestamp);
            const values = data.map(entry => entry.value);
            
            createChart(`chart-${deviceId}`, timestamps, values);
        })
        .catch(error => console.error(`Error fetching ${sensor} data:`, error));
}

function createChart(chartId, labels, data) {
    const canvas = document.getElementById(chartId);
    if (!canvas) {
        console.error(`Canvas with id ${chartId} not found!`);
        return;
    }

    const ctx = canvas.getContext("2d");

    // Check if chart already exists and update instead of recreating
    if (charts[chartId]) {
        charts[chartId].data.labels = labels;
        charts[chartId].data.datasets[0].data = data;
        charts[chartId].update();
    } else {
        charts[chartId] = new Chart(ctx, {
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
                    x: { title: { display: true, text: "Timestamp" } },
                    y: { title: { display: true, text: "Temperature (°C)" } }
                }
            }
        });
    }
}

function updateChart(mac_address, deviceId) {
    fetch(`/api/temperature/${mac_address}`)
        .then(response => response.json())
        .then(data => {
            const timestamps = data.map(entry => entry.timestamp);
            const values = data.map(entry => entry.value);

            if (charts[`chart-${deviceId}`]) {
                charts[`chart-${deviceId}`].data.labels = timestamps;
                charts[`chart-${deviceId}`].data.datasets[0].data = values;
                charts[`chart-${deviceId}`].update();
            }
        })
        .catch(error => console.error(`Error updating chart for ${mac_address}:`, error));
}