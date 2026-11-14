# Plan maestro de tesis y comparaciones — 4 de noviembre de 2026

> **Orientación vigente desde el 13-11-2026:** el autor comunicó el título y
> los dos ejes indicados por el profesor: concatenación Top-k y comparación
> del uso directo con activación por margen. La estructura y prioridades
> actuales están en [PLAN_TOPK_MARGEN_2026-11-13.md](PLAN_TOPK_MARGEN_2026-11-13.md).
> Este documento conserva el historial de resultados, auditorías y reservas.

**Actualización 08-11:** se incorporó el trabajo de Carlos del PR 6 y se
documentó una [conciliación inicial](CONCILIACION_CARLOS_SOTA_TIMING_2026-11-08.md).
Sus resultados usan tiempos amortizados batch=32 en otra GPU, no equivalentes
a nuestra latencia online batch=1; Neshov e HyTex tienen diferencias de receta
y la alerta de cinco filas Outex queda pendiente de comprobación independiente.
No se modificaron resultados sellados ni se ejecutaron modelos. Las prioridades
son auditar procedencia y predicciones de Carlos y trazar las filas Outex antes
de mezclar cifras o diseñar nuevas mediciones.

**Rastreo Outex 08-11:** [detalle y huellas](TRAZABILIDAD_OUTEX_CARLOS_2026-11-08.md).
En el reporte de Carlos Completa-22 usa ambos bloques señalados, diversidad/SVM
usa ViT-B/16 y Top-4 ninguno. En el panel online local las 30 llamadas
primarias de las tres filas test señaladas fueron correctas; esto no cuantifica
efectos indirectos de las dos filas train ni verifica la hipótesis sobre los
embeddings. Los CSV examinados de Carlos no contienen predicciones por imagen.

**Actualización Outex 09-11:** [auditoría de huellas](AVANCE_OUTEX_HUELLAS_2026-11-09.md).
Las filas 1034 y 1302 están en train. Los hashes L2 de ViT histórico y de
ViT/DeiT enmendados coinciden con los recibos; el DeiT histórico difiere del
enmendado, como anticipa la configuración que regeneró ese bloque. Hay que
verificar la alerta y su impacto; no trasladarla automáticamente a ambos bloques
del panel ni declarar ausencia de efecto.

## Alcance y criterio

Esta es la hoja de ruta vigente para coordinar lo que ya se midió con los
materiales preparados para la defensa. Conserva como antecedentes el
[plan de réplicas](PLAN_REPLICAS_PAPERS_2026-11-02.md), los protocolos
Neshov, KTH y DeepLumina y los informes de resultados citados abajo. Esta
actualización se basó en archivos y estados existentes; no ejecutó modelos ni
modificó manuscrito, diapositivas, guion, colas o resultados sellados.

Última inspección: 2026-11-04, horario America/Asuncion. No se observó worker
de benchmark en la lista de procesos. Esa constatación es puntual: volver a
comprobar procesos y lock GPU antes de cualquier ejecución futura.

**Avance de conciliación 04-11:** se auditaron las llamadas emparejadas de los
seis datasets disponibles: 1.780 comparaciones por condición y 230 por
dataset, con IDs, etiquetas, hashes, predicciones y tiempos comprobados.
[Informe y tablero completo](../../results/analysis/reconciliation_full_panel_20261104_v1/INFORME.md).
Las 46 condiciones DeepLumina terminadas registran avisos de no convergencia de
Liblinear y quedan **sujetas a revisión científica**, aunque sus llamadas sean
trazables. En los modelos guardados y verificados por hash, 1.653/2.441
clasificadores binarios alcanzaron el límite de 10.000 iteraciones; ver
[inspección de iteraciones](../../results/analysis/deeplumina_niter_review_20261104_v1/summary.json).
Una inspección independiente del gradiente primal sobre los rasgos de
entrenamiento guardados está en el
[diagnóstico de optimización](../../results/analysis/deeplumina_stationarity_review_20261104_v1/INFORME.md):
no es el criterio dual de parada ni permite calcular el impacto en F1. En
CUReT y Outex todos los binarios inspeccionados llegaron al límite. No se
reentrenó, extrajo ni evaluó test durante el diagnóstico.
Se preparó una [propuesta separada de tablero y guion de defensa](PROPUESTA_GUION_Y_TABLERO_VERIFICADO_2026-11-04.md)
con cifras trazadas y reservas; aún no se modificaron la presentación ni la tesis.
DTD además conserva una condición interrumpida en `requires_review`. No se
cambian los estados sellados ni se realizan reintentos automáticos.

