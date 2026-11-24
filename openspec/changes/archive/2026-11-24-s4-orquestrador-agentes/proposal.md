# Proposal

## Why

O chat envia toda mensagem para `/juridico`, então perguntas de benefícios, de risco ou de serviços recebem uma resposta jurídica ou uma recusa. Benefícios, triagem e rede já existem como módulos no navegador, mas a conversa não chega até eles. Há também uma lacuna de segurança e de uso: quando o alerta de 190 dispara, `enviar()` para depois de `mostrarAlerta()`, e a pergunta que vinha junto nunca é respondida, embora a spec `conversa` peça o alerta *antes* da resposta. A S4 entrega o primeiro sistema multiagentes do curso.

Métricas do ROADMAP afetadas, que formam o critério de pronto da S4: **acurácia de elegibilidade ≥ 90%** e **sensibilidade para risco alto = 100%** nos casos fictícios. O roteamento é medido como evidência, sem meta.

## What Changes

- Rota nova `POST /orquestrar` com orquestração em duas etapas: primeiro uma regra por palavras-chave, que só decide quando casa exatamente um agente numa mensagem com uma pergunta só; senão, o LLM escolhe numa lista fechada (`juridico`, `beneficios`, `triagem`, `rede`, `fora_do_tema`) com saída JSON validada e temperatura 0. Se o JSON for inválido ou o LLM estiver fora do ar, a reserva é o `juridico`.
- O servidor devolve só o agente e os campos tirados do **texto** (`beneficio`, `ra`, `violencia_sexual_recente`). Benefícios ("tenho direito?"), triagem e rede rodam no navegador, com o perfil, que nunca sai do aparelho. A pergunta jurídica é respondida no mesmo pedido.
- Dentro de benefícios, "tenho direito?" vai para a regra no navegador; "o que é / como funciona?" vai para o RAG de benefícios (`s4-rag-beneficios`). Sem essa mudança, vai para o jurídico, como hoje. Explicações sobre o auxílio-aluguel da Lei Maria da Penha vão sempre para o jurídico.
- Várias perguntas numa mensagem: a mesma chamada ao LLM separa e reescreve até 3 perguntas independentes. O sistema responde uma e mostra as outras como perguntas sugeridas. Com mais de 3, pede para enviar o resto separadamente.
- Ordem: alerta de risco primeiro, depois triagem, depois a ordem em que a usuária escreveu.
- Alerta com pergunta: o 190 aparece primeiro, com o botão "Continuar com minha pergunta". Texto com sinal de risco só vai ao servidor se ela tocar no botão (`alerta_visto: true`), e a resposta volta com o 190 ainda visível.
- Modo "ajudando outra pessoa": botão que envia só `ajudando: true`; o jurídico passa a falar na terceira pessoa, e os textos dos agentes do navegador também mudam.
- Fora do tema: recusa padrão com Ligue 180 e Defensoria, sem chamar o RAG.
- Resultado de benefícios no chat em cartão, com o contrato comum da `s3-beneficios`.
- Registro de roteamento só com quem decidiu (`regra`, `llm`, `reserva`) e o agente, nunca o texto.
- `responder()` de `app/rag/resposta.py` recebe eixos, instruções e limite por parâmetro. O `/juridico` continua exatamente como foi avaliado na S3.
- Casos fictícios da S4 (elegibilidade, triagem e roteamento), conferidos por uma pessoa que não os escreveu; medição das duas metas e relatório curto da S4.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `conversa`: o encaminhamento passa a ser em duas etapas, e o cenário "Mensagem com risco e pergunta" passa a exigir o botão "Continuar com minha pergunta". Entram requisitos para separar várias perguntas, ordenar as respostas, recusar o fora do tema, não ter memória entre perguntas, mostrar o cartão de benefícios, registrar o roteamento sem texto e usar o modo de ajuda só com a indicação do modo.
- `avaliacao`: entram os conjuntos de casos da S4 (elegibilidade, triagem e roteamento), com conferência por outra pessoa, e a medição das metas da S4 por regra, sem corretor externo.

## Impact

- **Código novo:** a rota `/orquestrar` e o módulo do orquestrador no servidor, as regras de roteamento em arquivo versionado, o módulo do chat que despacha para os agentes do navegador, os testes com LLM falso e os conjuntos de casos em `avaliacao/conjuntos/s4/`.
- **Código alterado:** `app/main.py`, `app/rag/resposta.py` (parâmetros, sem mudar o `/juridico`), `web/app.js` (`enviar()`, alerta e modo de ajuda), `web/index.html`, `web/sw.js`, `tests/test_pwa.py`, `scripts/validar_conjuntos.py`.
- **Depende de:** `s3-beneficios` (contrato comum), `s3-triagem-fonar` e `s3-frontend-e-perfil`. Usa a função de ordenar serviços de `s4-rede-atendimento` quando ela existir; sem ela, o cartão de rede leva para a tela Onde buscar ajuda. **Não depende** de `s4-rag-beneficios`.
- **Privacidade (LGPD):** o perfil e as respostas de benefícios e da triagem continuam só no aparelho. O pedido leva só o texto, `alerta_visto` e `ajudando`, sem histórico. O servidor recusa campos a mais, como `perfil` ou `historico`. O registro guarda só o rótulo do roteamento. Nenhuma spec de `privacidade-seguranca` muda. O texto continua indo ao DeepSeek conforme a decisão de 09/11, agora também para classificar a mensagem.
- **Segurança da usuária:** texto com sinal de risco nunca vai ao LLM sem o toque em "Continuar". O 190 continua visível acima da resposta. A checagem de risco no servidor continua valendo para páginas antigas. A regra de benefícios nunca afirma direito garantido.
- **Fora desta mudança:** memória de conversa, envio do perfil ao servidor, mudança no `/juridico` e no `/mensagem`, o RAG de benefícios (`s4-rag-beneficios`), a busca por CEP e as listas de CRAS e saúde (`s4-rede-atendimento`), rodada com corretor externo na S4 e o refinamento das perguntas sugeridas (item 2 da ordem de corte da S4).
