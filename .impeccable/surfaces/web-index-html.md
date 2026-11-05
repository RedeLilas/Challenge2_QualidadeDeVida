---
version: 1
slug: "web-index-html"
primary_target: "web/index.html"
related_targets: []
---

# Surface: conversa (web/index.html)

Mode: Operate. Build path: code-led (no image generation on this machine).

Audience and job: she opens the app in a short private moment, types a question in plain words, reads a plain answer, and can vanish in one tap. The aggressor may glance at the screen.

Constraints: camouflage as "Anotações"; quick exit always visible; conversation only in memory; Android entry-level and 3G; no web fonts; WCAG 2.1 AA; offline shell with a clear "answers need internet" notice.

Out of scope here: suggested questions (S4), 190 alert screen (s2-alerta-risco-190), profile (S3).

## Direction contract

THESIS: a conversation that looks like a calm Brasília object, a wall of Athos Bulcão tiles, not like a help hotline; it refuses the category default of grey chat with a purple "support" accent and soft rounded bubbles.

OWN-WORLD: chalk-white ground tinted cool, deep cobalt as the house colour (header band, her messages, send action), ink near-black blue for text. One tile module (square with a quarter circle) drawn as SVG is the only ornament: header strip and app icon. Square corners (2px), 1px cobalt-tinted rules, system sans.

STORY: she sees a plain notes-like app, understands at once she can write, gets an answer in short sentences, and knows the Sair button is always there.

FIRST VIEWPORT: cobalt header 56px with "Anotações" left and a white "Sair" button right; 12px tile strip under it (raised from 8px: the module is unreadable below 12px), the module in four rotations in an irregular order like a Bulcão wall; one short greeting tile; message list fills the rest; input and send fixed at the bottom above the safe area.

FORM: assigned grounded candidate 3 of 7 (Athos Bulcão tiles). seed:f0e158989f38ef06. Raise from transit-diagram challenger: fixed-size labels and one strong line colour for the active path (cobalt only marks her messages and the send action).

SIGNATURE: each new message sets into the column like a tile laid on a wall: 160ms 6px rise, ease-out, no bounce, no fade (content visible from the first frame); off under prefers-reduced-motion.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
