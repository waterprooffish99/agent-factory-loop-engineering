# Agent Factory Loop Engineering

This repository contains the completed implementations of **Project 1** and **Project 2** from the **Panaversity Agent Factory Loop Engineering Crash Course**.

Loop Engineering is the discipline of structuring AI agent workflows into closed decision cycles: **Observe → Reason → Act → Validate**. Instead of open-ended conversational prompting, loop-engineered systems operate against explicit contracts, external verifiable checkers, and defined stopping conditions.

---

## 📂 Repository Structure

```text
agent-factory-loop-engineering/
├── README.md                                 # Course overview & loop engineering concepts
├── .gitignore                                # Clean repository ignore rules
│
├── project-1-iss-loop/                       # Concept 4: In-Session Heartbeat Loop
│   ├── README.md                             # ISS Live Telemetry Tracking documentation
│   ├── CLAUDE.md                             # Agent entry point & AGENTS.md link
│   ├── AGENTS.md                             # Agent guidance for live tool execution
│   ├── .claude/
│   │   ├── settings.json                     # Pre-granted permissions for loop beats
│   │   └── skills/
│   │       └── iss-position/
│   │           ├── SKILL.md                  # Skill definition & presentation rules
│   │           └── scripts/
│   │               └── iss.py                # Real-time satellite telemetry fetcher
│
└── project-2-goal-driven-portfolio/          # Concept 5: Goal-Driven Closed Loop
    ├── README.md                             # Full architecture, multi-agent pipeline & takeover audit
    ├── spec.md                               # The 20 Mechanical (M1-M20) + 6 Judgment (J1-J6) promises
    ├── check.py                              # Automated mechanical checker
    ├── render.sh                             # Multi-viewport headless Chromium rendering engine
    ├── progress.md                           # Build audit trail & reviewer verification report
    ├── profile.template.md                   # Source-of-truth profile template
    ├── .claude/
    │   ├── agents/                           # Specialized single-responsibility agent prompts
    │   │   ├── profile-extractor.md          # Phase 0: Ground truth extractor
    │   │   ├── design-director.md            # Phase 1: Design decision maker
    │   │   ├── content-writer.md             # Phase 2: Copywriter grounded in facts
    │   │   ├── frontend-builder.md           # Phase 3: Frontend implementation specialist
    │   │   ├── reviewer.md                   # Phase 5: Read-only visual judge
    │   │   └── check-maker.md                # Phase 6: Pipeline contract acceptance gate
    │   └── skills/
    │       ├── frontend-design/SKILL.md      # Frontend craft & anti-document guidelines
    │       └── page-proof/SKILL.md           # Screenshot proof & verification harness
    └── site/
        ├── profile.md                        # Ground truth facts for Salman Hassan
        ├── design.md                         # Executable design decision & tokens
        ├── content.md                        # Copy strictly grounded in profile facts
        ├── index.html                        # Semantic HTML5 agent-loop web structure
        ├── style.css                         # Accessible dark theme with CSS scales
        ├── desktop.png                       # 1280px full-page desktop screenshot
        ├── mobile.png                        # 390px true viewport mobile screenshot
        └── fold.png                          # 1280x900 above-the-fold screenshot
```

---

## 🚀 Projects Overview

### [Project 1: Watch the Space Station (ISS Heartbeat Loop)](./project-1-iss-loop/)
- **Core Concept:** In-session recurring loops (Concept 4).
- **Behavior:** Fires on a fixed timer (`/loop 1m`) to query the live International Space Station location via `api.wheretheiss.at`.
- **Key Insight:** Demonstrates honest real-time telemetry observation vs. LLM memory hallucination. Explores the boundary of in-session loops that terminate when the session closes.

### [Project 2: Build Your Portfolio (Goal-Driven Loop)](./project-2-goal-driven-portfolio/)
- **Core Concept:** Goal-driven autonomous execution (Concept 5).
- **Behavior:** Operates against a two-half specification requiring **Condition 1** (`python3 check.py site` = `20/20 passing`) and **Condition 2** (Independent reviewer `PASS` on all six judgment promises J1–J6).
- **Key Insight:** Implements a strict **maker-checker split** across 7 distinct phases, preventing self-grading bias and ensuring factual fidelity, responsive design (390px), and genuine web-native craft. Includes a full audit trail of session recovery after a previous agent crash.

---

## 👤 Author

**Salman Hassan**  
AI & Agentic Technology | Digital FTE Systems  
- **GitHub:** [@waterprooffish99](https://github.com/waterprooffish99)  
- **LinkedIn:** [Salman Hassan](https://www.linkedin.com/in/salman-hassan-14b486285/)  
- **Email:** `salmanhasssan1986@gmail.com`
