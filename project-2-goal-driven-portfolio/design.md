# The design decision
The page is an autonomous agent loop — the hero declares the objective, each section is a phase that renders its output and passes context forward, and the sticky nav shows the loop's current position, making the portfolio itself a demonstration of loop engineering.

## Why this person
Salman builds "systems that operate with minimal human intervention" using Spec-Driven Development and Loop Engineering. His five projects are all agentic workflows (Aura Engine, Paper Watch, Sentinel RAG, Forge Automation, Digital FTE). The page mirrors his craft: every section is a phase with a contract, the nav is the loop counter, and the whole thing runs without a server.

## How the page carries it out
- Hero = objective declaration (largest type, viewport-sized, states what the loop achieves)
- Each section = a phase card with a status indicator; projects render as a grid of "completed phases"
- Sticky nav = loop position tracker (highlights current phase, shows progress)
- At 390px: single-column phase stack, nav collapses to progress dots, hero min-height pins to phone fold, grid becomes stacked cards

## Tokens
:root {
  --bg: #0a0f1a; --fg: #e8edf5; --accent: #00d4aa;
  --text-xs: 0.75rem; --text-sm: 0.875rem; --text-base: 1rem; --text-lg: 1.25rem;
  --text-xl: clamp(2rem, 5vw, 3.5rem); --text-2xl: clamp(3rem, 10vw, 7rem);
  --space-1: 0.25rem; --space-2: 0.5rem; --space-3: 1rem; --space-4: 2rem;
  --space-5: 4rem; --space-6: 8rem;
  --measure: 47ch;
}