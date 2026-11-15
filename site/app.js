"use strict";
// ---------- Ajustes de quem mantém o site ----------
const SHOW_PREFEITO = false;   // ligar só depois de conferir os números dos vereadores
const SHOW_FOTOS = true;       // fotos vêm do próprio SAPL; desligue se a Câmara pedir
const MANTENEDOR = "";         // ex.: "Mantido por Fulano de Tal, morador de Cunha"
const CONTATO_ERRO = "";       // ex.: "erros@valeemfoco.org"
const PASSO = 20;              // itens por vez nas listas
// ---------------------------------------------------

const GRUPOS = [
  ["pedido", "Pedidos de melhoria", "Indicações: o vereador pede algo ao prefeito."],
  ["cobranca", "Cobranças", "Requerimentos e moções de apelo ou repúdio."],
  ["homenagem", "Homenagens e pesar", "Moções de aplauso e de pesar, títulos, nomes de rua e datas comemorativas."],
  ["lei", "Leis e regras", "Projetos que criam ou mudam regras do município."],
  ["outro", "Trâmite interno", "Redações finais, pedidos de urgência e documentos internos."],
];
const $ = (id) => document.getElementById(id);
const nf = new Intl.NumberFormat("pt-BR");
const reais = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
let relogioPlacar = 0;
let D = null;          // dados da cidade e legislatura escolhidas
let CIDADES = [];
let porId = new Map();
let nomeVereador = new Map();
let pedidoAtual = 0;   // evita que uma resposta atrasada sobrescreva a escolha mais recente

function h(tag, attrs, ...filhos) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v == null) continue;
    if (k === "class") el.className = v; else if (k.startsWith("on")) el.addEventListener(k.slice(2), v); else el.setAttribute(k, v);
  }
  for (const f of filhos.flat()) if (f != null && f !== false) el.append(f.nodeType ? f : document.createTextNode(String(f)));
  return el;
}
const limpa = (el) => { while (el.firstChild) el.firstChild.remove(); return el; };
const semAcento = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const dataBr = (iso) => iso ? iso.slice(0, 10).split("-").reverse().join("/") : "";
const fonte = (caminho, texto) => h("a", { href: D.cidade.sapl + caminho, target: "_blank", rel: "noopener" }, texto);
const pct = (a, b) => b ? Math.round((a / b) * 100) + "%" : "sem dado";

async function json(url) {
  const r = await fetch(url, { cache: "no-cache" });
  if (!r.ok) throw new Error(url + " " + r.status);
  return r.json();
}

async function iniciar() {
  try {
    CIDADES = await json("dados/cidades.json");
  } catch (e) {
    $("titulo").textContent = "Não foi possível carregar os dados";
    $("linha-fina").textContent = "Tente de novo em alguns minutos.";
    return;
  }
  const q = new URLSearchParams(location.search);
  const sel = $("sel-cidade");
  for (const c of CIDADES) sel.append(h("option", { value: c.slug, disabled: !c.ativa }, c.ativa ? c.nome : c.nome + " (em breve)"));
  const ativa = CIDADES.find((c) => c.ativa && c.slug === q.get("cidade")) || CIDADES.find((c) => c.ativa);
  if (!ativa) { $("titulo").textContent = "Nenhuma cidade disponível ainda"; return; }
  sel.value = ativa.slug;
  sel.addEventListener("change", () => trocar(sel.value, null));
  $("sel-leg").addEventListener("change", () => trocar(sel.value, $("sel-leg").value));
  $("campo-busca").addEventListener("input", () => { limiteBusca = PASSO; buscar(); });
  $("busca-mais").addEventListener("click", () => { limiteBusca += PASSO * 2; buscar(); });
  $("filtro-partido").addEventListener("change", cartoes);
  $("ordem").addEventListener("change", cartoes);
  await trocar(ativa.slug, q.get("leg"));
}

