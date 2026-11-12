# Tasks

## 1. Leitura de artigos com separador de milhar (terça, 10/11)

- [x] 1.1 Corrigir a leitura de "Art. 1.584." em `app/rag/planalto.py` e o identificador do dispositivo; verificação: novos testes em `tests/test_ingestao.py` cobrem "Art. 1.584.", "Art. 699-A." e "Art. 147 - Ameaçar"
- [x] 1.2 Corrigir `RE_ARTIGO` e `RE_MAIS_ARTIGOS` em `app/rag/resposta.py`, comparando o artigo sem o ponto; verificação: novos testes em `tests/test_juridico.py` cobrem "art. 1.584", "art. 1584", "arts. 1.583 e 1.584" e a recusa quando só há o art. 1 de outra norma
- [x] 1.3 Incluir Código Civil e Código de Processo Civil em `LEIS_JURIDICAS` e `APELIDOS`, com a Lei 14.713/2023 como apelido; verificação: teste em que uma resposta correta menciona a Lei 14.713/2023 e não é recusada

## 2. Ampliação da base (terça, 10/11)

- [ ] 2.1 Acrescentar ao Código Penal, em `dados/fontes/fontes.yaml`, os arts. 121-A, 138, 139, 140, 148, 163, 181, 182, 183, 213, 215-A e 218-C; verificação: `uv run python -m app.rag.coleta --norma decreto-lei-2848-1940` grava um arquivo em `dados/fontes/dispositivos/` com todos os artigos pedidos
- [ ] 2.2 Incluir Código Civil (art. 1.584) e CPC (art. 699-A) em `fontes.yaml`, no eixo `juridico`, conferindo URL e URN oficiais, e coletar; verificação: os dois artigos aparecem em `dados/fontes/dispositivos/` com o número completo
- [ ] 2.3 Revisar o relatório em `dados/fontes/relatorios/` e rodar `uv run python -m app.rag.ingestao`; verificação: cada artigo da spec tem ao menos um trecho em `dados/leis/` com URL e data, e `uv run pytest` passa
- [ ] 2.4 Atualizar a quantidade de normas no `README.md`; verificação: o número citado é igual ao de normas em `fontes.yaml`

## 3. Recalibração (quinta, 12/11)

- [ ] 3.1 Rodar de novo o teste rápido com a base ampliada; verificação: `uv run pytest tests/test_indice.py` mantém ao menos 9 de 10 perguntas no top 5
- [ ] 3.2 Recalibrar `LIMITE_SIMILARIDADE` só com as perguntas de desenvolvimento, sem usar o conjunto oficial, e registrar os valores em `openspec/changes/s3-base-legal-ampliada/design.md`; verificação: nenhuma pergunta de desenvolvimento do tema é recusada pelo limite, e o comentário em `app/rag/resposta.py` não cita mais as 50 perguntas
- [ ] 3.3 Rodar a suíte de risco/190 e a suíte completa; verificação: `uv run pytest` passa sem falso negativo

## Workflow follow-up

- Atualizar o status no `ROADMAP.md` e arquivar a mudança, depois de `openspec validate s3-base-legal-ampliada` passar.
