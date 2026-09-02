# Agent Factory Loop Engineering

This repository contains the completed implementations of **Project 1**, **Project 2**, **Project 3**, and **Project 4** from the **Panaversity Agent Factory Loop Engineering Crash Course**.

Loop Engineering is the discipline of structuring AI agent workflows into closed decision cycles: **Observe → Reason → Act → Validate**. Instead of open-ended conversational prompting, loop-engineered systems operate against explicit contracts, external verification, persistent state across sessions, and defined stopping conditions.

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
│   └── .claude/
│       ├── settings.json                     # Pre-granted permissions for loop beats
│       └── skills/
│           └── iss-position/
│               ├── SKILL.md                  # Skill definition & presentation rules
│               └── scripts/
│                   └── iss.py                # Real-time satellite telemetry fetcher
│
├── project-2-goal-driven-portfolio/          # Concept 5: Goal-Driven Closed Loop
│   ├── README.md                             # Full architecture, multi-agent pipeline & takeover audit
│   ├── spec.md                               # The 20 Mechanical (M1-M20) + 6 Judgment (J1-J6) promises
│   ├── check.py                              # Automated mechanical checker
│   ├── render.sh                             # Multi-viewport headless Chromium rendering engine
│   ├── progress.md                           # Build audit trail & reviewer verification report
│   ├── profile.template.md                   # Source-of-truth profile template
│   ├── .claude/
│   │   ├── agents/                           # Specialized single-responsibility agent prompts
│   │   │   ├── profile-extractor.md          # Phase 0: Ground truth extractor
│   │   │   ├── design-director.md            # Phase 1: Design decision maker
│   │   │   ├── content-writer.md             # Phase 2: Copywriter grounded in facts
│   │   │   ├── frontend-builder.md           # Phase 3: Frontend implementation specialist
│   │   │   ├── reviewer.md                   # Phase 5: Read-only visual judge
│   │   │   └── check-maker.md                # Phase 6: Pipeline contract acceptance gate
│   │   └── skills/
│   │       ├── frontend-design/SKILL.md      # Frontend craft & anti-document guidelines
│   │       └── page-proof/SKILL.md           # Screenshot proof & verification harness
│   └── site/
│       ├── profile.md                        # Ground truth facts for Salman Hassan
│       ├── design.md                         # Executable design decision & tokens
│       ├── content.md                        # Copy strictly grounded in profile facts
│       ├── index.html                        # Semantic HTML5 agent-loop web structure
│       ├── style.css                         # Accessible dark theme with CSS scales
│       ├── desktop.png                       # 1280px full-page desktop screenshot
│       ├── mobile.png                        # 390px true viewport mobile screenshot
│       └── fold.png                          # 1280x900 above-the-fold screenshot
│
├── project-3-morning-brief/                  # Concepts 6 & 12: Scheduled Loop & Persistent Spine
│   ├── AGENTS.md                             # Agent instructions: always run script, never answer from memory
│   ├── CLAUDE.md                             # Agent entry point & AGENTS.md link
│   ├── .gitignore                            # Ignores generated briefs/, progress.md, __pycache__/
│   ├── loop_test.py                          # Minimal test file with TODO marker for detection demo
│   └── .claude/
│       ├── settings.json                     # Pre-authorized unattended permissions
│       └── skills/
│           └── morning-brief/
│               ├── SKILL.md                  # 5-phase loop cadence instructions
│               └── scripts/
│                   └── brief.py              # Main loop engine: spine read → scan → delta filter → spine write
│
└── project-4-fix-loop/                       # Concept 7: Maker-Checker with PASS/FAIL Gating
    ├── fix-loop.sh                           # Orchestrator: branch → implement → diff → review → gate
    ├── utils.py                              # Target file with functions (contains off-by-one bug)
    ├── plant-bug.sh                          # Test helper: introduces off-by-one bug into utils.py
    ├── bad-fix.sh                            # Test helper: introduces deliberately wrong fix
    └── .claude/
        └── skills/
            ├── fix-impl/
            │   └── SKILL.md                  # Fix implementer skill (read → root cause → edit → confirm)
            └── fix-review/
                └── SKILL.md                  # Fix reviewer skill (correctness, safety, scope → PASS/FAIL)
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

### [Project 3: The Morning Brief with a Memory (Scheduled Loop & Spine)](./project-3-morning-brief/)
- **Core Concept:** Scheduled unattended loops (Concept 6) & Durable state persistence (Concept 12: The Spine).
- **Behavior:** Runs on an unattended schedule (`0 9 * * 1-5`) to read `progress.md` (the spine), scan the repository for delta items (`TODO`, `FIXME`, git commits), filter out already-known items via stable SHA-256 signatures, compile structured morning briefs in `briefs/`, and persist updated checkpoints.
- **Key Insight:** Proves the spine works via the two-beat test: Beat 2 builds on Beat 1 and eliminates context amnesia. Features fault diagnosis from the spine alone, strict human gate enforcement for risky operations, and 100% offline standard-library execution verified by an independent mechanical checker and judgment reviewer.

### [Project 4: The Fix Loop (Maker-Checker with PASS/FAIL Gating)](./project-4-fix-loop/)
- **Core Concept:** Maker-checker with PASS/FAIL gating (Concept 7).
- **Behavior:** A 5-step orchestrator creates an isolated git branch, asks an AI implementer to fix a bug in `utils.py`, captures the diff, sends it to an independent AI reviewer that must output exactly `PASS` or `FAIL`, and gates the commit on a PASS verdict.
- **Key Insight:** The implementer and reviewer are separate AI invocations with no shared context—the implementer cannot grade its own work. FAIL verdicts cause the branch to be deleted; PASS verdicts are committed and optionally pushed as a PR.

---

## 👤 Author

**Salman Hassan**  
AI & Agentic Technology | Digital FTE Systems  
- **GitHub:** [@waterprooffish99](https://github.com/waterprooffish99)  
- **LinkedIn:** [Salman Hassan](https://www.linkedin.com/in/salman-hassan-14b486285/)  
- **Email:** `salmanhasssan1986@gmail.com`