async function trocar(slug, leg) {
  const c = CIDADES.find((x) => x.slug === slug);
  const legs = c.legislaturas || [];
  const numero = legs.map(String).includes(String(leg)) ? leg : legs[0];
  limpa($("sel-leg"));
  for (const n of legs) $("sel-leg").append(h("option", { value: n }, n + "ª legislatura"));
  $("sel-leg").value = numero;
  const meu = ++pedidoAtual;
  let dados;
  try {
    dados = await json(`dados/${slug}-${numero}.json`);
  } catch (e) {
    if (meu !== pedidoAtual) return;
    $("conteudo").hidden = true;
    $("titulo").textContent = c.nome + ": dados ainda não disponíveis";
    $("linha-fina").textContent = "Este período ainda não foi coletado.";
    return;
  }
  if (meu !== pedidoAtual) return;
  D = dados;
  history.replaceState(null, "", `?cidade=${slug}&leg=${numero}`);
  porId = new Map(D.materias.map((m) => [m.id, m]));
  nomeVereador = new Map(D.vereadores.map((v) => [v.id, v.nome]));
  desenhar();
}

function desenhar() {
  const c = D.cidade, l = D.legislatura;
  const anos = `${l.inicio.slice(0, 4)} a ${l.fim.slice(0, 4)}`;
  document.title = `${c.nome} em Foco: o que cada vereador faz`;
  $("titulo").textContent = `${c.nome} em Foco`;
  $("linha-fina").textContent = `Vereadores de ${c.nome}-${c.uf}, com dados oficiais da Câmara. ${l.numero}ª legislatura, ${anos}.`;
  limpa($("atualizado")).append("Dados lidos do sistema da Câmara em " + dataBr(D.gerado_em) + ". ", fonte("/", "Abrir a fonte oficial"));
  $("conteudo").hidden = false;

  const dosVereadores = D.materias.filter((m) => m.au.length);
  const conta = (g) => dosVereadores.filter((m) => m.g === g).length;
  limpa($("numeros")).append(
    numero(D.vereadores.length, "vereadores e suplentes no período"),
    numero(dosVereadores.length, "propostas de vereadores"),
    numero(conta("pedido"), "pedidos de melhoria"),
    numero(conta("homenagem"), "homenagens e moções de pesar"),
    numero(D.sessoes.com_registro, "sessões com presença registrada"),
  );
  placar();
  chips();
  $("campo-busca").value = "";
  limiteBusca = PASSO;
  buscar();
  repetidos();
  grupos(dosVereadores);
  partidos();
  cartoes();
  prefeito();
  metodo();
  $("rodape-quem").textContent = MANTENEDOR || "Projeto cívico independente.";
}

const numero = (n, rotulo) => h("div", { class: "numero" }, h("b", null, nf.format(n)), h("span", null, rotulo));

function item(m) {
  const autores = m.au.map((id) => nomeVereador.get(id)).filter(Boolean);
  const quem = m.pref ? "Prefeito / Poder Executivo" : autores.join(", ");
  return h("li", { class: "item " + m.g },
    h("div", { class: "cab" }, fonte("/materia/" + m.id, m.rot), h("span", null, dataBr(m.d)), quem && h("span", null, quem)),
    h("p", null, m.e),
    m.st && h("div", { class: "rodape" }, "Situação na Câmara: ", h("span", { class: "selo" }, m.st)));
}

// ---------- busca ----------
let limiteBusca = PASSO;
function chips() {
  const cont = new Map();
  for (const m of D.materias) for (const [cat, nome] of m.l) if (cat === "bairro") cont.set(nome, (cont.get(nome) || 0) + 1);
  const top = [...cont].sort((a, b) => b[1] - a[1]).slice(0, 10);
  limpa($("chips-bairros")).append(...top.map(([nome]) => h("button", {
    class: "chip", type: "button",
    onclick: () => { $("campo-busca").value = nome.replace(/^Bairro (d[aeo]s? )?/i, ""); limiteBusca = PASSO; buscar(); },
  }, nome.replace(/^Bairro (d[aeo]s? )?/i, ""))));
}
function buscar() {
  const termo = semAcento($("campo-busca").value.trim());
  const lista = limpa($("busca-resultado"));
  if (termo.length < 3) {
    $("busca-contagem").textContent = termo ? "Digite pelo menos 3 letras." : "";
    $("busca-mais").hidden = true;
    return;
  }
  const achados = D.materias.filter((m) => semAcento(m.e).includes(termo) || m.l.some((x) => semAcento(x[1]).includes(termo))).sort((a, b) => b.d.localeCompare(a.d));
  $("busca-contagem").textContent = achados.length
    ? `${nf.format(achados.length)} proposta(s) citam “${$("campo-busca").value.trim()}”. As mais recentes primeiro.`
    : "Nenhuma proposta cita esse nome neste período. Isso não quer dizer que nada foi feito: pode estar escrito de outro jeito.";
  lista.append(...achados.slice(0, limiteBusca).map(item));
  $("busca-mais").hidden = achados.length <= limiteBusca;
}

