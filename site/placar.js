"use strict";
// Placar do subsídio: estimativa do valor fixado em norma, mês a mês, no horário de Brasília.
const FUSO_BRASILIA_MS = 3 * 3600 * 1000;

function pagoAte(mensal, inicio, fim, agoraMs) {
  const [anoIni, mesIni] = inicio.split("-").map(Number);
  const [anoFim, mesFim] = fim.split("-").map(Number);
  const t = new Date(agoraMs - FUSO_BRASILIA_MS);   // campos UTC deste objeto = relógio de Brasília
  const ano = t.getUTCFullYear(), mes = t.getUTCMonth();
  const mesesCheios = (ano - anoIni) * 12 + (mes + 1 - mesIni);
  if (mesesCheios < 0) return 0;
  const mesesDoPeriodo = (anoFim - anoIni) * 12 + (mesFim - mesIni) + 1;
  if (mesesCheios >= mesesDoPeriodo) return mesesDoPeriodo * mensal;
  const comeco = Date.UTC(ano, mes, 1), proximo = Date.UTC(ano, mes + 1, 1);
  return (mesesCheios + (t.getTime() - comeco) / (proximo - comeco)) * mensal;
}

if (typeof module !== "undefined") module.exports = { pagoAte };
