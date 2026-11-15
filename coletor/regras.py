"""Regras do Vale em Foco: as mesmas para todas as cidades e todos os vereadores.

Tudo aqui é função pura (sem internet), para poder ser testado.
"""
import html
import re
import unicodedata

GRUPO_POR_SIGLA = {
    "IND": "pedido",
    "REQ": "cobranca",
    "MOC": "homenagem",
    "PL": "lei", "PDL": "lei", "PR": "lei", "PELOM": "lei", "EMD": "lei", "SUBEM": "lei",
}

# Projetos que, pelo texto, são homenagem e não mudança de regra.
_BEM_PUBLICO = (r"(?:rua|avenida|pra[cç]a|travessa|estrada|rodovia|viela|ponte|logradouro|via|escola|creche|"
                r"pr[eé]dio|pr[oó]prio|gin[aá]sio|quadra|unidade|centro|sala|pra[cç]a|campo|est[aá]dio|posto)")
_HOMENAGEM = re.compile(
    r"(?<!direitos de )denomina\w*(?: como| de| d[aeo]s?| a| o| à)* " + _BEM_PUBLICO + r"\b|"
    r"d[aá] nome|t[ií]tulo de cidad|honra ao m[eé]rito|\bmedalha\b|\bcomenda\b|"
    r"diploma de (?:honra|m[eé]rito|gratid)|institui (?:o )?dia (?:municipal )?d",
    re.IGNORECASE,
)
_POSICAO = re.compile(r"\b(apelo|rep[uú]dio|protesto)\b", re.IGNORECASE)
_URGENCIA = re.compile(r"\burg[eê]ncia\b.*\btramita|\bregime de urg[eê]ncia\b", re.IGNORECASE)


def classificar(sigla, ementa):
    texto = re.sub(r"\s+", " ", ementa or "")  # espaço duplo ou quebra de linha não pode mudar o resultado
    grupo = GRUPO_POR_SIGLA.get(sigla, "outro")
    if grupo == "lei" and _HOMENAGEM.search(texto):
        return "homenagem"
    if sigla == "MOC" and _POSICAO.search(texto):
        return "cobranca"   # moção de apelo ou repúdio cobra alguém; não homenageia
    if sigla == "REQ" and _URGENCIA.search(texto):
        return "outro"      # pedido de urgência é trâmite interno
    return grupo


def chave(texto):
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


_TIPOS = {
    "rua": ("via", "Rua"), "avenida": ("via", "Avenida"), "av": ("via", "Avenida"),
    "estrada": ("via", "Estrada"), "travessa": ("via", "Travessa"), "rodovia": ("via", "Rodovia"),
    "praca": ("via", "Praça"), "ponte": ("via", "Ponte"), "bairro": ("bairro", "Bairro"),
}
_NOME = r"[A-ZÀ-Ý][\wÀ-ÿ'’-]*"
_LOCAL = re.compile(
    r"\b(rua|avenida|av\.?|estrada|travessa|rodovia|pra[cç]a|ponte|bairro)\s+"
    r"((?:(?i:d[aeo]s?)\s+)?" + _NOME + r"(?:\s+(?:(?:d[aeo]s?|e)\s+)?" + _NOME + r"){0,5})",
    re.IGNORECASE,
)


def extrair_locais(ementa):
    """Acha ruas, estradas e bairros citados no texto. É uma busca por padrão, não um cadastro."""
    achados = []
    vistos = set()
    for m in _LOCAL.finditer(ementa or ""):
        nome = m.group(2)
        # o IGNORECASE vale para a palavra-tipo; o nome precisa começar com maiúscula de verdade
        primeira = re.sub(r"^(?i:d[aeo]s?)\s+", "", nome)
        if not primeira[:1].isupper():
            continue
        nome = _corta_minusculas(nome)
        categoria, rotulo = _TIPOS[chave(m.group(1)).rstrip(".")]
        local = f"{rotulo} {nome}"
        if chave(local) not in vistos:
            vistos.add(chave(local))
            achados.append((categoria, local))
    return achados


_CONECTIVO = re.compile(r"^(d[aeo]s?|e)$", re.IGNORECASE)


def _corta_minusculas(nome):
    """Mantém só a sequência de palavras com maiúscula (e conectivos entre elas)."""
    palavras = nome.split()
    fim = 0
    for i, p in enumerate(palavras):
        if p[:1].isupper():
            fim = i + 1
        elif not _CONECTIVO.match(p):
            break
    return " ".join(palavras[:fim])


def vias_repetidas(materias):
    """Vias citadas em mais de um pedido. Não afirma que o problema é o mesmo: só que a via se repete."""
    grupos = {}
    for m in materias:
        if m["g"] != "pedido":
            continue
        for categoria, local in m["l"]:
            if categoria != "via":
                continue
            g = grupos.setdefault(chave(local), {"local": local, "ids": []})
            if m["id"] not in g["ids"]:
                g["ids"].append(m["id"])
    repetidas = [g for g in grupos.values() if len(g["ids"]) >= 2]
    return sorted(repetidas, key=lambda g: (-len(g["ids"]), chave(g["local"])))


