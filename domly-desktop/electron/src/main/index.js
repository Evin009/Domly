import { app, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { authController } from './controllers/authController'

function createWindow() {
  const win = new BrowserWindow({
    width: 420,
    height: 620,
    resizable: false,
    center: true,
    title: 'Domly',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false
    }
  })

  if (process.env['ELECTRON_RENDERER_URL']) {
    win.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    win.loadFile(join(__dirname, '../renderer/index.html'))
  }

  return win
}

app.whenReady().then(() => {
  authController.register(ipcMain)
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