## 1. Qué está hecho

| Bloque | Estado comprobado | Fuente y reservas |
|---|---|---|
| Panel común de nuestros métodos | **94/94 condiciones**; 362.640 llamadas primarias, más 9.400 observaciones adicionales | [Cobertura auditada](../../results/analysis/blocker_resolution_20261101/full_panel_online_v1/coverage.json). No repetir; conserva reservas DTD, KTH y cambios de representación Outex/Soil. |
| Neshov adaptado al panel común | **47/47 condiciones**, 36.264 llamadas: 15 FMD y 32 en los otros cinco datasets | Receta **BEiTv2+MLP**, no atribuirle automáticamente una cabeza LogReg. [FMD](../../results/analysis/neshov_fmd_batch1_external_summary_20261102_v1/summary.json) y [extensión](../../results/analysis/neshov_batch1_extension_summary_20261103_v1/INFORME.md). |
| Neshov FMD paper-like | **100/100**, 10.000 llamadas; accuracy 94,22 %, macro-F1 medio por fold 94,19 %, 16,767 ms/llamada | [Auditoría](../../results/analysis/neshov_paperlike_fmd_10x10_consolidated_20261103_v1/INFORME.md). Paper: accuracy 96,7 %; diferencia −2,48 pp. Split/semillas y versiones son aproximados. |
| HyTexNet y 6LBP+dCellNN, adaptados | **47/47 condiciones cada uno** en el panel común | [Cobertura por dataset](../../results/analysis/external_adaptation_coverage_20261102_v2/coverage.csv). Incluye la recuperación autorizada de infraestructura de HyTex/Outex y CellNN/FMD; no repetir. |
| KTH aproximado al reparto de un tercio | **1 condición completa por método**, 3.168 llamadas cada uno | [HyTex](../../results/analysis/kth_paperlike_hytex_summary_20261103_v1/summary.json): F1 0,93944; [CellNN](../../results/analysis/kth_paperlike_cellnn_summary_20261103_v1/summary.json): F1 0,62382. Hay 44 muestras físicas compartidas entre fit/test y selección de poses/escalas no confirmada por autores. No mezclar con el panel separado por muestra física. |
| DeepLumina adaptado | **46/47 condiciones terminadas en ejecución**, todas con avisos de no convergencia; DTD **9/10** | [Auditoría de convergencia](../../results/analysis/deeplumina_convergence_review_20261104_v1/summary.json); las 46 condiciones requieren revisión científica. `DTD s42_f3` está en `requires_review` tras timeout de 3.600 s durante train. No presentar DTD como cobertura completa ni repetir automáticamente. |
| Material de defensa | `paper/tesis.pdf`: **71 páginas**, generado el 03-11; `paper/presentacion_defensa.pdf`: **17 páginas**, generado el 04-11; existe guion nuevo | Son trabajo del equipo y se preservan. Antes de exponer, resolver las discrepancias de la sección 3. El dossier del 23-10 se autodeclara histórico. |

## 2. Referencia de F1 y latencia por dataset

La tabla siguiente recoge únicamente los resúmenes auditados existentes. Cada
celda expresa **macro-F1 medio por condición / latencia media en ms por
llamada**. Son adaptaciones evaluadas en el panel común; las mediciones de los
métodos corresponden a fechas/estados de hardware distintos, por lo que las
comparaciones de latencia son descriptivas, no un experimento simultáneo. Los
resultados DeepLumina de la tabla son observaciones trazadas **sujetas a
revisión científica** por los avisos de no convergencia; no son cierre validado.

