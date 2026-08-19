# The design decision

The page is an agent loop — each section is one phase of observe → reason → act → validate, and the layout moves through them in sequence like an agent completing its cycle.

## Why this person

Salman builds Digital FTE systems where agents perform business roles by running loops: they observe conditions, reason about what to do, act using tools, and validate results until task completion. His Loop Engineering project is explicitly about agents that "repeatedly observe, reason, act, and validate." The page structure mirrors the pattern he engineers — it's built on his model, not borrowed from a template.

## How the page carries it out

- The hero **observes**: "AI & Agentic Technology | Digital FTE Systems" — what this agent (Salman) does
- The about section **reasons**: the problem space — real business work, SME automation, the transition from operations to engineering
- The projects section **acts**: three systems he's shipped, each one a different agent implementation
- Contact is the **validate** phase: where an employer or collaborator confirms capability and makes contact
- At 390px, the loop survives as a vertical flow — one phase per screen, scroll is the progression through the cycle
- Section transitions use subtle reveals (18px, 0.7s) so each phase "arrives" as the reader reaches it — the loop advancing

## Tokens

```css
:root {
  /* Colour — foreground on background and accent on background both >= 4.5:1 */
  --bg: #0B0D11;           /* deep obsidian canvas */
  --fg: #F3F4F6;           /* crisp off-white, 17.67:1 on --bg */
  --accent: #E86328;       /* electric amber/orange, 5.78:1 on --bg */
  --bg-card: #131720;
  --bg-card-hover: #181E2A;
  --bg-tag: #1A212E;
  --border: #232B3B;
  --border-accent: #E86328;
  --border-muted: #1B212D;
  --text-muted: #9CA3AF;
  --text-dim: #6B7280;
  
  /* Type scale */
  --text-xs: 0.72rem;      /* 11.5px — labels, meta */
  --text-sm: 0.86rem;      /* 13.8px — secondary text */
  --text-base: 1.05rem;    /* 16.8px — body */
  --text-lg: 1.28rem;      /* 20.5px — section leads */
  --text-xl: clamp(1.8rem, 4vw, 2.5rem);      /* 28–40px — section headers */
  --text-2xl: clamp(2.8rem, 8vw, 5.2rem);     /* 45–83px — hero voice */
  
  /* Space scale */
  --space-1: 0.35rem;      /* 5.6px — tight gaps */
  --space-2: 0.7rem;       /* 11.2px — inline spacing */
  --space-3: 1.25rem;      /* 20px — card gaps */
  --space-4: 2rem;         /* 32px — section internal */
  --space-5: 3.5rem;       /* 56px — between major groups */
  --space-6: 6rem;         /* 96px — phase transitions */
  
  /* Measure */
  --measure: 48ch;         /* comfortable reading measure */
}
```
