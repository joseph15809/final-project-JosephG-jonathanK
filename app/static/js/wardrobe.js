document.addEventListener("DOMContentLoaded", () => {
    const dashboardBtn = document.getElementById("dashboard-button");
    const profileBtn = document.getElementById("profile-button");

    dashboardBtn.addEventListener("click", () => {
        window.location.href = "/dashboard";
    });

    profileBtn.addEventListener("click", () => {
        window.location.href = "/profile";
    });

    fetch("/api/wardrobe", {
        method: "GET"
    })
    .then(response => response.json())
    .then(data => {
        let clothesList = document.getElementById("clothes-list");
        clothesList.innerHTML = "";

        data.forEach(item => {
            const card = document.createElement("div");
            card.classList.add("clothes-card");

            // Name, type, color
            const nameInput = document.createElement("input");
            nameInput.type = "text";
            nameInput.classList.add("clothing-name");
            nameInput.value = item.name;
            nameInput.disabled = true;
            const typeInput = document.createElement("input");
            typeInput.type = "text";
            typeInput.value = item.type;
            typeInput.disabled = true;
            const colorInput = document.createElement("input");
            colorInput.type = "text";
            colorInput.value = item.color;
            colorInput.disabled = true;

            // Edit Button
            const editButton = document.createElement("button");
            editButton.classList.add("edit-button");
            editButton.textContent = "Edit";

            // Save Button
            const saveButton = document.createElement("button");
            saveButton.classList.add("save-button");
            saveButton.textContent = "Save";
            saveButton.style.display = "none";

            // Remove Button
            const removeButton = document.createElement("button");
            removeButton.classList.add("remove-button");
            removeButton.textContent = "Remove";

            // Toggle Edit Mode
            editButton.addEventListener("click", () => {
                nameInput.disabled = false;
                nameInput.focus();
                typeInput.disabled = false;
                typeInput.focus();
                colorInput.disabled = false;
                colorInput.focus();
                editButton.style.display = "none";
                saveButton.style.display = "inline-block";
            });

            // Save Changes
            saveButton.addEventListener("click", () => {
                fetch(`/api/wardrobe/update`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({"id": item.id, "name": nameInput.value, "clothes_type": typeInput.value, "color": colorInput.value})
                })
                .then(response => response.json())
                .then(() => {
                    nameInput.disabled = true;
                    typeInput.disabled = true;
                    colorInput.disabled = true;
                    editButton.style.display = "inline-block";
                    saveButton.style.display = "none";
                });
            });

            removeButton.addEventListener("click", () => {
                fetch(`/api/wardrobe/remove`, {
                    method: "DELETE",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({"id": item.id, "name": nameInput.value, "clothes_type": typeInput.value, "color": colorInput.value})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        card.remove(); // Removes item from the UI
                    } else {
                        alert("Error removing clothing item");
                    }
                })
                .catch(error => {
                    console.error("Error:", error);
                    alert("Failed to remove clothing item");
                });
            });
            // Assemble Card
            card.appendChild(nameInput);
            card.appendChild(typeInput);
            card.appendChild(colorInput);
            card.appendChild(editButton);
            card.appendChild(saveButton);
            card.appendChild(removeButton);
            clothesList.appendChild(card);
        });
    });
});