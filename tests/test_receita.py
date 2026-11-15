import unittest
from coletor import regras as r
from coletor import tce


def linha(alinea, valor):
    return {"orgao": "PREFEITURA", "mes": "Janeiro", "ds_alinea": alinea, "vl_arrecadacao": valor}


MESES = {
    1: [linha("11125000 - Imposto sobre a Propriedade Predial e Territorial Urbana", "21.937,87"),
        linha("11145100 - Impostos sobre Serviços", "231.151,69"),
        linha("17115110 - Cota-Parte do FPM", "1.000.000,00")],
    2: [linha("11125000 - Imposto sobre a Propriedade Predial e Territorial Urbana", "100,13"),
        linha("11220100 - Taxas pela Prestação de Serviços em Geral", "-0,01"),
        linha("11125300 - Impostos sobre Transmissão &quot;Inter Vivos&quot; de Bens Imóveis", "50,00")],
}


class ResumoReceita(unittest.TestCase):
    def setUp(self):
        self.x = r.resumo_receita(2026, MESES)

    def test_total_soma_tudo_inclusive_repasses(self):
        self.assertEqual(self.x["total"], 1253239.68)

    def test_impostos_sao_so_as_alineas_de_impostos_e_taxas(self):
        self.assertEqual(self.x["impostos"], 253239.68)

    def test_guarda_ano_e_ultimo_mes_com_dado(self):
        self.assertEqual((self.x["ano"], self.x["ate_mes"]), (2026, 2))

    def test_itens_juntam_a_mesma_alinea_e_vem_do_maior_para_o_menor(self):
        self.assertEqual(self.x["itens"][0], {"nome": "Impostos sobre Serviços", "valor": 231151.69})
        self.assertEqual(self.x["itens"][1], {"nome": "Imposto sobre a Propriedade Predial e Territorial Urbana", "valor": 22038.0})

    def test_nome_sem_codigo_e_sem_entidade_html(self):
        self.assertIn('Impostos sobre Transmissão "Inter Vivos" de Bens Imóveis', [i["nome"] for i in self.x["itens"]])

    def test_sem_nenhum_mes_nao_ha_receita(self):
        self.assertIsNone(r.resumo_receita(2026, {}))


class ReceitasDoAno(unittest.TestCase):
    def test_para_no_primeiro_mes_vazio_depois_de_ter_dado(self):
        pedidos = []

        def buscar(mes):
            pedidos.append(mes)
            return [linha("11145100 - ISS", "1,00")] if mes <= 3 else []
        self.assertEqual(sorted(tce.receitas_do_ano(buscar)), [1, 2, 3])
        self.assertEqual(pedidos, [1, 2, 3, 4])

    def test_ano_sem_dado_devolve_vazio(self):
        self.assertEqual(tce.receitas_do_ano(lambda mes: []), {})


class TravaReceita(unittest.TestCase):
    def test_receita_do_mesmo_ano_nao_pode_encolher(self):
        antes = {"ano": 2026, "ate_mes": 9, "total": 100.0, "impostos": 10.0}
        self.assertTrue(r.receita_suspeita({"ano": 2026, "ate_mes": 5, "total": 50.0, "impostos": 5.0}, antes))

    def test_ano_novo_recomeca_do_zero_sem_alarme(self):
        antes = {"ano": 2026, "ate_mes": 12, "total": 100.0, "impostos": 10.0}
        self.assertFalse(r.receita_suspeita({"ano": 2027, "ate_mes": 1, "total": 5.0, "impostos": 1.0}, antes))

    def test_primeira_coleta_passa(self):
        self.assertFalse(r.receita_suspeita({"ano": 2026, "ate_mes": 1, "total": 5.0, "impostos": 1.0}, None))