// ---------- vias repetidas ----------
function repetidos() {
  const caixa = limpa($("lista-repetidos"));
  let mostradas = 8;
  const botao = $("repetidos-mais");
  const pinta = () => {
    limpa(caixa);
    if (!D.repetidos.length) caixa.append(h("p", { class: "apoio" }, "Nenhuma via aparece em mais de um pedido neste período."));
    for (const r of D.repetidos.slice(0, mostradas)) {
      const ms = r.ids.map((id) => porId.get(id)).filter(Boolean).sort((a, b) => a.d.localeCompare(b.d));
      const det = h("details", { class: "via" }, h("summary", null, r.local, h("span", null, ms.length + " pedidos")));
      det.addEventListener("toggle", () => { if (det.open && !det.querySelector("ol")) det.append(h("ol", { class: "lista" }, ms.map(item))); });
      caixa.append(det);
    }
    botao.hidden = D.repetidos.length <= mostradas;
  };
  botao.onclick = () => { mostradas += 12; pinta(); };
  pinta();
}

// ---------- homenagem ou trabalho ----------
function barra(cont, total) {
  return h("div", { class: "barra", role: "img", "aria-label": GRUPOS.map(([g, n]) => `${n}: ${cont[g] || 0}`).join("; ") },
    GRUPOS.filter(([g]) => cont[g]).map(([g, n]) => h("i", { class: g + "-bg", style: `width:${(cont[g] / total) * 100}%`, title: `${n}: ${cont[g]}` })));
}
function grupos(ms) {
  const total = {};
  for (const m of ms) total[m.g] = (total[m.g] || 0) + 1;
  const caixa = limpa($("barras-grupos"));
  caixa.append(h("div", { class: "legenda" }, GRUPOS.map(([g, n]) =>
    h("span", { style: `--c: var(--${g})` }, `${n}: ${nf.format(total[g] || 0)}`))));
  const maior = Math.max(1, ...D.vereadores.map((v) => v.propostas.total));
  for (const v of [...D.vereadores].sort((a, b) => b.propostas.total - a.propostas.total)) {
    caixa.append(h("div", { class: "barra-linha" }, h("div", { class: "rot" }, v.nome, " ", h("span", { class: "partido" }, `(${v.propostas.total})`)), barra(v.propostas, maior)));
  }
  caixa.append(h("p", { class: "apoio" }, "Proposta assinada por mais de um vereador conta para cada um. Por isso a soma das barras passa do total."));
}

