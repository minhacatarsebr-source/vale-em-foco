import unittest
from coletor import regras as r


class Classificar(unittest.TestCase):
    def test_indicacao_e_pedido(self):
        self.assertEqual(r.classificar("IND", "Indica ao Prefeito a troca de lâmpadas"), "pedido")

    def test_requerimento_e_cobranca(self):
        self.assertEqual(r.classificar("REQ", "Requer informações sobre a obra"), "cobranca")

    def test_mocao_e_homenagem(self):
        self.assertEqual(r.classificar("MOC", "Moção de aplauso ao atleta"), "homenagem")

    def test_projeto_de_lei_comum_e_lei(self):
        self.assertEqual(r.classificar("PL", "Altera a Lei Complementar 1.250"), "lei")

    def test_projeto_que_da_nome_a_rua_e_homenagem(self):
        self.assertEqual(r.classificar("PL", "Dispõe sobre denominação de Rua como Izaltino José dos Santos."), "homenagem")

    def test_titulo_de_cidadao_e_homenagem(self):
        self.assertEqual(r.classificar("PDL", "Concede Título de Cidadão Cunhense ao senhor Fulano"), "homenagem")

    def test_titulo_com_espaco_duplo_ou_quebra_de_linha_tambem_e_homenagem(self):
        self.assertEqual(r.classificar("PDL", "CONCESSÃO DE  TÍTULO DE\nCIDADANIA ao senhor Fulano"), "homenagem")

    def test_naming_rights_nao_e_homenagem(self):
        self.assertEqual(r.classificar("PL", "Dispõe sobre direitos de denominação (naming rights) em eventos esportivos"), "lei")

    def test_denominacao_de_programa_nao_e_homenagem(self):
        self.assertEqual(r.classificar("PL", "Dispõe sobre a denominação do Programa Congada Mirim"), "lei")

    def test_recomendacao_e_diploma_escolar_nao_sao_homenagem(self):
        self.assertEqual(r.classificar("PL", "Acolhe recomendação do Tribunal de Contas"), "lei")
        self.assertEqual(r.classificar("PL", "Exige diploma de nível superior para o cargo"), "lei")

    def test_mocao_de_apelo_ou_repudio_e_cobranca(self):
        self.assertEqual(r.classificar("MOC", "Moção de Apelo ao Governador do Estado"), "cobranca")
        self.assertEqual(r.classificar("MOC", "Moção de repúdio à concessionária"), "cobranca")

    def test_requerimento_de_urgencia_e_tramite_interno(self):
        self.assertEqual(r.classificar("REQ", "Requer urgência especial na tramitação do Projeto de Lei 10"), "outro")

    def test_tipo_desconhecido_e_outro(self):
        self.assertEqual(r.classificar("PAR", "Parecer da comissão"), "outro")


class Locais(unittest.TestCase):
    def test_extrai_estrada_e_para_na_palavra_minuscula(self):
        e = "cascalhamento do morro na estrada do Paiolzinho sentido antigo Bar do Jeni."
        self.assertEqual(r.extrair_locais(e), [("via", "Estrada do Paiolzinho")])

    def test_extrai_bairro_com_conectivo(self):
        e = "manutenção do alambrado da quadra no Bairro do Alto do Cruzeiro."
        self.assertEqual(r.extrair_locais(e), [("bairro", "Bairro do Alto do Cruzeiro")])

    def test_extrai_rua_e_bairro_da_mesma_ementa(self):
        e = "tapa-buracos na Rua Major Santana, no bairro Vila Rica"
        self.assertEqual(r.extrair_locais(e), [("via", "Rua Major Santana"), ("bairro", "Bairro Vila Rica")])

    def test_sem_local_devolve_lista_vazia(self):
        self.assertEqual(r.extrair_locais("Indica a contratação de médico pediatra"), [])

    def test_chave_ignora_acento_e_caixa(self):
        self.assertEqual(r.chave("Rua José Arantes"), r.chave("RUA JOSE ARANTES"))

    def test_abreviacao_av_vira_avenida(self):
        self.assertEqual(r.extrair_locais("poda na Av. Padre Rodolfo")[0], ("via", "Avenida Padre Rodolfo"))


class Repetidos(unittest.TestCase):
    def mat(self, i, grupo, locais):
        return {"id": i, "g": grupo, "l": locais}

    def test_via_com_dois_pedidos_aparece(self):
        ms = [self.mat(1, "pedido", [["via", "Rua A"]]), self.mat(2, "pedido", [["via", "RUA A"]]),
              self.mat(3, "pedido", [["via", "Rua B"]])]
        self.assertEqual(r.vias_repetidas(ms), [{"local": "Rua A", "ids": [1, 2]}])

    def test_bairro_nao_conta_como_via_repetida(self):
        ms = [self.mat(1, "pedido", [["bairro", "Bairro X"]]), self.mat(2, "pedido", [["bairro", "Bairro X"]])]
        self.assertEqual(r.vias_repetidas(ms), [])

    def test_homenagem_nao_conta_como_pedido_repetido(self):
        ms = [self.mat(1, "pedido", [["via", "Rua A"]]), self.mat(2, "homenagem", [["via", "Rua A"]])]
        self.assertEqual(r.vias_repetidas(ms), [])

    def test_ordena_pela_quantidade(self):
        ms = [self.mat(i, "pedido", [["via", "Rua B"]]) for i in (1, 2)] + \
             [self.mat(i, "pedido", [["via", "Rua A"]]) for i in (3, 4, 5)]
        self.assertEqual([x["local"] for x in r.vias_repetidas(ms)], ["Rua A", "Rua B"])


