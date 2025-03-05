document.addEventListener("DOMContentLoaded", () => {
    const loginContainer = document.querySelector(".login-container");
    const signupContainer = document.querySelector(".signup-container");

    login.addEventListener("click", () => {
        window.location.href = "/login";
    });

    signupContainer.addEventListener("click", () => {
        window.location.href = "/signup";
    });
});