const test = require("node:test");
const assert = require("node:assert");
const { pagoAte } = require("../site/placar.js");

const brt = (iso) => Date.parse(iso + "-03:00");
const M = 63375;

test("antes do início do período o placar é zero", () => {
  assert.strictEqual(pagoAte(M, "2025-01-01", "2028-12-31", brt("2024-12-31T23:00:00")), 0);
});
test("um mês inteiro vale uma folha mensal", () => {
  assert.strictEqual(pagoAte(M, "2025-01-01", "2028-12-31", brt("2025-02-01T00:00:00")), M);
});
test("metade do mês vale metade da folha", () => {
  assert.strictEqual(pagoAte(M, "2025-01-01", "2028-12-31", brt("2025-01-16T12:00:00")), M / 2);
});
test("o mês é o de Brasília, não o do aparelho de quem lê", () => {
  // 01/02 às 02h UTC ainda é 31/01 às 23h em Brasília
  const v = pagoAte(M, "2025-01-01", "2028-12-31", Date.parse("2025-02-01T02:00:00Z"));
  assert.ok(v < M && v > M * 0.99);
});
test("depois do fim do período o placar para em 48 folhas", () => {
  assert.strictEqual(pagoAte(M, "2025-01-01", "2028-12-31", brt("2030-06-01T00:00:00")), 48 * M);
});
test("o placar sobe com o passar dos segundos", () => {
  const a = pagoAte(M, "2025-01-01", "2028-12-31", brt("2026-11-15T12:00:00"));
  const b = pagoAte(M, "2025-01-01", "2028-12-31", brt("2026-11-15T12:00:01"));
  assert.ok(b > a);
});
