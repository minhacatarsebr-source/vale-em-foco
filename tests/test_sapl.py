import unittest
import urllib.parse
from coletor.sapl import Sapl, ColetaIncompleta


class Falso(Sapl):
    """Sapl sem internet: devolve páginas prontas e guarda os endereços pedidos."""
    def __init__(self, paginas):
        super().__init__("https://x.leg.br", "teste", pausa=0)
        self.paginas, self.urls = paginas, []

    def _get(self, url):
        self.urls.append(url)
        return self.paginas[len(self.urls) - 1]


def pagina(ids, total, proxima):
    return {"results": [{"id": i} for i in ids], "pagination": {"next_page": proxima, "total_entries": total}}


class Tudo(unittest.TestCase):
    def test_junta_todas_as_paginas(self):
        s = Falso([pagina([1, 2], 3, 2), pagina([3], 3, None)])
        self.assertEqual([x["id"] for x in s.tudo("a/")], [1, 2, 3])

    def test_pede_ordem_fixa_por_id(self):
        s = Falso([pagina([1], 1, None)])
        s.tudo("a/", ano=2025)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(s.urls[0]).query)
        self.assertEqual(q["o"], ["id"])
        self.assertEqual(q["ano"], ["2025"])

    def test_linha_repetida_entre_paginas_barra_a_coleta(self):
        s = Falso([pagina([1, 2], 3, 2), pagina([2], 3, None)])
        with self.assertRaises(ColetaIncompleta):
            s.tudo("a/")

    def test_total_diferente_do_informado_barra_a_coleta(self):
        s = Falso([pagina([1, 2], 5, None)])
        with self.assertRaises(ColetaIncompleta):
            s.tudo("a/")


if __name__ == "__main__":
    unittest.main()
