# Correcciones ARS aplicadas a la tesis — 15 de noviembre de 2026

El autor aprobó continuar con las correcciones y los análisis de resultados
guardados. Se conservan el título, accuracy como métrica principal y el recorrido
Top-k directo → activación por margen. Ningún ajuste, extracción, predicción de
modelo o cronometraje científico nuevo fue necesario en esta etapa.

## Respuesta a los quince puntos

| Punto | Cambio y evidencia | Estado |
|---|---|---|
| REV-01 | Ganancia ResMLP k4→5 corregida a 0,2305 puntos porcentuales de accuracy, con medias sin redondear. | Aplicado |
| REV-02 | Referencia principal de N-gramas apunta a accuracy; macro-F1 queda identificado aparte. | Aplicado |
| REV-03 | Pie de latencias vinculado a accuracy y métricas complementarias de las mismas llamadas; cifras originales conservadas. | Aplicado |
| REV-04 | Detalles de serialización, calentamiento y preprocesamiento KTH trasladados al Anexo D; criterio y alcance permanecen en resultados. | Aplicado |
| REV-05 | Rangos/cuantiles por condición y sensibilidad dejando un dataset fuera. No se inventan intervalos con particiones dependientes. | Aplicado |
| REV-06 | Misma familia principal Individual/Completa-22/Top-4 en accuracy, sin KTH histórico, para ambos clasificadores. | Aplicado |
| REV-07 | OOF E1 descrito como condicionado al Top-4 archivado; no se reaprendió el ranking dentro de cada OOF. | Aplicado |
| REV-08 | Matriz de alcance Outex por archivo, bloque y resultado; se repitió la comprobación de hashes de arrays existentes. | Delimitado; procedencia física completa abierta |
| REV-09 | Como la identidad de todas las matrices históricas no queda confirmada, se conserva sensibilidad sin Outex en los CSV; no reemplaza el resultado canónico ni demuestra daño. | Condición atendida, sin imputar corrupción |
| REV-10 | Antecedente de selección de métodos de textura de Puig, García y Meléndez (2010), con DOI verificado. | Aplicado |
| REV-11 | Antecedente de combinación/compresión de Khan et al. (2015), distinguiendo selección de bloques y fusión tardía. | Aplicado |
| REV-12 | Tabla en el PDF con representación, dimensión, checkpoint, cabeza, protocolo local y diferencias de los cuatro comparadores externos. | Aplicado |
| REV-13 | CNN, MLP y SFFS definidos; se explica que SFFS puede retirar bloques tras incorporaciones. | Aplicado |
| REV-14 | Ecuación del coseno, rango, invariancia de escala y alcance del umbral 0,999. | Aplicado |
| REV-15 | Dependencia OOF de la cascada histórica explicada en el método principal, separada de la selección de base/cuantil. | Aplicado |

## Qué añaden los análisis

E1 mantiene seis datasets y 27 condiciones. La diferencia media equiponderada
de accuracy margen menos directo es **+0,0132211 pp**. Al dejar fuera cada
dataset por turno varía de **−0,0192224 a +0,0746888 pp**. Son sensibilidades
descriptivas, no intervalos poblacionales ni autorización para escoger una
exclusión. Se conservan ganancias y pérdidas por dataset y condición.

Sin KTH histórico, la misma familia estática principal da Friedman exacto
**p=0,1242284 en SVM** y **p=0,5216049 en ResMLP**, con 7.776 permutaciones;
ningún par es significativo tras Holm. Esto no modifica las cuatro condiciones
KTH del cierre E1, que pertenecen a otro archivo.

El cotejo Outex reproduce los hashes normalizados de ViT en ambos directorios
y de DeiT enmendado en el panel. DeiT histórico no coincide con el recibo del
panel. No se transforma esa diferencia en una afirmación de daño global ni
se considera validada independientemente la procedencia de cada fila.

## Trazabilidad de la revisión

- [Revisión original](REVISION_ARS_TESIS_2026-11-15.md), conservada como corte histórico.
- [Análisis guardados y hashes](../../results/analysis/ars_revision_existing_analyses_20261115_v1/README.md).
- [Aplicación y alcance del gate](../../results/analysis/ars_thesis_revision_20261115_v1/README.md).
- [Plan vigente](PLAN_TOPK_MARGEN_2026-11-13.md).

Los antecedentes se verificaron en las fuentes primarias:
[Puig et al., editorial](https://www.sciencedirect.com/science/article/abs/pii/S0031320310002062),
[Khan et al., editorial](https://www.sciencedirect.com/science/article/abs/pii/S0167865514002451)
y [copia de los autores](https://research.cs.aalto.fi/cbir/papers/prl2015.pdf).
No se presentan como métodos adicionales ejecutados.

## Continuación

La versión compilada tiene **94 páginas**, con **106 pruebas aprobadas**.
Se verificaron 48 enlaces de hashes de fuentes/tablas y se revisaron visualmente
las páginas, con detalle de las tablas nuevas. El registro LaTeX final no tiene
referencias indefinidas ni desbordes. El recibo completo es
[release.json](../../results/analysis/ars_thesis_revision_20261115_v1/release.json).

La corrección editorial queda separada de una nueva revisión independiente o
una aprobación académica. Siguen pendientes la latencia física de las nuevas
políticas y Top-4 más N-gramas. Antes de medir, se debe completar y congelar
implementación/pesos/runtime y resolver la fidelidad de las tres condiciones
con ViT señaladas en el protocolo online. No se autorizan retries científicos
por el mero cierre de esta revisión. Las reservas Outex, KTH/DTD y DeepLumina
permanecen visibles.
