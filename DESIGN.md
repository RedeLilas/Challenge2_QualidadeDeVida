---
name: Anotações
description: A private conversation that looks like a calm Brasília tile wall, not a help hotline.
colors:
  cobalto: "#1e4597"
  cobalto-forte: "#163777"
  topo: "#1e4597"
  sobre-cobalto: "#ffffff"
  chao: "#f4f6f9"
  azulejo: "#ffffff"
  tinta: "#142036"
  tinta-suave: "#4a5670"
  linha: "#d5dce8"
  sair-pressionado: "#dfe6f3"
  cobalto-escuro: "#2c55a8"
  cobalto-forte-escuro: "#3a66be"
  topo-escuro: "#13254d"
  chao-escuro: "#0e1626"
  azulejo-escuro: "#172238"
  tinta-escuro: "#e6ebf4"
  tinta-suave-escuro: "#a9b4c8"
  linha-escuro: "#2b3a57"
  faixa-quadrado-escuro: "#4a76cc"
typography:
  title:
    fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    letterSpacing: "0"
  body:
    fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.5
  body-small:
    fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.5
  input:
    fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.4
  label:
    fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 700
rounded:
  raio: "2px"
spacing:
  passo: "8px"
  junta: "12px"
  passo-2: "16px"
  passo-3: "24px"
  medida: "40rem"
components:
  header-topo:
    backgroundColor: "{colors.topo}"
    textColor: "{colors.sobre-cobalto}"
    typography: "{typography.title}"
    height: "56px"
  button-sair:
    backgroundColor: "{colors.sobre-cobalto}"
    textColor: "{colors.cobalto-forte}"
    typography: "{typography.label}"
    rounded: "{rounded.raio}"
    padding: "0 16px"
    height: "44px"
    width: "72px"
  button-sair-active:
    backgroundColor: "{colors.sair-pressionado}"
    textColor: "{colors.cobalto-forte}"
  button-enviar:
    backgroundColor: "{colors.cobalto}"
    textColor: "{colors.sobre-cobalto}"
    rounded: "{rounded.raio}"
    size: "48px"
  button-enviar-hover:
    backgroundColor: "{colors.cobalto-forte}"
    textColor: "{colors.sobre-cobalto}"
  button-enviar-disabled:
    backgroundColor: "{colors.linha}"
    textColor: "{colors.tinta-suave}"
  tile-assistente:
    backgroundColor: "{colors.azulejo}"
    textColor: "{colors.tinta}"
    typography: "{typography.body}"
    rounded: "{rounded.raio}"
    padding: "12px 14px"
  tile-usuaria:
    backgroundColor: "{colors.cobalto}"
    textColor: "{colors.sobre-cobalto}"
    typography: "{typography.body}"
    rounded: "{rounded.raio}"
    padding: "12px 14px"
  tile-erro:
    backgroundColor: "{colors.azulejo}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.raio}"
    padding: "12px 14px"
  tile-pensando:
    textColor: "{colors.tinta-suave}"
    rounded: "{rounded.raio}"
    padding: "12px 14px"
  input-envio:
    backgroundColor: "{colors.azulejo}"
    textColor: "{colors.tinta}"
    typography: "{typography.input}"
    rounded: "{rounded.raio}"
    padding: "12px 14px"
    height: "48px"
  aviso-offline:
    backgroundColor: "{colors.azulejo}"
    textColor: "{colors.tinta}"
    typography: "{typography.body-small}"
    padding: "10px 16px"
---

# Design System: Anotações

## Overview

**Creative North Star: "The Bulcão Wall"**

The app is a single conversation column laid out like a wall of Athos Bulcão tiles in a Brasília building: chalk-white tiles on a cool ground, deep cobalt as the one house colour, ink-blue text, square corners. It must read as an ordinary notes utility to anyone glancing at the phone, so the system is quiet, flat, and plain; its only ornament is one tile module (a square holding a quarter circle), used in the 12px strip under the header and in the app icon. It deliberately refuses the help-hotline category look: grey chat, a purple "support" accent, soft rounded bubbles.

Density is calm and mobile-first: one 40rem column, generous 17px body text, 44 to 48px touch targets, and a composer pinned above the safe area. Light and dark schemes are both first-class and switch only through `prefers-color-scheme`; every role token is remapped on `:root`, nothing is restyled per component except the tile strip's SVG.

Motion is a single gesture: a new message settles into the column with a short rise, nothing else animates.

**Key Characteristics:**
- One house colour (cobalt) marking exactly three things: the header band, her messages, the send action.
- Square-cornered tiles (2px) separated by 12px joints, flat, no shadows.
- One ornament: the quarter-circle tile module, never anywhere else.
- System sans only; no web fonts.
- States and errors stay inside the chalk/cobalt/ink palette.

## Colors

A two-temperature palette: cool chalk and ink neutrals carrying almost everything, with one saturated cobalt doing all the signalling.