| Dataset | Neshov BEiTv2+MLP | DeepLumina | HyTexNet | 6LBP+dCellNN |
|---|---:|---:|---:|---:|
| FMD | 0,94213 / 16,890 | 0,85591 / 53,326 | 0,74142 / 31,181 | 0,24765 / 29,655 |
| CUReT | 0,99396 / 14,273 | 0,98806 / 52,998 | 0,98307 / 32,413 | 0,69337 / 31,025 |
| Outex-13 | 0,91930 / 14,612 | 0,90727 / 53,539 | 0,89275 / 29,040 | 0,63557 / 29,911 |
| SoilOriginal | 0,86310 / 19,168 | 0,80501 / 57,803 | 0,78796 / 33,114 | 0,35497 / 32,985 |
| KTH-TIPS2b | 0,92448 / 16,479 | 0,87437 / 51,568 | 0,82586 / 30,977 | 0,57503 / 31,937 |
| DTD | 0,80203 / 16,791 | **incompleto: 9/10** | 0,62415 / 33,512 | 0,21618 / 31,520 |

Fuentes: [Neshov FMD](../../results/analysis/neshov_fmd_batch1_external_summary_20261102_v1/summary.json),
[Neshov otros datasets](../../results/analysis/neshov_batch1_extension_summary_20261103_v1/INFORME.md),
[HyTex/CellNN](../../results/analysis/external_adaptation_coverage_20261102_v2/coverage.csv),
y los seis directorios `deeplumina_*_external_summary_20261103_v1` en
`results/analysis/`. DeepLumina/DTD tiene un resumen explícitamente parcial;
se omite su media aquí hasta completar o decidir cómo reportar la excepción.

## 3. Conciliación necesaria antes de usar el cuadro nuevo en defensa

**Prioridad alta: no sustituir las fuentes auditadas por el cuadro consolidado
del 04-11 hasta reconstruir su procedencia.** El archivo
`results/analysis/external_sota_full_panel_summary_20261104_v1/summary.json`
no identifica en su propio contenido los recibos o archivos de predicción de
cada cifra y difiere de los resúmenes auditados. Ejemplos concretos:

| Caso | Cuadro nuevo | Fuente auditada existente | Acción |
|---|---:|---:|---|
| HyTex, DTD | 9/10, F1 0,6363, 31,83 ms | **10/10**, F1 0,62415, 33,512 ms | Trazar qué llamadas y qué recuperación usa cada tabla; no marcar 9/10 como el estado definitivo. |
| CellNN, FMD | F1 0,4329 | **15/15**, F1 0,24765 | Revisar identidades de método, partición, fila y agregación. |
| CellNN, Outex-13 | F1 0,8282 | **1/1**, F1 0,63557 | Trazar predicciones, etiquetas, hash y receta. |
| Neshov, DTD | `BEiTv2+LogReg`, F1 0,8397, 22,86 ms | `BEiTv2+MLP` batch-1, **10/10**, F1 0,80203, 16,791 ms | Establecer si LogReg es otra variante medida; no sustituir la MLP ni atribuirle esos valores sin trazabilidad. |

El cuadro nuevo suma 141.584 llamadas según sus propias cuatro cifras, pero
esa suma no reconcilia todavía con las coberturas auditadas arriba; no usarla
como total definitivo hasta enlazar las llamadas exactas. Tampoco se debe
convertir un promedio 9/10 de DTD en promedio de dataset completo.

El [guion de defensa](GUION_DEFENSA_MESA_EVALUADORA.md) y
`paper/presentacion_defensa.tex` usan el cuadro nuevo y contienen afirmaciones
que requieren revisión antes de exponer:

1. DeepLumina alcanzó **90,00 % en un fold** FMD (`s2026_f2`); la media
   auditada de las 15 condiciones es **85,53 %** de accuracy. Un mejor fold
   no demuestra reproducción exacta de 90,15 % publicado. La media de CUReT
   tampoco prueba identidad de código, pesos o partición. Son adaptaciones.
2. El guion afirma superioridad y menor latencia frente a todos los competidores,
   pero su propia tabla da KTH Adaptive F1 0,9236 frente a Neshov LogReg 0,9293,
   y DTD Adaptive 54,4 ms frente a HyTex 31,8 ms. Aunque se concilien las
   fuentes, deben mostrarse **ganancias y pérdidas por dataset**, sin declarar
   dominancia universal y con reserva temporal.
