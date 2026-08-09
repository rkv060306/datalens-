// Auth Module JS
document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const userBadge = document.getElementById("user-name-badge");

  // Load user status
  const userStr = localStorage.getItem("datalens_user");
  if (userStr && userBadge) {
    try {
      const u = JSON.parse(userStr);
      userBadge.textContent = u.name || u.email || "Guest Analyst";
    } catch (e) {}
  }

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;

      try {
        const res = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Login failed");

        APIClient.setAuthToken(data.access_token);
        localStorage.setItem("datalens_user", JSON.stringify(data.user));
        APIClient.showToast("Login successful!", "success");
        setTimeout(() => window.location.href = "index.html", 800);
      } catch (err) {
        APIClient.showToast(err.message, "error");
      }
    });
  }

  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = document.getElementById("name").value;
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;
      const confirmPassword = document.getElementById("confirmPassword")?.value;

      if (confirmPassword && password !== confirmPassword) {
        APIClient.showToast("Passwords do not match!", "error");
        return;
      }

      try {
        const res = await fetch("/api/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Registration failed");

        APIClient.setAuthToken(data.access_token);
        localStorage.setItem("datalens_user", JSON.stringify(data.user));
        APIClient.showToast("Account created successfully!", "success");
        setTimeout(() => window.location.href = "index.html", 800);
      } catch (err) {
        APIClient.showToast(err.message, "error");
      }
    });
  }
});

function logoutUser() {
  localStorage.removeItem("datalens_token");
  localStorage.removeItem("datalens_user");
  APIClient.showToast("Logged out.", "info");
  setTimeout(() => window.location.href = "index.html", 500);
}
