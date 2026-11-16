# Reglas para elegir k con la curva interna de macro-F1 y metrica externa resultante.
# Uso (SVM):
#   awk -F, -v MET=accuracy -f reglas_k.awk \
#     results/exploratory/k_sweep/<ds>/k_sweep_inner.csv results/exploratory/k_sweep/<ds>/k_sweep.csv ...
# (pares inner/outer de los seis datasets; para ResMLP, results/exploratory/resmlp/k_sweep/).
# MET = accuracy o macro_f1. Promedia condiciones dentro de cada dataset y luego datasets.
# Codo con tolerancia t: ultimo k antes de la primera ganancia interna menor que t.
FNR == 1 { sub(/\r$/, ""); delete h; for (i = 1; i <= NF; i++) h[$i] = i; isinner = ("inner_f1" in h); next }
{ sub(/\r$/, "")
  key = $1 SUBSEP $3 SUBSEP $4; k = $5 + 0
  if (isinner) { inn[key, k] = $(h["inner_f1"]); ds[key] = $1; if (k > maxk[key]) maxk[key] = k }
  else out[key, k] = $(h[MET]) }
END {
  nr = split("argmax,elbow0.001,elbow0.005,elbow0.01,fix3,fix4,fix6", R, ",")
  for (key in ds) {
    K = maxk[key]
    for (r = 1; r <= nr; r++) {
      rule = R[r]
      if (rule == "argmax") { best = 1; for (k = 2; k <= K; k++) if (inn[key, k] > inn[key, best]) best = k; kk = best }
      else if (rule ~ /^elbow/) { t = substr(rule, 6) + 0; kk = K; for (k = 1; k < K; k++) if (inn[key, k + 1] - inn[key, k] < t) { kk = k; break } }
      else kk = substr(rule, 4) + 0
      d = ds[key]; S[r, d] += out[key, kk]; Kc[r, d] += kk; N[r, d]++; DS[d] = 1
    }
  }
  for (r = 1; r <= nr; r++) {
    sm = 0; sk = 0; nd = 0
    for (d in DS) { sm += S[r, d] / N[r, d]; sk += Kc[r, d] / N[r, d]; nd++ }
    printf "%-12s k_medio=%.2f %s=%.4f (datasets=%d)\n", R[r], sk / nd, MET, sm / nd, nd
  }
}
