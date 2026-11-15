import pathlib
import tempfile
import unittest
from coletor import paginas

HTML = '<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n<link rel="stylesheet" href="estilo.css">\n</head><body></body></html>'


class PaginaDaCidade(unittest.TestCase):
    def test_pagina_da_cidade_busca_os_arquivos_na_pasta_de_cima(self):
        self.assertIn('<head>\n<base href="../">', paginas.pagina_da_cidade(HTML))

    def test_pagina_sem_head_e_erro_e_nao_arquivo_quebrado(self):
        with self.assertRaises(ValueError):
            paginas.pagina_da_cidade("<p>sem cabeça</p>")


class Gerar(unittest.TestCase):
    def test_so_cidade_ativa_ganha_pasta(self):
        with tempfile.TemporaryDirectory() as t:
            site = pathlib.Path(t)
            (site / "index.html").write_text(HTML)
            feitas = paginas.gerar(site, [{"slug": "cunha", "ativa": True}, {"slug": "taubate", "ativa": False}])
            self.assertEqual(feitas, ["cunha"])
            self.assertIn('<base href="../">', (site / "cunha" / "index.html").read_text())
            self.assertFalse((site / "taubate").exists())
