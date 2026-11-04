# Primer avance del panel externo local

## Material Passport

- Fecha: 28-10-2026. Tipo: resultado de ejecución, ARS inline.
- Alcance: FMD, semilla 42, partición externa 0; 800 imágenes de entrenamiento,
  200 externas. No son las medias de FMD ni la tabla final de seis datasets.
- Estado: SVM y ResMLP completados y reproducidos desde cabezas guardadas.
  Latencia física pendiente.
- Protocolo previo: `PROTOCOLO_PANEL_EXTERNO_LOCAL_2026-10-28.md`.

## Resultado SVM de esta partición

| Método | Macro-F1 externo | Exactitud | Rescate condicional |
| --- | ---: | ---: | ---: |
| Completa-22 | 0,939764 | 0,940 | No aplica |
| Top-4 | 0,959648 | 0,960 | No aplica |
| Ensamble diversidad | 0,954599 | 0,955 | No aplica |
| Ensamble tómbola | 0,954599 | 0,955 | No aplica |
| Selección adaptativa con margen | 0,964815 | 0,965 | 16,5% |

La ruta seleccionada internamente usa SigLIP como base y un rescate concatenado
de DINOv2-base, DINOv2-large, EVA02-base y SigLIP. El umbral congelado es
0,9360840916633606, seleccionado del cuantil interno 0,1. El rescate reemplaza
la clase base cuando el margen es menor que ese umbral. Cada extractor puede
reutilizarse dentro de la ruta, sin duplicar la adquisición de SigLIP.

En esta partición la diferencia de macro-F1 es aproximadamente +0,00517 frente
a Top-4 y +0,01022 frente a cada ensamble. Son diferencias descriptivas en 200
imágenes; no se declara significancia, superioridad global o no inferioridad.

El costo de diseño seleccionado internamente (37,557 ms en el perfil analítico)
**no es una medición de tiempo**. No se publica en la columna de latencia ni se
usa para calcular una aceleración física. Tampoco se espera que el cuantil
interno 10% fuerce la misma fracción de activación en prueba.

## Resultado ResMLP de la misma partición

| Método | Macro-F1 externo | Exactitud | Rescate condicional |
| --- | ---: | ---: | ---: |
| Completa-22 | 0,944786 | 0,945 | No aplica |
| Top-4 | 0,959756 | 0,960 | No aplica |
| Ensamble diversidad | 0,954674 | 0,955 | No aplica |
| Ensamble tómbola | 0,964815 | 0,965 | No aplica |
| Selección adaptativa con margen | 0,954674 | 0,955 | 14% |

La base seleccionada es SigLIP y el rescate combina dos miembros: (DINOv2-base,
DINOv2-large, EVA02, SigLIP) y (DINOv2-base, EVA02, ResNet101, SigLIP).
El umbral de ResMLP es 1,6733895540237427 y se seleccionó con scores OOF de
ResMLP; no fue transferido desde SVM. El presupuesto y la receta de selección
no se cambiaron con el resultado externo.

En esta condición la ruta adaptativa **pierde** aproximadamente 0,00508 frente
a Top-4 y 0,01014 frente a tómbola, empata numéricamente con diversidad y supera
a Completa-22 aproximadamente en 0,00989. No se afirma que el ahorro físico
compense esas pérdidas: ese ahorro aún no fue medido.

Los dos F1 de ensambles reconstruidos coinciden con los JSON archivados para
esta condición, tanto con el diagnóstico de escala de lote como con escala
de entrenamiento. La reconstrucción nueva usa CPU para las cabezas.

Se reprodujeron las 1.000 clases/compuertas de ResMLP individualmente desde
las cabezas guardadas, sin reajustarlas. F1 y exactitud coinciden con el CSV.
Sumando SVM: 2.000 filas reproducidas, sobre las mismas 200 imágenes externas,
no 2.000 imágenes independientes.

## Reconciliación SVM y repetición

Los dos ensambles reconstruidos coinciden en macro-F1 con sus JSON archivados
para esta condición. En este caso el diagnóstico de normalización por lote
externo y la escala congelada de entrenamiento producen el mismo F1; eso no
prueba que todos los scores o predicciones históricos sean idénticos, ni que
se reproduzcan así las otras 93 condiciones.

El auditor separado recargó las cabezas y ejecutó cada imagen individualmente:
1.000/1.000 clases y decisiones de compuerta coinciden con el CSV de la nueva
ejecución; F1 y exactitud coinciden con la tabla. No se reajustaron cabezas.
Esta comprobación usa embeddings: no demuestra fidelidad de extracción online.

## Artefactos

- Ejecución: `results/exploratory/local_external_panel_20261028/FMD_s42_f0_svm/`.
- Repetición: `results/analysis/local_external_panel_20261028/FMD_s42_f0_svm/`.
- Preflight online separado: `results/analysis/local_online_parity_20261028/FMD_s42_f0_svm/`.
- ResMLP: `results/exploratory/local_external_panel_20261028/FMD_s42_f0_resmlp/`.

Se guardan decisiones anteriores al test, particiones internas, scores OOF,
modelos, escalas, predicciones, métricas, auditorías SVD y hashes. El manuscrito
y las cifras históricas se conservan sin modificaciones.

## Pendiente

### Bloqueo físico detectado, sin alterar la tolerancia

El preflight online pasó en BEiT-v2 y ConvNeXt-v2 para las dos imágenes fijas.
Se detuvo en DeiT-small, primera imagen (fila 3): dimensión y finitud correctas,
pero error máximo 0,1966250092, mayor que 0,0001, y coseno -0,00399.
El cargador informó que `pooler.dense.weight` y `pooler.dense.bias` faltaban en
el checkpoint y fueron inicializados. El adaptador actual toma `pooler_output`
si existe, por lo que esa salida no tiene una procedencia entrenada demostrada.
Es una causa candidata concreta; todavía no se ha verificado si el token CLS
reproduce el vector archivado.

Se preservó la ejecución fallida en el directorio de preflight, no se relajó
la tolerancia y no se publicaron tiempos. Se solicitó dirección para diagnosticar
CLS y corregir el adaptador solo si coincide, conservando los archivos originales.
La reproducción de las cabezas sobre embeddings guardados no queda invalidada
por este fallo del adaptador de extracción online.

Actualización autorizada: CLS no pasó la tolerancia en la primera imagen. El
adaptador permanece intacto. El diagnóstico tuvo además un fallo de registro,
corregido sin repetir la extracción. Resultado y límites en
`RESULTADO_DIAGNOSTICO_DEIT_CLS_2026-10-28.md`.

### Ampliación pendiente

Comprobar extracción y cronometraje físico emparejado, y
ampliar al resto de condiciones de FMD y de los otros cinco datasets. Una
partición no rellena ninguna media agregada de la tabla final por dataset.
