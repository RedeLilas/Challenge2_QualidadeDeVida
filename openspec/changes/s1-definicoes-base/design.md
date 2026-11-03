# Design

## Context

Esta mudança só converte documentação: não há código. A fonte é `Challenge 2 - Definições do Projeto Semana 1.md` (29/10/2026). Depois dela, foram decididos: escopo DF, ausência de entrevistas, stack (Python + PWA, LLM local e DeepSeek) e deploy desde a S2.

## Goals / Non-Goals

**Goals:**
- Todo requisito da Semana 1 tem um lugar em uma spec e ao menos um cenário verificável.
- As specs refletem o escopo DF e a validação sem especialistas.

**Non-Goals:**
- Decidir a implementação (fica nos `design.md` das mudanças de cada semana).
- Decidir a plataforma de deploy e o tratamento LGPD do DeepSeek (decisões da S2).

## Decisions

### Rastreabilidade Semana 1 → specs

| Origem (S1) | Capacidade | Requisito |
| :--- | :--- | :--- |
| RF01 | `privacidade-seguranca` | Perfil opcional e mínimo (município → RA ou CEP) |
| RF02 | `orientacao-juridica` | Resposta fundamentada com citação; Identificação das formas de violência |
| RF03 | `beneficios` | Classificação de elegibilidade; O que falta e onde pedir; Regras auditáveis com vigência |
| RF04 | `triagem-risco` | Triagem de urgência baseada no Fonar |
| RF05 | `triagem-risco` | Alerta de risco imediato; Regras de risco auditáveis |
| RF06 | `rede-atendimento` | Todos (ampliado com a rede de proteção do DF) |
| RF07 | `privacidade-seguranca` | Saída rápida; Sem histórico persistente; Apagar dados |
| RF08 | `conversa` | Perguntas sugeridas; Encaminhamento ao agente certo |
| RF09 | `conversa` | Pergunta por áudio; Leitura de documento fotografado |
| RNF01 | `triagem-risco`, `interface-pwa` | Alerta em até 2 s; Tempo de resposta (p95 ≤ 10 s) |
| RNF02 | `privacidade-seguranca`, `plataforma` | Perfil só no aparelho; Dados pessoais fora dos logs; Envio mínimo; Decisão de privacidade do provedor |
| RNF03 | `orientacao-juridica`, `beneficios` | Citação com norma, artigo e data |
| RNF04 | `privacidade-seguranca` | Aparência discreta; Saída rápida; Sem histórico |
| RNF05 | `beneficios`, `triagem-risco` | Distinção entre provável e confirmado; Aviso de limite da triagem |
| RNF06 | `interface-pwa`, `orientacao-juridica` | Linguagem simples; Acessibilidade; Celular básico; Base legal versionada |
| Seção 8 | `avaliacao` | Metas de qualidade; Comparação LLM x RAG; Usabilidade com colegas |
| Stakeholder "pessoas de confiança" | `conversa`, `triagem-risco` | Modo de ajuda a outra pessoa; cenário de risco relatado por terceira |

### Ajustes em relação à Semana 1

- **Nota de profissionais (seção 8) removida**: não haverá entrevistas; a usabilidade é medida só pelo SUS com colegas.
- **"Julgado por especialista" → LLM juiz + revisão em dupla de 20%**: a equipe escreve o gabarito com fonte.
- **RF06 ampliado**: a lista curada da rede de proteção do DF vem da pesquisa documental (`s2-fontes-df`).
- **Novas capacidades `plataforma` e `avaliacao`**: tornam verificáveis o deploy desde a S2 e a medição das métricas.

### Specs como comportamento-alvo

O OpenSpec trata `openspec/specs/` como o comportamento atual do sistema. Aqui, a base é arquivada antes do código existir, então as specs descrevem o **comportamento-alvo**. O que já está implementado é acompanhado pelas mudanças de cada semana e pelo `ROADMAP.md`. Mudanças futuras que alterem um requisito usam deltas `MODIFIED`.

## Risks / Trade-offs

- **Specs à frente do código**: alguém pode supor que um requisito já funciona. Mitigação: o `ROADMAP.md` mostra o status de cada mudança.
- **Sem validação externa**: os requisitos jurídicos e de benefícios dependem da leitura da equipe. Mitigação: toda regra cita a norma, e a limitação é declarada no relatório final.
