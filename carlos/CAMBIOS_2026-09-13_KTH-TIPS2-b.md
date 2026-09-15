# Cambios del 13 de septiembre de 2026

**Para:** Joaquín Delgado
**De:** Carlos Ayala
**Objeto:** reincorporación de KTH-TIPS2-b al protocolo confirmatorio

---

## 0. Por qué esto no está todavía en GitHub

Corrí todo esto localmente y armé el commit (`6c506c0`), pero mi usuario
(`CarlosAyala00`) no tiene permiso de push sobre el repo. Necesito que me
agregues como colaborador, o te mando el patch/fork. Mientras tanto, este
`.md` resume todo lo que corrí para que puedas revisarlo sin esperar al
merge.

---

## 1. Qué se hizo y por qué

KTH-TIPS2-b estaba descartado del protocolo confirmatorio vigente (v3) por
"estar saturado" (`04_resultados.md`: *"Dataset saturado (no incluido en
v3)"*). Ese diagnóstico salía del pipeline exploratorio viejo, que evaluaba
con un 5-fold aleatorio simple — y ese split dejaba imágenes de la **misma
muestra física** en train y test, lo cual infla el resultado a F1≈0.999 sin
que signifique nada.

Lo corrí de nuevo con el **protocolo oficial** (Caputo, Hayman y Mallikarjuna,
ICCV 2005): entrenar con **una** muestra física de cada material, testear con
las **otras tres**, rotando → 4 folds fijos, sin fuga entre train/test.
Con ese protocolo real, **KTH-TIPS2-b no está saturado** (F1 ≈ 0.80–0.87), así
que lo reincorporé como dataset de extensión nuevo, con el mismo patrón que
Outex13/Soil/VisTex (manifiesto verificado + auditoría + nested CV).

Dataset: 4.752 imágenes, 11 materiales × 4 muestras × 108 imágenes, descargado
de la fuente oficial (KTH CVAP). Se extrajeron los 20 descriptores canónicos
del estudio.

## 2. Resultados — protocolo base (20 descriptores)

4 splits oficiales × {SVM, ResMLP}, macro-F1 promedio ± std:

| Método | SVM | ResMLP |
|---|---:|---:|
| Mejor individual | 0.798 ± 0.033 | 0.807 ± 0.054 |
| GFS | 0.810 ± 0.039 | 0.824 ± 0.029 |
| **Concatenación completa** | **0.870 ± 0.047** | **0.854 ± 0.049** |
| Mejor familia homogénea (transformer) | 0.816 ± 0.047 | 0.841 ± 0.032 |

**Diferencia importante con DTD/FMD/CUReT:** ahí GFS empata o supera a la
concatenación completa. Acá **pierde en las 4 particiones con ambos
clasificadores** (`gfs_vs_full_concat`: 0/4 victorias, ver
`results/extensions/kth_tips2b/paired_comparisons.csv`). El extractor más
elegido por GFS es `vit_b16` (75% de las particiones), después `swin_t` /
`dinov2` / `resnet101`.

## 3. Resultados — 21° descriptor (RGB Pixel N-gram)

Corrido igual que para DTD/FMD/CUReT/Outex13
(`scripts/run_rgb_ngram_multibase.sh KTHTIPS2b`). El n-grama **no aporta
nada**: GFS no lo seleccionó en ninguna de las 8 condiciones, y la
concatenación completa con 21 bloques da prácticamente lo mismo que con 20
(SVM 0.870→0.862, ResMLP 0.854→0.855). Ver
`results/extensions/kth_tips2b/ngram21/`.

## 4. Control Top-k

También corrí el control de "los k descriptores individualmente más fuertes"
(mismo k que GFS) — lo necesitábamos para el input de las pruebas SCI2S.
Está en `results/extensions/kth_tips2b/topk_individual_control/`.

## 5. Sobre las pruebas SCI2S (Friedman/CONTROLTEST/MULTIPLETEST)

**Todavía no las corrí.** `scripts/build_nonparametric_analysis.py` (el que
arma el CSV de entrada para las pruebas Java) tiene hardcodeado que la
"familia homogénea" ganadora es siempre `self_supervised` — cierto para
DTD/FMD/CUReT/Outex13, pero en KTH-TIPS2-b gana `transformer`. Ya armé una
versión generalizada (`scripts/build_nonparametric_analysis_kth.py`) que
resuelve la columna "Homogénea" dinámicamente por dataset en vez de
hardcodearla, sin tocar el script original ni los números ya publicados.

Faltan más datasets por agregar antes de correr la prueba estadística final
(así lo pidió Carlos, para no rehacerla varias veces) — la corremos una sola
vez cuando estén todos.

## 6. Archivos nuevos/modificados

**Código**
- `src/kth_tips2b_extension.py` — extracción/auditoría (espeja
  `vistex_reference12_extension.py`)
- `results/confirmatory/recovery/kth_tips2b/build_kth_tips2b_manifest.py` —
  construye y valida el manifiesto desde el archivo oficial descargado
- `results/confirmatory/recovery/kth_tips2b/chunked_extract.py` — extracción
  por tandas (necesario porque mi WSL se reiniciaba solo cada ~55 min; con
  esto un corte pierde ~7 min en vez de una pasada completa de ~80 min)
- `scripts/run_extension_protocol.sh`, `run_rgb_ngram_multibase.sh`,
  `run_topk_individual_control.sh` — caso `KTHTIPS2b` agregado
- `scripts/build_nonparametric_analysis_kth.py` — generaliza la columna
  "Homogénea" (ver punto 5)
- `experiments/test_kth_tips2b_manifest.py` — 5 tests sintéticos del
  manifiesto (no necesitan el dataset real, corren con `pytest experiments/`)

**Docs**
- `docs/DATASETS.md`, `results/confirmatory/sample_manifests/ORDER_AND_SPLIT_PROTOCOL.md`
  — documentan la fuente oficial, el layout esperado y el protocolo de 4 folds

**Resultados**
- `results/extensions/kth_tips2b/` completo (base + ngram21 + topk_individual_control)

**Fix de infraestructura (no relacionado a KTH-TIPS2-b directamente)**
- 25 scripts `.sh` tenían CRLF (checkout en Windows) y bash los rechazaba
  (`set -o pipefail` fallaba). Agregué `.gitattributes` para forzar LF.

## 7. Para reproducir

```bash
# 1. Descargar KTH-TIPS2-b (variante -b, 108 img/muestra) de
#    csc.kth.se/cvap/databases/kth-tips en data/KTH-TIPS2-b/<material>/sample_<a-d>/*.png

# 2-6: ver docs/DATASETS.md sección "KTH-TIPS2-b" (comandos exactos paso a paso)
```
