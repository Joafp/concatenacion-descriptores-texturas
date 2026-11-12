# TiO multiescala 2023: auditoría de receta y código

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent; pdf.
- Origin Mode: auditoría técnica de viabilidad, no benchmark.
- Origin Date: 2026-11-02, 14:01–14:07 UTC.
- Verification Status: ANALYZED; fuente y código parcialmente inspeccionados.
- Version Label: multiscale2023_readiness_v1.

## Fuente y lectura

PDF local docs/referencias/applsci-13-01291.pdf, DOI10.3390/app13031291,
SHA256fbe4602f27b94cc863551496a8172f3440a9d22d97ac103dd9ebf2828cd4c743.
Preflight estructural PASS17páginas sinwarnings; sidecar guardado de stdout.
Texto derivado multiscale2023.txt. Se leyeron secciones2.2,3,4/4.1 y
disponibilidad; páginas6/7 renderizadas e inspeccionadas (Figura2/Algoritmo1).
No declaración de lectura humana completa ni reproducción de porcentajes.

La receta usa pirámide gaussiana L0original,L1,L2; separación RGB, BiT14,
Haralick13,GLCM6 yentropía/información. Concatenación TiO315, minmax ajustado
solo en train,clasificador LDA o variantes HistoB/LightB/CatBoost. No basta
usar nuestroGLCMhistórico o concatenar descriptores del pool de22.

Ambigüedades por resolver antes de ejecución:

- Abstract dice Gaussian–Laplacian; método/Algoritmo1 especifica gaussiana.
  No sustituir niveles por residuos laplacianos silenciosamente.
- Bloques declarados126+117+54+18=315; la descripción también llama
  tridimensional al bloque entropía/multiinformación. Tres valores porcada
  una de nueve vistas serían27, no18. Hace falta aclarar definición/orden.
- Grayscale paraGLCM/Haralick tras separar canales no fija discretización,
  distancias/ángulos/agregación ni bordes; filtrosGaussian ytratamiento de
  intensidad/bins deben quedar explícitos. BiT presenta casos de filtrado.
- Parámetros deLDA/boosters ypresupuesto de selección no son una receta
  completa verificable en los pasajes inspeccionados. No tomar defaults por
  hiperparámetros delpaper ni aplicar tuning sobre test.
- KTH-TIPS original810imágenes yOutexTC00011-r960 no son KTHTIPS2b ni nuestro
  OutexTC00013. Cualquier panel común sería ADAPTACIÓN declarada.

## Repositorio primario referenciado por el paper

https://github.com/stevetmat/BioInspiredFDesc

Consulta de árbol API sin clonar ni instalar; treeSHA
a1749b45e8ef07bda8056453f0ca8e0ebfcc3cbb. La API expone un árbol, no se
declara que este SHA sea commit ni que reproduzca el estado de2023.
Lecturasraw fijadas a ese identificador respondieron correctamente.
Licencia raízMIT ysrc/LICENSEBSD con obligación de conservar avisos.
No código externo ejecutado, paquetes instalados ni pesos/datasets descargados.

Árbol observado: src/BiT.py11123bytes,ClassBit.py25024,Channel_Split.py10853,
Biodiversity.py4870,Taxonomic.py6163; main.py383. CMIG/README.md248 y
EBiT/README.md216 son avisos, no implementaciones completas. Incluye también
resources/test.png33214 ypyc históricos no ejecutados/descargados.

Inspección deBiT.py confirmó funciones biodiversity ytaxonomy con7medidas
cada una. ClassBit/Channel_Split tienen selección deunsharp/crimmins y
normalización yconcatenación RGB/R/G/B: no es elpipelineTiO315. No se
encontró un fichero deTiO/pirámide/Haralick/GLCM/clasificador en elárbol
inspeccionado; esto no prueba ausencia de versiones externas uotras ramas.
ElREADME remite alBiT2021 DOI10.1016/j.patcog.2021.108382, no ofrece por sí
solo validación de fidelidad deTiO2023.

Fuentes pequeñas consultadas, no vendorizadas:

- https://api.github.com/repos/stevetmat/BioInspiredFDesc/git/trees/main?recursive=1
- https://github.com/stevetmat/BioInspiredFDesc/blob/main/README.md
- https://github.com/stevetmat/BioInspiredFDesc/blob/main/src/BiT.py
- https://github.com/stevetmat/BioInspiredFDesc/blob/main/src/ClassBit.py
- https://github.com/stevetmat/BioInspiredFDesc/blob/main/src/Channel_Split.py
- https://github.com/stevetmat/BioInspiredFDesc/blob/main/src/LICENSE

Estado: AUTHOR_LINKED_COMPONENT_CODE_IDENTIFIED_FULL_TIO_RECIPE_PENDING.
Cero modelos completos entrenados y cero llamadas online TiO. Siguiente
acción: verificar versión/artefactos delpipeline o auditar otro paper viable;
no presentar el componenteBiT como método completo, no improvisar dimensiones.
