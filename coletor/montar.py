"""Transforma os dados brutos do SAPL no arquivo que o site lê. Sem internet aqui."""
import math
import re
from collections import Counter

from . import regras

GRUPOS = ("pedido", "cobranca", "homenagem", "lei", "outro")
EMENTA_MAX = 600


def _https(url):
    return re.sub(r"^http://", "https://", url) if url else ""


def _data_br(iso):
    a, m, d = iso.split("-")
    return f"{d}/{m}/{a}"


def montar(cidade, legislatura, bruto, gerado_em):
    ini, fim = legislatura["data_inicio"], legislatura["data_fim"]

    # --- quem é quem
    mandatos = {}
    for m in bruto["mandatos"]:
        mandatos.setdefault(m["parlamentar"], []).append({
            "inicio": m["data_inicio_mandato"] or ini,
            "fim": m["data_fim_mandato"] or fim,
            "titular": bool(m["titular"]),
            "afastamento": m["tipo_afastamento"] is not None,
            "observacao": (m.get("observacao") or "").strip(),
        })
    sigla_partido = {p["id"]: p["sigla"] for p in bruto["partidos"]}
    partido = {}
    for f in sorted(bruto["filiacoes"], key=lambda f: f["data"] or ""):
        # vale a filiação mais recente que cobre algum trecho da legislatura, não a de hoje
        if (f["data"] or "") <= fim and (f["data_desfiliacao"] or "9999") >= ini:
            partido[f["parlamentar"]] = sigla_partido.get(f["partido"], "")

    tipo_exec = {t["id"] for t in bruto["tipos_autor"] if "executivo" in t["descricao"].lower()}
    tipo_parl = {t["id"] for t in bruto["tipos_autor"] if t["descricao"].lower() == "parlamentar"}
    autor_parl = {}       # id do autor -> id do parlamentar
    autores_exec = {}     # id do autor -> nome
    for a in bruto["autores"]:
        if a["tipo"] in tipo_exec or a["nome"].lower().startswith("poder executivo"):
            autores_exec[a["id"]] = a["nome"]
        elif a["tipo"] in tipo_parl and a["object_id"] in mandatos:
            # o tipo importa: comissões e órgãos reaproveitam os mesmos números de object_id
            autor_parl[a["id"]] = a["object_id"]

    # --- propostas
    tipos = {t["id"]: t for t in bruto["tipos"]}
    desc_status = {s["id"]: s["descricao"] for s in bruto["status"]}
    ultima, data_ultima = {}, {}
    for t in sorted(bruto["tramitacoes"], key=lambda t: (t["data_tramitacao"] or "", t["id"])):
        ultima[t["materia"]] = desc_status.get(t["status"], "")
        data_ultima[t["materia"]] = t["data_tramitacao"] or ""

    materias = []
    propostas = {pid: Counter() for pid in mandatos}
    exec_cont = Counter()
    for m in sorted(bruto["materias"], key=lambda m: (m["data_apresentacao"] or "", m["id"])):
        tipo = tipos.get(m["tipo"], {"sigla": "?", "descricao": "Proposta"})
        grupo = regras.classificar(tipo["sigla"], m["ementa"])
        ementa = re.sub(r"\s+", " ", m["ementa"] or "").strip()
        do_exec = [a for a in m["autores"] if a in autores_exec]
        exec_cont.update(do_exec)
        vereadores = sorted({autor_parl[a] for a in m["autores"] if a in autor_parl})
        for pid in vereadores:
            propostas[pid][grupo] += 1
        materias.append({
            "id": m["id"],
            "sg": tipo["sigla"],
            "rot": f"{tipo['descricao']} nº {m['numero']}/{m['ano']}",
            "d": m["data_apresentacao"] or "",
            "e": ementa[:EMENTA_MAX] + ("…" if len(ementa) > EMENTA_MAX else ""),
            "g": grupo,
            "au": vereadores,
            "pref": bool(do_exec),
            "st": ultima.get(m["id"], ""),
            "ds": data_ultima.get(m["id"], ""),
            "l": [list(x) for x in regras.extrair_locais(ementa)],
        })

    # --- sessões e presença
    hoje = gerado_em[:10]
    sessoes = [{"id": s["id"], "data": s["data_inicio"], "nome": s["__str__"]}
               for s in bruto["sessoes"] if s["data_inicio"] <= hoje]  # sessão marcada para o futuro não conta
    ids_sessoes = {s["id"] for s in sessoes}
    presentes = {}
    for p in bruto["presencas"]:
        if p["sessao_plenaria"] in ids_sessoes:
            presentes.setdefault(p["sessao_plenaria"], set()).add(p["parlamentar"])
    # lista com menos da metade das cadeiras é lista pela metade (ainda sendo digitada): trata como sem registro
    cadeiras = sum(1 for ms in mandatos.values() for m in ms if m["titular"])
    minimo = max(1, math.ceil(cadeiras / 2))
    presentes = {sid: nomes for sid, nomes in presentes.items() if len(nomes) >= minimo}
    sem_registro = [f"{s['nome']} ({_data_br(s['data'])})"
                    for s in sorted(sessoes, key=lambda s: s["data"]) if s["id"] not in presentes]
    justificadas = Counter(j["parlamentar"] for j in bruto["justificativas"] if j["sessao_plenaria"] in ids_sessoes)

    # --- votos: valem pela sessão em que aconteceram, não pela data em que foram digitados
    sessao_da_pauta = {("ordem", o["id"]): o["sessao_plenaria"] for o in bruto["ordens"]}
    sessao_da_pauta.update({("expediente", e["id"]): e["sessao_plenaria"] for e in bruto["expedientes"]})
    sessao_da_votacao = {
        v["id"]: sessao_da_pauta.get(("ordem", v["ordem"])) or sessao_da_pauta.get(("expediente", v["expediente"]))
        for v in bruto["votacoes"]}
    votacoes_validas = {vid for vid, sid in sessao_da_votacao.items() if sid in ids_sessoes}
    votos = {pid: [] for pid in mandatos}
    nominal = {}  # votação -> {parlamentar: letra}
    for v in bruto["votos"]:
        if v["parlamentar"] in votos and v["votacao"] in votacoes_validas:
            votos[v["parlamentar"]].append(v["voto"])
            nominal.setdefault(v["votacao"], {})[v["parlamentar"]] = regras.letra_do_voto(v["voto"])

    # --- voto por projeto: só votações com nomes lançados; o total oficial serve de conferência
    data_sessao = {s["id"]: s["data"] for s in sessoes}
    resultado = {r["id"]: r["nome"] for r in bruto.get("resultados", [])}
    votacoes = []
    for v in bruto["votacoes"]:
        if v["id"] not in nominal:
            continue
        nomes = nominal[v["id"]]
        oficial = [v.get("numero_votos_sim"), v.get("numero_votos_nao"), v.get("numero_abstencoes")]
        tem_oficial = all(n is not None for n in oficial)
        contado = [sum(1 for x in nomes.values() if x == letra) for letra in "sna"]
        titulo = re.search(r"\d+ - (.+?) em ", v.get("__str__") or "")
        votacoes.append({
            "id": v["id"], "m": v["materia"], "t": titulo.group(1) if titulo else "",
            "d": data_sessao[sessao_da_votacao[v["id"]]], "r": resultado.get(v.get("tipo_resultado_votacao"), ""),
            "of": oficial if tem_oficial else None, "ok": not tem_oficial or contado == oficial, "v": nomes,
        })
    votacoes.sort(key=lambda v: (v["d"], v["id"]), reverse=True)

    # --- quem presidiu a Câmara nesta legislatura (presidente só vota em casos específicos)
    sl = {x["id"] for x in bruto["sessoes_legislativas"]}
    mesas = {m["id"] for m in bruto["mesas"] if m["sessao_legislativa"] in sl}
    cargo_pres = {c["id"] for c in bruto["cargos_mesa"] if c["descricao"].strip().lower() == "presidente"}
    presidiu = {c["parlamentar"] for c in bruto["composicoes"] if c["mesa_diretora"] in mesas and c["cargo"] in cargo_pres}

    vereadores = []
    for p in bruto["parlamentares"]:
        pid = p["id"]
        if pid not in mandatos:
            continue
        cont = {g: propostas[pid][g] for g in GRUPOS}
        cont["total"] = sum(cont.values())
        vereadores.append({
            "id": pid,
            "nome": p["nome_parlamentar"],
            "nome_completo": p["nome_completo"],
            "partido": partido.get(pid, ""),
            "foto": _https(p.get("fotografia")),
            "titular": all(m["titular"] for m in mandatos[pid]),
            "observacao": " ".join(m["observacao"] for m in mandatos[pid] if m["observacao"]),
            "propostas": cont,
            "presenca": regras.presenca(pid, mandatos[pid], sessoes, presentes),
            "justificadas": justificadas[pid],
            "votos": regras.resumo_votos(votos[pid]),
            "presidiu": pid in presidiu,
        })
    vereadores.sort(key=lambda v: regras.chave(v["nome"]))

    prefeito_id = exec_cont.most_common(1)[0][0] if exec_cont else None
    pessoas_exec = [a for a in exec_cont if not autores_exec[a].lower().startswith("poder executivo")]
    if pessoas_exec:
        prefeito_id = max(pessoas_exec, key=lambda a: exec_cont[a])

    # --- subsídio: valor fixado em norma, cadastrado à mão em config/cidades.json (o PDF oficial é imagem)
    norma = (cidade.get("subsidios") or {}).get(str(legislatura["numero"]))
    subsidio = norma and {**norma, "cadeiras": cadeiras,
                          "mensal": norma["presidente"] + norma["vereador"] * (cadeiras - 1)}
    if subsidio and subsidio.get("executivo"):  # prefeito e vice; secretários ficam fora (o número deles não está na lei)
        ex = subsidio["executivo"]
        subsidio["executivo"] = {**ex, "mensal": ex["prefeito"] + ex["vice"]}

    return {
        "cidade": {k: cidade[k] for k in ("slug", "nome", "uf", "sapl")},
        "legislatura": {"numero": legislatura["numero"], "inicio": ini, "fim": fim},
        "gerado_em": gerado_em,
        "vereadores": vereadores,
        "materias": materias,
        "repetidos": regras.vias_repetidas(materias),
        "prefeito": {"nome": autores_exec.get(prefeito_id, ""), "total": sum(1 for m in materias if m["pref"])},
        "subsidio": subsidio or None,
        "votacoes": votacoes,
        "sessoes": {"total": len(sessoes), "com_registro": len(presentes), "sem_registro": sem_registro},
        "controle": {
            "presencas": sum(v["presenca"]["presentes"] for v in vereadores),
            "votos": sum(len(x) for x in votos.values()),
            "com_autor": sum(1 for m in materias if m["au"]),
            "votacoes_divergentes": sum(1 for v in votacoes if not v["ok"]),
        },
    }
