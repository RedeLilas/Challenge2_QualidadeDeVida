# Proposal

## Why

A PWA hoje só tem a conversa e o botão Sair. A triagem, os benefícios e a lista de serviços precisam de telas, e benefícios dependem de dados da usuária. O grupo decidiu em 10/11 trazer o perfil para a S3, guardado só no navegador, e incluir uma mudança de front-end.

Métricas do ROADMAP afetadas: acurácia de elegibilidade (≥ 90%, S4), porque o perfil alimenta as regras, e usabilidade (SUS ≥ 70, S7).

## What Changes

- Navegação entre Conversa, Triagem, Perfil, Benefícios e Onde buscar ajuda, com a saída rápida em todas as telas.
- Formulário de perfil com os campos da spec, mais idade, estado civil e número de pessoas da casa.
- **BREAKING (produto):** Benefícios e Onde buscar ajuda passam a exigir o formulário. O chatbot e a triagem continuam sem ele.
- O perfil fica guardado no navegador, sem banco de dados e sem envio ao servidor.
- Função para apagar rapidamente os dados do perfil.
- O teste que proíbe armazenamento no aparelho passa a permitir só o perfil. A conversa continua sem persistência.
- A tela Onde buscar ajuda lista a rede de proteção já levantada, sem busca por região.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `privacidade-seguranca`: redefine os campos do perfil, o acesso às funções que exigem o formulário, a saída rápida e a função de apagar dados.
- `interface-pwa`: acrescenta a navegação entre as funções.

## Impact

- **Código:** `web/index.html`, `web/app.js`, `web/styles.css`, `web/sw.js`, novo `web/perfil.js`, nova rota de leitura da rede de proteção em `app/main.py`.
- **Testes:** `tests/test_pwa.py`.
- **Documentos:** `PRODUCT.md`, que hoje diz que nada digitado sobrevive ao fechamento da aba e aponta para o caminho antigo das specs.
- **Depende de:** nenhuma outra mudança. `s3-triagem-fonar` e `s3-beneficios` usam a navegação e o perfil desta mudança.
- **Privacidade (LGPD):** renda, idade, estado civil e medida protetiva ficam no aparelho, sem nome ou documento, e são apagáveis. O perfil não vai ao servidor nem ao LLM. Nenhuma regra da S3 usa o estado civil, o que precisa de finalidade registrada (LGPD, art. 6º, III).
- **Segurança da usuária:** o perfil persistente pode ser visto por quem tiver acesso ao celular, e a exigência do formulário atrasa o acesso a serviços. As mitigações estão no design: 190 e Ligue 180 sempre visíveis, "prefiro não informar", saída rápida que apaga o perfil e chave neutra de armazenamento.
- **Fora desta mudança:** regras de benefícios (`s3-beneficios`), regras da triagem (`s3-triagem-fonar`), busca por RA ou CEP e CNES (S4), modo "ajudando outra pessoa" (S4), nome e ícone finais (S6).
