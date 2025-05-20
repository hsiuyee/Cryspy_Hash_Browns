async function fetchFileList() {
    try{
        const result = await window.electronAPI.list_file();
        if (result.success) {
            const files = result.files;
            const tbody = document.getElementById("file-body");
            tbody.innerHTML = "";  

            files.forEach(file => {
                const tr = document.createElement("tr");

                // file name column 
                const nameTd = document.createElement("td");
                nameTd.textContent = file;
                tr.appendChild(nameTd);

                // Download button column
                const btnTd = document.createElement("td");
                const btn = document.createElement("button");
                btn.textContent = "Download";
                const sid = sessionStorage.getItem('sid'); // TODO: Modify ? 
               btn.onclick = () => {
                window.electronAPI.download(file, sid);
                };

                btnTd.appendChild(btn);
                tr.appendChild(btnTd);

                tbody.appendChild(tr);
            });
        } else {
            document.getElementById("downloadMsg").textContent = result.error || "File list retrieval failed!";
        }
    }catch(err){
        const msg = document.getElementById("downloadMsg");
        msg.innerHTML = "Unexpected error occurred!";
        msg.style.color = "red";
    }
}

window.onload = fetchFileList;