class Presenca(unittest.TestCase):
    SESSOES = [{"id": 1, "data": "2025-02-01"}, {"id": 2, "data": "2025-03-01"}, {"id": 3, "data": "2025-10-01"}]

    def test_conta_presentes_sobre_sessoes_com_registro(self):
        pres = {1: {10, 11}, 2: {10}, 3: {10, 11}}
        m = [{"inicio": "2025-01-01", "fim": "2028-12-31", "titular": True, "afastamento": False}]
        self.assertEqual(r.presenca(11, m, self.SESSOES, pres),
                         {"presentes": 2, "sessoes": 3, "comparavel": True})

    def test_sessao_sem_registro_nao_entra_na_conta(self):
        pres = {1: {10}, 3: {10}}  # sessão 2 sem nenhum registro
        m = [{"inicio": "2025-01-01", "fim": "2028-12-31", "titular": True, "afastamento": False}]
        self.assertEqual(r.presenca(10, m, self.SESSOES, pres)["sessoes"], 2)

    def test_suplente_so_conta_sessoes_do_proprio_mandato(self):
        pres = {1: {10}, 2: {10}, 3: {10, 12}}
        m = [{"inicio": "2025-09-01", "fim": "2028-12-31", "titular": False, "afastamento": False}]
        self.assertEqual(r.presenca(12, m, self.SESSOES, pres),
                         {"presentes": 1, "sessoes": 1, "comparavel": False})

    def test_titular_afastado_nao_e_comparavel(self):
        pres = {1: {10}, 2: {10}, 3: {10}}
        m = [{"inicio": "2025-01-01", "fim": "2028-12-31", "titular": True, "afastamento": True}]
        self.assertFalse(r.presenca(11, m, self.SESSOES, pres)["comparavel"])


    def test_longa_sequencia_sem_aparecer_nao_e_comparavel(self):
        sessoes = [{"id": i, "data": f"2025-{1 + i // 28:02d}-{1 + i % 28:02d}"} for i in range(12)]
        pres = {s["id"]: ({10, 11} if s["id"] < 3 else {10}) for s in sessoes}  # 11 some depois da 3ª
        m = [{"inicio": "2025-01-01", "fim": "2028-12-31", "titular": True, "afastamento": False}]
        self.assertFalse(r.presenca(11, m, sessoes, pres)["comparavel"])
        self.assertTrue(r.presenca(10, m, sessoes, pres)["comparavel"])


class Votos(unittest.TestCase):
    def test_soma_por_tipo_de_voto(self):
        vs = ["Sim", "Sim", "Não", "Abstenção", "Não Votou"]
        self.assertEqual(r.resumo_votos(vs), {"sim": 2, "nao": 1, "abstencao": 1, "nao_votou": 1})

    def test_voto_desconhecido_vai_para_outros(self):
        self.assertEqual(r.resumo_votos(["Sim", "???"]), {"sim": 1, "nao": 0, "abstencao": 0, "nao_votou": 0, "outros": 1})


class Trava(unittest.TestCase):
    def dados(self, v=11, m=1000, s=50, presencas=500, votos=2000, com_autor=800):
        return {"vereadores": [{}] * v, "materias": [{}] * m, "sessoes": {"com_registro": s},
                "controle": {"presencas": presencas, "votos": votos, "com_autor": com_autor}}

    def test_presencas_sumirem_barra(self):
        self.assertTrue(r.problemas_da_coleta(self.dados(presencas=300), self.dados()))

    def test_votos_sumirem_barra(self):
        self.assertTrue(r.problemas_da_coleta(self.dados(votos=100), self.dados()))

    def test_nenhuma_proposta_com_autor_barra(self):
        self.assertTrue(r.problemas_da_coleta(self.dados(com_autor=0), None))

    def test_coleta_normal_passa(self):
        self.assertEqual(r.problemas_da_coleta(self.dados(), self.dados(m=990)), [])

    def test_primeira_coleta_sem_anterior_passa(self):
        self.assertEqual(r.problemas_da_coleta(self.dados(), None), [])

    def test_sem_vereadores_barra(self):
        self.assertTrue(r.problemas_da_coleta(self.dados(v=0), None))

    def test_queda_grande_de_propostas_barra(self):
        self.assertTrue(r.problemas_da_coleta(self.dados(m=500), self.dados(m=1000)))

    def test_sessoes_sumirem_barra(self):
        self.assertTrue(r.problemas_da_coleta(self.dados(s=10), self.dados(s=50)))


if __name__ == "__main__":
    unittest.main()
