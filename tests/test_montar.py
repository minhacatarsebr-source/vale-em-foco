import unittest
from coletor.montar import montar

CIDADE = {"slug": "cunha", "nome": "Cunha", "uf": "SP", "sapl": "https://sapl.exemplo.leg.br"}
LEG = {"numero": 19, "data_inicio": "2025-01-01", "data_fim": "2028-12-31"}


def bruto():
    return {
        "parlamentares": [
            {"id": 11, "nome_parlamentar": "Ana", "nome_completo": "Ana Silva", "fotografia": "http://sapl.exemplo.leg.br/media/a.jpg"},
            {"id": 12, "nome_parlamentar": "Beto", "nome_completo": "Beto Souza", "fotografia": None},
            {"id": 99, "nome_parlamentar": "Antigo", "nome_completo": "De Outra Legislatura", "fotografia": None},
        ],
        "mandatos": [
            {"parlamentar": 11, "data_inicio_mandato": "2025-01-01", "data_fim_mandato": "2028-12-31", "titular": True, "tipo_afastamento": None, "observacao": ""},
            {"parlamentar": 12, "data_inicio_mandato": "2025-09-01", "data_fim_mandato": "2028-12-31", "titular": False, "tipo_afastamento": None, "observacao": "Assumiu em 01/09/2025."},
        ],
        "filiacoes": [
            {"parlamentar": 11, "partido": 1, "data": "2015-01-01", "data_desfiliacao": "2020-01-01"},
            {"parlamentar": 11, "partido": 2, "data": "2020-02-01", "data_desfiliacao": None},
        ],
        "partidos": [{"id": 1, "sigla": "AAA"}, {"id": 2, "sigla": "BBB"}],
        "autores": [
            {"id": 20, "nome": "Ana", "tipo": 2, "object_id": 11},
            {"id": 21, "nome": "Beto", "tipo": 2, "object_id": 12},
            {"id": 33, "nome": "Fulano Prefeito", "tipo": 7, "object_id": None},
            {"id": 40, "nome": "Comissão de Justiça", "tipo": 4, "object_id": 11},  # mesmo número da Ana
        ],
        "tipos_autor": [{"id": 4, "descricao": "Comissão"}, {"id": 2, "descricao": "Parlamentar"}, {"id": 7, "descricao": "Chefe do Poder Executivo"}],
        "tipos": [{"id": 9, "sigla": "IND", "descricao": "Indicação"}, {"id": 5, "sigla": "PL", "descricao": "Projeto de Lei"},
                  {"id": 10, "sigla": "MOC", "descricao": "Moção"}],
        "materias": [
            {"id": 1, "tipo": 9, "numero": 1, "ano": 2025, "data_apresentacao": "2025-02-01", "ementa": "Tapa-buraco na Rua Um", "autores": [20]},
            {"id": 2, "tipo": 9, "numero": 2, "ano": 2025, "data_apresentacao": "2025-03-01", "ementa": "Iluminação na Rua Um", "autores": [20, 21]},
            {"id": 3, "tipo": 10, "numero": 1, "ano": 2025, "data_apresentacao": "2025-03-02", "ementa": "Moção de aplauso", "autores": [21]},
            {"id": 5, "tipo": 5, "numero": 8, "ano": 2025, "data_apresentacao": "2025-04-02", "ementa": "Altera o regimento", "autores": [40]},
            {"id": 4, "tipo": 5, "numero": 7, "ano": 2025, "data_apresentacao": "2025-04-01", "ementa": "Abre crédito adicional", "autores": [33]},
        ],
        "status": [{"id": 43, "descricao": "Aguardando resposta do Executivo"}, {"id": 44, "descricao": "Respondida pelo Executivo"}],
        "tramitacoes": [
            {"id": 100, "materia": 1, "status": 43, "data_tramitacao": "2025-02-05"},
            {"id": 101, "materia": 1, "status": 44, "data_tramitacao": "2025-03-05"},
            {"id": 102, "materia": 2, "status": 43, "data_tramitacao": "2025-03-06"},
        ],
        "sessoes": [
            {"id": 1, "data_inicio": "2025-02-03", "__str__": "1ª Ordinária"},
            {"id": 2, "data_inicio": "2025-10-06", "__str__": "20ª Ordinária"},
            {"id": 3, "data_inicio": "2025-10-20", "__str__": "21ª Ordinária"},
        ],
        "presencas": [
            {"sessao_plenaria": 1, "parlamentar": 11},
            {"sessao_plenaria": 2, "parlamentar": 11}, {"sessao_plenaria": 2, "parlamentar": 12},
            {"sessao_plenaria": 777, "parlamentar": 11},  # sessão de outra legislatura
        ],
        "votos": [
            {"parlamentar": 11, "voto": "Sim", "votacao": 1}, {"parlamentar": 11, "voto": "Não", "votacao": 2},
            {"parlamentar": 12, "voto": "Sim", "votacao": 2},
            {"parlamentar": 11, "voto": "Não", "votacao": 3},
        ],
        "votacoes": [{"id": 1, "materia": 4, "ordem": 50, "expediente": None},
                     {"id": 2, "materia": 3, "ordem": None, "expediente": 60},
                     {"id": 3, "materia": 3, "ordem": 51, "expediente": None}],  # lançada depois, mas de sessão antiga
        "ordens": [{"id": 50, "sessao_plenaria": 1}, {"id": 51, "sessao_plenaria": 777}],
        "expedientes": [{"id": 60, "sessao_plenaria": 2}],
        "justificativas": [{"parlamentar": 11, "sessao_plenaria": 3}, {"parlamentar": 11, "sessao_plenaria": 777}],
        "sessoes_legislativas": [{"id": 9}],
        "mesas": [{"id": 90, "sessao_legislativa": 9}, {"id": 80, "sessao_legislativa": 5}],
        "cargos_mesa": [{"id": 1, "descricao": "Presidente"}, {"id": 2, "descricao": "Vice-Presidente"}],
        "composicoes": [{"parlamentar": 11, "cargo": 1, "mesa_diretora": 90}, {"parlamentar": 12, "cargo": 2, "mesa_diretora": 90},
                        {"parlamentar": 12, "cargo": 1, "mesa_diretora": 80}],
    }


