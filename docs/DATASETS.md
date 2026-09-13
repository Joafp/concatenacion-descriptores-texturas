# Datasets

Los píxeles **no** se versionan. Colocá las fuentes bajo `data/` (ignorado por Git)
siguiendo la disposición que usan los scripts de extracción y los manifiestos en
`results/confirmatory/sample_manifests/`.

## Bloque principal

| Dataset | Muestras | Clases | Dónde obtenerlo | Notas de protocolo |
|---|---:|---:|---|---|
| DTD | 5.640 | 47 | [robots.ox.ac.uk/~vgg/data/dtd](https://www.robots.ox.ac.uk/~vgg/data/dtd/) | 10 splits oficiales |
| FMD | 1.000 | 10 | [people.csail.mit.edu/celiu/CVPR2010](https://people.csail.mit.edu/celiu/CVPR2010/FMD/) | 3 semillas × 5 folds agrupados (protocolo del estudio) |
| CUReT | 5.612 | 61 | Subconjunto Oxford 61×92 vistas en escala de grises | Dos mitades complementarias de 46 condiciones |

## Extensiones

| Dataset | Muestras | Clases | Notas |
|---|---:|---:|---|
| Outex_TC_00013 (color) | 1.360 | 68 | Partición oficial 680/680. Pin del ZIP usado en el estudio: ver `results/confirmatory/FINAL_AUDIT.md` |
| Soil Original | 1.140 | 7 | Suplementario |
| VisTex Reference-12 | 140 | 12 | Suplementario; manifiesto en `results/confirmatory/sample_manifests/` |
| KTH-TIPS2-b | 4.752 | 11 | Protocolo oficial de 4 folds fijos (ver abajo). Reincorporado para comparar contra Neshov et al. 2025 (Electronics), que usa el mismo dataset y protocolo |

### KTH-TIPS2-b

Fuente: [www.csc.kth.se/cvap/databases/kth-tips](https://www.csc.kth.se/cvap/databases/kth-tips/) (KTH CVAP,
Mallikarjuna et al. 2006). Descargar la variante **KTH-TIPS2-b** (108 imágenes
por muestra, no la variante -a con 72).

Disposición esperada tras descomprimir:

```text
data/KTH-TIPS2-b/<material>/sample_<a|b|c|d>/*.png
```

11 materiales x 4 muestras físicas x 108 imágenes = 4.752 imágenes. Este
dataset estuvo en una fase exploratoria anterior del proyecto y fue excluido
del protocolo confirmatorio vigente por estar saturado (F1 ≈ 1.0); ver
`results/confirmatory/sample_manifests/ORDER_AND_SPLIT_PROTOCOL.md`.

**Protocolo oficial** (Caputo, Hayman y Mallikarjuna, ICCV 2005): entrenar con
las imágenes de **una** muestra física, testear con las **otras tres**,
rotando sobre las 4 muestras (a, b, c, d) → 4 folds fijos, sin split de
validación oficial.

Pasos para generar el manifiesto y correr el protocolo (una vez descargado el
dataset en la máquina con GPU):

```bash
# 1. Construir el manifiesto (verifica conteos e integridad, falla si algo no calza)
python results/confirmatory/recovery/kth_tips2b/build_kth_tips2b_manifest.py \
  --root data/KTH-TIPS2-b

# 2. Extraer los 20 descriptores canónicos
.venv-confirmatory/bin/python src/kth_tips2b_extension.py extract --extractor all

# 3. Auditar (gate obligatorio; también copia el manifiesto verificado a
#    results/extensions/kth_tips2b/sample_manifests/KTHTIPS2b.csv, que es
#    donde run_confirmatory_nested.py lo espera)
.venv-confirmatory/bin/python src/kth_tips2b_extension.py audit

# 4. Correr el protocolo confirmatorio (4 folds oficiales x 2 clasificadores)
bash scripts/run_extension_protocol.sh KTHTIPS2b

# 5. Análisis consolidado
.venv-confirmatory/bin/python src/analyze_confirmatory_results.py \
  --output results/extensions/kth_tips2b
```

## Disposición esperada

Tras descargar y descomprimir, los scripts confirmanorios buscan árboles bajo
`data/confirmatory_sources/<Dataset>/` (ver `results/confirmatory/RECOVERY_REQUIREMENTS.md`
y `ORDER_AND_SPLIT_PROTOCOL.md`).

Orden de filas de embeddings: siempre el de los CSV en
`results/confirmatory/sample_manifests/`.

## Embeddings

Tras tener las imágenes, regenerá los 20 bloques con los extractores de `src/`
(por ejemplo `src/01_extract_features.py` y los scripts de reextracción en
`experiments/`). Los arrays van a:

- `embeddings_confirmatory/<Dataset>/` — bloque DTD / FMD / CUReT
- `embeddings_extensions/<Dataset>/` — Outex, Soil, VisTex

Esas carpetas también están ignoradas por Git (~800 MB+). Si compartís un mirror
interno de embeddings, documentá la URL aquí o en el README del remoto.
