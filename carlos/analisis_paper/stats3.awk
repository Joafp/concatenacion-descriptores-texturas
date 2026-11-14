# Friedman / Iman-Davenport / post hoc Holm / Wilcoxon exacto para 3 metodos
# Uso: awk -F, -v M="Individual,Completa-22,Top-4" -f stats3.awk archivo.csv
function erfc(x,   t, y, s) { s = 1; if (x < 0) { s = -1; x = -x }
  t = 1 / (1 + 0.3275911 * x)
  y = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429)))) * exp(-x * x)
  return s == 1 ? y : 2 - y }
function p2norm(z) { if (z < 0) z = -z; return erfc(z / sqrt(2)) }
function abs(x) { return x < 0 ? -x : x }
function wilcoxon_exact(a, b, n,   i, j, d, ad, r, cnt, total, W, Wp, Wm, mask, s, ext, obs, idx, tmp, k) {
  # a[], b[] por dataset 1..n; devuelve p bilateral exacto (sin ceros ni empates esperados)
  for (i = 1; i <= n; i++) { d[i] = a[i] - b[i]; ad[i] = abs(d[i]) }
  for (i = 1; i <= n; i++) { r[i] = 1; tmp = 0
    for (j = 1; j <= n; j++) { if (j != i && ad[j] < ad[i]) r[i]++; if (j != i && ad[j] == ad[i]) tmp++ }
    r[i] += tmp / 2 }
  Wp = 0; Wm = 0; total = 0
  for (i = 1; i <= n; i++) { total += r[i]; if (d[i] > 0) Wp += r[i]; else if (d[i] < 0) Wm += r[i] }
  obs = (Wp < Wm ? Wp : Wm); WPLUS = Wp; WMINUS = Wm
  cnt = 0
  for (mask = 0; mask < 2 ^ n; mask++) { s = 0; k = mask
    for (i = 1; i <= n; i++) { if (k % 2 == 1) s += r[i]; k = int(k / 2) }
    ext = (s < total - s ? s : total - s)
    if (ext <= obs + 1e-9) cnt++ }
  return cnt / 2 ^ n }
BEGIN { nm = split(M, names, ",") }
NR == 1 { for (i = 1; i <= NF; i++) col[$i] = i; next }
{ n++; ds[n] = $1; for (j = 1; j <= nm; j++) v[n, j] = $(col[names[j]]) + 0 }
END {
  k = nm
  for (i = 1; i <= n; i++) for (j = 1; j <= k; j++) {
    r = 1; t = 0
    for (l = 1; l <= k; l++) if (l != j) { if (v[i, l] > v[i, j]) r++; else if (v[i, l] == v[i, j]) t++ }
    R[j] += r + t / 2 }
  S = 0; printf "Rangos medios:"
  for (j = 1; j <= k; j++) { Rm[j] = R[j] / n; S += Rm[j] ^ 2; printf " %s=%.4f", names[j], Rm[j] }
  print ""
  chi = 12 * n / (k * (k + 1)) * (S - k * (k + 1) ^ 2 / 4)
  pchi = exp(-chi / 2)   # df = 2 (k = 3)
  d1 = k - 1; d2 = (k - 1) * (n - 1)
  F = (n - 1) * chi / (n * (k - 1) - chi)
  pF = (d2 / (d2 + d1 * F)) ^ (d2 / 2)   # cola superior F(2, d2)
  printf "Friedman chi2=%.4f p=%.4f | Iman-Davenport F=%.4f p=%.4f (df %d,%d)\n", chi, pchi, F, pF, d1, d2
  se = sqrt(k * (k + 1) / (6 * n)); np = 0
  for (a = 1; a <= k; a++) for (b = a + 1; b <= k; b++) { np++
    z = (Rm[a] - Rm[b]) / se; pp[np] = p2norm(z); lab[np] = names[a] " vs " names[b]; zz[np] = z }
  # Holm
  for (i = 1; i <= np; i++) ord[i] = i
  for (i = 1; i <= np; i++) for (j = i + 1; j <= np; j++) if (pp[ord[j]] < pp[ord[i]]) { t = ord[i]; ord[i] = ord[j]; ord[j] = t }
  prev = 0
  for (i = 1; i <= np; i++) { h = (np - i + 1) * pp[ord[i]]; if (h > 1) h = 1; if (h < prev) h = prev; prev = h; holm[ord[i]] = h }
  for (i = 1; i <= np; i++) printf "  Post hoc %-28s z=%7.4f p=%.4f pHolm=%.4f\n", lab[i], zz[i], pp[i], holm[i]
  # Wilcoxon exacto, pares
  nw = 0
  for (a = 1; a <= k; a++) for (b = a + 1; b <= k; b++) { nw++
    for (i = 1; i <= n; i++) { xa[i] = v[i, a]; xb[i] = v[i, b] }
    wp[nw] = wilcoxon_exact(xa, xb, n); wl[nw] = names[a] " vs " names[b]; wpl[nw] = WPLUS; wmi[nw] = WMINUS
    dm = 0; for (i = 1; i <= n; i++) dm += xa[i] - xb[i]; wd[nw] = dm / n }
  for (i = 1; i <= nw; i++) o2[i] = i
  for (i = 1; i <= nw; i++) for (j = i + 1; j <= nw; j++) if (wp[o2[j]] < wp[o2[i]]) { t = o2[i]; o2[i] = o2[j]; o2[j] = t }
  prev = 0
  for (i = 1; i <= nw; i++) { h = (nw - i + 1) * wp[o2[i]]; if (h > 1) h = 1; if (h < prev) h = prev; prev = h; wh[o2[i]] = h }
  for (i = 1; i <= nw; i++) printf "  Wilcoxon %-28s dif=%+.4f W+=%g W-=%g p=%.4f pHolm=%.4f\n", wl[i], wd[i], wpl[i], wmi[i], wp[i], wh[i]
}
