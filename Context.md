# ARIA Project - Concise Context

**Project Name:** ARIA (AI-Powered Voice-Controlled Smart Home)  
**Duration:** 4 weeks  
**Team:** 2 developers  
**Status:** Ready to start

---

## WHAT IS ARIA?

A **voice-controlled smart home system** where you speak commands and Claude AI controls your home devices.

**Example:**

```
You: "Turn on living room lights and set temperature to 72"
         ↓
ARIA captures voice
         ↓
Claude understands intent
         ↓
Controls your SmartRent devices
         ↓
You hear: "Lights are on, temperature set to 72"
```

**Key Features:**

- Speak commands naturally
- Claude AI understands what you mean
- Works from anywhere (cloud-hosted)
- Controls 5 types of devices: lights, thermostat, locks, sensors, scenes

---

## THE ARCHITECTURE (Simple View)

```
You speak
    ↓
Desktop App (on your MacBook)
    ├─ Captures voice
    ├─ Sends to Claude API
    └─ Plays response back
         ↓
    Claude API
    ├─ Understands command
    ├─ Calls your MCP server
    └─ Gets device status
         ↓
    Remote MCP Server (on Railway.app)
    ├─ Defines 5 smart home tools
    ├─ Controls SmartRent devices
    └─ Returns results
         ↓
    SmartRent API
    ├─ Turns lights on/off
    ├─ Adjusts thermostat
    ├─ Locks/unlocks doors
    └─ Controls scenes
         ↓
Your devices physically respond
```

---

## TWO SEPARATE CODE REPOSITORIES

### **Repository 1: aria-smartrent-mcp**

**What:** Remote MCP server (the brain)  
**Where:** Cloud (Railway.app)  
**Language:** Python + Flask  
**Runs:** 24/7

**What it does:**

- Listens for commands from Claude
- Defines 5 smart home tools
- Calls SmartRent API
- Returns results

**5 Tools:**

1. `get_device_status()` - Check device status
2. `control_light(room, action, brightness)` - Control lights
3. `set_temperature(temp, mode)` - Adjust thermostat
4. `lock_door(door, action)` - Lock/unlock doors
5. `set_scene(scene)` - Activate scenes (movie mode, sleep mode, etc)

---

### **Repository 2: aria-voice-assistant**

**What:** Desktop voice app (the interface)  
**Where:** Your MacBook  
**Language:** Python + tkinter/PyQt  
**Runs:** When you launch it

**What it does:**

- Shows desktop window
- Captures voice from microphone
- Sends to Whisper API (transcription)
- Shows what you said
- Sends text to Claude API
- Claude calls your MCP server
- Plays response back through speaker
- Shows device responses

---

## 4-WEEK BUILD PLAN

### **Week 1-2: Build Backend (aria-smartrent-mcp)**

**Person A Lead**

Day-by-day:

- **Day 1-2:** Create Flask app, project structure, version control
- **Day 2-4:** Build MCP server (handles Claude requests)
- **Day 4-5:** Implement 5 tools (light, temp, lock, scene, status)
- **Day 5-6:** Test everything locally
- **Day 6-7:** Deploy to Railway.app (go live!)

**Result:** Live server at `https://aria-smartrent-[yourname].railway.app`

---

### **Week 2-3: Connect External Services**

**Person B Lead**

- **Day 8-10:** Set up Claude API integration
- **Day 10-12:** Set up Whisper (speech-to-text)
- **Day 12-13:** Set up ElevenLabs (text-to-speech)
- **Day 13-14:** Test full pipeline (voice → Claude → devices → voice)

**Result:** All services working together

---

### **Week 3-4: Build Frontend (aria-voice-assistant)**

**Person A Lead**

- **Day 15-17:** Create desktop app with UI (buttons, text display)
- **Day 17-19:** Add microphone capture and speaker output
- **Day 19-21:** Connect to remote MCP server
- **Day 21-24:** Polish, test, document

**Result:** Working voice app on your MacBook

---

## TECH STACK (Simple)

