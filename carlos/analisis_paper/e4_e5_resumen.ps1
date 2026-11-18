# Resume E4 (activacion por margen con ResMLP, 27 condiciones) y E5 (Top-4 + N-gramas, 47 condiciones)
# a partir de las auditorias de Joaquin. Medias por dataset y media equiponderada de seis datasets;
# no inferioridad de E4 con la misma regla que E1 (t de Student, 5 g.l.). Sin ajustes ni predicciones nuevas.
# Uso, desde la raiz del repo: powershell -File carlos/analisis_paper/e4_e5_resumen.ps1
$root = (Get-Location).Path
$inv = [System.Globalization.CultureInfo]::InvariantCulture
$out = @()

$j = Get-Content -Raw "$root\results\analysis\e4_resmlp_complete_audit_20261116_v1\summary.json" | ConvertFrom-Json
$out += '== E4: ResMLP con los bloques Top-4 de SVM (dataset,cond,acc_directo,acc_margen,dif,f1_directo,f1_margen,escaladas)'
$rows = foreach ($g in ($j.cases | Group-Object dataset)) {
  [pscustomobject]@{ ds = $g.Name; n = $g.Count
    da = ($g.Group | ForEach-Object { $_.direct.accuracy } | Measure-Object -Average).Average
    sa = ($g.Group | ForEach-Object { $_.selected.accuracy } | Measure-Object -Average).Average
    df = ($g.Group | ForEach-Object { $_.direct.macro_f1 } | Measure-Object -Average).Average
    sf = ($g.Group | ForEach-Object { $_.selected.macro_f1 } | Measure-Object -Average).Average
    rf = ($g.Group | ForEach-Object { $_.request_fraction } | Measure-Object -Average).Average }
}
foreach ($r in $rows) { $out += [string]::Format($inv, '{0},{1},{2:F4},{3:F4},{4:+0.0000;-0.0000},{5:F4},{6:F4},{7:F3}', $r.ds, $r.n, $r.da, $r.sa, $r.sa - $r.da, $r.df, $r.sf, $r.rf) }
$d = $rows | ForEach-Object { $_.sa - $_.da }
$m = ($d | Measure-Object -Average).Average
$sd = [math]::Sqrt((($d | ForEach-Object { ($_ - $m) * ($_ - $m) }) | Measure-Object -Sum).Sum / 5)
$se = $sd / [math]::Sqrt(6)
$c = $j.cases | ForEach-Object { $_.selected.accuracy - $_.direct.accuracy }
$out += [string]::Format($inv, 'Media: acc directo {0:F4}, margen {1:F4}; F1 directo {2:F4}, margen {3:F4}; escaladas {4:F4} (condicion {5:F3} a {6:F3})',
  ($rows.da | Measure-Object -Average).Average, ($rows.sa | Measure-Object -Average).Average,
  ($rows.df | Measure-Object -Average).Average, ($rows.sf | Measure-Object -Average).Average,
  ($rows.rf | Measure-Object -Average).Average, ($j.cases.request_fraction | Measure-Object -Minimum).Minimum,
  ($j.cases.request_fraction | Measure-Object -Maximum).Maximum)
$out += [string]::Format($inv, 'Diferencia media {0:+0.00000;-0.00000}; DE {1:F5}; cota inferior unilateral 95 % (t5 = 2,01505) {2:F5}; t frente a -0,01 = {3:F2}; frente a -0,005 = {4:F2}',
  $m, $sd, $m - 2.01505 * $se, ($m + 0.01) / $se, ($m + 0.005) / $se)
$out += [string]::Format($inv, 'Por condicion: {0:+0.0000;-0.0000} a {1:+0.0000;-0.0000}; mejor {2}, igual {3}, peor {4}',
  ($c | Measure-Object -Minimum).Minimum, ($c | Measure-Object -Maximum).Maximum,
  ($c | Where-Object { $_ -gt 1e-12 }).Count, ($c | Where-Object { [math]::Abs($_) -le 1e-12 }).Count, ($c | Where-Object { $_ -lt -1e-12 }).Count)

$e5 = Get-Content -Raw "$root\results\analysis\e5_secondary_complete_20261116_v1\summary.json" | ConvertFrom-Json
$out += '== E5: Top-4 frente a Top-4 + N-gramas, SVM, 47 condiciones (dataset,acc_top4,acc_top4ng,dif,f1_top4,f1_top4ng)'
$sa = 0; $sb = 0; $fa = 0; $fb = 0; $n = 0
foreach ($p in $e5.datasets.PSObject.Properties) { $v = $p.Value; $n++
  $sa += $v.top4.accuracy; $sb += $v.top4_plus_ngram.accuracy; $fa += $v.top4.macro_f1; $fb += $v.top4_plus_ngram.macro_f1
  $out += [string]::Format($inv, '{0},{1:F4},{2:F4},{3:+0.0000;-0.0000},{4:F4},{5:F4}', $p.Name, $v.top4.accuracy, $v.top4_plus_ngram.accuracy, $v.top4_plus_ngram.accuracy - $v.top4.accuracy, $v.top4.macro_f1, $v.top4_plus_ngram.macro_f1) }
$out += [string]::Format($inv, 'Media: acc {0:F4} -> {1:F4} ({2:+0.0000;-0.0000}); F1 {3:F4} -> {4:F4}', $sa / $n, $sb / $n, ($sb - $sa) / $n, $fa / $n, $fb / $n)
$out | Set-Content -Encoding utf8 "$root\carlos\analisis_paper\e4_e5_resumen.txt"
$out