class Montar(unittest.TestCase):
    def setUp(self):
        self.d = montar(CIDADE, LEG, bruto(), gerado_em="2026-11-14T12:00:00")
        self.v = {v["nome"]: v for v in self.d["vereadores"]}

    def test_so_entram_vereadores_com_mandato_na_legislatura(self):
        self.assertEqual(sorted(self.v), ["Ana", "Beto"])

    def test_partido_e_a_filiacao_em_aberto(self):
        self.assertEqual(self.v["Ana"]["partido"], "BBB")

    def test_sem_filiacao_cadastrada_fica_vazio(self):
        self.assertEqual(self.v["Beto"]["partido"], "")

    def test_coautoria_conta_para_cada_autor(self):
        self.assertEqual(self.v["Ana"]["propostas"], {"pedido": 2, "cobranca": 0, "homenagem": 0, "lei": 0, "outro": 0, "total": 2})
        self.assertEqual(self.v["Beto"]["propostas"]["pedido"], 1)
        self.assertEqual(self.v["Beto"]["propostas"]["homenagem"], 1)

    def test_presenca_ignora_sessao_sem_registro(self):
        self.assertEqual(self.v["Ana"]["presenca"], {"presentes": 2, "sessoes": 2, "comparavel": True})

    def test_suplente_conta_so_o_proprio_periodo(self):
        self.assertEqual(self.v["Beto"]["presenca"], {"presentes": 1, "sessoes": 1, "comparavel": False})
        self.assertEqual(self.v["Beto"]["observacao"], "Assumiu em 01/09/2025.")

    def test_proposta_de_comissao_nao_vai_para_vereador_de_mesmo_numero(self):
        self.assertEqual(self.v["Ana"]["propostas"]["lei"], 0)

    def test_votos_por_vereador(self):
        self.assertEqual(self.v["Ana"]["votos"], {"sim": 1, "nao": 1, "abstencao": 0, "nao_votou": 0})

    def test_voto_de_sessao_de_outra_legislatura_fica_de_fora(self):
        self.assertEqual(self.v["Ana"]["votos"]["nao"], 1)

    def test_so_quem_presidiu_nesta_legislatura_e_marcado(self):
        self.assertTrue(self.v["Ana"]["presidiu"])
        self.assertFalse(self.v["Beto"]["presidiu"])

    def test_falta_justificada_e_contada_so_nas_sessoes_da_legislatura(self):
        self.assertEqual(self.v["Ana"]["justificadas"], 1)

    def test_partido_e_o_do_periodo_e_nao_o_de_hoje(self):
        b = bruto()
        b["filiacoes"] = [{"parlamentar": 11, "partido": 1, "data": "2020-01-01", "data_desfiliacao": "2029-06-01"},
                          {"parlamentar": 11, "partido": 2, "data": "2029-06-02", "data_desfiliacao": None}]
        d = montar(CIDADE, LEG, b, gerado_em="2030-01-01T00:00:00")
        self.assertEqual(d["vereadores"][0]["partido"], "AAA")

    def test_sessao_futura_nao_entra_nem_como_sem_registro(self):
        b = bruto()
        b["sessoes"].append({"id": 4, "data_inicio": "2026-11-16", "__str__": "Futura"})
        d = montar(CIDADE, LEG, b, gerado_em="2026-11-14T12:00:00")
        self.assertEqual(d["sessoes"]["total"], 3)

    def test_lista_de_presenca_pela_metade_conta_como_sem_registro(self):
        b = bruto()
        for pid in (13, 14, 15):
            b["mandatos"].append({"parlamentar": pid, "data_inicio_mandato": "2025-01-01", "data_fim_mandato": "2028-12-31",
                                  "titular": True, "tipo_afastamento": None, "observacao": ""})
        d = montar(CIDADE, LEG, b, gerado_em="2026-11-14T12:00:00")  # 4 titulares: sessão 1 só tem 1 nome
        self.assertEqual(d["sessoes"]["com_registro"], 1)
        self.assertIn("1ª Ordinária (03/02/2025)", d["sessoes"]["sem_registro"])

    def test_controle_guarda_as_somas_para_a_trava(self):
        self.assertEqual(self.d["controle"], {"presencas": 3, "votos": 3, "com_autor": 3})

    def test_situacao_e_a_tramitacao_mais_recente(self):
        m = {m["id"]: m for m in self.d["materias"]}
        self.assertEqual(m[1]["st"], "Respondida pelo Executivo")
        self.assertEqual(m[2]["st"], "Aguardando resposta do Executivo")
        self.assertEqual(m[3]["st"], "")

    def test_materia_do_prefeito_e_marcada(self):
        m = {m["id"]: m for m in self.d["materias"]}
        self.assertTrue(m[4]["pref"])
        self.assertFalse(m[1]["pref"])
        self.assertEqual(self.d["prefeito"]["nome"], "Fulano Prefeito")

    def test_materia_traz_link_da_fonte_oficial(self):
        self.assertEqual(self.d["cidade"]["sapl"] + "/materia/1", "https://sapl.exemplo.leg.br/materia/1")
        self.assertEqual(self.d["materias"][0]["rot"][:8], "Indicaçã")

    def test_foto_vira_https(self):
        self.assertEqual(self.v["Ana"]["foto"], "https://sapl.exemplo.leg.br/media/a.jpg")

    def test_via_repetida_e_sessoes_sem_registro(self):
        self.assertEqual(self.d["repetidos"], [{"local": "Rua Um", "ids": [1, 2]}])
        self.assertEqual(self.d["sessoes"], {"total": 3, "com_registro": 2, "sem_registro": ["21ª Ordinária (20/10/2025)"]})


if __name__ == "__main__":
    unittest.main()
