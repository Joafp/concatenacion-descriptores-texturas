# HyTexNet ADAPTADO: extensión fija a Outex13Official1360

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: ejecución técnica de extensión autorizada.
- Origin Date: 2026-11-02.
- Verification Status: protocolo previo a extracción, fit y llamadas Outex.
- Version Label: hytex_outex_adaptation_v1.

Hereda sin cambios PROTOCOLO_HYTEX_ADAPTACION_FMD_2026-11-02.md: RGB128,
descriptor514 + DenseNet121 GAP1024 congelado offline FP32, head256/ReLU/
dropout0.5, Adam0.001/wd0.0001/betas0.9/0.999,100 épocas, batch32, semilla42,
última época sin selección por test. Ningún ajuste por resultados FMD/CUReT/DTD.
Es adaptación local completa, no reproducción de cifras ni código de autores.

Una condición: Outex13Official1360, seed42/fold0, official_split1 sin invertir;
680 train y680 test,68 clases,1360 filas exactas. Exigir concordancia entre
ambos heads locales, índices archivados y columna official_split train/test.
Verificar etiquetas de todas las filas contra el array canónico y su hash
archivado, verdad de predictions.csv y hashes de todas las imágenes. Normalizar
solo source_sha256→sha256 en un CSV nuevo conservando orden/path/label/group.
No usar predicciones como etiquetas ni embeddings como features de este método.

Mismo runner sellado: extract batch1 y gate first/last fit batch1→batch1,
maxabs≤1e-4 con vectores conservados; train; online; audit. Cinco warmups fit
excluidos, una llamada archivo-a-clase por test, F1 y ns/ms de esas mismas
llamadas, sin caché online. Global GPU lock y CPU dos hilos durante cuatro
etapas, sin fits/extracciones concurrentes. Timeouts7200/1800/14400/300s.
Fallo científico requiere revisión, sin retry ni cambio de tolerancia/método.

Salidas nuevas, fuentes/pesos/paquetes/particiones selladas antes del despacho.
Consolidar solo1/1 y680 llamadas auditadas, comparando ambos heads×cinco métodos
en iguales filas. Conservar pérdidas y ganancias; hardware compartido y fechas
distintas impiden afirmar comparación contemporánea aislada. Representación
DeiT corregida de nuestros comparadores Outex permanece declarada. No medias
de seis datasets, inferencia estadística ni equivalencia con cifras publicadas.
Panel propio y FMD/CUReT/DTD cerrados no se repiten; Neshov sigue requires_review.
