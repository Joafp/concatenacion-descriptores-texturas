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
