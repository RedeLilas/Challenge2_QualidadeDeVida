# Proposal

## Why

`dados/leis/` tem 18 normas, mas o RAG só busca nas 5 do eixo jurídico. As 11 normas de benefícios (eixos `beneficios` e `df`: Bolsa Família, LOAS, Cartão Prato Cheio, Cartão Gás, Aluguel Social do DF e benefícios eventuais do DF) estão indexadas, e nenhum agente busca nelas. Assim, "o que é o cartão gás?" ou "como funciona o Aluguel Social?" vão para o jurídico e são recusadas. A verificação de citação também lê mal essas normas, nos dois sentidos: recusa citações corretas, como "(Lei 8.742/1993, art. 20)", porque o rótulo é "Lei 8.742/1993 (LOAS)", e aceita citações de outra norma, como "(Decreto 42.376, art. 3º)" sem o ano, porque a norma fica sem reconhecimento e qualquer art. 3º recuperado serve. Com 11 normas de benefícios, esse segundo erro vira risco real.

Métrica do ROADMAP: nenhuma meta da S4 depende desta mudança. A fidelidade às fontes (100% citadas, ≤ 5% sem suporte) é a referência da regra de citação. Pela decisão da equipe, esta mudança é **testada, não medida**: não há rodada com corretor externo na S4, e o relatório da S4 declara isso. É a **primeira a ser cortada** se a S4 apertar; nesse caso, vai para a S6.

## What Changes

- RAG de benefícios só para **explicar** ("o que é", "como funciona", "quem pode"), nos eixos `beneficios` e `df`. Ele nunca decide se a pessoa tem direito: manda para a tela Benefícios ou para o CRAS.
- Reaproveita o fluxo do RAG jurídico, com `responder()` parametrizado em `s4-orquestrador-agentes`, sem duplicar o código.
- Instruções próprias: só explicar, com a mesma regra de citação e de "não sei responder com segurança", e aviso com a data da coleta da norma, porque valores mudam por decreto.
- Apelidos de todas as normas de benefícios na verificação de citação, com e sem o ano, incluindo "LOAS", "Lei 8.742", "Lei 6.623", "Lei Distrital 6.623", "Portaria 49" e "Decreto 42.376". Quando os trechos recuperados vêm de mais de uma norma, um artigo sem norma reconhecida é recusado. O `/juridico` não muda.
- Limite de similaridade próprio para esses eixos, calibrado só com as perguntas de desenvolvimento de benefícios (o 0,81 continua só no jurídico).
- Teste de recuperação por benefício: a norma certa no top 5.
- Perguntas de desenvolvimento de benefícios em arquivo próprio, em linguagem leiga, com extras "quase do tema" (imposto de renda, FGTS, seguro-desemprego, aposentadoria).
- Ligação ao `/orquestrar`: a pergunta de explicação de benefício passa a usar este RAG, em vez do jurídico.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `beneficios`: passa a ter a explicação de benefícios com citação conferida, sem decidir direito individual, com a data da coleta, recusa fora da base e cobertura da recuperação por benefício.
- `avaliacao`: passa a ter o conjunto de desenvolvimento de benefícios, separado da base da S3, e a regra de que uma medição futura use um conjunto separado e congelado antes.

## Impact

- **Código alterado:** `app/rag/resposta.py` (apelidos, verificação com a regra de norma não reconhecida e instruções de benefícios), o módulo do orquestrador (ponto de troca da explicação) e testes novos em `tests/`.
- **Arquivos novos:** `avaliacao/conjuntos/s4/desenvolvimento_beneficios.yaml` e o teste de recuperação por benefício.
- **Depende de:** a tarefa 1.1 de `s4-orquestrador-agentes` (parametrizar `responder()`, terça cedo) e as perguntas de desenvolvimento, escritas na terça, para a calibração de quinta.
- **Privacidade (LGPD):** só o texto da pergunta vai ao DeepSeek, como no jurídico (decisão de 09/11). Nenhum perfil, nenhum dado de benefício e nenhum CEP.
- **Segurança da usuária:** o agente nunca diz se ela tem direito, o que evita falsa expectativa. Valores vêm com a data da coleta. Citação de outra norma é recusada.
- **Fora desta mudança:** decidir elegibilidade (continua na regra do aparelho), a Lei 14.737/2023 (acompanhante, eixo `saude`), que fica para quando o jurídico ampliar eixos, mudanças no `/juridico` e no limite de 0,81, a rodada de avaliação com corretor externo e novas regras de elegibilidade para os benefícios distritais.
