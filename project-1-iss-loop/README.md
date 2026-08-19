# Project 1: Watch the Space Station (ISS Heartbeat Loop)

> **Panaversity Agent Factory — Loop Engineering Crash Course: Concept 4**  
> *In-session recurring loops: Observe on a heartbeat while you watch.*

---

## 🛰 Project Overview

Project 1 demonstrates an **in-session heartbeat loop**. The AI agent is configured with specialized tools and pre-granted permissions to continuously track and report the live orbital telemetry of the International Space Station (ISS) every minute without requiring repetitive user prompts.

The ISS travels at approximately **7.65 km/s (27,500+ km/h)**. Because satellite positions change dynamically every second, recalling a position from model training weights or estimating an orbit is fundamentally inaccurate. This project establishes the principle of **honest tool-driven observation**: every loop beat fetches fresh telemetry from an external API (`api.wheretheiss.at`), extracts the exact coordinates, altitude, speed, and visibility, and formats the output consistently.

---

## ⚙️ How the Loop Works

```text
               ┌───────────────────────────┐
               │    User Starts Session    │
               │  /loop 1m track the ISS   │
               └─────────────┬─────────────┘
                             │
                             ▼
               ┌───────────────────────────┐
         ┌────►│       Heartbeat Beat      │◄────┐
         │     │ (Fires every 60 seconds)  │     │
         │     └─────────────┬─────────────┘     │
         │                   │                   │
         │                   ▼                   │
         │     ┌───────────────────────────┐     │
         │     │  Fetch Live Telemetry     │     │
         │     │  (python3 iss.py)         │     │
         │     └─────────────┬─────────────┘     │
         │                   │                   │
         │                   ▼                   │
         │     ┌───────────────────────────┐     │
         │     │  Render Telemetry Card &  │     │
         │     │  Identify Geographic Area │     │
         │     └─────────────┬─────────────┘     │
         │                   │                   │
         └───────────────────┴───────────────────┘
```

### 1. The Heartbeat Trigger
Using Claude Code's `/loop` slash command (or timer schedules), the agent establishes a recurring timer:
```bash
/loop show me the location of the ISS every minute
```

### 2. Live Telemetry Fetching
The agent delegates data retrieval to the bundled script `.claude/skills/iss-position/scripts/iss.py`.
- **API Endpoint:** `https://api.wheretheiss.at/v1/satellites/25544`
- **Zero Cache / Zero Fallback:** If the network request fails, the script exits non-zero and reports the error. The agent never hallucinates a plausible position.

### 3. Display Card Output
Every beat renders an aligned telemetry card followed by an interpretive geographic summary:

```text
  🛰  INTERNATIONAL SPACE STATION            live · 17:17:57 UTC
  ──────────────────────────────────────────────────────────
     Position    49.2° S      105.8° W
     Altitude    432 km
     Speed       27,557 km/h   (7.65 km/s)
     Sunlight    in sunlight
  ──────────────────────────────────────────────────────────

Deep in the southern Pacific, roughly halfway between New Zealand and Chile.
```

---

## ⏱ The In-Session Lifecycle Boundary

A critical distinction taught in this project is that this is an **in-session loop**:
- **Session Bound:** The loop lives entirely in memory during the active CLI session.
- **What Happens When the Session Ends:** When you close your terminal or exit the session, **the loop immediately terminates**.
- **The Kitchen Timer Analogy:** An in-session loop is like a kitchen timer — it rings while you are in the kitchen, but it is not a background daemon, a cron job, or a persistent autonomous system.

---

## 📁 Repository Structure

| Path | Purpose |
| :--- | :--- |
| `AGENTS.md` | Universal instruction file read by any AI agent, establishing the rule to always run `iss.py` rather than answering from memory. |
| `CLAUDE.md` | Single-line import ensuring Claude Code imports `AGENTS.md`. |
| `.claude/settings.json` | Pre-granted tool permissions (`Bash`, `WebFetch`) so the recurring loop executes smoothly without interrupting the user for permissions every minute. |
| `.claude/skills/iss-position/SKILL.md` | Skill contract specifying card formatting, geographical elaboration, and failure handling. |
| `.claude/skills/iss-position/scripts/iss.py` | Python 3 standard library script for HTTP request handling, JSON parsing, and card rendering. |

---

## 🧠 Key Takeaways & Lessons Learned

1. **Tool Observation Beats LLM Memory:** Fast-moving real-world data cannot be predicted or recalled. Grounding an agent in dedicated deterministic tools is the foundation of agentic engineering.
2. **Frictionless Loop Beats:** Recurring loops need pre-authorized permissions (`.claude/settings.json`); otherwise, approval dialogues break the automated cadence.
3. **Failure Honesty:** In an automated loop, a failed beat that reports an error is infinitely better than a plausible guess that corrupts telemetry.
4. **Session Boundaries:** In-session loops are ideal for real-time monitoring while at your desk, but long-running or goal-driven tasks require state persistence, external verification, and safety caps (the basis of Project 2).
