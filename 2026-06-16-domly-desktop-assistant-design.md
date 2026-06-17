# Domly — Voice-Controlled Smart Home Desktop App — Design Spec
**Date:** 2026-06-16
**Status:** Approved

---

## What We're Building

Domly is a downloadable desktop app (Mac + Windows) that lets users control their SmartRent smart home devices entirely by voice, hands-free, using a wake word — similar in feel to Alexa/Siri, but running on the user's computer and powered by Claude.

This supersedes the older `Context.md` in this repo, which described a simpler 2-week prototype without wake word detection, conversation mode, or a proper account system. This spec reflects the actual agreed design.

---

## Team & Task Split

| Task | Repo | Owner | Stack |
|---|---|---|---|
| Python Sidecar (voice/AI core) | `domly-desktop` (python/ subfolder) | You | Python — wake word, STT, Claude orchestration, `smartrent-mcp`, TTS |
| Electron UI + Backend/Auth | `domly-desktop` (electron/ subfolder) + `domly-backend` | Friend | Electron, Node.js, Express, MongoDB |
| Landing Page | `domly-landing` | Both | React / Next.js |

Finalized split: you own the Python sidecar exclusively. Your friend owns the Electron UI (tray icon, login window, conversation history window) and the backend (auth, credential storage). The two halves of `domly-desktop` communicate over a local WebSocket connection (see IPC section below).

---

## Architecture Overview

```
domly-landing (marketing site)
    ↓ user downloads installer
domly-desktop (Electron + Python sidecar)
    ↓ user logs in once
domly-backend (Node/Express/MongoDB)
    ↓ returns SmartRent credentials (encrypted)
domly-desktop caches credentials locally
    ↓
Python sidecar: wake word → STT → Claude → smartrent-mcp tools → TTS
    ↓
SmartRent API → user's real devices
```

`domly-desktop` reuses the existing published `smartrent-mcp` package (PyPI) as its MCP tool layer — no need to rebuild device control logic.

---

## Desktop App — Detailed Flow

### Startup
1. Electron main process launches
2. Spawns Python sidecar as a background process
3. Python sidecar starts a local WebSocket server (e.g. `ws://127.0.0.1:8765`)
4. Electron connects to it as a WebSocket client
5. If no cached credentials → Electron shows login window

### IPC — WebSocket Contract (Python sidecar ↔ Electron)

The Python sidecar is the WebSocket **server**; Electron is the **client**. Messages are JSON.

**Electron → Sidecar:**
```json
{ "type": "set_credentials", "sr_email": "...", "sr_password": "..." }
{ "type": "mute" }
{ "type": "unmute" }
{ "type": "quit" }
```

**Sidecar → Electron (status pushes):**
```json
{ "type": "status", "state": "idle" | "listening" | "processing" | "speaking" | "error" }
{ "type": "conversation_event", "role": "user" | "assistant", "text": "..." }
{ "type": "error", "message": "..." }
```

This contract is the boundary between your work and your friend's — as long as both sides honor it, you can each build and test independently before integrating.

### Login (first run only)
1. User enters email/password in Electron login window
2. Electron calls `domly-backend` `/auth/login`
3. Backend returns SmartRent credentials (decrypted, over HTTPS)
4. Electron sends `set_credentials` message to Python sidecar over WebSocket
5. Sidecar caches credentials locally (encrypted) so it doesn't need them resent on next launch

### Background Listening (steady state)
1. Python sidecar runs a wake word engine (e.g. Porcupine) continuously, listening for "Hey Domly"
2. Menu bar / system tray icon shows idle state
3. On wake word detected:
   - Short audio/visual cue (chime + icon change)
   - Starts recording microphone audio
   - Voice Activity Detection (VAD) determines when user stopped speaking
4. Recorded audio sent to Whisper → transcribed text
5. Transcribed text sent to Claude API, with `smartrent-mcp` tools available
6. Claude calls one or more MCP tools (e.g. `switch_control`, `set_temperature`) against the user's real SmartRent devices
7. Claude's text response sent to ElevenLabs → audio → played back to user
8. App stays in "conversation mode" for ~8 seconds after responding:
   - If user speaks again (no wake word needed) → repeats steps 4-8
   - If silence for 8 seconds → returns to wake-word-only listening

### Window (optional, opened via tray icon)
- Conversation history (recent commands + responses)
- Connection/device status
- Settings: re-login, mic selection, log out

---

## Backend — API Contract

`domly-backend` must implement, at minimum:

```
POST /auth/signup
Body: { email, password, sr_email, sr_password }
- Verifies SmartRent credentials work before storing
- Hashes platform password, encrypts SmartRent password
- Returns: { token }

POST /auth/login
Body: { email, password }
- Returns: { token }

GET /auth/credentials
Header: Authorization: Bearer <token>
- Returns: { sr_email, sr_password } (decrypted, HTTPS only)
```

Internal implementation (database schema, encryption method, session vs JWT) is left to the backend owner to design — this spec only fixes the external contract the desktop app depends on.

---

## Landing Page — Scope

```
/           → hero, demo, download CTA
/download   → OS-detected installer download (Mac .dmg / Windows .exe)
/signup     → account creation, links to domly-backend
/docs       → setup guide, FAQ, troubleshooting
```

No device control happens on the landing page — purely marketing + distribution + account entry point.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| No credentials cached on launch | Show login window, block wake word activation until logged in |
| Wake word false positive, no speech follows | Silent return to idle after ~3 seconds, no API calls made |
| Whisper / Claude / ElevenLabs API failure | Spoken fallback: "Sorry, I'm having trouble right now" + visual error in app window |
| No internet connection | Wake word detection still works locally; commands fail with spoken/visual offline message |
| Mic permission denied (OS-level) | Clear settings prompt shown on first launch |
| SmartRent credentials invalid/expired | Spoken/visual prompt to re-login |

---

## What's NOT in Scope (v1)

- Cross-device sync of conversation history
- Multiple SmartRent accounts per user
- Custom wake word training
- Mobile app
- Scenes/automation beyond what `smartrent-mcp` already supports (lights, thermostat, locks, sensors)
- Billing/subscriptions

---

## Build Order

1. `domly-backend` — auth + credential storage (friend, can start immediately, independent of desktop app)
2. `domly-desktop` Python core — wake word, STT, Claude orchestration, `smartrent-mcp` integration, working against mock/local credentials first
3. `domly-desktop` Electron shell — UI, tray icon, login window, wired to real `domly-backend` once both are ready
4. `domly-landing` — built in parallel once the product has something demoable
5. Integration testing across all three
6. Packaging (electron-builder) for Mac + Windows distribution
