document.addEventListener("DOMContentLoaded", () => {
    fetch("/api/wardrobe", {
        method: "GET"
    })
    .then(response => response.json())
    .then(data => {
        let removeList = document.getElementById("remove-list");
        let clothesList = document.getElementById("clothes-list");
        removeList.innerHTML = "";
        clothesList.innerHTML = "";
        data.forEach(item => {
            const option = document.createElement("option");
            const clothes = document.createElement("p");
            let optionString = "";
            let clothesString = "";
            optionString = "<option value='" + item.name + "'>" + item.name + "</option>";
            clothesString = "<p>" + item.name + "</p>";
            option.innerHTML = optionString;
            clothes.innerHTML = clothesString;
            removeList.appendChild(option);
            clothesList.appendChild(clothes);
        });
    })
    .catch(error => {
        console.error("Error fetching wardrobe items");
        removeList.innerHTML = "<option value=''>Error loading items</option>";
        clothesList.innerHTML = "<p>Error loading clothes</p>";
    });
});
