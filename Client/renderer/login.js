function goToRegister() {
    window.location.href = "register.html";
}

document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const result = await window.electronAPI.login(email, password);
    
    const msg = document.getElementById("message");
  
    if (result.success) {
      sessionStorage.setItem('email', result.email);
      sessionStorage.setItem('apiBaseUrl', result.apiBaseUrl);
      msg.innerHTML = "OTP sent! Redirecting to OTP page...";
      setTimeout(() => {
        window.location.href = "otp.html";
      }, 2000);
    } else {
      msg.innerHTML = result.error || "Login failed!";
      msg.style.color = "red";
    }
  });