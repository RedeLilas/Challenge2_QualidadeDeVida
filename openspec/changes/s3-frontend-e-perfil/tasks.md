# Tasks

## 1. Navegação (terça, 10/11)

- [ ] 1.1 Criar a navegação e as seções de Conversa, Triagem, Perfil, Benefícios e Onde buscar ajuda em `web/index.html`, `web/app.js` e `web/styles.css`, seguindo `DESIGN.md`, com a conversa como primeira tela; verificação: `tests/test_pwa.py` confere as seções, a saída rápida fora delas e a conversa inicial
- [ ] 1.2 Incluir os novos arquivos no service worker e subir a versão do cache; verificação: `tests/test_pwa.py` confere a lista, e as telas abrem sem internet na verificação manual

## 2. Perfil e armazenamento (quinta, 12/11)

- [ ] 2.1 Criar `web/perfil.js`, com leitura, escrita e remoção de uma única chave neutra, e o formulário com os campos da spec e "prefiro não informar"; verificação: testes em QuickJS cobrem salvar, ler, apagar e campo não informado
- [ ] 2.2 Alterar `tests/test_pwa.py` para verificar todos os scripts de `web/`, permitindo armazenamento só em `web/perfil.js`; verificação: o teste falha se `app.js` ou outro script usar armazenamento
- [ ] 2.3 Criar o botão "apagar meus dados", que remove só o perfil; verificação: teste confere que o cache do service worker não é apagado, e a verificação manual confirma o alerta de 190 sem internet depois de apagar
- [ ] 2.4 Fazer a saída rápida apagar o perfil, sem apagar em `pagehide`; verificação: testes conferem a remoção em `sair()` e a verificação manual confirma que o perfil continua depois de fechar a aba
- [ ] 2.5 Confirmar que o perfil não sai do aparelho; verificação: teste confere que nenhuma requisição de `web/` inclui dados do perfil

## 3. Telas que exigem o formulário (sexta, 13/11)

- [ ] 3.1 Exigir o formulário em Benefícios e Onde buscar ajuda, mantendo conversa e triagem livres, com 190 e Ligue 180 visíveis; verificação: testes conferem o bloqueio das duas telas, a liberação das demais e os telefones na tela
- [ ] 3.2 Criar a rota GET sem parâmetros da rede de proteção e a tela Onde buscar ajuda, com fonte, data, orientação para confirmar por telefone e os serviços da RA do perfil primeiro; verificação: testes conferem a rota e os campos, e nenhum dado do perfil é enviado
- [ ] 3.3 Atualizar `PRODUCT.md` com a exceção do perfil e o caminho atual das specs; verificação: o arquivo não diz mais que o perfil local está fora de escopo
- [ ] 3.4 Registrar a finalidade do estado civil neste `design.md`; verificação: a questão aberta do design foi resolvida
- [ ] 3.5 Conferir teclado, rótulos e foco nas novas telas e rodar a suíte completa; verificação: a verificação manual está registrada e `uv run pytest` passa, incluindo a suíte de risco/190

## Workflow follow-up

- Atualizar o status no `ROADMAP.md` e arquivar a mudança, depois de `openspec validate s3-frontend-e-perfil` passar.
