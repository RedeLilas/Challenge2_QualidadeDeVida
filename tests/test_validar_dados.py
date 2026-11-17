"""Testes automatizados para os dados levantados em s2-fontes-df."""

from pathlib import Path

from scripts.validar_dados import (
    validar_cep,
    validar_fonar,
    validar_normas,
    validar_rede_protecao,
    validar_tudo,
)


def test_rede_protecao_df_valida():
    assert validar_rede_protecao() == []


def test_normas_csv_valido():
    assert validar_normas() == []


def test_fonar_notas_valido():
    assert validar_fonar() == []


def test_validar_tudo_sem_erros():
    assert validar_tudo() == []


def test_rede_protecao_rejeita_cep_fora_do_df_ra_invalida_e_duplicata(tmp_path: Path):
    csv_invalido = tmp_path / "rede_invalida.csv"
    csv_invalido.write_text(
        "nome,tipo,ra,endereco,cep,telefone,horario,fonte_url,data_verificacao,competencia_cnes\n"
        "Serviço A,CMB,Asa Sul,Rua 1,01001-000,(61) 3181-1474,24h,https://www.mulher.df.gov.br/telefone-das-unidades-2/,2026-11-05,\n"
        "Serviço A,CEAM,Ceilândia,Rua 2,72215-110,(61) 3372-2619,8h às 18h,https://www.tjdft.jus.br/informacoes/cidadania/nucleo-judiciario-da-mulher/telefones-uteis,2026-11-05,\n",
        encoding="utf-8",
    )
    erros = validar_rede_protecao(csv_invalido)
    assert any("RA 'Asa Sul'" in e for e in erros)
    assert any("fora da faixa do Distrito Federal" in e for e in erros)
    assert any("serviço duplicado 'Serviço A'" in e for e in erros)


def test_normas_detecta_divergencia_com_fontes_yaml(tmp_path: Path):
    normas_csv = tmp_path / "normas.csv"
    normas_csv.write_text(
        "norma,esfera,tema,artigos_relevantes,resumo,vigencia_inicio,fonte_url,data_verificacao\n"
        "Lei 11.340/2006,federal,juridico,art. 1º,Resumo,2006-09-22,https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm,2026-11-05\n"
        "Lei Distrital 6.623/2020,distrital,beneficio,art. 1º,Resumo,2020-07-08,https://www.sinj.df.gov.br/sinj/Norma/outro.html,2026-11-05\n",
        encoding="utf-8",
    )
    fontes_yaml = tmp_path / "fontes.yaml"
    fontes_yaml.write_text(
        "normas:\n"
        '  - id: lei-df-6623-2020\n'
        '    citacao: "Lei Distrital 6.623/2020"\n'
        '    url: "https://www.sinj.df.gov.br/sinj/Norma/8f17787cca524d5da839b613d96d9164/Lei_6623_25_06_2020.html"\n',
        encoding="utf-8",
    )
    erros = validar_normas(normas_csv, fontes_yaml)
    assert any("Lei Distrital 6.623/2020" in e for e in erros)


# --- s4-rede-atendimento, tarefa 1.5 (dados fictícios; a URL dos Correios é a da fonte real) ---

CABECALHO_REDE = "nome,tipo,ra,endereco,cep,telefone,horario,fonte_url,data_verificacao,competencia_cnes\n"
URL_CORREIOS = "https://buscacepinter.correios.com.br/app/faixa_cep_uf_localidade/index.php"


def _rede(tmp_path: Path, *linhas: str) -> list[str]:
    caminho = tmp_path / "rede.csv"
    caminho.write_text(CABECALHO_REDE + "".join(l + "\n" for l in linhas), encoding="utf-8")
    return validar_rede_protecao(caminho)


def _cep(tmp_path: Path, *linhas: str) -> list[str]:
    caminho = tmp_path / "cep.csv"
    caminho.write_text("cep_inicio,cep_fim,fonte_url,data_verificacao\n" + "".join(l + "\n" for l in linhas), encoding="utf-8")
    return validar_cep(caminho)


def test_tabela_de_cep_do_repositorio_valida():
    assert validar_cep() == []


