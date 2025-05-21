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
                const sid = sessionStorage.getItem('sid');

                btn.onclick = async () => {
                    const response = await window.electronAPI.download(file, sid);

                    const msg = document.getElementById("downloadMsg");
                    if(response.success) {
                        msg.innerHTML = `File downloaded successfully to ${response.filePath}`;
                        msg.style.color = "green";
                    }else{
                        msg.innerHTML = response.error || "Download failed!";
                        msg.style.color = "red";
                    }
                };

                btnTd.appendChild(btn);
                tr.appendChild(btnTd);

                // Grant Access button column
                const grantTd = document.createElement("td");
                const grantBtn = document.createElement("button");
                grantBtn.textContent = "Grant Access";
                grantBtn.onclick = async () => {
                    // jump to grant.html 
                    sessionStorage.setItem('file', file);
                    window.location.href = "grant.html";
                };

                grantTd.appendChild(grantBtn);
                tr.appendChild(grantTd);

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