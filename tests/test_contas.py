import unittest
from coletor import contas


def pg(orgao, evento, fornecedor, ident, valor):
    return {"orgao": orgao, "evento": evento, "nm_fornecedor": fornecedor, "id_fornecedor": ident, "vl_despesa": valor}


PJ = "CNPJ - PESSOA JURÍDICA - 00000000000100"
PF = "PESSOA FÍSICA - ***"
MESES = {
    1: [pg("PREFEITURA MUNICIPAL DE X", "Valor Pago", "POSTO A LTDA", PJ, "1.000,50"),
        pg("PREFEITURA MUNICIPAL DE X", "Empenhado", "POSTO A LTDA", PJ, "9.999,00"),
        pg("PREFEITURA MUNICIPAL DE X", "Valor Pago", "FULANO DE TAL", PF, "200,00"),
        pg("CÂMARA MUNICIPAL DE X", "Valor Pago", "PAPELARIA B", PJ, "50,00")],
    2: [pg("PREFEITURA MUNICIPAL DE X", "Valor Pago", "POSTO A LTDA", PJ, "499,50"),
        pg("PREFEITURA MUNICIPAL DE X", "Valor Pago", "ONIBUS C SA", PJ, "3.000,00"),
        pg("PREFEITURA MUNICIPAL DE X", "Valor Pago", "BELTRANA", PF, "100,00")],
}


class ResumoDespesa(unittest.TestCase):
    def setUp(self):
        self.x = contas.resumo_despesa(2026, MESES)

    def test_pago_da_prefeitura_soma_so_pagamentos_da_prefeitura(self):
        self.assertEqual(self.x["pago"], 4800.0)

    def test_pago_da_camara_fica_separado(self):
        self.assertEqual(self.x["camara_pago"], 50.0)

    def test_fornecedores_sao_so_empresas_do_maior_para_o_menor(self):
        self.assertEqual(self.x["fornecedores"], [{"nome": "ONIBUS C SA", "valor": 3000.0}, {"nome": "POSTO A LTDA", "valor": 1500.0}])

    def test_pessoa_fisica_entra_so_como_soma_sem_nome(self):
        self.assertEqual(self.x["pessoas_fisicas"], {"pagamentos": 2, "valor": 300.0})
        self.assertNotIn("FULANO", str(self.x))

    def test_guarda_ano_e_ultimo_mes(self):
        self.assertEqual((self.x["ano"], self.x["ate_mes"]), (2026, 2))

    def test_lista_de_fornecedores_tem_limite(self):
        muitos = {1: [pg("PREFEITURA MUNICIPAL DE X", "Valor Pago", f"EMPRESA {i}", PJ, "1,00") for i in range(40)]}
        self.assertEqual(len(contas.resumo_despesa(2026, muitos)["fornecedores"]), contas.MAX_FORNECEDORES)

    def test_sem_mes_nao_ha_despesa(self):
        self.assertIsNone(contas.resumo_despesa(2026, {}))


def item(conta, valor, coluna="DESPESAS LIQUIDADAS ATÉ O BIMESTRE (d)"):
    return {"conta": conta, "coluna": coluna, "valor": valor}


ITENS = [item("DESPESAS (EXCETO INTRA-ORÇAMENTÁRIAS) (I)", 300.0), item("Saúde", 200.0), item("Atenção Básica", 200.0),
         item("Educação", 100.0), item("Ensino Fundamental", 100.0), item("Saúde", 999.0, "DOTAÇÃO INICIAL"),
         item("TOTAL (III) = (I + II)", 300.0)]


class ResumoAreas(unittest.TestCase):
    def test_areas_sao_as_funcoes_e_nao_as_subfuncoes(self):
        x = contas.resumo_areas(2026, 4, ITENS)
        self.assertEqual(x["itens"], [{"nome": "Saúde", "valor": 200.0}, {"nome": "Educação", "valor": 100.0}])
        self.assertEqual((x["ano"], x["bimestre"], x["total"]), (2026, 4, 300.0))

    def test_se_a_soma_das_areas_nao_fecha_com_o_total_nao_publica(self):
        self.assertIsNone(contas.resumo_areas(2026, 4, ITENS[:3] + ITENS[5:]))

    def test_sem_itens_nao_ha_areas(self):
        self.assertIsNone(contas.resumo_areas(2026, 4, []))


class UltimoBimestre(unittest.TestCase):
    def test_procura_do_mais_recente_para_tras(self):
        pedidos = []

        def buscar(b):
            pedidos.append(b)
            return ITENS if b <= 4 else []
        self.assertEqual(contas.ultimo_bimestre(buscar), (4, ITENS))
        self.assertEqual(pedidos, [6, 5, 4])

    def test_ano_sem_relatorio(self):
        self.assertEqual(contas.ultimo_bimestre(lambda b: []), (None, []))
