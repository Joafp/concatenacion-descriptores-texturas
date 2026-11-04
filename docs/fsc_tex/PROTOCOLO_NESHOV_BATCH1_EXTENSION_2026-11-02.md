# Neshov adaptado con extracción individual: ampliación del panel

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: continuación de evaluación comparativa previamente autorizada.
- Origin Date: 2026-11-02, America/Asuncion.
- Verification Status: protocolo prospectivo; sin resultados de esta ampliación.

Después de auditar las 15 condiciones FMD completas de la nueva versión batch1,
evaluar CUReT, DTD, Outex-13, Soil y KTH-TIPS2b con el mismo sistema y receta
que `PROTOCOLO_NESHOV_BATCH1_CORREGIDO_2026-11-02.md`. Reutilizar únicamente las
particiones previamente verificadas y manifiestos de imágenes de las colas
CellNN; no reutilizar sus características ni sus clasificadores. Comprobar hashes,
grupos, clases, cobertura y tamaño del último lote BatchNorm antes de despachar.

Cobertura nueva: CUReT 2 condiciones/5612 llamadas, DTD 10/18800, Outex-13
1/680, Soil 15/3420 y KTH 4/4752: 32 condiciones y 33264 llamadas. La MLP
externa es una sola, no duplicarla bajo las cabezas SVM y ResMLP locales.
Dos hilos CPU, un benchmark GPU a la vez y lock global durante las cuatro etapas.
Extraer fit desde archivo en lote 1, comprobar reextracción del primero/último
con tolerancia 1e-4, entrenar la misma cabeza fijada y medir cada archivo test
en llamadas individuales. Nada de selección por F1 o test, caché online,
relajación de tolerancia, omisión o retry automático. Un primer caso exitoso
por dataset habilita las demás condiciones del mismo dataset; un fallo deja ese
dataset en revisión, pero no modifica los demás ya autorizados.

Se mantienen las reservas DTD físicas, KTH por muestras físicas y la diferencia
de representación local fija para Soil/Outex. Cada dataset se agrega únicamente
si completa su cobertura. Las ejecuciones son ADAPTACIONES al panel común y no
reproducen automáticamente los porcentajes, métricas o splits del artículo.
