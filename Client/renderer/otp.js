const apiBaseUrl = sessionStorage.getItem('apiBaseUrl');
const email = sessionStorage.getItem('email');

document.getElementById('otpUsername').innerText = `OTP already sent to ${email}`;

document.getElementById('otpForm').addEventListener('submit', async function(event) {
    event.preventDefault(); 

    const otp = document.getElementById('otp').value;
    console.log(email, otp);

    try {
        const result = await window.electronAPI.otp(email, otp);
        const msg = document.getElementById('otpMsg');
        if (result.success) {
            msg.innerHTML = "OTP verified! Redirecting...";
            setTimeout(() => {
                window.location.href = "main.html";
            }, 2000);
        } else {
            msg.innerHTML = result.error || "OTP verification failed!";
            msg.style.color = "red";
        }
    } catch (err) {
        logger.error(err.message);
    }
});