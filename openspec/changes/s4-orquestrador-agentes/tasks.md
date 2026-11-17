# Tasks

## 1. Base comum (terça, 17/11, manhã)

- [x] 1.1 Parametrizar `responder()` em `app/rag/resposta.py` com `eixos`, `instrucoes` e `limite`, com os valores da S3 como padrão (primeira tarefa da terça, pela frente do RAG de benefícios, antes das outras mudanças no arquivo); verificação: `tests/test_juridico.py` passa sem alteração, e um teste novo confere que `/juridico` usa `{"juridico"}`, `INSTRUCOES` e 0,81
- [x] 1.2 Revisar o contrato do `/orquestrar` do design com as frentes do servidor e do navegador e criar um arquivo de respostas de exemplo (uma por agente, mais alerta sem e com `alerta_visto`, várias perguntas e excesso); verificação: um teste valida cada exemplo contra o modelo Pydantic da resposta

## 2. Servidor: regra e classificação (terça, 17/11)

- [x] 2.1 Criar `regras/roteamento.json` (palavras por agente, marcas de "tenho direito?", marcas de várias perguntas e apelidos do auxílio-aluguel) e a etapa de regra, sem acento e em minúsculas; verificação: testes cobrem a decisão com um agente só, a não decisão com dois agentes, com 2+ "?" e com "e também", "outra coisa" e "além disso", o par auxílio-aluguel (explicação → jurídico; "tenho direito?" → benefícios) e o Aluguel Social → benefícios
- [x] 2.2 Tirar do texto `beneficio`, `ra` e `violencia_sexual_recente`, com `ra` restrito a `RAS_DF`; verificação: testes cobrem RA da lista, RA fora da lista → `null`, benefício sem regra → `"outro"`, e um teste confere que a lista do servidor é igual a `RAS_DF` de `web/dados.js`, sem "Outra RA do DF" e "Prefiro não informar"
- [x] 2.3 Classificar pelo LLM com instrução de lista fechada, temperatura 0 e saída validada; JSON inválido, agente fora da lista ou `LLMIndisponivel` levam à reserva `juridico`; verificação: testes com LLM falso cobrem cada caso e conferem a temperatura 0
- [x] 2.4 Separar e ordenar até 3 perguntas (triagem primeiro, depois a ordem escrita), devolvendo até 2 em `outras_perguntas` e `excedeu` com mais de 3; verificação: testes com LLM falso cobrem duas perguntas, triagem depois de benefício, quatro perguntas e o uso do texto original quando há só uma pergunta

## 3. Servidor: rota `/orquestrar` (terça, 17/11, e quinta, 19/11)

- [x] 3.1 Criar `POST /orquestrar` com pedido `{texto, alerta_visto, ajudando}`, que recusa campos a mais, e com `risco.avaliar` antes de tudo (terça); verificação: testes conferem 422 com `perfil` ou `historico`, só o alerta sem `alerta_visto` (com um LLM falso que falha se for chamado) e `risco_imediato: true` junto com a resposta quando há `alerta_visto`
- [x] 3.2 Responder no mesmo pedido: jurídico por `responder()`, fora do tema com o texto fixo (Ligue 180 e Defensoria, sem índice e sem LLM de resposta), explicação de benefícios por um ponto de troca que usa o jurídico enquanto `s4-rag-beneficios` não existir, e 503 com o LLM fora do ar (terça); verificação: testes com índice e LLM falsos cobrem cada caminho, e `/juridico` continua com os mesmos testes
- [x] 3.3 Registrar o roteamento no logger `rede_lilas.orquestrador` só com `decidido_por` e `agente` (terça); verificação: teste com `caplog` envia um texto marcado e confere que ele, as perguntas reescritas e os campos não aparecem no log
- [x] 3.4 Criar `INSTRUCOES_AJUDANDO` (terceira pessoa, como apoiar sem expor a vítima, respeito à decisão dela) e usá-las no jurídico com `ajudando: true` (quinta); verificação: testes conferem a instrução enviada ao LLM com e sem a flag e que `INSTRUCOES` não mudou (`tests/test_instrucoes_sem_rag.py` passa)

## 4. Navegador: chat (terça, 17/11, com a resposta falsa; quinta, 19/11, ligado ao servidor)

