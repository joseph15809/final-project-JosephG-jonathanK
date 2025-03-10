document.addEventListener("DOMContentLoaded", () => {
    const dashboardBtn = document.getElementById("dashboard-button");
    const profileBtn = document.getElementById("profile-button");

    dashboardBtn.addEventListener("click", () => {
        window.location.href = "/dashboard";
    });

    profileBtn.addEventListener("click", () => {
        window.location.href = "/profile";
    });
});