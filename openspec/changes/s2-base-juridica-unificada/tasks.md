# Tasks

## 1. Coleta e leitor unificados (quinta, 05/11)

- [x] 1.1 Mover com `git mv` os dados e a coleta do `backend/` para `dados/fontes/` e `app/rag/` (`versoes.py`, `coleta.py`), ajustando caminhos e imports; verificação: `uv run pytest` passa e `git log --follow` mostra o histórico dos arquivos movidos
- [x] 1.2 Unificar `app/rag/planalto.py` com as correções dos dois leitores e remover `backend/app/ingestao/planalto.py`; verificação: testes de que o Código Penal tem os arts. 147 e 147-A separados e de que "(VETADO." sem parêntese é reconhecido
- [x] 1.3 Adicionar `coleta.py --reprocessar` e reprocessar as 16 normas a partir de `dados/fontes/raw/`; verificação: relatório em `dados/fontes/relatorios/` revisado, com as diferenças explicadas

## 2. Trechos e índice (quinta, 05/11)

- [x] 2.1 Adicionar `eixo` às normas de `fontes.yaml` e generalizar `app/rag/ingestao.py` para gerar `dados/leis/<norma_id>.jsonl` de todas as normas; verificação: a Lei 11.340/2006 continua com 109 trechos e toda norma tem trechos com url e data de acesso
- [x] 2.2 Adicionar o filtro `eixos` a `Indice.buscar()` e rodar o teste das personas com `eixos={"juridico"}`; verificação: artigo esperado no top 5 em pelo menos 9 de 10, e "violência patrimonial" recupera o art. 7º no índice completo
- [ ] 2.3 Portar a busca manual para `app/rag/buscar.py` com `--eixo`; verificação: "ele quebrou minhas coisas, isso é violência?" traz a Lei 11.340/2006, art. 7º, IV, no top 5

## 3. Remoção e documentação (sexta, 06/11)

- [ ] 3.1 Remover o restante de `backend/` (índice Chroma, `indexar.py`, `requirements.txt`, `README.md`, `.gitignore`); verificação: `git ls-files backend` vazio e `uv run pytest` passa
- [ ] 3.2 Criar o `README.md` da raiz com o fluxo coleta → ingestão → busca → testes; verificação: os comandos do README rodam do zero num clone limpo
- [ ] 3.3 Rodar a suíte de risco/190 (se `s2-alerta-risco-190` já tiver entregado `tests/test_risco.py`), atualizar o status no `ROADMAP.md` e arquivar a mudança
