"""Robô diário: python3 -m coletor.coletar [slug-da-cidade]

Uma cidade que falha não derruba as outras; a que falhou mantém o último arquivo bom.
"""
import datetime
import json
import os
import pathlib
import sys

from . import regras, sapl, tce
from .montar import montar

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "site" / "dados"


def receita_do_ano(cidade, contato, ano, anterior):
    """Receita publicada pelo TCE-SP. Se a leitura falhar ou vier estranha, vale a última boa."""
    try:
        nova = regras.resumo_receita(ano, tce.receitas_do_ano(tce.buscador(cidade["tce_sp"], ano, contato)))
        if nova is None or regras.receita_suspeita(nova, anterior):
            raise RuntimeError("receita veio vazia ou menor que a anterior")
        return nova
    except Exception as e:
        print(f"  receita não atualizada ({e}). Mantida a anterior.", file=sys.stderr)
        return anterior


def coletar_cidade(cidade, contato):
    cliente = sapl.Sapl(cidade["sapl"], contato)
    for numero in cidade["legislaturas"]:
        destino = SAIDA / f"{cidade['slug']}-{numero}.json"
        leg, bruto = sapl.baixar(cliente, numero)
        agora = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        novo = montar(cidade, leg, bruto, gerado_em=agora)
        anterior = json.loads(destino.read_text()) if destino.exists() else None
        ano = int(agora[:4])
        novo["receita"] = None
        if cidade.get("tce_sp") and novo["legislatura"]["inicio"][:4] <= str(ano) <= novo["legislatura"]["fim"][:4]:
            novo["receita"] = receita_do_ano(cidade, contato, ano, (anterior or {}).get("receita"))
        motivos = regras.problemas_da_coleta(novo, anterior)
        if motivos:
            raise RuntimeError(f"legislatura {numero} não publicada: " + "; ".join(motivos))
        provisorio = destino.with_suffix(".tmp")  # grava inteiro antes de trocar: nunca fica arquivo pela metade
        provisorio.write_text(json.dumps(novo, ensure_ascii=False, separators=(",", ":")))
        os.replace(provisorio, destino)
        print(f"  {destino.name}: {len(novo['vereadores'])} vereadores, {len(novo['materias'])} propostas, "
              f"{novo['sessoes']['com_registro']} sessões com registro ({cliente.pedidos} pedidos até aqui)")


def main(argv):
    cfg = json.loads((RAIZ / "config" / "cidades.json").read_text())
    SAIDA.mkdir(parents=True, exist_ok=True)
    falhas = 0
    for cidade in cfg["cidades"]:
        if not cidade.get("ativa") or (argv and cidade["slug"] not in argv):
            continue
        print(cidade["nome"])
        try:
            coletar_cidade(cidade, cfg["contato_robo"])
        except Exception as e:  # mantém o último arquivo bom desta cidade
            falhas += 1
            print(f"  FALHOU ({e}). Mantido o arquivo anterior.", file=sys.stderr)
    indice = [{k: c.get(k) for k in ("slug", "nome", "uf", "ativa", "legislaturas", "sapl")} for c in cfg["cidades"]]
    (SAIDA / "cidades.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
