"use strict";
// Seções de fiscalização: voto por projeto, resposta aos requerimentos e despesa da Prefeitura.
// Usa os ajudantes de app.js (h, $, limpa, fonte, D...), que já existem quando estas funções são chamadas.

// ---------- como cada um votou ----------
const VOTOS = [["s", "Sim"], ["n", "Não"], ["a", "Abstenção"], ["x", "Não votou"], ["o", "Outro registro"]];
let limiteVotacoes = 0;

function itemVotacao(v) {
  const m = porId.get(v.m);
  const linhas = VOTOS.map(([letra, nome]) => {
    const quem = Object.keys(v.v).filter((id) => v.v[id] === letra).map((id) => nomeVereador.get(Number(id)) || "?").sort((a, b) => a.localeCompare(b, "pt-BR"));
    return quem.length ? h("div", { class: "voto voto-" + letra }, h("b", null, `${nome} (${quem.length}): `), quem.join(", ")) : null;
  });
  return h("li", { class: "item lei" },
    h("div", { class: "cab" }, fonte("/materia/" + v.m, (m && m.rot) || v.t || "Abrir a proposta"), h("span", null, "Sessão de " + dataBr(v.d)), v.r && h("span", { class: "selo" }, v.r)),
    m && h("p", null, m.e), linhas,
    !v.ok && v.of && h("div", { class: "rodape" }, `Atenção: o total oficial da Câmara registra ${v.of[0]} sim, ${v.of[1]} não e ${v.of[2]} abstenções, diferente da lista de nomes acima.`));
}

function votacoes() {
  const todas = D.votacoes || [];
  $("votacoes").hidden = !todas.length;
  if (!todas.length) return;
  const divididas = todas.filter((v) => Object.values(v.v).some((x) => x === "n" || x === "a"));
  const filtro = $("votacoes-divididas");
  filtro.checked = divididas.length > 0;
  limiteVotacoes = PASSO;
  const pinta = () => {
    const lista = filtro.checked ? divididas : todas;
    $("votacoes-contagem").textContent = `${nf.format(todas.length)} votações com o voto de cada vereador registrado. ${nf.format(divididas.length)} tiveram voto contra ou abstenção.`;
    limpa($("votacoes-lista")).append(...lista.slice(0, limiteVotacoes).map(itemVotacao));
    $("votacoes-mais").hidden = lista.length <= limiteVotacoes;
  };
  filtro.onchange = () => { limiteVotacoes = PASSO; pinta(); };
  $("votacoes-mais").onclick = () => { limiteVotacoes += PASSO; pinta(); };
  pinta();
}

// ---------- os requerimentos tiveram resposta? ----------
const dias = (a, b) => Math.round((Date.parse(b) - Date.parse(a)) / 864e5);
const mediana = (xs) => { const o = [...xs].sort((a, b) => a - b), n = o.length; return n ? (n % 2 ? o[(n - 1) / 2] : Math.round((o[n / 2 - 1] + o[n / 2]) / 2)) : null; };

function respostas() {
  const reqs = D.materias.filter((m) => m.sg === "REQ" && m.au.length);
  $("respostas").hidden = !reqs.length;
  if (!reqs.length) return;
  const porSituacao = new Map();
  for (const m of reqs) { const k = m.st || "Sem situação registrada"; porSituacao.set(k, (porSituacao.get(k) || []).concat(m)); }
  const ordem = [...porSituacao.entries()].sort((a, b) => b[1].length - a[1].length);
  limpa($("respostas-situacoes")).append(...ordem.map(([nome, ms]) => {
    const prazos = /^resposta publicada/i.test(nome) ? ms.filter((m) => m.d && m.ds).map((m) => dias(m.d, m.ds)).filter((n) => n >= 0) : [];
    const meio = mediana(prazos);
    return h("li", null, h("span", null, nome, meio != null && h("small", null, ` · em geral ${meio} dias entre o pedido e o registro da resposta`)), h("b", null, nf.format(ms.length)));
  }));
  const pendentes = reqs.filter((m) => /aguard|n[ãa]o publicad|n[ãa]o respond/i.test(m.st)).sort((a, b) => a.d.localeCompare(b.d));
  $("respostas-contagem").textContent = `${nf.format(reqs.length)} requerimentos de vereadores neste período.` + (pendentes.length ? ` ${nf.format(pendentes.length)} constam sem resposta publicada:` : "");
  limpa($("respostas-lista")).append(...pendentes.map(item));
}

// ---------- para onde vai o dinheiro ----------
function despesa() {
  const d = D.despesa;
  $("despesa").hidden = !d;
  if (!d) return;
  const ate = `de janeiro a ${MESES[d.ate_mes - 1]} de ${d.ano}`;
  limpa($("despesa-numeros")).append(
    h("div", { class: "numero" }, h("b", null, reais.format(d.pago)), h("span", null, `pagos pela Prefeitura ${ate}`)),
    h("div", { class: "numero" }, h("b", null, reais.format(d.camara_pago)), h("span", null, `pagos pela Câmara ${ate}`)));
  const a = d.areas, caixa = limpa($("despesa-areas"));
  $("despesa-areas-titulo").hidden = !a;
  if (a) {
    const maior = Math.max(...a.itens.map((x) => x.valor));
    caixa.append(h("p", { class: "apoio" }, `Despesa liquidada (serviço entregue e conferido) de janeiro a ${MESES[a.bimestre * 2 - 1]} de ${a.ano}: ${reais.format(a.total)}. `, link("https://siconfi.tesouro.gov.br/", "Fonte: Tesouro Nacional, relatório entregue pela Prefeitura")));
    for (const x of a.itens) caixa.append(h("div", { class: "barra-linha area" }, h("div", { class: "rot" }, x.nome),
      h("div", null, h("div", { class: "barra" }, h("i", { class: "lei-bg", style: `width:${(x.valor / maior) * 100}%` })), h("small", null, `${reais.format(x.valor)} · ${Math.round((x.valor / a.total) * 100)}%`))));
  }
  limpa($("despesa-fornecedores")).append(...d.fornecedores.map((f) => h("li", null, h("span", null, f.nome), h("b", null, reais.format(f.valor)))));
  limpa($("despesa-notas")).append(
    `Pagamentos em nome da própria Prefeitura aparecem assim no portal, que não detalha o que são. Pessoas físicas não são listadas pelo nome: somam ${reais.format(d.pessoas_fisicas.valor)} em ${nf.format(d.pessoas_fisicas.pagamentos)} pagamentos. `,
    link(TCE + D.cidade.slug, "Fonte: Tribunal de Contas do Estado de São Paulo"));
}
