# Design

## Context

`dados/fonar/notas.md` traz o texto de 2025 e a classificação de cada item para autoaplicação. As regras de risco imediato já usam o padrão de arquivo versionado (`regras/risco_imediato.json`) lido pela PWA (`web/risco.js`), servido em `/regras` e guardado pelo service worker, com testes em QuickJS (`tests/test_risco_js.py`). As páginas do CNJ bloquearam acesso automático, então ninguém conferiu ainda se o PDF oficial define níveis de risco.

## Goals / Non-Goals

**Goals:**
- Regras legíveis pela equipe e testáveis caso a caso.
- Funcionar offline, como o alerta de 190.

**Non-Goals:**
- Pontuação numérica.
- Personalizar a triagem com o perfil. As respostas não vêm do perfil nem vão para ele.

## Decisions

### Arquivo de regras próprio
`regras/triagem_fonar.json` guarda versão, fonte, ordem das perguntas, opções e o efeito de cada opção (`alto`, `atencao`, `nenhum` ou `indeterminado`). Alternativa descartada: colocar as regras no JavaScript, que dificultaria a revisão por quem não programa.

### Avaliação como função pura
`web/triagem.js` recebe regras e respostas e devolve o próximo passo ou o resultado, sem tocar na tela. Assim, os testes em QuickJS percorrem as combinações sem navegador. Alternativa descartada: lógica junto da tela, sem teste automatizado.

### As 13 perguntas
Gatilhos: itens 1, 2, 5 (só para abrir o 5.1), 5.1 e 11. Atenção: itens 3, 4, 6, 9, 12, 13, 15 e 22. O item 5.1 só deixa de ser perguntado quando a usuária diz que nunca registrou ocorrência nem pediu medida. Se ela pular o item 5, o 5.1 é perguntado, porque a dúvida não pode reduzir o nível.

### Respostas que contam como afirmativas
Nos itens de atenção, qualquer opção "sim" conta, inclusive no item 15, em "sofri violência nesse período, mas não atualmente". No item 4, conta qualquer comportamento marcado. É a leitura conservadora exigida pela spec.

### Pulo em pergunta de atenção
A decisão de 09/11 trata só dos quatro gatilhos. A spec exige o nível mais alto na dúvida e proíbe reduzir o nível por falta de resposta, então pulo ou "não sei" em pergunta de atenção resulta em "atenção".

### Precedência dos resultados
Alto confirmado, depois "não foi possível descartar risco alto", depois atenção e, por fim, sem sinais graves. Um gatilho confirmado depois de um pulo ainda resulta em alto.

### Textos
Os textos são fixos e ficam no arquivo de regras, em linguagem simples. Os resultados de nível alto trazem a ligação para o 190 e como pedir medida protetiva. Todos trazem o aviso de limite e o Ligue 180.

### Teste em QuickJS
A triagem segue o padrão atual dos testes de JavaScript, que passou no Mac e não compilou na máquina Windows. A troca por Node é uma proposta ainda sem confirmação e fica fora desta mudança.

## Risks / Trade-offs

- **O PDF oficial pode definir níveis próprios** → É a primeira tarefa. Se houver níveis oficiais, eles substituem esta proposta, e a mudança é ajustada com `/opsx:update` antes de implementar.
- **Falso negativo em um gatilho** → Testes percorrem cada gatilho, cada pulo e as combinações com perguntas de atenção, e a suíte falha em qualquer caso que reduza o nível.
- **A pergunta pode reavivar sofrimento** → Os itens "adaptável com cuidado" têm redação acolhedora e podem ser pulados, sem reduzir o nível.
- **A triagem tem até 13 perguntas e a usuária pode estar com pressa** → Os gatilhos vêm primeiro e a triagem encerra no primeiro gatilho alto.

## Verificação Manual Registrada (12/11/2026)

- **Abertura e execução sem internet (tarefa 3.2):** Com o Service Worker (`interface-v12`) instalado e o navegador offline, a seção de Avaliação de Risco (`#sec-fonar`) carrega `web/triagem.js` e `regras/triagem_fonar.json` do cache local e executa todas as etapas até o resultado final.
- **Saída rápida durante a triagem (tarefa 3.3):** Respondendo perguntas no meio da triagem e acionando `"Saída rápida"` (ou `Esc`), a página é substituída pelo site neutro e, ao retornar para a aplicação, nenhuma resposta anterior da triagem reaparece.
