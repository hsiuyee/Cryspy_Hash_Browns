const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  login: (email, password) => ipcRenderer.invoke('login', { email, password }),
  register: (email, password) => ipcRenderer.invoke('register', { email, password }), 
  otp: (email, otp) => ipcRenderer.invoke('otp', { email, otp }),
  otp_register: (email, otp) => ipcRenderer.invoke('otp_register', { email, otp }),
  upload: (fileName, fileType, fileBuffer, sid) => ipcRenderer.invoke('upload', { fileName, fileType, fileBuffer, sid }),
  list_file: () => ipcRenderer.invoke('list_file'),
  download: (fileName, sid, savePath) => ipcRenderer.invoke('download', { fileName, sid, savePath }),
  grant_access: (fileName, email, sid) => ipcRenderer.invoke('grant_access', { fileName, email, sid }),
});
