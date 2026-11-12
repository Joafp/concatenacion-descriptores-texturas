# Reproducción de cifras publicadas: evidencia y brechas

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: auditoría de fidelidad de experimentos publicados.
- Origin Date: 2026-11-02, America/Asuncion.
- Verification Status: documentación primaria consultada; ninguna cifra declarada reproducida.

## Regla de comparación

El panel común propio y los comparadores adaptados miden macro-F1 y accuracy
desde predicciones completas y tiempos por la misma llamada. Los resultados
publicados que siguen son **accuracy**; no se deben comparar numéricamente con
macro-F1. Las particiones ya observadas y la experimentación posterior forman
análisis exploratorio. Reproducir el protocolo fuente es otra evaluación.

## HyTexNet, KTH-TIPS2b

- Fuente primaria: Gupta, Mishra y Shrivastava, DOI
  `10.1016/j.knosys.2026.115482`, PDF local
  `docs/referencias/1-s2.0-S095070512600225X-main.pdf`, SHA256
  `28169c0ec5d14654fffd347282c18caee99026bdf856149ffb3a46ae3f845e53`.
- El artículo informa **99,79 % de accuracy** en KTH-TIPS2b. En la descripción
  de su evaluación, dos poses, tres iluminaciones y seis escalas forman un
  tercio del dataset para entrenar; el resto se emplea en test. Falta verificar
  los identificadores exactos y la implementación de esa partición.
- Nuestra adaptación usa cuatro particiones que separan muestras físicas:
  tres muestras para fit y una para test. No es el mismo split. La fuente
  describe por un lado ausencia de fine-tuning y por otro entrenamiento
  end-to-end; nuestra elección fue congelar DenseNet. También hay parámetros
  locales de transformación/entrenamiento y checkpoint exacto no verificado.
- Acción: documentar el split fuente exacto y resolver la receta con evidencia
  verificable. Si no se consigue, rotular cualquier reconstrucción como
  aproximación y conservar ambos resultados, incluso si difieren.

## 6LBP+dCellNN, KTH-TIPS2b

- Fuente primaria: Chang, Ji y Zhu, DOI `10.1016/j.eswa.2023.122100`, PDF local
  `docs/referencias/1-s2.0-S0957417423026027-main.pdf`.
- El artículo informa **91,29 % de accuracy** para 6LBP+dCellNNs en KTH-TIPS2b.
  Emplea entrenamiento con dos poses, tres iluminaciones y seis escalas: un
  tercio de las imágenes. OTC12 no equivale a nuestro Outex-13. El paper no
  evalúa FMD entre sus cuatro datasets informados.
- Hay una discrepancia entre la descripción de ese protocolo y la fuente que
  cita para él. La tabla de datasets de Liu et al. (2016),
  `https://www.ee.cuhk.edu.hk/~xgwang/papers/liuLFGWPtip16.pdf`, indica para
  KTH-TIPS2b 3564 imágenes de entrenamiento y 1188 de test (3/4 frente a 1/4),
  mientras CellNN e HyTexNet describen 1/3 de imágenes para entrenamiento.
  Se conserva como contradicción documental: citar a Liu no resuelve por sí
  solo qué partición concreta usaron CellNN o HyTexNet ni autoriza homologar
  resultados numéricos publicados bajo repartos diferentes.
- Tenemos implementación y checkpoint compatibles de los autores, pero la
  evaluación común usa el split 3 muestras físicas / 1 y configuración local
  de MLP; sus resultados no reproducen automáticamente el protocolo fuente.
- Acción: verificar desde los archivos de autores y la fuente los identificadores
  precisos de pose, iluminación y escala y los parámetros del clasificador. Un
  split de imágenes que comparta muestras físicas entre train/test debe marcarse
  expresamente y no sustituye nuestra evaluación por muestras físicas.
- La guía primaria de KTH `https://www.csc.kth.se/cvap/databases/kth-tips/kth-tips2.pdf`
  identifica escalas 2–10 e imágenes 1–12: 1–3, 4–6 y 7–9 corresponden a tres
  poses con tres iluminaciones; 10–12 son luz ambiente. Esa guía aclara el
  significado de los nombres pero no indica cuáles dos poses y seis escalas
  eligieron los autores de CellNN o HyTexNet.
- Se consultó el árbol público del commit de autores
  `299502cbb2243ecb78018110236871f261aa92b2`: ofrece `main_otc12.py`, pero
  no contiene un runner KTH específico en ese árbol. Esto no demuestra que
  no exista código KTH en otra versión o ubicación.

## Neshov BEiTv2, FMD

- Fuente primaria: Neshov et al., DOI `10.3390/electronics14234779`, PDF local
  `docs/referencias/electronics-14-04779 (1).pdf`, SHA256
  `e9d5eb4c004e6ae17e615a0043dfdee4ef76122931848d28fd7ea49992fbec67`.
- El artículo informa **96,7 % de accuracy** en FMD. Describe diez repeticiones
  de 10-fold CV, semilla base 42 multiplicada por el índice de repetición,
  batch de entrenamiento 32, 100 épocas, Adam, learning rate 0,001 y weight
  decay 0,0001. Falta establecer con código fuente la indexación de repetición,
  el método exacto de generación de pliegues y el estado de RNG por cabeza.
- Entorno del paper: Python 3.10.16, PyTorch 2.5.1, NumPy 2.0.1 y timm 1.0.15.
  Entorno actual: Python 3.12.13, PyTorch 2.12.1+cu126 y timm 1.0.28. No se
  ha comprobado el entorno original ni descargado sus dependencias grandes.
- La cola actual usa 3 semillas × 5 pliegues del panel común, no 10 × 10. Es
  una evaluación adaptada y no permite declarar reproducido el 96,7 %.
- Acción: auditar si existe código publicado y revisar tamaño/licencias de un
  entorno separado antes de instalarlo. Congelar las decisiones que no puedan
  verificarse, etiquetarlas como aproximaciones y no buscar la semilla o ajuste
  que fuerce el número del artículo.

## Lectura de PDFs

Se revisó el texto local con Poppler; las cifras y descripciones anteriores se
vinculan por sección y DOI. La comprobación estructural automatizada en Windows
no pudo crear el sidecar por falta de operaciones POSIX; no se convierte ese
intento en un PASS. El PDF de Neshov ya tiene una comprobación estructural PASS
documentada en `docs/fsc_tex/REPRODUCCION_NESHOV_BEITV2_2026-10-27.md`.
