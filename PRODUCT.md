# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primary:** a woman in a situation of, or at risk of, domestic violence in the Distrito Federal (persona Juliana). She decides alone, on her own phone, in a short moment of privacy. Low digital familiarity is expected.
- **Secondary:** a trusted person helping someone else (persona Camila, "estou ajudando outra pessoa" mode).
- **Adverse stakeholder:** the aggressor, who may have access to the phone and may react if he finds out she is looking for help. Every design decision assumes he can see the screen.

## Product Purpose

Help her recognize rights violations, assess how urgent her situation is, and find benefits and support services, in plain Portuguese, through a conversation. Success: correct, sourced guidance (law, article, date) and an immediate 190 alert when there is imminent risk.

## Positioning

Answers come only from curated official legal texts (federal laws plus DF norms), with citations, and the system refuses when the sources do not support an answer. Services are limited to the DF network, located by Região Administrativa or CEP.

## Operating Context

- Android entry-level phones, slow 3G connections, often used in a hurry and in secret.
- Installed as a PWA from Chrome; interface and the 190 alert must work offline.
- Validation uses only fictional cases; no real victims, no interviews. Usability (SUS) with classmates in week 7.

## Capabilities and Constraints

- Stack: FastAPI backend serving a PWA in plain HTML/CSS/JS. No frontend framework, no build step.
- Conversation lives only in the memory of the open tab; never in `localStorage`, never on the server.
- Quick exit on every screen: one tap clears the conversation and calls `location.replace()` to a weather forecast page, so Back does not reopen the app.
- No notifications. Server logs carry only technical data, never message text.
- Opening screen is the conversation itself, ready to type.
- Out of scope for now: suggested questions (week 4), local profile (week 3), final name and icon (week 6), full WCAG audit (week 6).

## Brand Commitments

- "Rede Lilás" is the project name only. It MUST NOT appear in the installed app name, icon, page title, or anywhere visible to someone glancing at the phone.
- Provisional app name: a neutral utility name ("Anotações"). The icon and name must not mention violence, women, or reporting.
- Voice: plain language, short sentences, legal terms explained in one simple sentence. Calm and direct, never alarming, never pitying.

## Evidence on Hand

- Product definitions: `docs/Challenge 2 - Definições do Projeto Semana 1.md`.
- Requirements: `openspec/changes/s1-definicoes-base/specs/`.
- Legal base: `dados/leis/`, `dados/fontes/fontes.yaml`.
- No testimonials, users, logos, or real cases exist. Do not fabricate any.

## Product Principles

1. Safety before features: if a choice could expose her to the aggressor, it loses.
2. Leave no trace: nothing she typed survives closing the tab or tapping exit.
3. Camouflage over branding: the app must look ordinary at a glance.
4. Plain words: she should understand every line on first read.
5. Works on the worst phone and the worst connection she might have.

## Accessibility & Inclusion

WCAG 2.1 AA on the main screens (conversation, profile, services). Low digital literacy, small screens, possible one-handed and hurried use.
