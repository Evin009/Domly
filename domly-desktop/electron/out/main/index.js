"use strict";
const electron = require("electron");
const path = require("path");
const BACKEND_URL = "http://localhost:4000";
async function post(path2, body) {
  const res = await fetch(`${BACKEND_URL}${path2}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}
async function get(path2, token) {
  const res = await fetch(`${BACKEND_URL}${path2}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}
const backendService = {
  signup: (payload) => post("/auth/signup", payload),
  login: (payload) => post("/auth/login", payload),
  getCredentials: (token) => get("/auth/credentials", token)
};
const authController = {
  register(ipcMain) {
    ipcMain.handle("auth:signup", async (_event, payload) => {
      try {
        const { token } = await backendService.signup(payload);
        return { success: true, token };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });
    ipcMain.handle("auth:login", async (_event, payload) => {
      try {
        const { token } = await backendService.login(payload);
        return { success: true, token };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });
  }
};
function createWindow() {
  const win = new electron.BrowserWindow({
    width: 420,
    height: 620,
    resizable: false,
    center: true,
    title: "Domly",
    webPreferences: {
      preload: path.join(__dirname, "../preload/index.js"),
      sandbox: false
    }
  });
  if (process.env["ELECTRON_RENDERER_URL"]) {
    win.loadURL(process.env["ELECTRON_RENDERER_URL"]);
  } else {
    win.loadFile(path.join(__dirname, "../renderer/index.html"));
  }
  return win;
}
electron.app.whenReady().then(() => {
  authController.register(electron.ipcMain);
  createWindow();
  electron.app.on("activate", () => {
    if (electron.BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});
electron.app.on("window-all-closed", () => {
  if (process.platform !== "darwin") electron.app.quit();
});
