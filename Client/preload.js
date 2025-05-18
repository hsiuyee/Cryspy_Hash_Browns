const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  login: (email, password) => ipcRenderer.invoke('login', { email, password }),
  register: (email, password) => ipcRenderer.invoke('register', { email, password }), 
  otp: (email, otp) => ipcRenderer.invoke('otp', { email, otp }),
});
