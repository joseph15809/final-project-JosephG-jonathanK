document.addEventListener("DOMContentLoaded", () => {
    const wardrobeBtn = document.getElementById("wardrobe-button");
    const profileBtn = document.getElementById("profile-button");

    wardrobeBtn.addEventListener("click", () => {
        window.location.href = "/wardrobe";
    });

    profileBtn.addEventListener("click", () => {
        window.location.href = "/profile";
    });
});