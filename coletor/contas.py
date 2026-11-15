"""Para onde vai o dinheiro: pagamentos (TCE-SP) e gasto por área (Tesouro Nacional). Regras puras e leitura."""
import json
import time
import urllib.parse
import urllib.request

from .regras import _centavos

MAX_FORNECEDORES = 15
SICONFI = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rreo"
COLUNA = "DESPESAS LIQUIDADAS ATÉ O BIMESTRE (d)"
# as 28 funções de governo da classificação oficial (Portaria MOG 42/1999); o resto do anexo são subfunções
FUNCOES = {
    "Legislativa", "Judiciária", "Essencial à Justiça", "Administração", "Defesa Nacional", "Segurança Pública",
    "Relações Exteriores", "Assistência Social", "Previdência Social", "Saúde", "Trabalho", "Educação", "Cultura",
    "Direitos da Cidadania", "Urbanismo", "Habitação", "Saneamento", "Gestão Ambiental", "Ciência e Tecnologia",
    "Agricultura", "Organização Agrária", "Indústria", "Comércio e Serviços", "Comunicações", "Energia",
    "Transporte", "Desporto e Lazer", "Encargos Especiais",
}


def resumo_despesa(ano, meses):
    """Pagamentos do ano. Empresa aparece pelo nome; pessoa física entra só na soma, sem nome."""
    if not meses:
        return None
    pago = camara = pf_valor = pf_n = 0
    empresas = {}
    for linhas in meses.values():
        for l in linhas:
            if l["evento"] != "Valor Pago":
                continue
            valor = _centavos(l["vl_despesa"])
            if l["orgao"].upper().startswith("CÂMARA"):
                camara += valor
                continue
            pago += valor
            if l["id_fornecedor"].upper().startswith("CNPJ"):
                empresas[l["nm_fornecedor"].strip()] = empresas.get(l["nm_fornecedor"].strip(), 0) + valor
            else:
                pf_valor += valor
                pf_n += 1
    maiores = sorted(empresas.items(), key=lambda i: (-i[1], i[0]))[:MAX_FORNECEDORES]
    return {
        "ano": ano, "ate_mes": max(meses), "pago": pago / 100, "camara_pago": camara / 100,
        "fornecedores": [{"nome": n, "valor": v / 100} for n, v in maiores],
        "pessoas_fisicas": {"pagamentos": pf_n, "valor": pf_valor / 100},
    }


def resumo_areas(ano, bimestre, itens):
    """Despesa liquidada por função de governo. Só publica se a soma das áreas fechar com o total oficial."""
    total, areas = None, {}
    for i in itens:
        if i["coluna"] != COLUNA or i["valor"] is None:
            continue
        if i["conta"].startswith("DESPESAS (EXCETO INTRA") and total is None:
            total = i["valor"]
        elif i["conta"] in FUNCOES and i["conta"] not in areas:
            areas[i["conta"]] = i["valor"]
    if total is None or abs(sum(areas.values()) - total) > 0.01:
        return None
    ordem = sorted(areas.items(), key=lambda a: -a[1])
    return {"ano": ano, "bimestre": bimestre, "total": total, "itens": [{"nome": n, "valor": v} for n, v in ordem]}


def ultimo_bimestre(buscar):
    """O relatório mais recente já entregue no ano: tenta do 6º bimestre para trás."""
    for b in range(6, 0, -1):
        itens = buscar(b)
        if itens:
            return b, itens
    return None, []


def buscador_tesouro(ibge, ano, contato, pausa=1.0):
    """Função que lê o Anexo 02 do RREO (despesa por função) de um bimestre."""
    def buscar(bimestre):
        q = urllib.parse.urlencode({"an_exercicio": ano, "nr_periodo": bimestre, "co_tipo_demonstrativo": "RREO",
                                    "no_anexo": "RREO-Anexo 02", "id_ente": ibge})
        time.sleep(pausa)
        req = urllib.request.Request(f"{SICONFI}?{q}", headers={"User-Agent": contato, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r).get("items", [])
    return buscar