// ---------- cartões ----------
function partidos() {
  const lista = [...new Set(D.vereadores.map((v) => v.partido).filter(Boolean))].sort();
  limpa($("filtro-partido")).append(h("option", { value: "" }, "Todos"), ...lista.map((p) => h("option", { value: p }, p)));
}
function cartoes() {
  const partido = $("filtro-partido").value, ordem = $("ordem").value;
  const taxa = (v) => v.presenca.comparavel && v.presenca.sessoes ? v.presenca.presentes / v.presenca.sessoes : 2;
  const ord = {
    nome: (a, b) => semAcento(a.nome).localeCompare(semAcento(b.nome)),
    total: (a, b) => b.propostas.total - a.propostas.total,
    pedido: (a, b) => b.propostas.pedido - a.propostas.pedido,
    homenagem: (a, b) => b.propostas.homenagem - a.propostas.homenagem,
    faltas: (a, b) => taxa(a) - taxa(b),
    nao: (a, b) => b.votos.nao - a.votos.nao,
  }[ordem];
  const lista = D.vereadores.filter((v) => !partido || v.partido === partido).sort(ord);
  limpa($("cartoes")).append(...lista.map(cartao));
}
function cartao(v) {
  const iniciais = v.nome.split(/\s+/).map((p) => p[0]).slice(0, 2).join("").toUpperCase();
  const semFoto = () => h("div", { class: "foto", "aria-hidden": "true" }, iniciais);
  let foto = semFoto();
  if (SHOW_FOTOS && v.foto) {
    foto = h("img", { class: "foto", src: v.foto, alt: "", loading: "lazy", referrerpolicy: "no-referrer" });
    foto.addEventListener("error", () => foto.replaceWith(semFoto()));
  }
  const p = v.presenca, vt = v.votos;
  const votosTotal = vt.sim + vt.nao + vt.abstencao + vt.nao_votou;
  // sem comparação possível, não mostra o "de N": pareceria contagem de faltas
  const presenca = !p.sessoes ? "sem registro"
    : p.comparavel ? `${p.presentes} de ${p.sessoes} (${pct(p.presentes, p.sessoes)})` : `presente em ${p.presentes}`;
  return h("article", { class: "cartao" },
    h("div", { class: "quem" }, foto, h("div", null, h("h3", null, v.nome),
      h("div", { class: "partido" }, [v.partido || "partido não informado", v.titular ? null : "suplente"].filter(Boolean).join(" · ")))),
    barra(v.propostas, Math.max(1, v.propostas.total)),
    h("dl", null,
      h("dt", null, "Pedidos de melhoria"), h("dd", null, v.propostas.pedido),
      h("dt", null, "Cobranças"), h("dd", null, v.propostas.cobranca),
      h("dt", null, "Homenagens e pesar"), h("dd", null, v.propostas.homenagem),
      h("dt", null, "Leis e regras"), h("dd", null, v.propostas.lei),
      h("dt", null, "Presença em sessões"), h("dd", null, presenca),
      h("dt", null, "Votos registrados"), h("dd", null, votosTotal ? `${vt.sim} sim · ${vt.nao} não` : "sem registro"),
      v.justificadas ? [h("dt", null, "Ausências justificadas"), h("dd", null, v.justificadas)] : null,
      (vt.abstencao || (vt.nao_votou && !v.presidiu)) ? [h("dt", null, "Abstenções / não votou"), h("dd", null, `${vt.abstencao} · ${vt.nao_votou}`)] : null),
    v.presidiu && h("p", { class: "obs" }, "Presidiu a Câmara neste período. Quem preside a sessão, em regra, só vota em casos previstos no regimento. Por isso tem menos votos registrados."),
    (v.observacao || !p.comparavel) && h("p", { class: "obs" },
      !p.comparavel ? "Suplência, afastamento ou longo período sem registro: o sistema não informa todas as datas de exercício, então a presença não é comparada com a dos demais. " : "", v.observacao),
    fonte("/parlamentar/" + v.id, "Ver a ficha oficial na Câmara"));
}

// ---------- prefeito ----------
function prefeito() {
  const sec = $("prefeito");
  sec.hidden = !SHOW_PREFEITO || !D.prefeito.total;
  if (sec.hidden) return;
  const ms = D.materias.filter((m) => m.pref).sort((a, b) => b.d.localeCompare(a.d));
  let limite = PASSO;
  const pinta = () => {
    $("prefeito-contagem").textContent = `${nf.format(ms.length)} propostas enviadas pelo Executivo neste período` + (D.prefeito.nome ? ` (autor mais frequente no sistema: ${D.prefeito.nome}).` : ".");
    limpa($("prefeito-lista")).append(...ms.slice(0, limite).map(item));
    $("prefeito-mais").hidden = ms.length <= limite;
  };
  $("prefeito-mais").onclick = () => { limite += PASSO * 2; pinta(); };
  pinta();
}

// ---------- placar do subsídio ----------
function placar() {
  clearInterval(relogioPlacar);
  const sub = D.subsidio, l = D.legislatura;
  $("placar").hidden = !sub;
  if (!sub) return;
  const mostra = () => { $("placar-valor").textContent = reais.format(pagoAte(sub.mensal, l.inicio, l.fim, Date.now())); };
  mostra();
  const calmo = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (Date.now() < Date.parse(l.fim + "T23:59:59-03:00")) relogioPlacar = setInterval(mostra, calmo ? 5000 : 100);
  $("placar-ritmo").textContent = `${reais.format(sub.mensal)} por mês, ${reais.format(sub.mensal / 30)} por dia.`;
  limpa($("placar-conta")).append(
    `Conta: 1 presidente a ${reais.format(sub.presidente)} mais ${sub.cadeiras - 1} vereadores a ${reais.format(sub.vereador)} por mês, desde ${dataBr(l.inicio)}. `,
    "É o valor fixado na norma, não a folha de pagamento: não entram encargos, décimo terceiro, diárias, assessores, descontos nem reajustes posteriores. ",
    fonte(sub.caminho, sub.norma));
}