### Primary
- **Bulcão Cobalt** (`cobalto`; dark `cobalto-escuro`): her messages, the send button, text selection, the offline notice's bottom rule, the error tile's border.
- **Deep Cobalt** (`cobalto-forte`; dark `cobalto-forte-escuro`): pressed and hover state of send, the focus ring everywhere outside the header, the input caret and focused border, the "Sair" label text.
- **Header Cobalt** (`topo`; dark `topo-escuro`): the header band and the strip's ground. Equals cobalt in light; drops to a near-navy in dark so the band does not glare. Also the `theme-color` per scheme.
- **On Cobalt** (`sobre-cobalto`): text and icons on cobalt, the "Sair" button fill, and the focus ring inside the header.

### Neutral
- **Chalk Ground** (`chao`; dark `chao-escuro`): page background and composer bar background; manifest `background_color`.
- **Tile White** (`azulejo`; dark `azulejo-escuro`): assistant tiles, error tile, offline notice, input field.
- **Ink** (`tinta`; dark `tinta-escuro`): all primary text.
- **Soft Ink** (`tinta-suave`; dark `tinta-suave-escuro`): secondary notes, placeholder, the "Escrevendo resposta…" tile, disabled send icon, the input's resting 1px stroke.
- **Joint Line** (`linha`; dark `linha-escuro`): 1px cobalt-tinted rules: assistant tile border, composer top rule, dashed "thinking" outline, disabled send fill.
- **Pressed Chalk** (`sair-pressionado`): only the pressed/hover fill of the white "Sair" button.
- **Strip Square, dark** (`faixa-quadrado-escuro`): the tile squares in the dark-scheme strip (discs there use `topo-escuro`). In light the strip uses white squares with cobalt discs.

### Named Rules
**The One House Colour Rule.** Cobalt marks only the header band, her messages, and the send action (plus focus and selection). Adding cobalt to a fourth kind of element dilutes the only signal the screen has.

**The Palette-Bound State Rule.** Errors and offline states are drawn with tile white, ink, and a 1px cobalt rule; never red, amber, or any hue outside the palette. Alarm colours would announce the app to an onlooker. The copy carries the meaning; the rule is a secondary cue.

## Typography

**Display Font:** none (no display role exists)
**Body Font:** system-ui stack (`system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif`)

**Character:** The phone's own sans, by product constraint (entry-level Android on 3G, no web fonts). It keeps the app indistinguishable from a native utility.

### Hierarchy
- **Title** (600, 1.125rem): the app name "Anotações" in the header; the only heading.
- **Body** (400, 1.0625rem, 1.5): every message tile; the base size of the page. Tiles cap at 88% of a 40rem column, so lines stay well under 75ch.
- **Body Small** (400, 0.9375rem): the secondary note in the greeting tile and the offline notice.
- **Input** (400, 16px, 1.4): the composer field. Never below 16px, which stops mobile browsers from zooming on focus.
- **Label** (700, body size): the "Sair" button.

### Named Rules
**The Flat Ramp Rule.** Hierarchy comes from weight and colour (ink vs. soft ink), not size jumps; the ramp spans only 0.9375rem to 1.125rem. Never add uppercase tracking labels or eyebrow text above content.

## Layout

A single centered column, `medida` (40rem) wide with 16px side gutters. Header and composer are full-bleed bands whose content aligns to the same column through a computed side inset (`max(16px, (100% - 40rem) / 2 + 16px)`) plus the safe-area insets, so on desktop the "Anotações" title, the tiles, and the input all share one left edge.

The page scrolls as a whole (body is a 100dvh flex column). The header (56px band plus 12px strip) is sticky at the top; the composer is sticky at the bottom with the bottom safe-area inset added to its padding. The conversation fills the space between.

Rhythm runs on an 8px step (`passo`): 8px inside the composer and between paragraphs in a tile, 12px joints between tiles (`junta`), 16px column gutters and top padding, 24px bottom padding. Tile padding is 12px by 14px. Assistant and error tiles hang left; her tiles hang right.

**The Shared Edge Rule.** Anything that spans the full width (bands, bars, notices) aligns its content to the 40rem column, never to the viewport edge.

## Elevation & Depth

Fully flat. There are no shadows anywhere. Depth is tonal: tile white sits on a slightly darker chalk ground, separated by 1px joint lines; the cobalt header band is the only heavy mass. Sticky header and composer separate from the scrolling column by colour (cobalt band; chalk bar with a 1px top rule), not by lift.

**The Laid Tile Rule.** Surfaces lie flat on the wall. Distinguish them with fill and a 1px rule, never with shadow, blur, or translucency.

## Shapes

Square-cornered everything: tiles, buttons, input, all at a barely softened 2px (`raio`). Borders are 1px solid; the only exception is the dashed 1px outline of the transient "thinking" tile, which marks it as not yet laid.

