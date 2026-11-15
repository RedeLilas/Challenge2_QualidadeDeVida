# Design

## Context

A PWA é uma página única em HTML, CSS e JS puros. `tests/test_pwa.py:73` proíbe armazenamento só em `app.js` e `sw.js`. O service worker guarda a interface e as regras do alerta de 190, e apaga os caches de versões antigas (`web/sw.js:29`). A saída rápida (`sair()` em `web/app.js:37`) apaga só a conversa. `dados/rede_protecao_df.csv` tem 21 serviços, sem CRAS, e a busca por RA ou CEP está na S4. `PRODUCT.md` assume que o agressor pode ver a tela e diz que nada digitado sobrevive ao fechamento da aba.

## Goals / Non-Goals

**Goals:**
- Dar uma estrutura de telas para triagem, perfil, benefícios e serviços, sem framework e sem etapa de build.
- Guardar o perfil no navegador, isolado da conversa.

**Non-Goals:**
- Banco de dados ou contas.
- Personalizar a conversa com o perfil.
- Auditoria WCAG completa (S6), embora os formulários já usem rótulos e foco corretos.

## Decisions

Decidido pelo grupo em 10/11: o chatbot funciona sem formulário, Benefícios e Onde buscar ajuda o exigem, o formulário tem idade e estado civil, os dados ficam no navegador e existe a função de apagar.

Propostas do planejamento, adotadas como padrão desta mudança: as subseções abaixo, salvo indicação.

### Armazenamento em `localStorage`, em `web/perfil.js`
A decisão fala em "cache do navegador". A implementação usa `localStorage`, que é o armazenamento local citado pela spec. Toda leitura e escrita fica em `web/perfil.js`, com uma única chave de nome neutro, porque alguém pode inspecionar o aparelho. Alternativas descartadas: Cache API, feita para respostas HTTP e apagada a cada nova versão do service worker; `sessionStorage`, que não sobrevive ao fechamento da aba; IndexedDB, mais complexo para um único registro.

### Teste de armazenamento com exceção explícita
`tests/test_pwa.py` passa a verificar todos os scripts de `web/` e a permitir armazenamento só em `web/perfil.js`. Assim, a conversa continua protegida, e uma nova tela não grava dados por engano. Alternativa descartada: remover a proibição, que abriria caminho para gravar a conversa.

### Apagar só o que é da usuária
"Apagar meus dados" remove apenas a chave do perfil. O cache do service worker fica, porque contém o alerta de 190 sem internet. Alternativa descartada: limpar todo o armazenamento do site, que tiraria o alerta offline.

### Saída rápida apaga o perfil
`PRODUCT.md` diz que nada digitado sobrevive a tocar em sair e que segurança vem antes de funcionalidade. Por isso `sair()` também apaga o perfil, ao custo de ela responder o formulário de novo. Confirmado pelo grupo em 10/11. Fechar a aba ou o evento `pagehide` não apaga o perfil, para que ele continue persistente.

### Telas como seções da mesma página
Cada função é uma seção alternada por botões, sem rota e sem framework. A conversa é a primeira tela. A alternativa de páginas separadas exigiria repetir a saída rápida e recarregar em conexão lenta.

### "Prefiro não informar" conta como preenchido
Cada campo aceita "prefiro não informar", e o valor fica marcado como ausente. Sem isso, o resultado "faltam informações" de benefícios nunca aconteceria, e o formulário seria um bloqueio maior.

### Formulário com dados estáveis
O formulário guarda só dados estáveis. As perguntas específicas de cada benefício ficam em Benefícios, só em memória.

### Onde buscar ajuda na S3
Lista os serviços de `dados/rede_protecao_df.csv` com fonte, data de verificação e orientação para confirmar por telefone, com os da RA do perfil primeiro. Os dados chegam por uma rota GET sem parâmetros (`GET /rede-protecao`), então nada da usuária vai ao servidor. É o que dá para entregar sem antecipar a busca por RA ou CEP da S4. Confirmado pelo grupo.

### Finalidade do campo `estado_civil`
O campo `estado_civil` faz parte do formulário de perfil para contextualizar a orientação jurídica sobre regime de bens, divórcio, dissolução de união estável, restituição de bens retidos e garantia de que o afastamento do lar por segurança não configura abandono de lar nem perda de direitos patrimoniais ou de guarda (Lei 11.340/2006, arts. 22 a 24), tanto na seção de Direitos & Leis quanto no orquestrador da S4.

## Risks / Trade-offs

- **A exigência do formulário atrasa quem procura uma delegacia às pressas, talvez perto do agressor** → 190 e Ligue 180 visíveis no formulário e nas telas bloqueadas, "prefiro não informar" e formulário curto.
- **O perfil persistente fica no celular** → Sem nome ou documento, chave neutra, função de apagar e saída rápida que apaga o perfil.
- **Os nomes "Benefícios" e "Onde buscar ajuda" na navegação podem denunciar o uso a quem vir a tela** → Os nomes seguem a decisão do grupo. O risco é revisado na S6, com o nome e o ícone finais.
- **Sem conexão, a lista de serviços não carrega** → A tela avisa e mantém 190 e Ligue 180 visíveis (com fallback local das unidades essenciais).

## Open Questions

- Nenhuma pendência aberta: a finalidade do campo `estado_civil` e a rota `GET /rede-protecao` sem parâmetros foram definidas e registradas na seção Decisions acima.

## Verificação Manual Registrada (12/11/2026)

- **Funcionamento sem internet (tarefa 1.2):** Com o Service Worker (`interface-v12`) ativo e o navegador em modo offline, todas as seções (`Início`, `Meu Perfil & Triagem`, `Benefícios Sociais`, `Direitos & Leis`, `Locais de Atendimento` e `Avaliação de Risco`) abrem normalmente sem conexão.
- **Apagar meus dados e alerta de 190 offline (tarefa 2.3):** Acionar o botão `"Apagar meus dados"` remove apenas a chave `anotacoes_preferencias_v1` do `localStorage` e preserva o cache do Service Worker; em seguida, mesmo sem internet, enviar uma frase de risco imediato no chat dispara imediatamente o alerta com `Ligar 190` (`tel:190`) e `Ligue 180` (`tel:180`).
- **Persistência ao fechar a aba vs. Saída rápida (tarefa 2.4):** Salvar o perfil, fechar a aba e reabrir mantém o perfil preenchido e limpa a conversa; tocar em `"Saída rápida"` (ou tecla `Esc`) apaga tanto a conversa quanto o perfil e redireciona via `location.replace()`.
- **Teclado, rótulos e foco (tarefa 3.5):** Todos os campos e filtros possuem `<label>` ou `aria-label`, os botões de opção usam `aria-pressed` e as abas usam `role="tab"` / `aria-selected`, permitindo navegação integral por teclado (`Tab`, `Enter`, `Espaço` e `Esc`).
