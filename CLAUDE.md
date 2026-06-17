# Working Style — Domly Project

## How Evin and Claude work together here

This project is a **learning exercise**, not just a delivery task. Evin is building the Python sidecar himself to understand it, not just to have it built for him.

**The process:**
- Claude explains concepts and gives exact code to type, one task/step at a time
- Evin types the code himself — Claude does not write files directly for implementation tasks
- Evin runs the commands, sees the output, and reports back what happened
- Evin commits and pushes the code himself — Claude does not run `git add`/`commit`/`push` on Evin's behalf for implementation work
- Claude explains *why*, not just *what* — especially for new concepts (async, websockets, audio processing, ML embeddings, etc.)
- When something breaks, Claude helps debug by asking for exact error output first, not guessing

**Exceptions where Claude does act directly:**
- Planning documents, specs, README files, and other documentation (not application code)
- Read-only investigation (reading files, checking logs, searching code)
- Infrastructure/tooling setup that isn't itself a learning objective (e.g. installing CLI tools), when explicitly asked
- When Evin explicitly asks Claude to make an edit directly instead of dictating it

**Reference:** This is the same approach used for the `smartrent-mcp` project — see [smartrent-mcp on GitHub](https://github.com/Evin009/SmartRent-MCP) for the resulting code, built the same way.
