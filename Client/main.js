const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { handleLogin, handleRegister, handleOTP } = require('./backend/auth.js');

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'), 
      contextIsolation: true, 
      nodeIntegration: false  
    }
  });

  mainWindow.loadFile('templates/login.html');
}

app.whenReady().then(() => {
  createWindow();
});

app.on('window-all-closed', function() {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Handle login event 
ipcMain.handle('login', handleLogin);

// Handle register event
ipcMain.handle('register', handleRegister);

// Handle enter otp event 
ipcMain.handle('otp', handleOTP);

