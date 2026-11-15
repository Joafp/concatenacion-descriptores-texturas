# Avance: accuracy principal y ampliación E1/E2

Fecha: 15 de noviembre de 2026, America/Asuncion.

**Este documento conserva el corte de 25/27.** Después de la autorización
se cerraron las dos condiciones KTH: el estado vigente es **27/27 en seis
datasets**, con 98 pruebas aprobadas. Véase el [informe de cierre posterior](CIERRE_FIDELIDAD_KTH_E1_E2_2026-11-15.md).
El PDF no fue recompilado con ese cierre nuevo.

## Qué quedó hecho

- La tesis principal usa **accuracy (exactitud)** como métrica principal.
  Se actualizaron resúmenes en español/inglés, objetivo, diseño, tablas,
  gráficos, contrastes, discusión y conclusiones. El título se conserva.
- Macro-F1, precisión macro y recall macro son complementarias. El ranking
  y la selección históricos basados en macro-F1 no se cambiaron de nombre
  ni se reconstruyeron escogiendo resultados de test.
- Se reconstruyeron resultados históricos desde 144 fuentes con hashes.
  Esa reconstrucción no ajusta modelos ni produce predicciones nuevas.
- E1/E2 sí es una ampliación nueva y autorizada: **25 condiciones completas
  de 27 previstas**, con cinco datasets completos y KTH parcial.
- El PDF tiene **87 páginas**, compila sin referencias indefinidas ni
  desbordes horizontales y fue revisado visualmente en sus 87 páginas.
- Pasaron **52 pruebas** de contratos, métricas, cobertura y trazabilidad.

## Resultado E1: mismo Top-4 en ambas rutas

| Dataset | Condiciones | Accuracy directa | Accuracy por margen | Estado |
|---|---:|---:|---:|---|
| DTD | 10/10 | 0,870266 | 0,871117 | Completo |
| FMD | 5/5 | 0,982000 | 0,983000 | Completo |
| CUReT | 2/2 | 0,998574 | 0,997862 | Completo |
| Outex | 1/1 | 0,929412 | 0,926471 | Completo |
| Soil | 5/5 | 0,928947 | 0,930702 | Completo |
| KTH | 2/4 | — | — | Sin media completa; dos casos en revisión |

La media equiponderada de los **cinco datasets completos** es 0,941839915
directa y 0,941830218 por margen: 94,1840 % y 94,1830 %. La diferencia es
aproximadamente −0,0010 puntos porcentuales. Wilcoxon exacto bilateral:
p=0,8125; esto no demuestra equivalencia.

La media de adquisición por componentes pasa de 507,63 a 127,58 ms:
reducción **proyectada** del 74,87 %. No es una nueva medición de latencia
online de las políticas completas. Las cifras históricas de otros regímenes
permanecen identificadas por separado.

Los 25 Top-4 directos nuevos reproducen exactamente accuracy y macro-F1 de
sus filas archivadas. Se guardaron predicciones, scores completos OOF/test,
orden de clases, índices, controles aleatorios de igual cantidad con 100
repeticiones, resultados de todas las bases solas en test y errores.

## Resultado E2: otras medidas de confianza

Se compararon margen, máximo y entropía del softmax con q=0,25/0,50/0,75,
reutilizando los scores de E1 sin nuevos ajustes. Hay dos análisis separados:

1. Umbral fijado en OOF, con fracciones reales de test informadas.
2. Diagnóstico por lote con exactamente la misma cantidad derivada; usa
   el orden de scores de test sin sus etiquetas y no es una política online.

Con q=0,25 y umbrales OOF, accuracy media fue 0,941830 con margen,
0,939736 con máximo y 0,932543 con entropía, con distintas fracciones reales.
No se escogió un q por su resultado de test. Las familias de nueve pares
con Holm, sobre cinco datasets completos, no detectan diferencias
significativas en accuracy. La selección previa de la base para margen
y la falta de calibración limitan una afirmación general de superioridad.

## Qué impide cerrar KTH

Se congeló un perfil con ocho extractores, pesos locales, 33 imágenes de
entrenamiento (tres por clase), cinco calentamientos, batch1, dos hilos CPU
y lock global. Se midió un modelo por vez, sin fits concurrentes.

