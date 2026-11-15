# Envios ao corretor

Corretor: **Gemini 4 Argon** (Google), escolhido pela equipe em 15/11/2026 (tarefa 4.1). O mesmo modelo corrige a rodada de desenvolvimento e a oficial.

| Envio | Rubrica |
|---|---|
| `envios/A-precisao.txt` e `envios/B-precisao.txt` | `precisao.md` |
| `envios/A-fidelidade.txt` e `envios/B-fidelidade.txt` | `fidelidade.md` |

## Antes de enviar

- Desligue a busca na web e a memória (contexto pessoal, conversas anteriores). No Google AI Studio, deixe a busca do Google ("Grounding with Google Search") desligada.
- O corretor não pode ter acesso ao repositório: envie só o texto.
- Não abra `mapa.yaml` antes de rodar `scripts/conferir.py`.

## Cada um dos quatro envios

1. Abra uma conversa nova.
2. Em uma única mensagem, cole o texto inteiro da rubrica e, logo abaixo, o texto inteiro do arquivo de envio.
3. Salve a resposta inteira, sem editar, em `<rodada>/retornos/<A|B>-<precisao|fidelidade>.json`. Pode ficar dentro de um bloco ```` ```json ````.
4. Registre o modelo, com o nome exato mostrado na interface, e a data em `<rodada>/retornos/registro.yaml`:

```yaml
A-precisao: {modelo: "Gemini 4 Argon", data: 2026-11-16}
A-fidelidade: {modelo: "Gemini 4 Argon", data: 2026-11-16}
B-precisao: {modelo: "Gemini 4 Argon", data: 2026-11-16}
B-fidelidade: {modelo: "Gemini 4 Argon", data: 2026-11-16}
```

Se a resposta vier cortada, não peça para continuar: salve como veio e rode a conferência, que aponta as linhas faltantes. Depois repita o envio em uma conversa nova.

## Conferência

```
uv run python -m scripts.conferir avaliacao/rodadas/<rodada>
```

Os quatro arquivos precisam sair aceitos. Se o corretor aprovar uma resposta errada de propósito, a correção daquele arquivo não vale, e a rubrica ou o modelo precisa mudar antes de um novo envio.