SEQUENCIA_LONGA = 8  # sessões seguidas sem aparecer: sinal de que saiu do cargo sem registro no sistema


def presenca(parlamentar_id, mandatos, sessoes, presentes_por_sessao):
    """Presença só sobre sessões que têm registro. Sessão sem registro não vira falta.

    `comparavel` é falso para suplente, para titular com afastamento e para quem some
    por muitas sessões seguidas: nesses casos o SAPL não diz em quais datas a pessoa
    estava de fato no exercício, e mostrar "faltas" seria injusto.
    """
    total = presentes = sequencia = maior = 0
    for s in sorted(sessoes, key=lambda s: s["data"]):
        registro = presentes_por_sessao.get(s["id"])
        if not registro:
            continue
        if not any(m["inicio"] <= s["data"] <= m["fim"] for m in mandatos):
            continue
        total += 1
        if parlamentar_id in registro:
            presentes += 1
            sequencia = 0
        else:
            sequencia += 1
            maior = max(maior, sequencia)
    comparavel = (bool(mandatos) and maior < SEQUENCIA_LONGA
                  and all(m["titular"] and not m["afastamento"] for m in mandatos))
    return {"presentes": presentes, "sessoes": total, "comparavel": comparavel}


_VOTO = {"sim": "sim", "nao": "nao", "abstencao": "abstencao", "nao votou": "nao_votou"}


_LETRA = {"sim": "s", "nao": "n", "abstencao": "a", "nao_votou": "x"}


def letra_do_voto(voto):
    return _LETRA.get(_VOTO.get(chave(voto)), "o")


def resumo_votos(votos):
    r = {"sim": 0, "nao": 0, "abstencao": 0, "nao_votou": 0}
    for v in votos:
        campo = _VOTO.get(chave(v))
        if campo:
            r[campo] += 1
        else:
            r["outros"] = r.get("outros", 0) + 1
    return r


def problemas_da_coleta(novo, anterior):
    """Lista de motivos para NÃO publicar. Lista vazia = pode publicar."""
    motivos = []
    if len(novo["vereadores"]) < 5:
        motivos.append(f"só {len(novo['vereadores'])} vereadores vieram na coleta")
    if not novo["materias"]:
        motivos.append("nenhuma proposta veio na coleta")
    controle = novo.get("controle") or {}
    if controle and not controle["com_autor"]:
        motivos.append("nenhuma proposta ficou ligada a um vereador")
    if anterior:
        pares = [("propostas", len(anterior["materias"]), len(novo["materias"])),
                 ("sessões com registro", anterior["sessoes"]["com_registro"], novo["sessoes"]["com_registro"])]
        antigo = anterior.get("controle") or {}
        nomes = {"presencas": "presenças", "votos": "votos", "com_autor": "propostas com autor vereador"}
        pares += [(nomes[k], antigo[k], controle[k]) for k in nomes if k in antigo and k in controle]
        for nome, antes, agora in pares:
            if agora < antes * 0.9:
                motivos.append(f"{nome} caíram de {antes} para {agora}")
    return motivos


def _centavos(texto):
    """'1.234,56' -> 123456 (em centavos, para a soma não acumular erro de arredondamento)."""
    return round(float(texto.replace(".", "").replace(",", ".")) * 100)


def resumo_receita(ano, meses):
    """Receita arrecadada no ano, pelo que o TCE-SP publica. `meses` é {mês: linhas}.

    Impostos e taxas municipais são as alíneas de código 11 (IPTU, ISS, ITBI, IR retido na fonte, taxas).
    O total inclui também os repasses do Estado e da União.
    """
    if not meses:
        return None
    total = impostos = 0
    itens = {}
    for linhas in meses.values():
        for l in linhas:
            codigo, _, nome = l["ds_alinea"].partition(" - ")
            valor = _centavos(l["vl_arrecadacao"])
            total += valor
            if codigo.startswith("11"):
                impostos += valor
                nome = html.unescape(nome).strip()
                itens[nome] = itens.get(nome, 0) + valor
    return {
        "ano": ano, "ate_mes": max(meses), "total": total / 100, "impostos": impostos / 100,
        "itens": [{"nome": n, "valor": v / 100} for n, v in sorted(itens.items(), key=lambda i: -i[1])],
    }


def receita_suspeita(nova, anterior):
    """No mesmo ano a arrecadação acumulada só cresce; se encolheu bastante, a leitura veio pela metade."""
    if not anterior or not nova or nova["ano"] != anterior["ano"]:
        return False
    return nova["ate_mes"] < anterior["ate_mes"] or nova["total"] < anterior["total"] * 0.9
