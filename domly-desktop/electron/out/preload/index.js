"use strict";
const electron = require("electron");
electron.contextBridge.exposeInMainWorld("domly", {
  invoke: (channel, data) => electron.ipcRenderer.invoke(channel, data),
  on: (channel, callback) => {
    const handler = (_event, ...args) => callback(...args);
    electron.ipcRenderer.on(channel, handler);
    return () => electron.ipcRenderer.removeListener(channel, handler);
  }
});
