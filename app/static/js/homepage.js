document.addEventListener("DOMContentLoaded", () => {
    const loginBtn = document.getElementById("login");
    const signupBtn = document.getElementById("signup");

    loginBtn.addEventListener("click", () => {
        window.location.href = "/login";
    });

    signupBtn.addEventListener("click", () => {
        window.location.href = "/signup";
    });
});