"""Leitura da API pública do SAPL. Devagar e se identificando."""
import datetime
import json
import time
import urllib.parse
import urllib.request

PAUSA = 1.0  # segundos entre pedidos


class ColetaIncompleta(RuntimeError):
    """A lista lida não fecha com o total que a própria Câmara informa."""


class Sapl:
    def __init__(self, base, contato, pausa=PAUSA):
        self.base = base.rstrip("/") + "/api/"
        self.contato = contato
        self.pausa = pausa
        self.pedidos = 0
        self._guardado = {}  # listas iguais pedidas para duas legislaturas são baixadas uma vez só

    def _get(self, url):
        for tentativa in range(3):
            time.sleep(self.pausa)
            self.pedidos += 1
            try:
                req = urllib.request.Request(url, headers={"User-Agent": self.contato, "Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    return json.load(r)
            except Exception as e:
                if tentativa == 2:
                    raise RuntimeError(f"{e} em {url}") from e
                time.sleep(10 * (tentativa + 1))

    def tudo(self, caminho, **filtros):
        """Todas as páginas de uma lista."""
        marca = (caminho, tuple(sorted(filtros.items())))
        if marca in self._guardado:
            return self._guardado[marca]
        filtros["page_size"] = 100
        filtros["o"] = "id"  # sem ordem fixa a paginação repete e perde linhas
        pagina, itens, total = 1, [], 0
        while pagina:
            filtros["page"] = pagina
            d = self._get(self.base + caminho + "?" + urllib.parse.urlencode(filtros))
            itens.extend(d["results"])
            total = d["pagination"]["total_entries"]
            pagina = d["pagination"]["next_page"]
        unicos = len({x["id"] for x in itens})
        if unicos != len(itens) or unicos != total:
            raise ColetaIncompleta(f"{caminho}: {len(itens)} linhas lidas, {unicos} únicas, {total} informadas")
        self._guardado[marca] = itens
        return itens


def baixar(sapl, numero_legislatura):
    """Baixa o necessário de uma legislatura. Devolve (legislatura, bruto)."""
    legs = {l["numero"]: l for l in sapl.tudo("parlamentares/legislatura/")}
    leg = legs[numero_legislatura]
    ini, fim = leg["data_inicio"], leg["data_fim"]
    materias = []
    ultimo_ano = min(int(fim[:4]), datetime.date.today().year)  # ano futuro devolve erro 500
    for ano in range(int(ini[:4]), ultimo_ano + 1):
        materias += sapl.tudo("materia/materialegislativa/", ano=ano)
    bruto = {
        "parlamentares": sapl.tudo("parlamentares/parlamentar/"),
        "mandatos": sapl.tudo("parlamentares/mandato/", legislatura=leg["id"]),
        "filiacoes": sapl.tudo("parlamentares/filiacao/"),
        "partidos": sapl.tudo("parlamentares/partido/"),
        "autores": sapl.tudo("base/autor/"),
        "tipos_autor": sapl.tudo("base/tipoautor/"),
        "tipos": sapl.tudo("materia/tipomaterialegislativa/"),
        "materias": materias,
        "status": sapl.tudo("materia/statustramitacao/"),
        # sem limite final: proposta de dezembro pode ser respondida na legislatura seguinte
        "tramitacoes": sapl.tudo("materia/tramitacao/", data_tramitacao__gte=ini),
        "sessoes": sapl.tudo("sessao/sessaoplenaria/", legislatura=leg["id"]),
        "presencas": sapl.tudo("sessao/sessaoplenariapresenca/"),
        "justificativas": sapl.tudo("sessao/justificativaausencia/"),
        # votos sem filtro de data: a data gravada é a da digitação, não a da sessão
        "votos": sapl.tudo("sessao/votoparlamentar/"),
        "votacoes": sapl.tudo("sessao/registrovotacao/"),
        "ordens": sapl.tudo("sessao/ordemdia/"),
        "expedientes": sapl.tudo("sessao/expedientemateria/"),
        "sessoes_legislativas": sapl.tudo("parlamentares/sessaolegislativa/", legislatura=leg["id"]),
        "mesas": sapl.tudo("parlamentares/mesadiretora/"),
        "cargos_mesa": sapl.tudo("parlamentares/cargomesa/"),
        "composicoes": sapl.tudo("parlamentares/composicaomesa/"),
    }
    return leg, bruto
