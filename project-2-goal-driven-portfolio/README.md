# Project 2: Build Your Portfolio (Goal-Driven Loop Engineering)

> **Panaversity Agent Factory — Loop Engineering Crash Course: Concept 5**  
> *Goal-driven loops: Define what "done" means and let specialized agents iterate until external proofs are satisfied.*

---

## 🎯 Project Overview

Project 2 moves beyond simple recurring timers into **goal-driven autonomous loops**. The objective is not merely to build a personal portfolio website, but to experience a multi-agent system governed by **strict contracts, external automated checkers, independent review gates, and safety caps**.

The portfolio is built strictly in `site/` from ground-truth facts in `site/profile.md`, guided by `spec.md`.

---

## 🏆 Defined Success Conditions

The goal is complete **only when both conditions are supported by actual evidence**:

```text
               ┌──────────────────────────────────────────────┐
               │              GOAL DEFINITION                 │
               │   Build portfolio in site/ from profile.md   │
               └──────────────────────┬───────────────────────┘
                                      │
                   ┌──────────────────┴──────────────────┐
                   ▼                                     ▼
      ┌─────────────────────────┐           ┌─────────────────────────┐
      │       Condition 1       │           │       Condition 2       │
      │   Mechanical Checker    │           │   Independent Review    │
      │  python3 check.py site  │           │   Judgments J1 to J6    │
      │      (20/20 PASS)       │           │     (VERDICT: PASS)     │
      └─────────────────────────┘           └─────────────────────────┘
```

1. **Condition 1 (Mechanical Proof):**  
   `python3 check.py site` outputs `20/20 passing` with exit code `0`.
2. **Condition 2 (Judgment Proof):**  
   An autonomous, strictly read-only reviewer agent inspects full-page rendered screenshots and returns `VERDICT: PASS` across all six judgment promises (J1–J6).

---

## 📜 The Two-Half Specification Architecture (`spec.md`)

Most software specifications fail because they only check easily computable syntax or rely entirely on subjective opinions. This project splits the contract into two complementary halves:

### Part A — Mechanical Promises (Proven by `check.py`)
- **M1:** Five sections exist in required order (`hero`, `about`, `projects`, `skills`, `contact`).
- **M2:** Document title contains user's name; `<html lang="en">` set.
- **M3:** Exactly one `<h1>`, heading hierarchy strictly followed without jumps.
- **M4:** Responsive viewport meta tag with `width=device-width` and `initial-scale=1.0`.
- **M5:** Alt text on all `<img>` tags (with `aria-hidden="true"` pairing for decorative images).
- **M6:** Color tokens only: `:root` defines `--fg`, `--bg`, `--accent` in hex; no literal colors outside `:root`.
- **M7:** WCAG AA contrast ratio ≥ 4.5:1 for body text and accent against background.
- **M8:** Zero placeholder text (`lorem ipsum`, `todo`, `example.com`, etc.).
- **M9:** Internal anchor links and local asset paths resolve without dangling references.
- **M10:** 100% offline — no external CDNs, fonts, or http/https stylesheets.
- **M11:** Sections not empty — counts derived dynamically from `profile.md` (3 projects, 14 skills).
- **M12:** Renders in headless Chromium with zero console errors.
- **M13:** Type and space scales declared in `:root` — no raw magic numbers in properties.
- **M14:** Body measure dynamically measured at **45–75 characters per line** on rendered DOM.
- **M15:** High-visibility `:focus-visible` styling for keyboard navigation.
- **M16:** Zero horizontal overflow at a 390px mobile viewport (`scrollWidth == 390px`).
- **M17:** Persistent fixed/sticky navigation with ≥ 3 in-page anchor links.
- **M18:** Dynamic interactive states (≥ 3 `:hover`, ≥ 1 `:focus-visible`, ≥ 3 `transition`/`animation`).
- **M19:** Hero section uses viewport units (`100svh`) with fluid typography (`clamp()`).
- **M20:** `@media (prefers-reduced-motion: reduce)` block properly respects motion preferences.

### Part B — Judgment Promises (Evaluated on Rendered Screenshots)
- **J1 (Factual Grounding):** Every checkable fact is true and strictly matches `profile.md` with zero inflation or fake metrics.
- **J2 (Project Clarity):** Projects clearly explain what they actually do and the engineer's specific contribution.
- **J3 (Specificity):** The About section reflects the author's real, unique background (combining fashion business operations with agentic AI).
- **J4 (Designed, Not Formatted):** Carries out an identifiable design decision across all sections rather than reading as an unstyled document.
- **J5 (Mobile Reflow):** Layout naturally adapts at 390px width into a purposeful vertical mobile flow.
- **J6 (Web-Native Experience):** Employs load-bearing digital capabilities (sticky navigation, state transitions, interactive cards, reveals) that could not have existed as a static PDF.

