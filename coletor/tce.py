"""Receita da Prefeitura no Portal da Transparência Municipal do TCE-SP. Devagar e se identificando."""
import json
import time
import urllib.request

BASE = "https://transparencia.tce.sp.gov.br/api/json/receitas"
PAUSA = 1.0


def buscador(municipio, ano, contato, pausa=PAUSA):
    """Devolve a função que lê um mês da receita do município."""
    def buscar(mes):
        url = f"{BASE}/{municipio}/{ano}/{mes}"
        for tentativa in range(3):
            time.sleep(pausa)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": contato, "Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    return json.load(r)
            except Exception as e:
                if tentativa == 2:
                    raise RuntimeError(f"{e} em {url}") from e
                time.sleep(10 * (tentativa + 1))
    return buscar


def receitas_do_ano(buscar):
    """Meses com dado, de janeiro em diante. O TCE publica com atraso: para no primeiro mês vazio."""
    meses = {}
    for mes in range(1, 13):
        linhas = buscar(mes)
        if not linhas:
            break
        meses[mes] = linhas
    return meses