// ---------- metodologia ----------
function metodo() {
  const s = D.sessoes;
  const caixa = limpa($("metodo-texto"));
  const bloco = (titulo, ...ps) => caixa.append(h("h3", null, titulo), ...ps.map((p) => h("p", null, p)));
  bloco("Fonte", ["Tudo vem do SAPL, o sistema oficial em que a Câmara registra propostas, sessões e votos. Um robô lê esses dados uma vez por dia, devagar e se identificando. Cada proposta e cada vereador têm link para a página oficial. ", fonte("/", "Abrir o SAPL da Câmara")]);
  bloco("Como as propostas são separadas",
    "Indicação é pedido de melhoria. Requerimento é cobrança. Moção é homenagem ou pesar. Projeto de lei, de resolução, de decreto legislativo e emenda são leis e regras.",
    "Exceções, pelo texto da proposta: projeto que dá nome a rua, escola ou outro bem público, concede título de cidadão, medalha, comenda, diploma de honra ou honra ao mérito, ou cria data comemorativa entra como homenagem. Moção de apelo, repúdio ou protesto entra como cobrança. Requerimento de urgência na tramitação entra como trâmite interno.",
    "A regra é automática e igual para todos; pode errar em casos isolados. O total de cada vereador inclui propostas depois retiradas ou reapresentadas.");
  bloco("Presença",
    `A presença conta só as sessões já realizadas em que a Câmara registrou a lista de presentes: ${s.com_registro} de ${s.total} neste período. Entram sessões ordinárias, extraordinárias, solenes e especiais.`,
    "Dado ausente não é falta. Sessão sem lista, ou com lista de menos da metade das cadeiras (sinal de registro incompleto), fica fora da conta. Ausência justificada aparece à parte quando a Câmara a registrou.",
    `Para suplentes, vereadores com afastamento e quem ficou ${8} ou mais sessões seguidas sem aparecer, o sistema não informa todas as datas de exercício. Nesses casos o site mostra só em quantas sessões a pessoa esteve presente, sem porcentagem e sem comparar.`,
    s.sem_registro.length ? "Sessões fora da conta: " + s.sem_registro.join("; ") + "." : null);
  bloco("Votos", "Só aparecem as votações nominais lançadas no sistema, contadas pela sessão em que aconteceram. Votação simbólica ou não lançada não aparece. “Não votou” é como o sistema registra, e não indica o motivo. Quem preside a sessão, em regra, só vota em casos previstos no regimento.");
  bloco("Ruas e bairros", "A busca procura o nome no texto oficial da proposta. A lista de vias repetidas junta pedidos que citam a mesma rua ou estrada, mesmo que tratem de assuntos diferentes.");
  if (D.subsidio) bloco("Subsídio", [`O placar multiplica o subsídio mensal fixado na ${D.subsidio.norma} pelas ${D.subsidio.cadeiras} cadeiras da Câmara e pelo tempo passado desde o início da legislatura. É uma estimativa: o site não lê a folha de pagamento. Quando um suplente assume, a conta segue sendo por cadeira. `, fonte(D.subsidio.caminho, "Abrir a norma")]);
  bloco("O que ainda não está aqui", (D.subsidio ? "Folha de pagamento, " : "Salário dos vereadores, ") + "obras, contratos e gastos. Só entram quando houver fonte oficial conferida.");
  const erro = limpa($("texto-erro"));
  erro.append("Compare com a página oficial pelo link de cada item. Se o site estiver diferente da Câmara, o erro é nosso e será corrigido. ");
  erro.append(CONTATO_ERRO ? "Escreva para " + CONTATO_ERRO + "." : "Se o erro estiver no registro da própria Câmara, a correção é pedida à secretaria da Câmara.");
}

iniciar();
