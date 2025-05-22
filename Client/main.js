const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { handleLogin, handleRegister, handleOTP, handleOTPRegister} = require('./backend/auth.js');
const { handleUpload, handleListFile, handleDownload} = require('./backend/file.js');
const { handleGrantAccess } = require('./backend/grant.js');

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

app.commandLine.appendSwitch('lang', 'zh-TW');  // 簡中 zh-CN，繁中 zh-TW

app.whenReady().then(() => {
  createWindow();
});

app.on('window-all-closed', function() {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// app.SetLocale('zh-TW');

// Authentication 
ipcMain.handle('login', handleLogin);
ipcMain.handle('register', handleRegister);
ipcMain.handle('otp', handleOTP);
ipcMain.handle('otp_register', handleOTPRegister);

// File operation 
ipcMain.handle('upload', handleUpload);
ipcMain.handle('list_file', handleListFile);
ipcMain.handle('download', handleDownload);

// Grant Access
ipcMain.handle('grant_access', handleGrantAccess);
