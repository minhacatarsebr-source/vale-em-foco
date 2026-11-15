"""Cria a página de cada cidade (site/<cidade>/index.html) a partir da página principal.

Uso: python3 -m coletor.paginas   -> o endereço fica valeemfoco.org/cunha
"""
import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def pagina_da_cidade(html):
    """A mesma página, avisando o navegador que estilo, scripts e dados ficam na pasta de cima."""
    if "<head>" not in html:
        raise ValueError("página principal sem <head>")
    return html.replace("<head>", '<head>\n<base href="../">', 1)


def gerar(site, cidades):
    html = pagina_da_cidade((site / "index.html").read_text())
    feitas = []
    for c in cidades:
        if c.get("ativa"):
            (site / c["slug"]).mkdir(exist_ok=True)
            (site / c["slug"] / "index.html").write_text(html)
            feitas.append(c["slug"])
    return feitas


if __name__ == "__main__":
    cfg = json.loads((RAIZ / "config" / "cidades.json").read_text())
    print("páginas de cidade:", ", ".join(gerar(RAIZ / "site", cfg["cidades"])))
    sys.exit(0)