The one curve in the system is inside the tile module: a square holding a quarter circle of 12px radius, repeated in four rotations in an irregular order across a 96x12px SVG period, like an irregular Bulcão wall. The app icon is the same module at 512px: a cobalt field with a white square holding two cobalt quarter circles.

**The One Module Rule.** The quarter-circle tile is the only ornament, and it lives only in the header strip and the icon. Curves belong to the module; containers stay square. The strip is never smaller than 12px tall: the module stops reading below that.

## Components

### Header and Tile Strip
Calm and immovable. A 56px cobalt band with "Anotações" left (title type, on-cobalt) and the "Sair" button right, followed by the 12px tile strip; both stick together at the top. In light the strip is white squares with cobalt quarter discs; in dark, `faixa-quadrado-escuro` squares with `topo-escuro` discs. The strip is decorative (`aria-hidden`).

### Buttons
- **Shape:** square, 2px corners, no border.
- **Sair (quick exit):** white fill, deep-cobalt bold label "Sair", at least 72x44px, always visible in the header in both schemes (the label stays deep cobalt in dark too). Pressed and hover go to pressed chalk. One tap clears the conversation and leaves; Escape does the same.
- **Enviar (send):** 48x48px cobalt square with an inline SVG arrow (22px, 2.25 stroke, square caps) in on-cobalt; accessible name "Enviar". Hover (pointer devices only) and pressed go to deep cobalt. Disabled while a reply is pending: joint-line fill, soft-ink icon.
- **Focus:** 3px deep-cobalt outline at 2px offset; inside the header the outline turns on-cobalt white.

### Message Tiles
- **Assistente:** tile white, 1px joint-line border, ink text, left-aligned, max 88% width. Text keeps line breaks (`pre-wrap`) and breaks long words anywhere.
- **Usuária:** cobalt fill, on-cobalt text, right-aligned, no border.
- **Abertura (greeting):** an assistant tile shipped in the HTML: "Escreva sua pergunta com suas palavras. Respondo de forma simples." with a soft-ink small note "A conversa some quando você toca em **Sair** ou fecha o app."
- **Erro:** tile white, ink text, 1px cobalt border, left-aligned. Shipped copy: "Não consegui responder agora. Tente de novo em alguns instantes. Se precisar falar com alguém, ligue 180 (gratuito, 24 horas).", "Sem internet. Sua mensagem não foi enviada. Tente de novo quando tiver conexão.", "A resposta está demorando. Tente de novo em alguns instantes."
- **Pensando:** transparent, 1px dashed joint-line outline, soft-ink "Escrevendo resposta…"; removed when the reply arrives.
- **Settle motion:** each new tile rises 6px into place over 160ms on `cubic-bezier(0.16, 1, 0.3, 1)`, transform only, so it is visible even if the animation never runs. Disabled under `prefers-reduced-motion`.

### Inputs / Fields
- **Style:** tile-white field, 1px soft-ink stroke, 2px corners, 12x14px padding, 48px minimum height, grows with content to 9.5rem. Placeholder "Escreva aqui" in soft ink at full opacity. Hidden label "Sua mensagem".
- **Focus:** 2px deep-cobalt outline at 0 offset plus deep-cobalt border; caret in deep cobalt.
- **Behaviour:** Enter sends, Shift+Enter breaks the line. No native validation bubble: an empty submit is silently ignored.

### Offline Notice
A full-width tile-white band under the header strip with ink small text and a 1px cobalt bottom rule, announced as status: "Sem internet. Você pode escrever, mas as respostas precisam de conexão." Shown only while offline.

## Do's and Don'ts

### Do:
- **Do** keep cobalt to the header band, her messages, and the send action, plus focus and selection (The One House Colour Rule).
- **Do** draw every error and system notice with tile white, ink, and a 1px cobalt rule, and let the plain pt-BR copy carry the meaning.
- **Do** keep all corners at 2px and all surfaces flat, separated by 1px rules.
- **Do** align full-width bands to the 40rem column through the shared side inset and add safe-area insets to sticky bars.
- **Do** keep touch targets at 44px minimum (Sair) and 48px for the send button and input.
- **Do** keep the quick-exit "Sair" white-on-cobalt in the header on every screen, in both schemes.
- **Do** remap colours only through the `:root` tokens for dark mode.

### Don't:
- **Don't** use red, amber, or any hue outside chalk, cobalt, and ink for errors, warnings, or offline states.
- **Don't** add shadows, blur, gradients, or translucency.
- **Don't** use the quarter-circle module anywhere except the header strip and the app icon, and never render the strip below 12px.
- **Don't** round containers beyond 2px or use soft pill bubbles; curves belong only to the tile module.
- **Don't** load web fonts.
- **Don't** add eyebrow or kicker labels, glyph-character icons, or icon fonts; icons are inline SVG.
- **Don't** put "Rede Lilás", or anything that mentions violence, women, or reporting, in any visible name, title, or icon.
