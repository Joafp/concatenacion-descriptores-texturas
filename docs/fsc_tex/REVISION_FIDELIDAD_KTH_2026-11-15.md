# Revisión de fidelidad KTH: incompatibilidad de entradas demostrada

Fecha: 15 de noviembre de 2026, America/Asuncion.

## Resultado y alcance

La ruta online utilizada en el perfil KTH no aplica el mismo preprocesamiento
que el código histórico de extracción para EVA-02 y SigLIP. En las **33
imágenes congeladas de entrenamiento**, las dos rutas producen tensores de
entrada diferentes para cada red.

Esto demuestra una incompatibilidad de entrada. **Todavía no demuestra que
esa diferencia explique por completo el coseno de embeddings fallido ni que
el adaptador candidato recupere fidelidad.** No se construyeron modelos,
no se ejecutaron forwards, no se extrajeron embeddings, no se produjeron
predicciones y no se midieron latencias nuevas. CUDA permaneció sin inicializar.

## Qué difiere

| Bloque | Código histórico aplicado con la configuración local auditada | Ruta online que falló |
|---|---|---|
| EVA-02 | `timm.data.create_transform`, evaluación: resize del lado corto a 248, bicúbico; center crop 224; normalización del modelo. | Resize directo a 224×224 con bilineal por defecto; center crop 224 sin efecto sobre esa salida; misma normalización declarada. |
| SigLIP | Resize explícito de `torchvision` a 224×224, bilineal por defecto; ToTensor; media/std del processor. | `AutoImageProcessor`, backend torchvision en el entorno actual, con `resample=3` (bicúbico) y salida 224×224. |

En KTH, las imágenes revisadas son de 200×200. En EVA, la ruta histórica
reconstruida conserva una región central tras el resize, mientras la online
incluye toda la imagen. En imágenes rectangulares la ruta manual además
cambiaría la geometría; ese caso se probó solo con una imagen sintética.

Las normalizaciones RGB de las recetas comparadas coinciden por bloque.
La normalización L2 final del vector no explica por sí sola un coseno bajo,
porque el coseno es invariante ante escalados positivos de los vectores.

## Comprobación en píxeles, no en embeddings

| Bloque | Imágenes reales | Tensores diferentes | Diferencia absoluta media del tensor normalizado |
|---|---:|---:|---:|
| EVA-02 | 33 | 33 | 0,33284655 |
| SigLIP | 33 | 33 | 0,01390743 |

Se guardaron 70 comparaciones: 33 imágenes reales y dos controles sintéticos
por bloque. Esas distancias se expresan en unidades de los **píxeles
normalizados de entrada**. No son diferencias de accuracy, latencia ni coseno
de características, y no se utilizan para aceptar una extracción científica.

Los hashes de las imágenes seleccionadas coinciden con los congelados. Los
4.752 labels de ambos caches coinciden con el manifiesto y el manifiesto de
recuperación conserva el mismo orden y SHA-256 de archivos. Los pesos y
configs locales revisados coinciden con las huellas del perfil fallido.

## Procedencia y límites que siguen abiertos

La función histórica `load_model_and_transform` mantiene el mismo AST en
los commits `2443995` y `e10bf40` y en el código revisado. Esto acredita la
estabilidad del código de la receta, **no la ejecución exacta que produjo
cada NPY**.

No se recuperó metadata individual de EVA-02/SigLIP que ligue cada embedding
original con su comando productor, hash de pesos y todas las versiones.
Las versiones observadas ahora son torch 2.12.1+cu126, torchvision
0.27.1+cu126, timm 1.0.28 y transformers 5.14.1. El perfil fallido registró
torch/timm; este relevamiento no completa retroactivamente su congelado
con versiones que no estaban registradas allí.

La receta histórica usa `SiglipVisionModel` y `pooler_output`; la online usa
`AutoModel.get_image_features`. En la biblioteca actual esta última llama
al modelo de visión. La diferencia de nombres de API no basta para afirmar
que otra capa sea la causa. La validación candidata debe conservar
explícitamente la salida de la receta histórica.

## Corrección candidata preparada

Se añadió [reference_preprocessing.py](../../src/reference_preprocessing.py),
con adaptadores de entrada que conservan las recetas históricas. No carga
pesos ni construye redes y no reemplaza el ejecutor que sustentó los
resultados anteriores. Ocho pruebas CPU verifican geometría, normalización,
interpolación, rechazo de configuraciones inválidas y ausencia de construcción
de modelos.

La comprobación de integridad confirma que no cambiaron los estados fallidos
de los perfiles ni el estado E1/E2. E1 sigue en **25/27**, con cinco datasets
completos. Los casos KTH 1 y 3 permanecen en revisión.

## Próximo paso concreto

La [propuesta de validación corregida](PROTOCOLO_VALIDACION_KTH_CORREGIDA_2026-11-15.md)
define una medición nueva con esta receta y el mismo mínimo de coseno 0,999.
Su ejecución requiere una decisión explícita sobre esa propuesta; las pruebas
CPU y el diagnóstico no autorizan repetir el fallo científico automáticamente.

Si la nueva validación pasa, se podrán preparar las dos condiciones E1 KTH
que no llegaron a ajustar modelos, sin repetir las otras 25. Los resultados
originales y sus fallos conservarán sus carpetas y hashes.

## Evidencia

- [Resumen de auditoría](../../results/analysis/kth_preprocessing_forensics_20261115_v1/summary.json).
- [Comparaciones de píxeles](../../results/analysis/kth_preprocessing_forensics_20261115_v1/pixel_preprocessing_pairs.csv).
- [Configuraciones y huellas de pesos](../../results/analysis/kth_preprocessing_forensics_20261115_v1/pipeline_configuration.json).
- [Provenance](../../results/analysis/kth_preprocessing_forensics_20261115_v1/provenance.json).
- [Script de auditoría sin inferencia](../../scripts/audit_kth_preprocessing_forensics.py).
