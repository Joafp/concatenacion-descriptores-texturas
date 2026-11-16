# Extrae de los 27 result.json de E1 una fila por condicion (ruta elegida, ruta ResNet-50,
# Top-4 directo, control aleatorio y etapa barata sola en test).
# Uso, desde la raiz del repo: powershell -File carlos/analisis_paper/e1_extraer.ps1
$root = (Get-Location).Path
$rows = Import-Csv "$root\results\analysis\top4_fixed_kth_completion_audit_20261115_v1\e1_conditions.csv"
$out = foreach ($r in $rows) {
  $j = Get-Content -Raw "$root\$($r.source_folder)\result.json" | ConvertFrom-Json
  $sel = $j.selected_cascade; $rn = $j.resnet50_route
  $cheapAcc = if ($sel.cheap) { $j.metrics.($sel.cheap).accuracy } else { [double]::NaN }
  [pscustomobject]@{
    id=$j.id; dataset=$j.dataset; blocks=($j.top4_blocks -join '+')
    route=$sel.route; cheap=$sel.cheap; q=$sel.q; frac=$sel.request_fraction
    sel_acc=$sel.metrics.accuracy; sel_f1=$sel.metrics.macro_f1; sel_ms=$sel.projected_component_ms
    dir_acc=$j.metrics.top4_direct.accuracy; dir_f1=$j.metrics.top4_direct.macro_f1; dir_ms=$j.direct_projected_component_ms
    rn_route=$rn.route; rn_q=$rn.q; rn_frac=$rn.request_fraction; rn_acc=$rn.metrics.accuracy; rn_ms=$rn.projected_component_ms
    rand_acc=$j.random_selected_route.accuracy.mean; rand_sd=$j.random_selected_route.accuracy.std
    cheap_acc=$cheapAcc; resnet_alone=$j.metrics.resnet50.accuracy
  }
}
$culture = [System.Globalization.CultureInfo]::InvariantCulture
$lines = @(($out[0].psobject.Properties.Name) -join ',')
foreach ($o in $out) {
  $lines += (($o.psobject.Properties.Value | ForEach-Object {
    if ($_ -is [double]) { $_.ToString('R', $culture) } else { "$_" } }) -join ',')
}
$lines | Set-Content -Encoding ascii "$root\carlos\analisis_paper\e1_condiciones.csv"
