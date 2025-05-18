const email = sessionStorage.getItem('email');
document.getElementById('welcome').innerText = `Welcome ${email}`;

function goToLogin() {
    sessionStorage.removeItem('email');
    window.location.href = "login.html";
}

document.getElementById("uploadForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const file = document.getElementById("fileInput").files[0];
    const sid = sessionStorage.getItem('sid');

    const arrayBuffer = await file.arrayBuffer(); 
    console.log(file.name);
    console.log(file.type);
    console.log(arrayBuffer);
    console.log(sid);

    const result = await window.electronAPI.upload(file.name, file.type, arrayBuffer, sid);

    const msg = document.getElementById("uploadMsg");
    if (result.success) {
        msg.innerHTML = `${result.fileName} uploaded successfully!`;
        msg.style.color = "green";
    } else {
        msg.innerHTML = result.error || "File upload failed!";
        msg.style.color = "red";
    }
})