# Domly — Voice-Controlled Smart Home Desktop App — Design Spec
**Date:** 2026-06-16
**Status:** Approved

---

## What We're Building

Domly is a downloadable desktop app (Mac + Windows) that lets a user control their SmartRent smart home devices entirely by voice, hands-free, using a wake word — similar in feel to Alexa/Siri, but running on the user's computer, powered by Claude, and **🆕 NEW: locked to one registered voice so only the owner can issue commands.**

This supersedes the older `Context.md` in this repo, which described a simpler 2-week prototype without wake word detection, conversation mode, voice authentication, or a proper account system. This spec reflects the actual agreed design.

---

## Team & Repos

| Repo | Purpose |
|---|---|
| `domly-desktop` | Desktop app — contains both the Python sidecar and the Electron UI as subfolders |
| `domly-backend` | Auth + SmartRent credential storage |
| `domly-landing` | Marketing site + download page |

The two of you own different halves of `domly-desktop`, plus `domly-backend` and `domly-landing` as described below. The Python sidecar and Electron UI communicate over a local WebSocket connection (contract defined in Evin's section).

---

## Architecture Overview

```
domly-landing (marketing site)
    ↓ user downloads installer
domly-desktop (Electron UI + Python sidecar)
    ↓ user logs in once
domly-backend (Node/Express/MongoDB)
    ↓ returns SmartRent credentials (encrypted)
domly-desktop caches credentials locally
    ↓
Python sidecar: wake word → 🆕 speaker verification → STT → Claude → smartrent-mcp tools → TTS
    ↓
SmartRent API → user's real devices
```

`domly-desktop` reuses the existing published `smartrent-mcp` package (PyPI) as its MCP tool layer — no need to rebuild device control logic.

---

## Evin — Python Sidecar (`domly-desktop/python/`)

**Owns:** The entire voice/AI core. Runs as a background process spawned by Electron. Exposes a local WebSocket server that Electron connects to.

### Responsibilities

1. **WebSocket server** — local server (e.g. `ws://127.0.0.1:8765`) that Electron connects to as a client
2. **Wake word detection** — continuously listens for "Hey Domly" using a local engine (e.g. Porcupine)
3. **🆕 NEW: Voice authentication (speaker verification)** — after wake word, verifies the speaker is the enrolled owner before processing any command
4. **🆕 NEW: Voice enrollment** — one-time setup flow where the user records sample phrases to create their voice profile
5. **Voice Activity Detection (VAD)** — determines when the user has stopped speaking
6. **Speech-to-text** — sends audio to Whisper, gets back transcribed text
7. **Claude orchestration** — sends transcribed text to Claude API with `smartrent-mcp` tools available, lets Claude call tools to control real devices
8. **Text-to-speech** — sends Claude's response to ElevenLabs, plays audio back
9. **Conversation mode** — keeps listening for ~8 seconds after each response so the user can follow up without repeating the wake word
10. **Local encrypted storage** — caches SmartRent credentials and 🆕 the voice embedding so the user isn't re-prompted on every launch

### Full Runtime Flow

```
Wake word detected
    ↓
Record audio
    ↓
🆕 NEW STEP: Speaker verification — does this voice match the enrolled owner?
    ↓ yes                                    ↓ no
Continue                          Reject — no action taken, optional
    ↓                              spoken "Voice not recognized"
Voice Activity Detection (VAD)
    ↓
Whisper → transcribed text
    ↓
Claude API (with smartrent-mcp tools)
    ↓
Claude calls tools → controls real SmartRent devices
    ↓
Claude's response → ElevenLabs → played back
    ↓
Stay in conversation mode for ~8 seconds
    ↓ user speaks again (no wake word needed)     ↓ silence
repeat from VAD                              return to wake-word-only listening
```

### 🆕 NEW: Voice Enrollment Flow (first-time setup)

1. Electron prompts user to record 3-5 short phrases
2. Each recorded sample is sent to the Python sidecar over WebSocket
3. Sidecar generates a voice embedding (numerical fingerprint) from the samples using a speaker verification model (e.g. `Resemblyzer` or `SpeechBrain`, both local/offline)
4. Embedding is stored locally, encrypted, alongside cached credentials
5. From then on, every wake-word trigger is checked against this embedding before any command is processed

### WebSocket IPC Contract (Python sidecar ↔ Electron)

The Python sidecar is the WebSocket **server**; Electron is the **client**. Messages are JSON.

**Electron → Sidecar:**
```json
{ "type": "set_credentials", "sr_email": "...", "sr_password": "..." }
{ "type": "enroll_voice_start" }                          // 🆕 NEW
{ "type": "enroll_voice_sample", "audio": "<base64>" }    // 🆕 NEW
{ "type": "mute" }
{ "type": "unmute" }
{ "type": "quit" }
```

**Sidecar → Electron (status pushes):**
```json
{ "type": "status", "state": "idle" | "listening" | "processing" | "speaking" | "error" }
{ "type": "conversation_event", "role": "user" | "assistant", "text": "..." }
{ "type": "enrollment_complete", "success": true }        // 🆕 NEW
{ "type": "voice_rejected" }                              // 🆕 NEW
{ "type": "error", "message": "..." }
```

This contract is the boundary between Evin's and Vaibhav's work — as long as both sides honor it, each can build and test independently before integrating.

---

## Vaibhav — Electron UI (`domly-desktop/electron/`) + Backend (`domly-backend`)

**Owns:** Everything the user sees and clicks, plus the account/auth system the desktop app depends on.

### Electron UI Responsibilities

1. **App shell** — spawns the Python sidecar as a background process on launch, connects to it as a WebSocket client
2. **Login window** — email/password form, calls `domly-backend` `/auth/login`, sends returned SmartRent credentials to the Python sidecar via `set_credentials`
3. **🆕 NEW: Voice enrollment screen** — guides the user through recording 3-5 phrases, streams each sample to the sidecar via `enroll_voice_sample`, shows success/failure based on `enrollment_complete`
4. **Menu bar / system tray icon** — reflects sidecar `status` messages (idle / listening / processing / speaking / error)
5. **Conversation history window** — displays `conversation_event` messages as a running log
6. **Settings** — re-login, mic selection, log out, mute/unmute toggle

### Backend (`domly-backend`) Responsibilities

Implement, at minimum, this API contract (internal implementation — database schema, encryption method, session vs JWT — is yours to design):

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

---

## Both — Landing Page (`domly-landing`)

```
/           → hero, demo, download CTA
/download   → OS-detected installer download (Mac .dmg / Windows .exe)
/signup     → account creation, links to domly-backend
/docs       → setup guide, FAQ, troubleshooting
```

No device control happens here — purely marketing, distribution, and account entry point. Vaibhav leads (React/Next.js), Evin contributes content, demo material, and testing.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| No credentials cached on launch | Show login window, block wake word activation until logged in |
| 🆕 No voice enrolled yet | Block wake word activation until enrollment completes |
| Wake word false positive, no speech follows | Silent return to idle after ~3 seconds, no API calls made |
| 🆕 Voice doesn't match enrolled owner | Reject command, optional spoken "Voice not recognized", no API calls made |
| Whisper / Claude / ElevenLabs API failure | Spoken fallback: "Sorry, I'm having trouble right now" + visual error in app window |
| No internet connection | Wake word + voice verification still work locally; commands fail with spoken/visual offline message |
| Mic permission denied (OS-level) | Clear settings prompt shown on first launch |
| SmartRent credentials invalid/expired | Spoken/visual prompt to re-login |

---

## What's NOT in Scope (v1)

- Cross-device sync of conversation history
- Multiple SmartRent accounts per user
- 🆕 Multiple enrolled voices per device (only one owner voice)
- Custom wake word training
- Mobile app
- Scenes/automation beyond what `smartrent-mcp` already supports (lights, thermostat, locks, sensors)
- Billing/subscriptions

---

## Build Order

1. `domly-backend` — auth + credential storage (Vaibhav, can start immediately, independent of desktop app)
2. `domly-desktop` Python sidecar — wake word, 🆕 voice enrollment + verification, STT, Claude orchestration, `smartrent-mcp` integration, TTS (Evin, working against mock/local credentials first)
3. `domly-desktop` Electron shell — UI, tray icon, login window, 🆕 enrollment screen, wired to real `domly-backend` and the Python sidecar once both are ready (Vaibhav)
4. `domly-landing` — built in parallel once the product has something demoable (both)
5. Integration testing across all three
6. Packaging (electron-builder) for Mac + Windows distribution