3. La paridad numérica de un componente o ejemplo no acredita la identidad del
   pipeline completo. Para Chang, el repo y el paper discrepan en la partición
   OTC12; para HyTex y DeepLumina no se verificó código oficial completo. La
   explicación causal de cifras publicadas requiere evidencia adicional.
4. El PDF de tesis lleva como título de portada «Fusión costo-consciente de
   descriptores de textura mediante ensambles y adquisición condicional»;
   el guion y la presentación usan otro título. Verificar cuál es el título
   aprobado antes de entregar. El dossier anterior se marca histórico.

No se han editado guion, diapositivas, tesis ni el cuadro del usuario: esta
lista deja las discrepancias verificables y su orden de resolución.

## 4. Orden de trabajo pendiente

1. **Conciliar evidencia por condición y llamada.** Completada la reconstrucción
   de 1.780 comparaciones para los casos con cobertura íntegra. Pendiente:
   identificar la fuente y receta de las cifras diferentes del cuadro nuevo,
   incluida la variante LogReg, antes de incorporarlas a la defensa. Si no
   aparece la fuente, rotular «no verificado». Una búsqueda local acotada de
   1.111 archivos no localizó los decimales literales de CellNN/FMD ni
   HyTex/DTD fuera del cuadro y sus citas; no demuestra inexistencia de una
   fuente alternativa. Ver
   [trazabilidad pendiente](../../results/analysis/reconciliation_full_panel_20261104_v1/FUENTES_TABLERO.md).
   Mantener las latencias de fechas distintas como descriptivas y mostrar
   ganancias y pérdidas.
2. **Revisar convergencia DeepLumina y DTD s42_f3.** Los logs de las 46
   condiciones terminadas contienen advertencias Liblinear de no convergencia;
   1.653/2.441 clasificadores binarios inspeccionados alcanzaron `max_iter`.
   Ese dato no cuantifica el impacto sobre F1. El caso DTD s42_f3 agotó el
   tiempo y sigue `requires_review`. La inspección descriptiva del gradiente
   primal ya está documentada, pero no cuantifica cambio de F1 ni sustituye el
   criterio dual. Preservar estados, modelos y logs, sin reintento ni cambio
   silencioso de solver o presupuesto. No presentar esas adaptaciones como
   validadas científicamente hasta completar la revisión.
3. **Preparar la corrección del material de defensa desde la tabla conciliada.**
   Distinguir adaptación, aproximación al protocolo y reproducción fiel;
   revisar explícitamente títulos, afirmaciones de fidelidad, comparaciones,
   cobertura, reservas KTH/DTD y el uso de métricas publicadas. Cualquier
   edición del manuscrito queda fuera de esta actualización del plan.
4. **Otros papers viables:** mantener inventario y fuentes primarias; OTC12
   continúa bloqueado por datos y por discrepancia entre split del paper y del
   repo. Preparar recetas y pruebas independientes sin bajar recursos grandes,
   contactar autores ni usar servicios pagos.
5. **Antes de nuevas corridas autorizadas:** congelar código, paquetes, pesos,
   seeds, particiones y presupuesto; guardar predicciones, tiempos y errores;
   usar F1 y tiempo de la misma llamada; un benchmark GPU, CPU a dos hilos y
   lock global, sin fits/extracciones concurrentes con medición. Mantener
   reservas KTH/DTD, datos ya observados y exclusión de VisTex.

## 5. Huellas de esta revisión

| Evidencia | SHA-256 |
|---|---|
| Cuadro externo nuevo `summary.json` | `e5cc8da9922ed29d84f8269f800aaafc0c7436d699bb7d26974fff984431c444` |
| Cobertura auditada HyTex/CellNN `coverage.csv` | `6095731c582ddbc215415c7672d2eaa6533abe0379826854e9b8927f130fb136` |
| Neshov DTD batch-1 `summary.json` | `43c52337db00dac5537b522f5782000c97765336e2df2e1875aab09d2e76cc04` |
| DeepLumina FMD `summary.json` | `6f5ac173323ac49f0bab9238a407e79614435e727d66ed989a00307cc377c5c1` |
| DeepLumina DTD s42_f3 `state.json` | `c439c71ce8e3200fba0c25a8daf676d4426c823a213d342cd59e0629f238852c` |
