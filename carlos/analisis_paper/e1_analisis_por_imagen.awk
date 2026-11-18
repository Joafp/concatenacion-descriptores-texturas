# Analisis por imagen de E1 (Top-4 directo frente a la cascada por margen).
# Entrada: e1_por_imagen.csv (salida de e1_por_imagen.sh).
# Uso, desde la raiz del repo:
#   awk -F, -v OUTDIR=carlos/analisis_paper -f carlos/analisis_paper/e1_analisis_por_imagen.awk carlos/analisis_paper/e1_por_imagen.csv
# Salidas en OUTDIR:
#   e1_mcnemar_compuerta.csv  una fila por condicion: McNemar exacto y calidad de la compuerta
#   e1_resumen_por_dataset.csv media, DE e IC 95 % entre folds; conteos de la compuerta sumados
#   e1_confusion.csv          matrices de confusion sumadas sobre las condiciones de cada dataset
#   e1_por_clase.csv          precision, recall y F1 por clase (de la matriz sumada)
# Columnas de entrada: 1 id, 2 dataset, 3 fold, 4 pos, 5 test_index, 6 y, 7 cheap, 8 top4, 9 cascade, 10 escalated

function lchoose(n, k,   i, s) { s = 0; for (i = 1; i <= k; i++) s += log(n - k + i) - log(i); return s }
function mcnemar_p(b, c,   n, k, i, s) {
  n = b + c; if (n == 0) return 1
  k = (b < c) ? b : c; s = 0
  for (i = 0; i <= k; i++) s += exp(lchoose(n, i) - n * log(2))
  s = 2 * s; return (s > 1) ? 1 : s
}
function tcrit(df) {  # t de Student bilateral al 95 %
  if (df == 1) return 12.7062; if (df == 2) return 4.3027; if (df == 3) return 3.1824
  if (df == 4) return 2.7764; if (df == 9) return 2.2622; return -1
}
NR == 1 { next }
{
  id = $1; ds = $2; y = $6; ch = $7; t4 = $8; ca = $9; es = $10
  if (!(id in N)) { order[++nc] = id; DS[id] = ds }
  N[id]++; okT[id] += (t4 == y); okC[id] += (ca == y); okB[id] += (ch == y)
  if (es) {
    E[id]++
    if (ch != y && t4 == y) R[id]++        # error de la etapa barata rescatado por Top-4
    if (ch == y && t4 != y) H[id]++        # acierto de la etapa barata perdido al escalar
  } else {
    if (ch != y && t4 == y) M[id]++        # error no detectado que Top-4 habria corregido (McNemar b)
    if (ch == y && t4 != y) S[id]++        # la etapa barata acierta donde Top-4 falla (McNemar c)
  }
  if (ch != y) { errB[id]++; if (es) errBesc[id]++ }
  if (!es) { noesc[id]++; noescOk[id] += (ch == y) }
  # matrices por condicion (para kappa) y sumadas por dataset
  cT[id, y, t4]++; cC[id, y, ca]++
  rowc[id, y]++; colT[id, t4]++; colC[id, ca]++
  if (!((ds, y) in seenk)) { seenk[ds, y] = 1; K[ds]++; cls[ds, K[ds]] = y }
  conf[ds, "top4", y, t4]++; conf[ds, "cascada", y, ca]++
}
function kappa(id, which, ds,   po, pe, i, cl, n, ok, col) {
  n = N[id]; ok = (which == "top4") ? okT[id] : okC[id]; po = ok / n; pe = 0
  for (i = 1; i <= K[ds]; i++) { cl = cls[ds, i]; col = (which == "top4") ? colT[id, cl] : colC[id, cl]; pe += rowc[id, cl] * col }
  pe /= n * n; return (pe < 1) ? (po - pe) / (1 - pe) : 1
}
END {
  f1 = OUTDIR "/e1_mcnemar_compuerta.csv"
  print "id,dataset,n,acc_top4,acc_cascada,kappa_top4,kappa_cascada,escaladas,frac_escalada,acc_barata_no_escaladas,errores_barata,errores_barata_escalados,recall_deteccion_errores,rescatados,perdidos_al_escalar,b_top4_acierta_cascada_falla,c_cascada_acierta_top4_falla,p_mcnemar_exacto,p_holm" > f1
  # Holm sobre las condiciones
  for (i = 1; i <= nc; i++) { id = order[i]; P[i] = mcnemar_p(M[id] + 0, S[id] + 0); idx[i] = i }
  for (i = 1; i <= nc; i++) for (j = i + 1; j <= nc; j++) if (P[idx[j]] < P[idx[i]]) { t = idx[i]; idx[i] = idx[j]; idx[j] = t }
  run = 0
  for (r = 1; r <= nc; r++) { v = (nc - r + 1) * P[idx[r]]; if (v > 1) v = 1; if (v < run) v = run; run = v; PH[idx[r]] = v }
  for (i = 1; i <= nc; i++) {
    id = order[i]; ds = DS[id]
    kt = kappa(id, "top4", ds); kc = kappa(id, "cascada", ds)
    accNo = (noesc[id] > 0) ? noescOk[id] / noesc[id] : -1
    rec = (errB[id] > 0) ? errBesc[id] / errB[id] : -1
    printf "%s,%s,%d,%.6f,%.6f,%.6f,%.6f,%d,%.6f,%.6f,%d,%d,%.6f,%d,%d,%d,%d,%.6g,%.6g\n", id, ds, N[id], okT[id]/N[id], okC[id]/N[id], kt, kc, E[id], E[id]/N[id], accNo, errB[id], errBesc[id], rec, R[id], H[id], M[id], S[id], P[i], PH[i] > f1
    # acumulados por dataset
    if (!(ds in nf)) dsorder[++nd] = ds
    nf[ds]++; at[ds, nf[ds]] = okT[id]/N[id]; ac[ds, nf[ds]] = okC[id]/N[id]; kT[ds, nf[ds]] = kt; kC[ds, nf[ds]] = kc
    sN[ds] += N[id]; sE[ds] += E[id]; sR[ds] += R[id]; sH[ds] += H[id]; sM[ds] += M[id]; sS[ds] += S[id]
    sErr[ds] += errB[id]; sErrEsc[ds] += errBesc[id]; sNo[ds] += noesc[id]; sNoOk[ds] += noescOk[id]
    if (PH[i] < 0.05) sig[ds]++
  }
  f2 = OUTDIR "/e1_resumen_por_dataset.csv"
  print "dataset,condiciones,llamadas,acc_top4_media,acc_top4_de,acc_top4_ic95_inf,acc_top4_ic95_sup,acc_cascada_media,acc_cascada_de,acc_cascada_ic95_inf,acc_cascada_ic95_sup,kappa_top4_media,kappa_cascada_media,frac_escalada,acc_barata_no_escaladas,recall_deteccion_errores,rescatados,perdidos_al_escalar,b_top4_acierta_cascada_falla,c_cascada_acierta_top4_falla,condiciones_holm_p_menor_005" > f2
  for (d = 1; d <= nd; d++) {
    ds = dsorder[d]; m = nf[ds]
    split("", tmp)
    for (w = 1; w <= 2; w++) {
      s = 0; for (i = 1; i <= m; i++) s += (w == 1 ? at[ds, i] : ac[ds, i]); mu = s / m
      v = 0; for (i = 1; i <= m; i++) v += ((w == 1 ? at[ds, i] : ac[ds, i]) - mu)^2
      sd = (m > 1) ? sqrt(v / (m - 1)) : -1; tc = tcrit(m - 1)
      lo = (m > 1 && tc > 0) ? mu - tc * sd / sqrt(m) : -1; hi = (m > 1 && tc > 0) ? mu + tc * sd / sqrt(m) : -1
      tmp[w, "mu"] = mu; tmp[w, "sd"] = sd; tmp[w, "lo"] = lo; tmp[w, "hi"] = hi
    }
    skt = 0; skc = 0; for (i = 1; i <= m; i++) { skt += kT[ds, i]; skc += kC[ds, i] }
    printf "%s,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%d,%d,%d,%d,%d\n", ds, m, sN[ds], tmp[1,"mu"], tmp[1,"sd"], tmp[1,"lo"], tmp[1,"hi"], tmp[2,"mu"], tmp[2,"sd"], tmp[2,"lo"], tmp[2,"hi"], skt/m, skc/m, sE[ds]/sN[ds], sNoOk[ds]/sNo[ds], sErrEsc[ds]/sErr[ds], sR[ds], sH[ds], sM[ds], sS[ds], sig[ds] + 0 > f2
  }
  f3 = OUTDIR "/e1_confusion.csv"; f4 = OUTDIR "/e1_por_clase.csv"
  print "dataset,metodo,clase_real,clase_predicha,conteo" > f3
  print "dataset,metodo,clase,soporte,precision,recall,f1" > f4
  split("top4 cascada", meth, " ")
  for (d = 1; d <= nd; d++) {
    ds = dsorder[d]
    for (w = 1; w <= 2; w++) {
      mt = meth[w]
      for (i = 1; i <= K[ds]; i++) { yi = cls[ds, i]; row = 0; for (j = 1; j <= K[ds]; j++) { yj = cls[ds, j]; v = conf[ds, mt, yi, yj] + 0; row += v; colsum[yj] += v; if (v > 0) print ds "," mt "," yi "," yj "," v > f3 }; rows[yi] = row }
      for (i = 1; i <= K[ds]; i++) {
        yi = cls[ds, i]; tp = conf[ds, mt, yi, yi] + 0
        pr = (colsum[yi] > 0) ? tp / colsum[yi] : 0; rc = (rows[yi] > 0) ? tp / rows[yi] : 0
        f = (pr + rc > 0) ? 2 * pr * rc / (pr + rc) : 0
        printf "%s,%s,%s,%d,%.6f,%.6f,%.6f\n", ds, mt, yi, rows[yi], pr, rc, f > f4
      }
      split("", colsum); split("", rows)
    }
  }
}
