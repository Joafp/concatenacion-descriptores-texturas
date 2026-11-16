# No inferioridad de Top-4 frente a Completa-22 sobre medias por dataset.
# Uso: awk -F, -v DELTA=0.01 -f no_inferioridad.awk results/analysis/thesis_accuracy_primary_20261115_v3/static_accuracy_svm.csv
# Columnas: dataset,Individual,Completa-22,Top-4. H0: Top-4 - Completa-22 <= -DELTA.
# t de Student con 5 grados de libertad (seis datasets): cota unilateral 95 % con t=2,015048 y
# valor p con la CDF cerrada para nu=5. Wilcoxon exacto unilateral sobre d + DELTA (2^n signos).
BEGIN { if (DELTA == "") DELTA = 0.01; PI = 3.141592653589793 }
FNR == 1 { sub(/\r$/, ""); for (i = 1; i <= NF; i++) h[$i] = i; next }
{ sub(/\r$/, ""); n++; d[n] = $(h["Top-4"]) - $(h["Completa-22"]) }
END {
  m = 0; for (k = 1; k <= n; k++) m += d[k]; m /= n
  s = 0; for (k = 1; k <= n; k++) s += (d[k] - m) ^ 2; sd = sqrt(s / (n - 1)); se = sd / sqrt(n)
  lb = m - 2.015048 * se
  tt = (m + DELTA) / se; th = atan2(tt, sqrt(5))
  A = (2 / PI) * (th + sin(th) * cos(th) * (1 + (2 / 3) * cos(th) ^ 2)); p = (1 - A) / 2
  for (k = 1; k <= n; k++) { e[k] = d[k] + DELTA; a[k] = (e[k] < 0 ? -e[k] : e[k]) }
  for (k = 1; k <= n; k++) { r[k] = 1; for (j = 1; j <= n; j++) if (j != k && a[j] < a[k]) r[k]++ }
  Wp = 0; for (k = 1; k <= n; k++) if (e[k] > 0) Wp += r[k]
  c = 0
  for (mask = 0; mask < 2 ^ n; mask++) { s2 = 0; x = mask; for (k = 1; k <= n; k++) { if (x % 2 == 1) s2 += r[k]; x = int(x / 2) } if (s2 >= Wp - 1e-9) c++ }
  printf "Delta_medio=%.4f de=%.4f cota95=%.4f t=%.3f p_t=%.4f W+=%d p_Wilcoxon=%.4f\n", m, sd, lb, tt, p, Wp, c / 2 ^ n
}