```
Backend Server:
- Python 3.9+
- Flask (web framework)
- Gunicorn (production server)
- Railway.app (hosting)

Desktop App:
- Python 3.9+
- tkinter or PyQt5 (UI)
- pyaudio (microphone)
- pygame (speaker)

External APIs (you don't build these):
- Claude API (Anthropic) - AI understanding
- Whisper (OpenAI) - speech to text
- ElevenLabs - text to speech
- SmartRent API - device control
```

---

## WHO DOES WHAT?

### **Person A**

- Week 1-2: Build MCP server backend
- Week 3-4: Build desktop voice app UI

### **Person B**

- Week 1-2: SmartRent API integration
- Week 2-3: Claude, Whisper, ElevenLabs integration
- Week 3-4: Audio handling (mic/speaker)

### **Both**

- Daily 15-min standup
- Code review before merging
- Final testing and documentation

---

## DEPLOYMENT FLOW

```
Step 1: Build locally
        └─ Code on your MacBook

Step 2: Deploy backend to Railway
        └─ aria-smartrent-mcp runs in cloud 24/7

Step 3: Run frontend locally
        └─ aria-voice-assistant runs on your MacBook

Step 4: They communicate via internet
        └─ Desktop app → Remote MCP server → SmartRent devices
```

---

## SUCCESS CRITERIA

**Backend working:**

- ✅ All 5 tools callable
- ✅ Devices respond correctly
- ✅ Deployed and live
- ✅ <2 second response time

**Frontend working:**

- ✅ Microphone captures voice
- ✅ Text displays on screen
- ✅ Claude responds with speech
- ✅ Speaker plays response
- ✅ <5 second total latency

**End result:**

- ✅ Speak command
- ✅ Hear response
- ✅ Devices controlled
- ✅ Two GitHub projects
- ✅ Portfolio-ready

---

## BEFORE YOU START

Get these:

- [ ] SmartRent API key
- [ ] Claude API key
- [ ] Whisper API key (OpenAI)
- [ ] ElevenLabs API key
- [ ] Railway.app account

Create:

- [ ] GitHub repo: aria-smartrent-mcp
- [ ] GitHub repo: aria-voice-assistant

Decide:

- [ ] Person A and Person B roles
- [ ] Daily standup time
- [ ] Communication channel (Slack, Discord, WhatsApp)

---

## QUICK START

**Day 1:**

```
Person A:
- Clone aria-smartrent-mcp
- Set up Python virtual environment
- Create basic Flask app
- Verify it runs on localhost:5000

Person B:
- Research SmartRent API
- Get API credentials
- Test connecting to SmartRent
```

**Daily:**

- 9 AM: 15-min standup
- 10 AM - 5 PM: Development
- End of day: Commit code, update progress

**Weekly:**

- Monday: Plan week
- Friday: Demo progress
- Sunday: Retrospective

---

## PORTFOLIO VALUE

When you finish, you have:

- 2 professional GitHub repositories
- Backend service running in cloud
- Desktop application working
- Integration with 4+ external APIs
- Complete documentation
- Interview-ready story

**Interview story:**

> "I built ARIA, a voice-controlled smart home system. It has two parts: a remote MCP server on the cloud that defines smart home tools, and a desktop voice app. When you speak a command, the app transcribes it with Whisper, sends to Claude API which calls my server tools, and the server controls SmartRent devices. Then the response converts to speech and plays back. The whole system is production-grade with error handling and logging."

---

## ONE-PAGE SUMMARY

| Aspect        | Details                                                    |
| ------------- | ---------------------------------------------------------- |
| **What**      | Voice-controlled smart home via Claude AI                  |
| **How**       | 2 GitHub repos: cloud MCP server + desktop app             |
| **Duration**  | 4 weeks (2 devs)                                           |
| **Tech**      | Python, Flask, Railway, Claude API                         |
| **Result**    | Speak command → home responds → you hear confirmation      |
| **Portfolio** | 2 professional projects, cloud deployment, API integration |

---

**That's it. Start building.**
