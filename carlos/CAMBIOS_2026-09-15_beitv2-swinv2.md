# Cambios del 15 de septiembre de 2026

**Para:** Joaquín Delgado
**De:** Carlos Ayala
**Objeto:** prueba de BEiTv2 y SwinV2 en KTH-TIPS2-b (para ver si competíamos con Electronics 2025) — resultado: no

---

## 0. Por qué lo probé

El paper de Neshov et al. (Electronics 2025, el que usa KTH-TIPS2-b/FMD/GTOS-Mobile/DTD/Soil) reporta su mejor resultado con **BEiTv2**, y usa **SwinV2** como una de las arquitecturas comparadas. Quise ver si agregando esos dos backbones a nuestro pool de descriptores nos acercábamos a sus números.

## 1. Qué se hizo

Agregué `beitv2_base` (`beitv2_base_patch16_224.in1k_ft_in22k_in1k`, 768-d) y
`swinv2_base` (`swinv2_base_window8_256.ms_in1k`, 1024-d) como dos descriptores
más — mismo mecanismo que los otros 20 (timm, pooled feature, frozen), sin
tocar el registro `CANONICAL_EXTRACTORS` que usan Outex13/Soil/VisTex. Extraje
los 4.752 embeddings de KTH-TIPS2-b para ambos y corrí el protocolo
confirmatorio completo (4 splits oficiales × SVM/ResMLP) con el pool de 22
descriptores, en una carpeta separada (`results/extensions/kth_tips2b/beitv2_swinv2/`)
para no pisar los resultados de 20 descriptores que ya tenés.

## 2. Resultado: no mejora nada

| Método | SVM (20 → 22) | ResMLP (20 → 22) |
|---|---:|---:|
| Concatenación completa | 0.870 → 0.868 | 0.854 → 0.858 |
| GFS | 0.810 → 0.810 | 0.824 → 0.817 |
| Mejor individual | 0.798 → 0.798 | 0.807 → 0.807 |

Todas las diferencias caen dentro del ruido entre particiones (los std ya
reportados en `nested_summary.csv` son de ±0.03 a ±0.05). GFS **nunca**
seleccionó BEiTv2 en ninguna de las 8 condiciones; SwinV2 reemplazó al Swin-T
viejo en 1 de 8 condiciones (ResMLP) sin cambiar el resultado final. `gfs_vs_full_concat`
sigue perdiendo 0/4 en ambos clasificadores, igual que con 20 descriptores
(`beitv2_swinv2/paired_comparisons.csv`).

## 3. Por qué no mejora (la explicación que le doy al profe)

Electronics 2025 no gana por usar BEiTv2 como "un descriptor más" — su método
**fusiona features de 4 capas internas de un único backbone** (early, dos
intermedias, final) + un MLP entrenable encima de esa fusión. Nosotros
extraemos **un solo vector pooled por backbone, congelado**, y lo sumamos al
pool de 20+ para que GFS decida si lo usa. Son mecanismos distintos:

- Su ventaja viene de **cómo combinan las capas de un mismo modelo**
  (información de bajo, medio y alto nivel del mismo backbone), no de que el
  backbone en sí sea mejor.
- Nuestro protocolo ya está cerca de su techo con los 20 descriptores
  actuales (DINOv2, ViT-B, Swin-T, etc. ya cubren bien el espacio de
  representaciones transformer). Agregar 2 backbones más fuertes en la MISMA
  arquitectura de fusión (concatenación de vector único + GFS) no destapa
  nada nuevo porque el cuello de botella no es "qué modelo", es "qué
  información dentro del modelo" — y ahí es donde ellos innovan con la
  fusión multinivel.

**Conclusión:** no tiene sentido seguir agregando backbones nuevos al pool
esperando igualar Electronics 2025 con este método. Si quisiéramos competir
de verdad en ese eje, habría que adoptar su idea de fusión multinivel (no es
poco trabajo), no simplemente sumar otro descriptor.

## 4. Archivos

- `src/01_extract_features.py`: 2 entradas nuevas en `EXTRACTORS`
  (`beitv2_base`, `swinv2_base`), aisladas del resto — no afecta a ningún
  otro dataset.
- `src/run_confirmatory_nested.py`: agregué esas 2 claves al dict `FAMILIES`
  (familia `transformer`), adición pura, no toca las existentes.
- `results/extensions/kth_tips2b/beitv2_swinv2/`: resultados completos de
  esta variante (no reemplaza los resultados de 20 descriptores).
