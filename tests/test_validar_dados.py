"""Testes automatizados para os dados levantados em s2-fontes-df."""

from pathlib import Path

from scripts.validar_dados import (
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
        "nome,tipo,ra,endereco,cep,telefone,horario,fonte_url,data_verificacao\n"
        "Serviço A,CMB,Asa Sul,Rua 1,01001-000,(61) 3181-1474,24h,https://www.mulher.df.gov.br/telefone-das-unidades-2/,2026-11-05\n"
        "Serviço A,CEAM,Ceilândia,Rua 2,72215-110,(61) 3372-2619,8h às 18h,https://www.tjdft.jus.br/informacoes/cidadania/nucleo-judiciario-da-mulher/telefones-uteis,2026-11-05\n",
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
