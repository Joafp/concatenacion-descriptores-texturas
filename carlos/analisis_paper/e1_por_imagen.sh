#!/usr/bin/env bash
# Extrae, para las 27 condiciones de E1, una fila por imagen de prueba:
#   id, dataset, fold, posicion, indice, clase real, prediccion de la etapa barata,
#   de Top-4 directo, de la cascada y si la cascada escalo (calculo Top-4).
# Fuente: scores_predictions.json.gz de cada condicion (predicciones ya guardadas).
# No ajusta modelos ni recalcula rasgos.
# Uso, desde la raiz del repo: bash carlos/analisis_paper/e1_por_imagen.sh
set -euo pipefail
LIST=results/analysis/top4_fixed_kth_completion_audit_20261115_v1/e1_conditions.csv
OUT=carlos/analisis_paper/e1_por_imagen.csv
echo "id,dataset,fold,pos,test_index,y,cheap,top4,cascade,escalated" > "$OUT"
awk -F, 'NR==1{for(i=1;i<=NF;i++){if($i=="id")a=i;if($i=="dataset")b=i;if($i=="outer_fold")c=i;if($i=="source_folder")d=i;if($i=="cheap")e=i}}
         NR>1{print $a","$b","$c","$d","$e}' "$LIST" |
while IFS=, read -r id ds fold src cheap; do
  json=$(zcat "$src/scores_predictions.json.gz")
  arr() { grep -o "\"$1\":\[[^]]*\]" <<<"$2" | head -1 | sed -E 's/^[^[]*\[//; s/\]$//'; }
  preds=$(grep -o '"predictions":{[^}]*}' <<<"$json")
  masks=$(grep -o '"request_masks":{[^}]*}' <<<"$json")
  paste -d, \
    <(arr test_indices "$json" | tr ',' '\n') \
    <(arr y_true "$json" | tr ',' '\n') \
    <(arr "$cheap" "$preds" | tr ',' '\n') \
    <(arr top4_direct "$preds" | tr ',' '\n') \
    <(arr selected_cascade "$preds" | tr ',' '\n') \
    <(arr selected_cascade "$masks" | tr ',' '\n') |
  awk -F, -v id="$id" -v ds="$ds" -v f="$fold" '{print id","ds","f","NR-1","$1","$2","$3","$4","$5","($6=="true"?1:0)}' >> "$OUT"
done
echo "filas: $(($(wc -l < "$OUT") - 1))"
