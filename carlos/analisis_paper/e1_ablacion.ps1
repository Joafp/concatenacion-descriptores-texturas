# Extrae de los 27 result.json de E1 la accuracy y la macro-F1 de cada variante de uso de Top-4:
# etapa barata sola, escalamiento aleatorio de la misma cantidad, cascada con ResNet-50,
# cascada con la etapa barata elegida y Top-4 directo. Sin ajustes ni predicciones nuevas.
# Uso, desde la raiz del repo: powershell -File carlos/analisis_paper/e1_ablacion.ps1
$root = (Get-Location).Path
$rows = Import-Csv "$root\results\analysis\top4_fixed_kth_completion_audit_20261115_v1\e1_conditions.csv"
$culture = [System.Globalization.CultureInfo]::InvariantCulture
$lines = @('id,dataset,cheap,base_acc,base_f1,rand_acc,rand_f1,rn_acc,rn_f1,cas_acc,cas_f1,dir_acc,dir_f1')
foreach ($r in $rows) {
  $j = Get-Content -Raw "$root\$($r.source_folder)\result.json" | ConvertFrom-Json
  $sel = $j.selected_cascade; $rn = $j.resnet50_route; $cheap = $sel.cheap
  $vals = @(
    $j.metrics.$cheap.accuracy, $j.metrics.$cheap.macro_f1,
    $j.random_selected_route.accuracy.mean, $j.random_selected_route.macro_f1.mean,
    $rn.metrics.accuracy, $rn.metrics.macro_f1,
    $sel.metrics.accuracy, $sel.metrics.macro_f1,
    $j.metrics.top4_direct.accuracy, $j.metrics.top4_direct.macro_f1
  ) | ForEach-Object { ([double]$_).ToString('R', $culture) }
  $lines += (@($j.id, $j.dataset, $cheap) + $vals) -join ','
}
$lines | Set-Content -Encoding ascii "$root\carlos\analisis_paper\e1_ablacion.csv"