- [x] 4.1 Criar `web/conversa.js` com funções puras para montar o pedido e transformar a resposta em blocos (resposta com fontes, fora do tema, explicação, oferta de triagem, sugestões e excesso), usando as respostas de exemplo (terça); verificação: testes em QuickJS cobrem cada exemplo e conferem que o pedido só tem `texto`, `alerta_visto` e `ajudando`
- [x] 4.2 Montar o cartão de benefício com `Beneficios.avaliar` e o perfil, filtrado por `campos.beneficio`, com convite ao formulário sem perfil e mensagem para `"outro"` (terça); verificação: testes em QuickJS com perfis fictícios conferem os campos do contrato comum (situação, norma, artigo, data, aviso), a ausência de "direito garantido" e o auxílio-aluguel como "depende de decisão judicial"
- [x] 4.3 Montar a lista curta de rede (até 3 serviços, ordenados por `campos.ra` ou pela RA do perfil, usando a função de `s4-rede-atendimento` se existir, senão a mesma RA e depois os plantões 24 horas) com botão para a lista completa (quinta); verificação: testes em QuickJS cobrem as duas formas de ordenar e a ausência de RA
- [x] 4.4 Fazer `enviar()` chamar `/orquestrar`: alerta local com o botão "Continuar com minha pergunta", texto guardado só em memória, reenvio com `alerta_visto: true` e linha de 190 acima da resposta quando `risco_imediato` vier junto (quinta); verificação: `tests/test_pwa.py` confere `Risco.avaliar` antes do `fetch`, que o envio só acontece pelo botão e que nenhum `fetch` leva perfil, respostas de benefícios ou da triagem; o teste da rota jurídica da tela passa a conferir `/orquestrar`
- [x] 4.5 Mostrar `outras_perguntas` como botões que enviam uma mensagem nova e apagar sugestões e texto em espera em `apagarConversa()` (quinta); verificação: `tests/test_pwa.py` confere a limpeza no `pagehide` e em `sair()`
- [x] 4.6 Criar o botão do modo "ajudando outra pessoa" (`aria-pressed`, só em memória) e os textos alternativos dos agentes do navegador (quinta); verificação: testes em QuickJS conferem o texto em terceira pessoa e `ajudando: true` no pedido, e `tests/test_pwa.py` confere que o estado não é gravado
- [x] 4.7 Incluir `web/conversa.js` no service worker e na lista de scripts verificados e subir a versão do cache (quinta); verificação: `tests/test_pwa.py` confere a lista e que só `web/perfil.js` usa armazenamento

## 5. Casos e medição (terça, 17/11, escrita; quinta, 19/11, conferência e medição)

- [x] 5.1 Escrever com o Claude `avaliacao/conjuntos/s4/elegibilidade.yaml`, com 20 a 30 perfis fictícios, a situação esperada por benefício e a fonte (artigo ou portaria) tirada do texto em `dados/leis/`, incluindo renda no corte, um real acima, "prefiro não informar" e perfil incompleto (terça); verificação: o arquivo carrega e cada caso tem fonte
- [x] 5.2 Escrever com o Codex `avaliacao/conjuntos/s4/triagem.yaml`, com respostas ao Fonar, o nível esperado e o item de `dados/fonar/notas.md` (terça); verificação: o arquivo carrega e tem casos de alto, "não foi possível descartar risco alto", atenção e sem sinais graves
- [x] 5.3 Escrever com o Codex `avaliacao/conjuntos/s4/roteamento.yaml`, com cerca de 30 mensagens em linguagem leiga e o agente esperado, incluindo "tenho direito?" e "o que é?", o par auxílio-aluguel e Aluguel Social, "como funciona o aluguel da Maria da Penha?", várias perguntas e fora do tema (terça); verificação: o arquivo carrega e cada mensagem passa pela regra de risco
- [x] 5.4 Validar os conjuntos da S4 em `scripts/validar_conjuntos.py` (fonte, autor, revisor diferente do autor, os quatro limites, os pares de roteamento), sem mudar a validação da S3 (terça); verificação: testes em `tests/test_validar_conjuntos.py` cobrem caso sem fonte, revisor igual ao autor e limite ausente
- [ ] 5.5 Conferir os gabaritos por uma pessoa que não escreveu os casos e registrar o nome em `conferencia.revisor`, mudando `conferencia.status` para `conferido` após a revisão (quinta); verificação: `uv run python -m scripts.validar_conjuntos s4` passa nos três arquivos
- [ ] 5.6 Medir a acurácia de elegibilidade (`Beneficios.avaliar` em QuickJS, por par perfil × benefício) e a sensibilidade para risco alto (`Triagem.avaliar` mais `tests/casos_risco.yaml`) (quinta); verificação: um teste falha com qualquer falso negativo de risco alto, e o script imprime a acurácia e os casos divergentes
- [ ] 5.7 Medir o roteamento: a regra sem LLM e os demais casos com o modelo de produção, registrando nome, data e versão (quinta); verificação: o resultado fica salvo em `avaliacao/rodadas/s4/` com a taxa de acerto e os erros
- [ ] 5.8 Escrever `docs/Relatório S4 - Sistema multiagentes.md` com as três medidas, o número de casos, a data, a ferramenta usada para redigir cada conjunto, a conferência por uma pessoa da equipe e a ausência de corretor externo (quinta); verificação: a revisão do relatório confere cada item da spec `avaliacao`

## 6. Integração (quinta, 19/11)

- [ ] 6.1 Rodar a suíte de risco/190 e a suíte completa e fazer no navegador o fluxo alerta → "Continuar" → resposta com 190 visível, uma pergunta de benefício com e sem perfil e uma com duas perguntas; verificação: `uv run pytest` passa sem falso negativo, e o fluxo manual fica registrado no design
- [ ] 6.2 Atualizar o status da mudança e o resultado das metas da S4 no `ROADMAP.md`; verificação: a tabela da S4 mostra o status e os valores medidos

## Workflow follow-up

- Arquivar a mudança depois de `openspec validate s4-orquestrador-agentes` passar e de atualizar o `ROADMAP.md`.