---

## 🤖 The Multi-Agent Pipeline & Maker-Checker Split

```text
Phase 0: Ground Truth      ──► profile-extractor (Extracts profile.md from CV)
Phase 1: Design Decision   ──► design-director   (Writes 1-sentence decision to design.md)
Phase 2: The Words         ──► content-writer    (Drafts content.md grounded in facts)
Phase 3: The Build         ──► frontend-builder  (Iterates index.html/style.css to 20/20)
Phase 4: The Render        ──► render.sh         (Headless Chromium multi-viewport capture)
Phase 5: The Judgment      ──► reviewer agent    (Read-only judge grading J1-J6 on PNGs)
Phase 6: Acceptance        ──► check-maker       (Audits all phase contracts for drift)
```

The system strictly enforces that **the agent that builds the page cannot be the agent that reviews it**.

---

## 🛠 Crash Recovery & Continuity Takeover Audit

During the initial execution by an earlier agent (Claude Code), the loop reached its mechanical pass (20/20) but **halted at its safety cap** during Phase 5 due to upstream 503/429 router rate limits on the subagent channel.

When taking over the workspace, a disciplined takeover process was executed:
1. **Verification Before Action:** Audited all files, git status, and checker outputs without blindly rebuilding.
2. **Honest Status Assessment:** Acknowledged that Condition 2 was incomplete and that the initial visual design was overly sparse.
3. **Visual & Structural Elevation:** Upgraded `style.css` and `index.html` to a sophisticated dark technical theme (`#0B0D11` obsidian canvas, `#F3F4F6` text, `#E86328` amber accent) that directly embodies the *"page as an agent loop"* state machine.
4. **Rendering Compatibility:** Updated `render.sh` to resolve the local Linux Playwright Chromium headless shell.
5. **Phase 5 Autonomous Review:** Launched an independent read-only reviewer subagent which graded the live screenshots and awarded `VERDICT: PASS` across all six judgment criteria.

---

## 📊 Final Verification Results

### 1. Mechanical Checker Verification
```text
$ python3 check.py site

  site   (profile.md declares 3 projects, 14 skills — M11 counts from there)
  [x] M1  five sections, in order
  [x] M2  title names you, lang set
  [x] M3  one h1, no skipped levels
  [x] M4  responsive viewport
  [x] M5  alt text declared right
  [x] M6  colours are tokens only
  [x] M7  contrast >= 4.5:1   -> fg/bg=17.67 accent/bg=5.78
  [x] M8  no placeholders
  [x] M9  links + assets resolve
  [x] M10 genuinely offline
  [x] M11 sections not empty   -> about=116w, articles=[95, 86, 79]w, skills=15/14
  [x] M12 renders, no console errors
  [x] M13 type+space are scales
  [x] M14 45-75 chars/line MEASURED   -> 50-62 chars/line
  [x] M15 focus-visible is styled
  [x] M16 no overflow at 390px   -> <title>W=390 S=390 O=NONE</title>
  [x] M17 navigable (sticky nav, 3+ links)
  [x] M18 responds (hover/focus/motion)   -> hover=4 focus-visible=3 motion=7
  [x] M19 hero uses the viewport
  [x] M20 reduced-motion respected

  20/20 passing
```

### 2. Independent Reviewer Verdict
- **J1 (Truth):** PASS
- **J2 (Project Specificity):** PASS
- **J3 (About Authenticity):** PASS
- **J4 (Design Execution):** PASS
- **J5 (390px Mobile Reflow):** PASS
- **J6 (Web-Native Craft):** PASS
- **Final Verdict:** `VERDICT: PASS`

---

## 🧠 Key Takeaways & Lessons Learned

1. **Self-Grading is an Anti-Pattern:** A single agent building and grading its own work will always convince itself the output is sufficient. The maker-checker split is essential for reliable AI workflows.
2. **Quota vs. Fact Traps:** Mechanical checks must derive requirements dynamically from the source of truth (e.g. counting skills from `profile.md`), rather than arbitrary hardcoded minimums, which otherwise create unsolvable infinite loops.
3. **The Power of Safety Caps:** Without iteration caps (e.g. max 15 checker attempts, max 3 review rounds), a loop chasing an unsatisfiable condition will burn API credits indefinitely. Giving up loudly with an audit trail is a feature.
4. **Separating Code from Truth:** A 20/20 mechanical score only proves structural validity. Visual judgment on actual rendered pixels is required to ensure genuine web craft.