def test_cep_de_servico_entre_as_duas_faixas_nao_e_do_df(tmp_path: Path):
    erros = _rede(tmp_path, "CRAS Fictício,CRAS,Gama,Rua 1,72800-000,(61) 0000-0000,8h às 17h,https://www.sedes.df.gov.br/unidades/,2026-11-17,")
    assert any("72800-000" in e and "fora da faixa do Distrito Federal" in e for e in erros)


def test_cras_aceito_e_saude_exige_competencia(tmp_path: Path):
    erros = _rede(
        tmp_path,
        "CRAS Fictício,CRAS,Gama,Rua 1,72405-000,(61) 0000-0000,8h às 17h,https://www.sedes.df.gov.br/unidades/,2026-11-17,",
        "CEPAV Fictício,Saúde,Gama,Rua 2,72405-000,(61) 0000-0001,7h às 19h,https://cnes.datasus.gov.br/,2026-11-17,",
        "CEPAV Fictício 2,Saúde,Gama,Rua 3,72405-000,(61) 0000-0002,7h às 19h,https://cnes.datasus.gov.br/,2026-11-17,2026-13",
    )
    assert not any("CRAS" in e and "tipo" in e for e in erros)
    assert any(":3: serviço de saúde sem competencia_cnes" in e for e in erros)
    assert any(":4: competencia_cnes '2026-13'" in e for e in erros)


def test_faixas_sobrepostas(tmp_path: Path):
    erros = _cep(
        tmp_path,
        f"70000-000,72799-999,{URL_CORREIOS},2026-11-17",
        f"72000-000,72100-000,{URL_CORREIOS},2026-11-17",
        f"73000-000,73699-999,{URL_CORREIOS},2026-11-17",
    )
    assert any("faixas sobrepostas nas linhas 2 e 3" in e for e in erros)


def test_faixa_fora_do_df(tmp_path: Path):
    erros = _cep(
        tmp_path,
        f"70000-000,72799-999,{URL_CORREIOS},2026-11-17",
        f"72800-000,72999-999,{URL_CORREIOS},2026-11-17",
        f"73000-000,73699-999,{URL_CORREIOS},2026-11-17",
    )
    assert any(":3: faixa fora do Distrito Federal" in e for e in erros)


def test_faixa_invertida_formato_fonte_e_data(tmp_path: Path):
    erros = _cep(
        tmp_path,
        f"72799-999,70000-000,{URL_CORREIOS},2026-11-17",
        "73000000,73699-999,https://www.sedes.df.gov.br/,17/11/2026",
    )
    assert any(":2: cep_inicio maior que cep_fim" in e for e in erros)
    assert any(":3: cep_inicio '73000000' fora do formato" in e for e in erros)
    assert any(":3: fonte_url" in e and "Correios" in e for e in erros)
    assert any(":3: data_verificacao '17/11/2026' inválida" in e for e in erros)


def test_faixas_precisam_cobrir_o_df(tmp_path: Path):
    erros = _cep(tmp_path, f"70000-000,72799-999,{URL_CORREIOS},2026-11-17")
    assert any("não cobrem exatamente o DF" in e for e in erros)


def test_correios_so_vale_na_tabela_de_cep(tmp_path: Path):
    erros = _rede(tmp_path, f"CRAS Fictício,CRAS,Gama,Rua 1,72405-000,(61) 0000-0000,8h às 17h,{URL_CORREIOS},2026-11-17,")
    assert any("não pertence a domínio oficial" in e for e in erros)


def test_cep_vazio_so_vale_para_cras(tmp_path: Path):
    erros = _rede(
        tmp_path,
        "CRAS Fictício,CRAS,Gama,Rua 1,,(61) 0000-0000,8h às 17h,https://www.sedes.df.gov.br/unidades/,2026-11-17,",
        "CEAM Fictício,CEAM,Gama,Rua 2,,(61) 0000-0001,8h às 17h,https://www.mulher.df.gov.br/,2026-11-17,",
    )
    assert not any(":2:" in e for e in erros)
    assert any(":3: coluna 'cep' vazia" in e for e in erros)