- EVA-02: coseno mínimo **0,931978**, frente al mínimo fijado **0,999**.
- SigLIP: coseno mínimo **0,981889**, frente al mismo mínimo.
- Los otros seis extractores superaron el umbral.

Los dos fallos científicos están en `requires_review` y no se repitieron.
Las condiciones KTH 1 y 3 dependen de esos costos; 2 y 4 completaron y se
muestran individualmente. No se sustituyeron costos, no se omitieron casos
y no se produjo una media parcial presentada como completa.

La primera preparación del perfil, antes de cargar modelos o medir, había
supuesto diez clases en vez de once. Se documentó como error de preparación
con cero llamadas científicas y se probó la corrección. Es distinto de los
fallos de fidelidad posteriores, que permanecen abiertos.

## Dónde están los archivos

- [Tesis PDF](../../paper/tesis.pdf) y [fuente](../../paper/tesis.tex).
- [Auditoría E1/E2](../../results/analysis/top4_fixed_e1_e2_audit_20261115_v1/summary.json).
- [Calidad por condición](../../results/analysis/top4_fixed_e1_e2_audit_20261115_v1/e1_conditions.csv).
- [Bases solas en test](../../results/analysis/top4_fixed_e1_e2_audit_20261115_v1/e1_cheap_candidate_test_metrics.csv).
- [Controles E2](../../results/analysis/top4_fixed_e1_e2_audit_20261115_v1/e2_conditions.csv).
- [Predicciones y scores comprimidos](../../results/exploratory/topk_cascade/top4_fixed_primary22_20261115_v1/conditions/).
- [Reconstrucción de accuracy histórica](../../results/analysis/thesis_accuracy_primary_20261115_v3/summary.json).
- [Decisión de métrica](DECISION_METRICA_ACCURACY_2026-11-15.md).

Los modelos de clasificación ajustados se conservan localmente con hashes;
la regla global del repositorio excluye archivos `*.joblib`. Los pesos de
extractores y embeddings también permanecen locales. Las predicciones,
scores y tablas permiten auditar las métricas sin reentrenar.

## Próximos pasos

1. Decidir sobre la [validación corregida KTH](PROTOCOLO_VALIDACION_KTH_CORREGIDA_2026-11-15.md).
   La revisión CPU encontró entradas distintas para las 33 imágenes de cada
   red; no prueba todavía fidelidad de embeddings recuperada. Los dos casos
   pendientes no ajustaron modelos. Una corrección de infraestructura no
   autoriza repetir el fallo científico automáticamente.
2. Revisar con autores y tutor la tesis y la interpretación del cambio de
   métrica, decidido después de observar resultados históricos.
3. Mantener E4 (cascada ResMLP), E5 (Top-4 más N-gramas), E6 (ViT online),
   E7 (memoria por política) y E8 (variación entre equipos) como pendientes.
4. Medir políticas completas en llamadas online cuando se haya resuelto
   fidelidad y congelado el protocolo correspondiente.

## Revisión posterior de KTH, sin nuevas corridas científicas

La [auditoría de preprocesamiento](REVISION_FIDELIDAD_KTH_2026-11-15.md)
identificó diferencias concretas de resize/recorte para EVA-02 y de
interpolación para SigLIP. Se conservaron pesos, imágenes, etiquetas y estados;
la fidelidad neuronal permanece en revisión. Se prepararon adaptadores de
entrada y un manifiesto de validación con presupuesto máximo de 66 llamadas
evaluadas y diez calentamientos, todavía no ejecutados.

La propuesta verifica los artefactos de las 25 condiciones completas,
incluidos los clasificadores locales, y que las dos KTH completas no dependen
de los componentes corregidos. La tesis de 87 páginas y sus números conservan
la versión ya publicada; esta etapa añade diagnóstico y preparación.

La suite ampliada pasó **66 pruebas en 42,56 s**. El diagnóstico y la
propuesta no ejecutaron ninguna llamada neuronal. [Registro de verificación](../../results/analysis/kth_reference_validation_proposal_20261115_v1/verification.json).
