# Nueva etapa: métodos publicados frente al panel local

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: continuación autorizada de implementación y evaluación comparativa.
- Origin Date: 2026-11-02, America/Asuncion.
- Verification Status: panel local ANALYZED; réplicas externas pendientes.
- Version Label: paper_replication_scope_v1.

## Autorización y objetivo

Petición nueva del autor: replicar todos los papers que sea posible y medir lo
mismo para comprobar si nuestro método también mejora a otros. Esta petición
autoriza preparar e implementar nuevas evaluaciones externas, no solo inventariar.
Se eligen decisiones técnicas rutinarias sin nuevas consultas; los protocolos
se documentan y congelan antes de las nuevas predicciones. No se presupone ganar.

No es una autorización ilimitada: conservar frenos ante fallos científicos,
recursos grandes, servicios de pago, mensajes a autores, licencias desconocidas,
ni permite manipular resultados o modificar manuscrito/commits/push. No VisTex.

## Comparación común

Referencia inmutable: results/analysis/blocker_resolution_20261101/full_panel_online_v1/.
Evaluar métodos completos, no mezclar F1 publicado con nuestros tiempos.
Cada método externo conserva su propio clasificador: una MLP publicada no se
convierte silenciosamente en SVM/ResMLP. Compararla separadamente con ambos
paneles nuestros. Una variante con otra cabeza se etiqueta como otra adaptación.

Cobertura objetivo por método compatible:47condiciones externas diferentes,
no94: FMD15, CUReT2, DTD10, Outex1, Soil15 y KTH4. Las94del panel local contienen
dos clasificadores; no duplicar un sistema externo idéntico para fingir94réplicas.
36264 llamadas primarias por método si cubre las47condiciones; cada predicción
y tiempo provienen de una misma llamada online. La observación adicional DTD
de9400llamadas no añade nuevas imágenes/condiciones al panel común.

Mantener manifiestos, índices y semillas de partición originales. Si cambia el
protocolo del paper, declarar adaptación al benchmark común. Reproducir además
sus splits publicados es otra evaluación, no sustituye este emparejamiento.
Test ya observado y diseño posterior al panel: análisis exploratorio explícito.

## Orden por viabilidad, no por resultado

| Prioridad | Método/familia | Acción y barrera |
| --- | --- | --- |
| 1 | Neshov BEiTv2 multicapa + MLP | Implementación y checkpoint offline disponibles; completar protocolo/runner47, preflight, comprobación real y primer datasetFMD antes de ampliar |
| 2 | Scabini et al., J.Imaging11,304 | Cerrar receta de cada sistema reproducible y sus clasificadores; no inventar un único método a partir de una media de tres clasificadores |
| 3 | RGB Pixel N-grams | Reconstruir sistema completo verificable; el bloque SVD local no acredita réplica |
| 4 | AsTexNet; HyTexNet | Verificar suficiencia de fórmula/código/checkpoint; no sustituir por MobileNet/DenseNet aislados |
| 5 | Compact color–texture2015; selección2010; ventanas2007; DeepLumina2022; multiescala2023; LBP+CellNN2024 | Fichas de fidelidad, factibilidad y tarea. No convertir segmentación por píxel en clasificación por imagen sin adaptación declarada |

Inventario fuente: docs/referencias/README.md y plan de comparadores27-10.
Cada ficha debe registrar DOI, fuente/versiones, implementación/licencia,
checkpoint/hash, preprocesamiento, representación, clasificador, entrenamiento,
particiones, hardware/costo, decisiones ambiguas y etiqueta de fidelidad.
No hallazgo de código no demuestra inexistencia. No reintentar HTTP429 en bucle.

## Secuencia operativa

1. Congelar protocolo específico y manifiesto por candidato antes de ejecutar.
2. Tests herméticos, preflight de hashes/índices/recursos y comprobación limitada
   en filas de entrenamiento fijadas de antemano, nunca seleccionadas por F1.
3. Entrenar solo en fit con receta fijada, sin elegir época o hiperparámetros
   por test. Guardar cabezas, historial, extracción y errores en carpetas nuevas.
4. Medir archivo-a-clase batch1 FP32, warmup fuera, residencia/carga explícitas,
   sin caché de features entre llamadas. Un benchmarkGPU y CPU2hilos. Registrar
   ambiente, procesos, timestamps y tiempos por imagen; no afirmar aislamiento.
5. Auditar desde llamadas crudas: cobertura, clases, filas, F1macro/accuracy,
   latencia media/mediana/p95, hashes. Parciales identificados sin media completa.
6. Contrastes descriptivos por dataset: deltaF1 y cociente de latencia, tanto
   donde ganamos como perdemos. No inventar margen de no inferioridad ni criterio
   retrospectivo para decir que una pérdida es aceptable. Estadística solo con
   familia/estimando fijados y unidad entre datasets, no folds independientes.
7. Tabla final: reproducción fiel / adaptación común / componente / pendiente,
   y motivo de cada método no ejecutado. No ocultar candidatos adversos.

## Estado de inicio

Panel local94/94 completo. Sin benchmarks activos al revisar este pedido.
Neshov: piloto800 de desarrollo reauditable y adaptador online con19tests,
pero todavía0condiciones externas y0latencias reales de ese sistema.
No presentar ese piloto como competidor externo ya medido. El siguiente trabajo
es el runner y preflight de Neshov conforme al protocolo específico nuevo.

## Prioridad temática confirmada y primer preflight

El autor confirmó como referencia los papers de su directorio que concatenan
o fusionan características. Priorizar esos sistemas completos; selección de
características y clasificación por píxel quedan como antecedentes o adaptaciones
distintas, no equivalentes automáticos. Neshov/Scabini siguen por plan previo.

Primer preflight completado sin modelos: scripts/prepare_neshov_fmd_external.py
congela15condiciones FMD en results/analysis/neshov_fmd_external_preflight_20261102_v1/
manifest.json. Verifica30fuentes de ambos clasificadores y concordancia exacta
de sus particiones,800fit/200test, cobertura1000test por cada una de3semillas,
sin fuga de grupos,10clases, hashes de1000imágenes y checkpoint offline.
3000llamadas externas planificadas, todavía0ejecutadas. No cambia índices ni
excluye filas por BatchNorm.14tests de preparación/adaptador pasan.
Falta runner, comprobación real de extracción y cabezas externas entrenadas.

## Despacho autónomo iniciado durante ausencia del autor

Autor pidió continuar sin él, regreso aproximado en12h. No es promesa de cerrar
todos los papers en ese plazo. Runner y cola preparados,32tests pertinentes
pasaron; preflight y todas las fuentes/paquetes revalidados antes del despacho.
Protocolo científico sellado conserva su hash original; detalles de ejecución en
DESPACHO_NESHOV_AUTONOMO_2026-11-02.md, sin alterar el protocolo durante la corrida.

Cola results/analysis/neshov_fmd_external_queue_20261102_v1/manifest.json,
SHA2564f43c3ba8b812987d52dad2d25b7d25f7a8d7e283200e77bf5932fba402a2a36.
15condiciones con cuatro etapas cada una; workerGPU54789 iniciado10:43:27UTC,
sesión48201, ventana12h. Primera extracciónPID54797. Todas las etapas bajo mismo
lockGPUglobal; cabezaCPU2hilos. No actividad concurrente propia de benchmark/fit.
Estado/avance en gpu.json y tasks/*/state.json; logs por etapa y jobs/*/status.json.
No modificar scripts/protocolo/preflight/pesos/archivos fuente sellados.

Heartbeat existente actualizado, ACTIVE cada15min, nuevo objetivo papers y
verificación de esta cola. No crea segundo worker ni repite panel94. Tras terminar
FMD auditar cobertura3000llamadas y preparar continuación CUReT/DTD/Outex/Soil/KTH
con el mismo protocolo y manifiestos propios; paralelismo de GPU prohibido.
Mientras haya benchmark activo, avanzar lectura/código/tests ligeros de otros
papers sin entrenamiento/extracción ni presión deCPU que contamine tiempos.
Ante fallo, conservar evidencia, marcar revisión y continuar tareas independientes;
no decidir automáticamente un retry científico. Reporte consolidado al regreso
con completas/parciales/fallidas/pendientes y resultados adversos visibles.

### Resultado del primer control y continuidad independiente

Neshov/FMD42/f0 se detuvo10:43:59UTC, antes del entrenamiento y de llamadas
externas: maxerror absoluto batch1/batch8 en filasfit0/999 fue .0039381981 y
.0055108070, frente a tolerancia .0001. Registro jobs/Neshov_FMD_s42_f0/extract/
parity.json y status.json, más logstage0. Requires_review; otras14blocked.
Worker54789 terminó normalmente; no hay Neshov corriendo ni resultadosF1/ms.
No repetir, cambiar batch/precisión/kernel/tolerancia ni reetiquetar el fallo
como infraestructura sin evidencia. Diagnóstico de código/receta puede avanzar
sin nuevas extracciones o mediciones; un nuevo experimento requiere disposición
explícita del fallo, no el permiso general de autonomía.

Trabajo independiente ya completado: inventario de11PDFlocales y hashes en
results/analysis/reference_paper_inventory_20261102_v1/inventory.json. Sin subir
PDF, interpretar contenido, afirmar licencia o descargar pesos.8tienen fila en
README;3faltaban al catálogo (Neshov, Scabini, RGBPixelNgrams), ahora identificados
en inventario sin inventar receta. Próximo trabajo autónomo: leer fuentes locales
con comprobación estructural, cerrar fichas de concatenación/fusión de Scabini,
Compactcolor–texture, AsTexNet/HyTexNet y demás candidatos; implementar solo donde
receta suficiente, fijar protocolo/preflight y avanzar independientemente de Neshov.
El heartbeat activo sigue este estado, no debe detener todo por la dependencia
fallida ni relanzar la cola sin cambio de autoridad. Sin presión por llegar a12h.

## Avance independiente de recetas, 02-11

Auditoría inicial Compactcolor–texture/AsTexNet en
results/analysis/paper_recipe_audit_20261102_v1/RECIPE_READINESS.md.
PDFs7/30páginas pasan preflightestructural; pasajes de método/protocolo leídos,
una página de ecuacionesAsTexNet inspeccionada visualmente. Lectura no sustituye
reproducción. Dependencias faltantes identificadas sin inventar defaults.
Operadores aisladosAsTexNet eq8–12/16–18 implementados,13tests pasan; no sistema
completo ni nuevas métricas. Próximo: completar fichasHyTexNet/DeepLumina y
verificar código/pesos oficiales que puedan cerrar recetas antes de adaptación.
Neshov no se repite; no procesos de benchmark activos en este corte.

## HyTexNet: siguiente candidato ejecutable como adaptación explícita

RecetasHyTexNet/DeepLumina auditadas, con ambigüedades registradas en
paper_recipe_audit_20261102_v1/RECIPE_READINESS.md. DescriptorHyTex514 y
cabeza1538→256→K implementados,9tests nuevos/22conAsTexNet pasan. No se cuenta
como método completo ni modelo entrenado. DenseNetcheckpoint ya local32.3MB,
hash comprobado offline; no descargar. Protocolo de adaptación nueva y prospectiva:
PROTOCOLO_HYTEX_ADAPTACION_FMD_2026-11-02.md. Parámetros no especificados por
paper se fijan explícitamente como locales, sin atribuirlos a los autores.
Siguiente tarea autónoma concreta: implementar adaptador completoHyTexNet
con cargaofflineestricta, tests, preflight/cola nuevaFMD y primer caso, siguiendo
ese protocolo, sin repetirNeshov. Etiqueta obligatoriaADAPTADO en reportes.
DeepLuminafc1000/ECOC no es nuestroResNetGAP/SVM; permanece receta pendiente,
sin decidir equivalencia por nombre del backbone ni copiar resultados publicados.

## HyTexNet adaptado: pipeline completo despachado, 02-11, 11:21 UTC

Implementados adaptadorofflineestricto y training fijo, runner de cuatro etapas
y preparador de cola.35tests pasan, incluido flujo sintético completo, fallo de
fidelidad con vectores preservados, bloqueo por upstreamcorrupto, auditoría y
reproducibilidad del fit. Ningún testnuevo usa imágenes reales para entrenar.
No afirmar paridad con código deautores ni porcentajes delpaper.

Cola independiente results/analysis/hytex_fmd_external_queue_20261102_v1/:
preflight.json y manifest.json sellados antes de modelo,1000imágenes/15particiones
verificadas, paquetes/pesos/código/protocolo revalidados. ManifiestoSHA256
94f40dc297e3516abad630a7ad7c1c24622d7cf005dee0305d842b748f18aa75.
Worker56637, sesión18682, inicio11:21:27UTC, ventana12h. Primer proceso56645
extraeFMD42/f0,451/800fit al corte, único workerGPU/lockglobal. No métricas nuevas
ni condiciones completas todavía. Resto14dependen de primera auditoría completa.
No alterar archivos sellados mientras corra. Detalles en
DESPACHO_HYTEX_ADAPTADO_2026-11-02.md. Neshov anterior intacto/requires_review.

Siguiente heartbeat: revisar esta cola ANTES de trabajo nuevo, no despachar otro
benchmark/extracción/fit. Cuando haya15auditorías, reagregar3000llamadas y comparar
contra ambos heads locales de iguales filas/semillas/folds. No preparar nuevos
resultados físicos bajo inferencia/carga concurrente; avanzar lectura/código solo
si no contamina CPU del benchmark. Si falla, conservar evidencia y trabajar en
fuentes independientes, sin retry automático.

Primer cierreHyTex: FMD42/f0 completó extracción,fit100épocas,200llamadas online
y auditoría. Consistenciafit batch1→batch1 error0en ambas filas fijadas, sin
modificar umbral. F1macroonline.678683764,accuracy.68,mediams28.220804215,
mediana22.5302675,p9559.6321425. Es UNA condición, no mediaFMD ni paperreplicado.
Resumen jobs/HyTex_FMD_s42_f0/audit/summary.json, auditoría enlaza estadoonline
SHA256ef155e7f303ecce59c8320e5b39deb42dd239814bec91f89ff5e776a12efdb4a.
Cola habilitó restantes y extraeFMD42/f1PID56714, mismo worker56637. Cobertura
HyTexadaptado1/15,200/3000llamadas. Neshov permanece bloqueado, sin retry.

## FMD HyTexadaptado cerrado:15/15 y3000llamadas

Worker56637all_tasks_terminal,15complete, sin procesos propios de benchmark al
corte de consolidación. Scriptnuevo consolidate_hytex_fmd_external.py,7tests
pasan; reagregacióncompletaexit0 en
results/analysis/hytex_fmd_external_summary_20261102_v1/. Se verificaron60recibos,
fuentes/particiones/cadenas entre etapas y rawcalls.150comparaciones por condición
con nuestros10pares(head×método),10resúmenes por dataset; sin omitir derrotas.
F1macro medio decondiciones.7414168220822994,media31.180759932ms de3000llamadas.
Nuestro adaptativoSVM.977600499/38.629833773ms;ResMLP.975969620/36.354072400ms:
mayorF1pero mayormsmedio que la adaptación. No dominancia ni réplica delpaper,
no inferenciaestadística ni equivalencia entre hardwaremomentos. Ver RESULTADO.md
con límites y CSV completos. SummarySHA25643ca6a521b0a03cb0c701d6a587398f5e4d8cac13d78d881b926991184aa9dc8.

Siguiente trabajo autónomo: extender mismoHyTexADAPTADO aCUReT(2direcciones),
luegoDTD(10),Outex(1),Soil(15),KTH(4), con protocolos deextensión y preflights
de manifiestos/índices/clases/grupos y carpetas nuevas. No repetirFMD. No asumir
schemaSoil idéntico alFMD; usar mapeos canónicos ya verificados y conservar
reservasKTH. Runner/colaFMD quedan como artefactos históricos sellados: usar
versiones nuevas si hace falta ampliarpreparación/consolidación. Ningún parámetro
de método se ajusta por esteF1. Prosigue verificación de otros papers de fusión
sin competir conbenchmark. Neshov sigue requiere revisión, nunca auto-retry.

## CUReT preparado y despachado, 02-11, 11:51UTC

Preparer nuevo scripts/prepare_hytex_curet_queue.py:11tests pasan con runner
(8casos nuevos de dirección/filas/etiquetas/grupos/cobertura más3contratos).
Verificados2direcciones complementarias y4fuentes locales de ambosheads,
61clases,5612archivos conhashes, verdad de predicciones archivadas/manifest,
índices ycheckpointoffline. Protocolo deextensión CURET fijado antes de llamadas;
parámetros heredados inalterados. No repetirFMD ni tocarNeshov.

Cola results/analysis/hytex_curet_external_queue_20261102_v1/manifest.json,
SHA25699dc75626ffd268e4a0c5b60df60133b971a974e0a16afbbde3e591d943bfbd5.
Worker57833/sesión37797, inicio11:51:19UTC, primerextractPID57835; ventana12h,
único lockGPUglobal/2hilosCPU. Extraídas2601/2806fit al corte;0condiciones
CUReT completas, no F1/ms nuevos todavía. Segunda dirección depende de primera
auditoría. No editar fuentes selladas duranteejecución. FMD15queda cerrado.

Consolidador nuevo scripts/consolidate_hytex_external_dataset.py y tests preparados
sin entrenar ni medir; ejecutar tests cuando no haya benchmark activo y usar
solo tras2auditorías/5612llamadas. No reutilizar el consolidadorFMD que exige200
porfold. Debe verificarchain/hashes/llamadas reales y comparar ambosheads×5métodos,
ponderando tiempos por número real de llamadas si los folds difieren (Soil).
No declarar completos otrosdatasets por tener un consolidador genérico.

## CUReT cerrado y DTD despachado — 2026-11-02, 12:12 UTC

CUReT HyTexNet ADAPTADO: dos condiciones completas, 5.612 llamadas online
auditadas y reagregadas; F1 macro medio 0,9830668097498063 y latencia media
32,41285442818959 ms. Consolidador multidataset: ocho tests pasan, ejecución
exit 0. Resultados en results/analysis/hytex_curet_external_summary_20261102_v1;
summary.json SHA256 6f6716fed152aefcccb00978abe16de1f55bd970986e52ea0e71867ccf2bf571.
Hay 20 comparaciones por condición y diez agregados head×método. Nuestro
adaptativo SVM obtiene 0,998395978 / 36,830131104 ms; ResMLP obtiene
0,998930736 / 30,472171798 ms. Son comparaciones descriptivas en hardware
compartido y momentos distintos: no inferencia estadística ni reproducción
de porcentajes publicados. FMD y CUReT completos; otros datasets no completos.

DTD: preparación contrastada contra 20 fuentes locales, etiquetas canónicas
de las 5.640 filas y particiones oficiales exactas. Conservadas exclusiones
por grupos compartidos con test (entre tres y once filas de entrenamiento
por split), manteniendo las 1.880 imágenes externas de cada split. La unión
de diez tests oficiales cubre 5.546 filas, no las 5.640: 94 nunca son test.
La primera preparación se detuvo por un guard incorrecto que exigía cubrir
todas las filas en dicha unión, antes de cargar modelos o crear la cola.
Se corrigió ese control contra la unión oficial y se añadió verificación
independiente del array completo de etiquetas y sus hashes; diez tests pasan.
No se cambió método, tolerancia ni particiones ni se repitió un fallo científico.

Cola nueva results/analysis/hytex_dtd_external_queue_20261102_v1/manifest.json,
SHA256 cac2fd912d968efe40c2021718be55f9582f3c0249859002d270f6f8af940fac.
Fuentes y paquetes verificados antes del despacho; sin otro worker activo.
Worker 58627, sesión 92162, inicio 12:12:06 UTC, primer extract PID 58635;
ventana de despacho 12 h, lock GPU global y CPU dos hilos. Diez condiciones,
18.800 llamadas planificadas, cero condiciones completas al despacho.
La auditoría del primer split habilita los nueve restantes. No modificar
fuentes selladas; no repetir Neshov requiere revisión ni los paneles cerrados.

### DTD: primer split auditado — 12:16 UTC

HyTex_DTD_s42_f0 cerró cuatro etapas a las 12:16:18 UTC: 1.880 llamadas,
F1 macro 0,6278908265695777 y media 33,35765404893617 ms de esas llamadas.
Summary SHA256 77b69cbab8b2190c41782a451d4b644c5c34a9926c5df96e990e878e4c0c535d.
Es una condición, NO una media DTD completa. El gate habilitó los nueve
restantes; worker 58627 continúa extrayendo split índice 1, PID 58727.
Sin segundo worker ni fit competidor. Consolidar únicamente tras 10/10.

### DTD: cinco splits completos — 12:31 UTC

Estados y resúmenes de auditoría de índices 0–4 completos: 5/10 condiciones,
9.400 llamadas auditadas (1.880 por split). No se calcula ni publica una
media DTD completa con esta cobertura parcial. Worker 58627 vivo, sexto
split (índice 5) en extracción PID 59046; mismo manifiesto sellado. No
intervenir ni iniciar otro fit/extracción/benchmark. Tras 10/10, auditar y
consolidar con consolidate_hytex_external_dataset.py en directorio nuevo;
luego preparar Outex, Soil y KTH conservando receta y reservas históricas.

### DTD: nueve auditorías completas — 12:46 UTC

Índices 0–8 completos: 9/10 condiciones, 16.920 llamadas auditadas. Último
split índice 9 en extracción (PID 59263), worker 58627 activo, sin duplicar.
Todavía no consolidar ni presentar media completa DTD. Próxima prioridad:
auditoría final y reagregación completa, seguida de preflight Outex de su
única partición oficial (680 entrenamiento / 680 test), contrastando ambos
heads y nombres reales Outex13Official1360; no asumir schema de CUReT.

## DTD cerrado; Outex detenido en preparación — 13:04 UTC

DTD terminó 10/10 a las12:49:26 UTC. Sin workers activos, se verificaron
fuentes/recibos/cadenas y reagregaron18.800 llamadas con exit0 en
results/analysis/hytex_dtd_external_summary_20261102_v1. F1 macro medio
0,624152670943813, media33,51206467335106ms de las mismas llamadas.
SummarySHA25682710cc3de9959567c124c03b6b8438bba1308b4fe51f16a47d189fe57553c57.
100 comparaciones por condición y10 agregadas, sin quitar pérdidas.
Nuestro adaptativo SVM0,866856520/54,353745514ms; ResMLP0,866019864/47,612719303ms:
mayorF1 pero mayor latencia que esta adaptación. Reserva física DTD/SVM
preservada, hardware compartido y fechas distintas; no dominancia ni
inferencia global ni reproducción de porcentajes publicados.

Outex preparador nuevo y protocolo prospectivo:680train/680test,68clases,
1360imágenes verificadas, ambos heads concordantes, doce tests pasan. Primera
preparación corrigió lectura de cinco bloques policy del archivo histórico,
verificando cada bloque completo en lugar de exigir un único bloque; ningún
modelo se ejecutó durante ese control. Cola creada en
results/analysis/hytex_outex_external_queue_20261102_v1, manifestSHA256
685427d07448bd817194be484ff2f9276add2f848a3a4467997e87e71f902ae4.

Despacho13:04:06 UTC worker59624 terminó requires_review a13:04:08: el
preflight omitió campo checkpoint_sha256 requerido por runner. KeyError
antes de cargar modelo, extraer imágenes o entrenar; cero llamadas online.
Conservar cola, estado y stage_0.log sin cambios ni retry. Es fallo de contrato
de infraestructura, no evidencia de discrepancia científica; los doce tests
no cubrían ese campo. Una futura corrección debe usar preparador versionado,
test de contrato integral y autorización compatible con la prohibición vigente
de repetir requires_review. Mientras tanto avanzar Soil/KTH nunca ejecutados,
sin tocar fuentes selladas ni presentar Outex como medido.

## SoilOriginal preparado y despachado — 13:18 UTC

Sin workers de cálculo activos al inicio. Nuevo protocolo
PROTOCOLO_HYTEX_EXTENSION_SOIL_2026-11-02.md y preparador independiente,
sin modificar fuentes históricas Outex/DTD. Once tests pasan (ocho de
preparación, tres contratos del runner), incluido payload con checkpoint_sha256.
Preflight verificó30fuentes de ambos heads,1140etiquetas del array canónico
contra manifiesto y hashes, cinco bloques de verdad por archivo,1140imágenes,
15particiones exactas con coberturas por semilla/grupos y concordancia heads.
Folds228 salvo seed123/fold1=229 yfold3=227; no omitir ni igualar filas.

Cola nueva results/analysis/hytex_soil_external_queue_20261102_v1/manifest.json,
SHA2563f86f18577d61c60fbfffe427c84bc86fae08e45bea7512bf062b12e37bd566e.
Worker59897/sesión28801, inicio13:18:38 UTC, primerextractPID59899,101/912fit
al corte;15condiciones y3420llamadas planificadas, cero condiciones completas.
Ventana12h, globalGPUlock,CPU2hilos, sin otros fits/extracciones. Primera
auditoría habilita14restantes, no modificar fuentes selladas. Tras15/15,
reagregar en carpeta nueva ponderando tiempos por llamadas reales; no media
de dataset completo antes. Outex y Neshov requires_review quedan intactos,
sin retry. KTH siguiente rama nunca ejecutada, conservando reserva histórica.

## Soil cerrado y preparación KTH — 13:34 UTC

SoilOriginal15/15 terminó13:32:10 UTC; se reagregaron3420llamadas completas
con consolidate_hytex_external_dataset.py, exit0, en
results/analysis/hytex_soil_external_summary_20261102_v1. F1 macro medio
0,787961802069162;media ponderada33,11436526491228ms. SummarySHA256
0cdb9d1881e5afa77f953d0865ea175120ce074b27e3f8cda27b20c6a08bcf17.
150comparaciones porcondición y10agregadas. AdaptativoSVM0,872540331/38,482833136ms,
ResMLP0,866818251/48,326247217ms: mayorF1 pero mayorlatencia que esta adaptación.
Conservar advertencia representaciónDeiT/cambiofechas/hardwarecompartido; no
dominancia, cifraspublicadas ni inferenciaestadística. Cuatro datasets cerrados.

Preparador/protocolo KTH nuevos: doce tests pasan junto alrunner, contrato
checkpoint/reserva y rechazo inversiónincorrecta/fuga física. Mismo método
sin ajustes. Inspección comprobó ruta data/KTH-TIPS2-b existente y hash de
etiquetas por primera aparición idéntico al archivado. No existe hog_labels
en embeddings_extensions/KTHTIPS2b: no se inventa ni descarga; verificar array
completo desde manifiesto contra hash archivado y bloques de verdad de ocho
fuentes locales. Preflight en curso, sin modelos/callsKTH aún;4condiciones,
3564train/1188test,4752llamadas planificadas. No repetir requires_reviewOutex.

KTH preflight completo y despacho13:34:18 UTC:8fuenteslocales y4752imágenes
conhash, etiquetas/índices/grupos/muestras físicos concordantes. Manifest
results/analysis/hytex_kth_external_queue_20261102_v1/manifest.json SHA256
9fbd93da564f1da51c958f7a20a88afb3e6f4ca0163dd3b4e236b7c209995e17.
Worker60664/sesión41162, primerextract60666 con251/3564fit al corte; único
workerGPU,CPU2hilos,ventana12h. Cero condiciones KTH completas. Primera
auditoría habilita tresrestantes; no editar fuentes selladas ni correr
tests/fits/extracciones competidores. Solo consolidar tras4/4 y4752llamadas.

## KTH cerrado; cinco datasets externos completos — 13:46 UTC

KTH4/4 terminó13:46:14 UTC, sin worker activo al corte,4752llamadas reagregadas
exit0 en hytex_kth_external_summary_20261102_v1. F1medio0,8258556692598311,
media30,977041996843436ms. SummarySHA256
b988d2c5fc1768e4998c7bbba99ddbee9ac0573ca126987f28ca3d7446536edd.
40comparaciones porcondición y10agregadas, reservas preservadas.

Estado descriptivo por dataset y bloqueos en
results/analysis/paper_recipe_audit_20261102_v1/PANEL_STATUS_1346.md:
HyTexadaptado46condiciones/35584llamadas en cinco datasets cerrados; Outex0/1,
faltan680llamadas. NO panel de seis completo ni media global. Neshov yOutex
requires_review sinretry. Próxima prioridad es auditoría de recetas/artefactos
de otros papers viables; no improvisar método para aumentar conteo.
Búsqueda primaria acotada no verificó repositorios oficiales deAsTexNet,
DeepLumina,Compact; MDPI429/Wiley403 posteriores preservados como limitaciones,
sin eludir ni descargar. La ausencia dehallazgo no prueba inexistencia.

## Auditoría TiO multiescala terminada — 14:07 UTC

Sin workers de cálculo activos; no duplicar ni reintentarOutex/Neshov.
Auditoría nueva MULTISCALE2023_READINESS.md en paper_recipe_audit_20261102_v1:
PDF17páginas PASSestructural, método/algoritmo y disponibilidad leídos,
páginas6/7 renderizadas. Repositorio enlazado por paper verificado, árbol
a1749b45e8ef07bda8056453f0ca8e0ebfcc3cbb, licenciasMIT/BSD e inspección de
código fuente pequeña sin clonar/instalar/ejecutar. Hay componenteBiT,
no pipelineTiO315 completo demostrado. Ambigüedaddimensional bloqueinfo18vs27
yparámetros de descriptores/clasificadores pendientes; no improvisar.
Estado AUTHOR_LINKED_COMPONENT_CODE_IDENTIFIED_FULL_TIO_RECIPE_PENDING,
cero nuevas llamadas. Seguir auditoría deCellNN2024 yotrosPDFs restantes;
no presentar componentes como métodos completos ni invertirparticionesKTH.

## Candidato LBP+dCellNN con fuente/pesos localizado — 14:22 UTC

CELLNN2024_READINESS.md:PDF12páginas PASS, métodos/materiales/disponibilidad
leídos,página5inspeccionada. Repositoriooficial LBP_Contour hallado conmodelo,
fusión yclasificador; checkpoint10.311bytes inspeccionado ensafeCPUload.
HEAD89fc3d6 usa cellula(4) incompatible concheckpoint. Historial permite
versiónautor299502cbb2243ecb78018110236871f261aa92b2 con mcellnn():20claves
coincidenestáticamente,FP32finitos, sinstrictFalse ni sustitucióndered.
Recibocellnn_author_static_receipt.json SHA256
86cb069539fd9807c2df5f44a2758d92f2879dc05ec278f3234bf1cd113560bc.
No importarentrypoint ni ejecutarfuente cruda, entrenarDRIVE ni descargargrandes.
Cero nuevas llamadas; estado AUTHOR_VERSION_SELECTED_IMPLEMENTATION_TESTS_PENDING.
Siguiente paso: protocolo ADAPTADO prospectivo6LBP+dCellNN+MLP400,portsinefectos,
paridad sintética contra versión fijada ytests antes decualquierfit/panelcomún.
No usarHEAD incompatible ni presentar esta auditoríacomoréplicacompleta.

## LBP+dCellNN: port yparidad sintética completos — 14:36 UTC

Protocolo prospectivo PROTOCOLO_CELLNN_ADAPTACION_FMD_2026-11-02.md fijó
6LBP+dCellNN768+MLP400, versiones locales/semilla42 ypresupuesto10000maxiter,
sinCV/tuning ni cambios por test. Descargado solo bundleautorrevisado43.281bytes,
fuentes guardadas como texto noentrypoint ycheckpointconhash. SinDRIVE.
Port nuevo src/cellnn_reference.py sinsideeffects deimport;8tests pasan,
rechazo deconstantes/nonfinite sinfallback, registrostrict20pesos.

Gate único check_cellnn_synthetic_parity.py conlockGPUglobal yCPU2hilos,
gradiente/checkerboard/randomseed42: los tres casos errorflotante0, contornos
binarios exactos ehistogramas768 exactos,preprocesoidéntico. VectoresPNG/NPZ
yhashes conservados en results/analysis/cellnn_synthetic_parity_20261102_v1.
StatusSHA256623308ebbda02ff562dd428e01e3dc91f5ba0be5a0d686de80c2d232b2cbe92e.
Exit0,sin workersrestantes. Fuenteport SHA256
4b33ae695e1c6972486fbf05bedd42a6cab6569fd06cccaac2c543b110cc7c18.
No repetirgate ni modificar port/protocolo sinversionnueva. Paridadsintética
no esbenchmark ni reproduccióndeF1: cero fits yllamadas externas delmétodo.

Siguiente: adapter archivo→768→MLPpredict_proba,headconfig explícita,cronómetro
sincronizado yrunner cuatroetapas conpreflight15particionesFMD. Testear antes
dedespacho;guardar probabilidades como tales,no llamarlaslogits. Primer fit
yprimer online aún pendientes. Outex/Neshovrequires_review ypanelesintactos.

## LBP+dCellNN completo preparado ydespachado — 14:51 UTC

Adapter src/cellnn_online_adapter.py: archivoOpenCV→blue128→contornosGPU/
LBP768→MLP400CPU→predict_proba, cronómetro sincronizado incluye rutaentera,
probabilidadesguardadas comotales(no logits), claseargmax deesamisma llamada.
Configuración MLP explícita coincide exactamente con get_params deversión1.9.0;
sin nuevos defaults/hyperparameters niCV. Runner independiente cuatroetapas,
hashes/recibos/cadenas, headstrict, fallo terminal ygatefeaturesexactas.

29tests pasan incluyendo dimensiones,contornos,probabilidades,ordenclases,
cronómetro,coberturafolds ycadena completa extract/train/online/audit con
datos/modelossintéticos mock(sinfitreal niGPU), másparidadautor yaarchivada.
Preflight verificó15particionesFMD,1000imágenes/labels/grupos, fuentesdeparidad,
pesos/paquetes/headparams congelados. No cambiafuenteHyTex niNeshov.

Nueva cola results/analysis/cellnn_fmd_external_queue_20261102_v1/manifest.json,
SHA256ac7453232802240c0ad0786e9474bfacee56117ac438eba1e570035357b50965.
Worker61901/sesión78440, inicio14:51:14 UTC, extract61909 con101/800fit al
corte. Único workerGPU,CPU2hilos,ventana12h.15condiciones/3000llamadas
planificadas,cero condicionescompletas aldespacho. Primeraauditoría habilita14.
No modificarsellados ni correrfits/extracciones/tests competidores.
Solo tras15/15: consolidar probabilidades/predicciones/tiemposraw ycomparar
ambosheads×cincométodos, sin usarconsolidadorHyTex queasume logits/metododistinto.
Es sistemacompletoADAPTADO, no reproducción deporcentajes ovariantesOTC12/KTH.

## Fallo de serialización y continuación SOLO nunca iniciados — 15:04 UTC

Colav1 terminó14:51:50:CellNN_FMD_s42_f0 requires_review enstage1. Extract800
completo,consistenciaexacta(error0);train guardóhead.joblib/head_params.json
pero JSON delhistorial rechazó np.float32(TypeError). Cero llamadasonline.
No se reanuda, repite nireutiliza esehead;colav1/runner/protocolo ytodos sus
artefactos intactos. Catorcedependientes estabanblocked sinPID,stage,argv,
started_utc,recibos ojobdir: nunca ejecutados, no parciales.

Corrección infraestructura entrypointv2 independiente: escalaresNumPy→.item()
antes deJSON, valorfloat32 exacto, JSONallow_nan=False intacto. No cambio de
fit,tolerancia,método,features,cronómetro,parámetros osemilla.36tests pasan,
incluido reproducirTypeError real, conversiónexacta yrechazoNaN/inf/arrays.
No modificar runnerbase; v2loimporta sellado yregistra SHA dewrapper enestados.
Reglas en CELLNN_INFRA_CONDICIONES_NO_INICIADAS_2026-11-02.md.

Nueva cola solo14nunca iniciados:
results/analysis/cellnn_fmd_never_started_queue_20261102_v2/manifest.json,
SHA2560b6baafdcc3c28dfa7cdeb00d799468173243f52ea71eccb42cd8dcaabba2046.
Worker62133/sesión58443,inicio15:04:51 UTC,primerextract62141 para42/f1,
101/800fit al corte. Primeranuevaauditoría habilita13restantes.2800llamadas
planificadas, cobertura máxima14/15FMD, nunca mediaFMDcompleta. ÚnicoGPUworker,
CPU2hilos,ventana12h. No repetir42/f0 ni cambiarleestadorequires_review.
Próximas ramasdatasets nuncaejecutados independientes son autorizadas; no
presentar las14condiciones como panelcompleto ni reemplazarlafaltante.

## CellNN FMD14auditados; CUReTdespachado — 15:20 UTC

Colanunca-iniciados terminó15:15:39 UTC,14/14complete. Auditorindependiente
consolidate_cellnn_external.py verificófuentes/recibos/cadenas/rawprobabilidades,
argmax,truth ytiming:2800llamadas. Modoindividual-audits-only en
results/analysis/cellnn_fmd_individual_audits_20261102_v1,14métricas porcondición,
140comparacioneshead×método. NO comparison_dataset.csv niningunamediaFMD;
full_dataset_complete=False,cobertura14/15. SummarySHA256
28509cffa320bf36954e682789c6187b09580ea4e48c691bc2e144d9a90c7401.
42/f0requires_review sigueintacto ysinrepetir. Cuatrotests antiagregadoparcial
pasan; once enconjunto conpreparadorCUReT yrechazosdecorrupción.

Protocolo prospectivo PROTOCOLO_CELLNN_EXTENSION_PANEL_COMUN_2026-11-02.md
fija extensiones nuncaejecutadas aCUReT,DTD,Outex,Soil,KTH, mismopipeline y
headparams; noFMDretry. Preparador nuevo lee solo particionesnormalizadas de
preflightsHyTexconfuentes/hash, nofeatures/heads, preservando reservas.
CUReT:2condiciones/5612archivosverificados,61clases,2806fit/2806testcadauna.

Cola results/analysis/cellnn_curet_external_queue_20261102_v1/manifest.json,
SHA256535b8d7284320d97323715813d4cb23c8d8c14811ac628c5a11df8b01d7fd981.
Worker62902/sesión56267,inicio15:20:34 UTC,extract62910 con201/2806fit alcorte.
ÚnicoGPUworker,CPU2hilos,ventana12h,ceroCUReTcondicionescompletas. Primera
auditoría habilitasegunda. Consolidarsolo2/2y5612llamadas. No tocarfuentes
selladas ni ejecutarfit/extracción/testcompetidores. DTDsiguiente, previa
prueba dedescartes heredados yprotocolo; noafirmarextensionesyaejecutadas.

## CellNN CUReT cerrado yDTDdespachado — 15:32 UTC

CUReT2/2 terminó15:27:02 UTC. Sin procesoscompetidores,se verificaron
recibos/cadenas/hashes y5612llamadasprobabilidades/raw:consolidaciónexit0 en
results/analysis/cellnn_curet_external_summary_20261102_v1. F1macro medio
0,6933675335753301,media31,0245325753742ms. SummarySHA256
7990d0529d7dc3f69020de0776c9ffec9e1dad1bb5ac918a275aed103e64002f.
20comparacionesporcondición y10agregadas,incluyendopérdidas. AdaptativoSVM
0,998395978/36,830131104ms;ResMLP0,998930736/30,472171798ms. No inferencia
deventajafísica porpequeñas diferencias demedias enfechasdistintas/hardware
compartido. EsADAPTACIÓN,cifraspaper noreproducidas. FMDsigue14/15sinmedia.

17tests pasan (13preparaciónCUReT/DTD,4antiagregaciónparcial). CasosDTD
rechazan reintegrodefitcongrupostest,omisiones,exclusionesincorrectas ytests
faltantes/duplicados. Preparador yreceta selladossinmodificar;se añadierontests.
PreflightDTD verificó5640imágenes,47clases,10particionesexactas,1880testcadauna
yexclusionesheredadas3–11filasfit;sinrepetirningúnexperimentoCellNNDTD.

Cola results/analysis/cellnn_dtd_external_queue_20261102_v1/manifest.json,
SHA256ba7d8171362bc546f23db04696c482619cc49684ff5ee5104fcc44ca12f87640.
Worker63192/sesión93243,inicio15:32:48 UTC,extract63200,201/3753fit alcorte.
ÚnicoGPUworker,CPU2hilos,ventana12h,cero condicionesDTDcompletas. Primera
auditoríahabilitanueverestantes.18800llamadasplanificadas,nocomo medidas.
No editarfuentes/correrotrosfits/extracciones/tests. Tras10/10consolidar;
despuésOutexCellNNnuncaejecutado,Soil,KTH, sinretryHyTexOutex/Neshov/FMDparcial.

### CellNN DTD: cuatro auditorías completas — 15:46 UTC

Índices0–3 complete,4/10,7520llamadasauditadas. Quinto split índice4
enextractPID63455,mismoworker63192 vivo. No nuevosfallosobservados niotro
worker. No mediasDTDcompletas/no consolidación hasta10/10. Fuentes/pesos/
headparams intactos; no iniciarfits/extracciones/testscompetidores.

### CellNN DTD: ocho auditorías completas — 16:01 UTC

Índices0–7 complete,8/10,15040llamadasauditadas. Novenosplitíndice8 enextract
PID63673,2501/3751fit alcorte;worker63192 vivo. Sinfallosnuevosobservados.
No consolidar nipublicar mediaDTDcompleta antes de10/10. Mantener colaactiva
sincompetidores; OutexCellNNsiguiente,nuncaejecutado, no confundir conHyTexOutex.

## CellNN DTD cerrado yOutexdespachado — 16:17 UTC

DTD10/10 terminó16:06:58 UTC. Sinworkerspropiosactivos,reagregacióncompleta
exit0 de18800llamadas conprobabilidades/argmax/truth/tiempos yhashes:
results/analysis/cellnn_dtd_external_summary_20261102_v1. F1macro medio
0,21618426956606546,media31,519920409574468ms. SummarySHA256
51688085e4f884b421ef44b31d6a464dcb9a99b8cf6e2d650b177428c3158ac9.
100comparacionesporcondición y10agregadas;F1bajo conservado sinajustes.
AdaptativoSVMlocal0,866856520/54,353745514ms;ResMLP0,866019864/47,612719303ms:
mayorF1 pero mayorlatencia que laadaptación. Reserva físicaDTD/SVM yhardware
compartido/fechasdistintas intactos; sininferenciaglobal nicifraspaperreproducidas.

24tests pasan(20preparadorCUReT/DTD/Outex,4consolidador): inversión,orden,
grupos,clases,testfaltante ycolumnaoficial alterada rechazados paraOutex.
No fuentescientíficas modificadas. PreflightOutexCellNNvalidó1360imágenes,
68clases,680fit/680test exactos. Condición nueva deOTROmétodo; no retrydel
HyTexOutexrequires_review, cuyosartefactos quedanintactos.

Cola results/analysis/cellnn_outex_external_queue_20261102_v1/manifest.json,
SHA25636087051177e2828e2c543ecacbd9da68aa230caca6c8d7a1b454e0f577a7a31.
Worker63979/sesión69347,inicio16:17:37 UTC,extract63987;680llamadasplanificadas,
ceroauditoríascompletas aldespacho. ÚnicoGPUworker,CPU2hilos,ventana12h.
Consolidarsolo1/1 y680llamadasauditadas;despuésSoil/KTHCellNNnuncaejecutados.
FMD14/15sinmedia yrequires_review42/f0,Neshov,HyTexOutex sinreintentar.

## CellNN Outex cerrado ySoildespachado — 16:32 UTC

OutexCellNN1/1 terminó16:18:41 UTC;se verificaron680llamadas/cadenas/hashes
yconsolidaronexit0 en cellnn_outex_external_summary_20261102_v1. F1macro
0,6355652763549626,media29,910913772058827ms. SummarySHA256
fc051d62dcdf7b9967aa7b95d7e734a039b197b29f7b99ee3169d75af5c87497.
Diezcomparacionescompletas incluyendopérdidas.AdaptativoSVMlocal0,927581357/
40,327672615ms;ResMLP0,960868749/21,648946828ms. MayorF1deambos,latencias
distintas porhead, sin inferenciavariafísicaaislada porfechas/hardwarecompartido.
Estaadaptación usaBcanal128ycheckpointautor;no esporcentajepaperreproducido.
HyTexOutexrequires_review sigueintacto;no semezclanmétodos ni se reintenta.

30tests preparación/consolidadorpasan,incluidos foldsSoil227/229 yrechazos
deidentidad,grupos,clases,tests/universo. PreflightSoilverificó1140imágenes,
7clases,15particionesexactas,coberturaporsemilla ylabelsarchivados. Mismo
método/headparams/pesos/tolerancias;ningúnajuste porbajoF1DTD/Outex.
Cola results/analysis/cellnn_soil_external_queue_20261102_v1/manifest.json,
SHA256f5ab7717bd58f6b4114db404935272b9482b989c4dece647c6be32e5c8965c14.
Worker64205/sesión58028,inicio16:32:38 UTC,extract64213,1/912fit alcorte.
15condiciones/3420llamadasplanificadas,ceroauditoríascompletas aldespacho.
ÚnicoGPUworker,CPU2hilos,ventana12h,primeranuevaauditoríahabilita14restantes.
Tras15/15consolidar ponderandotiempos porllamadasreales;despuésKTHCellNN.
No FMDmediacompleta, sigue14/15con42/f0enrevisiónsinretry.

## CellNN Soil cerrado yKTHdespachado — 16:47 UTC

Soil15/15 terminó16:46:14 UTC. Sinprocesospropiosactivos,auditadasyreagregadas
3420llamadasexit0 en cellnn_soil_external_summary_20261102_v1. F1macro medio
0,35496685877029893,mediaponderada32,98486323157895ms.SummarySHA256
55e3c517f58651710b7a768dbf2b677cc6709bcc6ba1a526e840f5d94abcbee1.
150comparacionesporcondición y10agregadas, sinomisiones/ajustesporbajoF1.
AdaptativoSVMlocal0,872540331/38,482833136ms;ResMLP0,866818251/48,326247217ms,
mayorF1 peromayorlatencia promedio,hardwarecompartido/fechasdistintas.
RepresentaciónDeiTcomparadoresSoil ycarácterADAPTADO conservados.

37tests pasan(33preparador y4consolidador),incluidoseparaciónmuestrasfísicas
KTH,rejecióninversión1/3,grupos/clases/identidad/testalterados. PreflightKTH
verificó4752imágenes,11clases,4particionesexactas3564train/1188test, sin
compartirmuestrasfísicas. No cambiosdeprotocolo,reservahistóricadecascadasintacta.
Cola results/analysis/cellnn_kth_external_queue_20261102_v1/manifest.json,
SHA256de416b777cb38d3cd1d2d0c089bf304e3e32a329bc6045aedfc39a812775b970.
Worker64938/sesión49285,inicio16:47:39 UTC,extract64941,201/3564fit alcorte;
4condiciones/4752llamadasplanificadas,ceroauditoríasKTHcompletas. ÚnicoGPUworker,
CPU2hilos,ventana12h,primeranuevaauditoríahabilitatresrestantes.
Consolidarsolo4/4;despuésactualizarcobertura deambasadaptaciones completas
pordataset,nosistemasconpanelesseiscompletos(FMDCellNN14/15,OutexHyTex0/1).

Corrección aritmética de planificación:47condiciones deUNmétodo externo suman
36264llamadas, no72528; la cifra anterior duplicaba los dosheads de nuestro
panel. 362640llamadas locales=36264×2heads×5métodos. No se quitaron condiciones
ni imágenes; FMD3000 yCUReT5612 siempre tuvieron conteos correctos. Testnuevo
comprueba el total por sistema, sin inferir nueva cobertura experimental.

## Corte consolidado para reunión semanal — 2026-11-02

Este corte reemplaza las descripciones de procesos activos anteriores, no los
resultados ni las reservas. Panel propio cerrado 94/94, 470 filas condición ×
método y 362640 llamadas primarias; 9400 observaciones DTD adicionales separadas.

LBP+dCellNN/KTH terminó 4/4 condiciones y 4752 llamadas auditadas. Summary:
`results/analysis/cellnn_kth_external_summary_20261102_v1/summary.json`, SHA256
`5fd8fd876f7b696cfd099d6f5b06b9fd52eace5b38f05d2cc725e141959aec7c`.
Macro-F1 medio 0.5750307215685133; tiempo medio 31.93726876094276 ms.

Cobertura externa en
`results/analysis/external_adaptation_coverage_20261102_v1/coverage.json`, SHA256
`7ca8af60a326bfe3cbfd62111baeaf4e50d9fead13b4df20a0b015365dfabf8e`:
HyTexNet adaptado y LBP+dCellNN adaptado tienen cinco datasets completos y
46/47 condiciones cada uno. HyTexNet/Outex 0/1 y CellNN/FMD 14/15 permanecen
incompletos/requieren revisión, sin medias completas inventadas ni reintentos.
Neshov mantiene el fallo científico de paridad, sin nueva medición.

Preparada exposición de nueve diapositivas, tablas editables, notas de fuentes
y guion oral en `results/analysis/weekly_presentation_20261102_v1/deliverables`.
Validaciones de paquete, geometría, fuentes y reimportación aprobadas; nueve
diapositivas inspeccionadas visualmente. Diferencias descritas como compromiso
F1–latencia, no superioridad estadística ni reproducción de porcentajes publicados.
Esta preparación no ejecutó experimentos, reintentó fallos, cambió el manuscrito
ni realizó commits. Próximo trabajo experimental conserva las restricciones
de revisión existentes y requiere recetas verificables para otros sistemas.

## Recuperaciones cerradas y nuevo Neshov individual — 2026-11-02

El autor pidió corregir los fallos y continuar hacia los resultados originales de
los papers. El criterio es reproducibilidad con evidencia, no seleccionar ni
ajustar por cercanía al valor publicado. Se fijó la autoridad y alcance en
`RECUPERACION_AUTORIZADA_Y_FIDELIDAD_PAPERS_2026-11-02.md`.

La cola `results/analysis/authorized_paper_infra_recovery_20261102_v1` terminó
ambos casos, cuatro etapas por caso. Se revisaron hashes de fuentes, recibos de
etapas, predicciones y tiempos; se verificaron de nuevo las fuentes del agregado
anterior de 14 condiciones. `external_adaptation_coverage_20261102_v2` registra
47/47 condiciones y 36264 llamadas por cada uno de HyTexNet y LBP+dCellNN
adaptados, con sus seis datasets completos. HyTexNet/Outex: macro-F1
0.8927455542401957, media 29.04045229852941 ms, 680 llamadas. CellNN/FMD:
macro-F1 promedio por 15 particiones 0.2476506444806386, media por llamada
29.655137729333337 ms, 3000 llamadas. Ambos son sistemas adaptados al panel;
no son cifras originales del paper ni prueban reproducción fiel. No se mezclan
medias incompletas ni F1 histórico con tiempos nuevos. Se mantienen reservas
KTH/DTD, fechas distintas y hardware compartido.

Neshov: diagnóstico nuevo en `neshov_batch_parity_diagnostic_20261102_v1`
reprodujo exactamente los dos errores lote8/lote1 originales; las repeticiones
dentro de cada tamaño de lote fueron exactas. El primer lanzamiento diagnóstico
falló antes de cargar el modelo por ruta de preflight; se resolvió leyendo el
argv sellado y verificando su hash. No evaluó imágenes ni modificó la cola vieja.
El gate lote8/lote1 original sigue fallido: no se declara pasado ni se modifica.

La nueva variante prospectiva usa extracción de fit individual y evaluación
individual, manteniendo checkpoint, capas, FP32, cabeza, semillas, particiones,
presupuesto y umbral 1e-4. Descripción y reservas en
`PROTOCOLO_NESHOV_BATCH1_CORREGIDO_2026-11-02.md`. 24 pruebas del runner y
adaptador pasaron antes de despachar. Cola nueva
`results/analysis/neshov_fmd_batch1_queue_20261102_v1`, manifiesto SHA256
`7132fae473215076b6f66a5895052620b03e93638ec0210d8512a0a62f4eece0`.
Worker 5289: condición FMD/42/f0 cerrada y 14 restantes secuenciales; verificar
estado vivo antes de actuar, auditar todas las llamadas, no tratar parciales
como medias completas ni volver a lanzar un fallo nuevo automáticamente.

Fidelidad original pendiente: el paper Neshov describe 10 repeticiones de
validación cruzada de 10 pliegues en FMD y publica accuracy; el panel común usa
3 semillas × 5 pliegues y reporta macro-F1 y accuracy. Versiones publicadas de
Python/PyTorch/timm difieren del entorno disponible. Falta verificar índices y
detalles no especificados antes de rotular una corrida como reproducción fiel.

## Neshov FMD común auditado y réplica aproximada 10 × 10

El panel común Neshov versión batch1 terminó y se reauditaron predicciones,
tiempos, 60 recibos de etapa y procedencia. Resumen en
`results/analysis/neshov_fmd_batch1_external_summary_20261102_v1`: 15/15,
3000 llamadas, F1 medio por partición 0.94213042191491 y tiempo medio por
llamada 16.890381723666664 ms. No es el resultado original del paper; el gate
previo batch8/batch1 continúa documentado como fallido. Comparaciones por los
dos clasificadores y cinco estrategias locales, con ganancias y pérdidas,
están en `comparison_dataset.csv` y `comparison_by_condition.csv`.

Se congeló una aproximación separada al protocolo FMD original de 10 repeticiones
× 10 folds, 100 condiciones y 10000 llamadas. Presupuesto, RNG, estratificación,
versiones locales y las decisiones no verificadas se declaran en
`PROTOCOLO_NESHOV_FMD_10X10_APROX_2026-11-02.md`. El paper informa 96.7 % de
accuracy, no F1; no seleccionar resultados para forzar coincidencia. Manifiesto
`results/analysis/neshov_paperlike_fmd_10x10_queue_20261102_v1/manifest.json`,
SHA256 `8d9259af0faaf5691124247ac731020f910e73dfe78088bf74aed600e28f371f`;
worker 7356 despachado. Primera condición auditada habilita las 99 restantes.
No calcular medias completas si falta alguna condición; auditar con
`scripts/consolidate_neshov_paperlike_fmd.py` tras 100/100. Siete pruebas nuevas
de agregadores, particiones, semillas y expansión pasaron antes del despacho.

La ampliación común Neshov a CUReT, DTD, Outex, Soil y KTH quedó preparada y
validada sin ejecutarse, 32 condiciones y 33264 llamadas. Manifiesto
`results/analysis/neshov_batch1_extension_queue_20261102_v1/manifest.json`,
SHA256 `d76b39cb95a8bda7c740624407bd3584a0c2e3b4ee9a96f6ce9eac515e9257a4`.
Despacharla tras la cola 10×10, sin solapamiento de GPU y siguiendo
`PROTOCOLO_NESHOV_BATCH1_EXTENSION_2026-11-02.md`.

En la documentación primaria apareció una discrepancia: CellNN e HyTexNet
describen KTH con un tercio de imágenes de entrenamiento y citan Liu 2016,
cuya tabla lista 3564/1188 imágenes de entrenamiento/test. La guía original
KTH identifica pose/iluminación en los códigos de imagen, pero no cuál subconjunto
eligieron esos autores. Se documentó sin homologar splits ni números en
`results/analysis/paper_original_fidelity_20261102_v1/EVIDENCIA_Y_RUTA.md`.

## KTH aproximado al tercio descrito en papers — preparado, no despachado

La guía oficial KTH identifica im1–3 como pose frontal con tres luces e im4–6
como pose derecha con esas luces; escalas 2–10. CellNN e HyTexNet no permiten
verificar qué dos poses ni seis escalas eligieron. Para una única aproximación
prospectiva se fijaron escalas 2–7 e imágenes 1–6 como fit: 1584 imágenes fit y
3168 test, con las 44 muestras físicas compartidas entre ambos. Selección local
no verificada contra autores, explícitamente distinta del panel robusto 3/1.

`PROTOCOLO_KTH_TERCIO_PAPERLIKE_2026-11-02.md`,
`scripts/prepare_kth_paperlike_queue.py` y pruebas sintéticas fijan el alcance.
No se han ejecutado ni los tests ni el preflight durante el benchmark Neshov
activo. Tras la cola 10×10, probar en aislamiento; si pasan, verificar recursos
y congelar preflight, ejecutar una vez ambos sistemas en cola nueva, auditar
3168 llamadas por sistema. Reportar accuracy/F1 y tiempos propios, sin afirmar
partición o cifras exactas de autores; no ajustar el subconjunto por resultados.
Los datos y la partición por muestras físicas previos permanecen intactos.

## Estado actualizado — 2026-11-03

La aproximación Neshov FMD 10×10 terminó y fue reagrupada en
`results/analysis/neshov_paperlike_fmd_10x10_summary_20261102_v1`: 100/100
condiciones, 10.000 llamadas, accuracy medio 0.94220, desviación descriptiva
entre repeticiones 0.00402, macro-F1 medio por pliegue 0.94192 y 16.767 ms
por llamada. El paper informa 0.967 de accuracy. La réplica exacta no se
consiguió ni se afirma; el protocolo local usa supuestos de partición/semillas
y versiones diferentes.

La aproximación KTH de un tercio terminó en dos ejecuciones independientes,
cada una con 3.168 llamadas: HyTex accuracy 0.93908, macro-F1 0.93944,
29.070 ms; LBP+dCellNN accuracy 0.66004, macro-F1 0.62382, 32.285 ms.
Los artículos informan accuracy 0.9979 y 0.9129 respectivamente. Mantener la
etiqueta de aproximación: se eligieron imágenes/escalas localmente y 44 muestras
físicas se comparten entre entrenamiento y prueba. No comparar como si fuera
el panel KTH separado por muestra.

La extensión Neshov batch-1 a CUReT, DTD, Outex-13, Soil y KTH-TIPS2b terminó
32/32 condiciones y 33.264 llamadas. Auditorías independientes por dataset,
comparaciones por estrategia, provenance y hashes están en
`results/analysis/neshov_batch1_extension_summary_20261103_v1/INFORME.md` y
en `results/analysis/neshov_batch1_{curet,dtd,outex13official1360,soiloriginal,kthtips2b}_summary_20261103_v1/`.
Es una adaptación Neshov al panel común, no reproducción fiel de porcentajes.
Los valores resumidos se conservan también en los archivos summary.json por
dataset. Soil registra pérdidas pequeñas frente a algunas variantes locales;
se informa el rango completo y no se selecciona un subconjunto ganador.

Siguiente paso: mantener cualquier nueva réplica separada por receta y dataset,
con comparación de las mismas llamadas online. No repetir estas tres colas ni
alterar sus fuentes selladas; cualquier diferencia de receta requiere nueva
cola, manifiesto y etiqueta metodológica.

## Auditoría de código público de papers, 2026-11-03

Inventario dirigido de los 11 PDFs de `docs/referencias`, artículos editoriales
y GitHub: ver `results/analysis/paper_code_availability_20261103_v1/INFORME.md`.
Hallazgos principales: Chang et al. enlaza directamente `UESTC-nnLab/LBP_Contour`;
la inspección de `main_otc12.py` confirmó que hay un flujo OTC12 con checkpoint
CellNN, fusión LBP+contornos, split codificado y MLP. Sin embargo, el preflight
detectó una discrepancia material: el PDF especifica 480 imágenes Inca/0° para
train y 8.640 para test, mientras el script particiona 4.560/4.560 e incorpora
parte de las iluminaciones no-Inca al entrenamiento. OTC12 tampoco está local.
Por integridad, no ejecutar el script como si midiera la partición publicada ni
corregirlo silenciosamente. Commit consultado: `89fc3d6097ab13f800c8d2828f4d6ed2225f3eb1`.
Ataky et al. enlaza
`stevetmat/BioInspiredFDesc` (MIT), pero la raíz es BiT v0.1.5 y CMIG/EBiT
contienen avisos de código futuro, no se acreditó el pipeline completo del
paper multiescala de 2023. Neshov enlaza bajo la cita [46] código de
split/aumento del proyecto Sheth et al. para clasificación de suelo, no el
sistema BEiTv2+agregación+MLP. No se localizó código oficial para los demás
títulos en la búsqueda realizada; esto no demuestra inexistencia. Ningún repo
se clonó o ejecutó, así que no afirmar paridad numérica. Auditoría offline
cerrada; hallazgos y URLs de fuentes en
`results/analysis/paper_code_availability_20261103_v1/INFORME.md`. Preflight
offline completado, pero medición bloqueada hasta conseguir OTC12 por vía
autorizada y resolver el conflicto de partición/licencia/semilla. Si se usa el
split que el paper describe con el método del repo, deberá ser una
reimplementación adaptada, con cola/manifiesto nuevos y etiqueta explícita; no
es ejecución exacta del script publicado. Nunca reutilizar los resultados
KTH/Outex-13 adaptados como réplica OTC12. Los cierres Neshov/KTH y paneles
previos permanecen sellados y no se repiten.

## Segunda pasada de disponibilidad de código, 03-11-2026

Se contrastaron declaraciones de disponibilidad en los PDFs/fuentes editoriales y
se hicieron búsquedas exactas de repositorios por nombre para HyTexNet,
AsTexNet, DeepLumina, RGB Pixel N-grams y Compact color-texture. No aparecieron
repositorios coincidentes en esas búsquedas. AsTexNet indica que datos
procesados/detalles de implementación se entregan bajo solicitud razonable;
HyTexNet indica que código/datos se entregarán bajo solicitud razonable. El
artículo de DeepLumina enlaza datasets pero no se encontró un enlace de código
en su disponibilidad; RGB Pixel N-grams describe dos variantes pero su ficha
editorial consultada tampoco enlaza implementación. “No localizado” no prueba
inexistencia. Evidencia, URLs, consulta y límites en
`results/analysis/paper_code_availability_20261103_v1/ANEXO_BUSQUEDA_CODIGO_20261103.md`.

No hay nuevo método listo para atribuir sus porcentajes al código original.
LBP_Contour sigue bloqueado por OTC12 ausente y split repo/paper contradictorio;
BioInspiredFDesc no acredita pipeline completo. Para avanzar sin autor/data
externos, cerrar primero ficha de receta para DeepLumina o RGB Pixel N-grams y,
si se implementa con la partición común local, etiquetar explícitamente como
adaptación/reimplementación, no reproducción fiel. No correr, bajar datos ni
solicitar materiales hasta sellar receta, recursos, versiones, semillas y
medición online.

## DeepLumina FMD: cierre de receta de adaptación, 03-11-2026

Preflight local encontró el FMD original (1000 imágenes), manifiesto de clases,
y una ResNet101 ImageNet timm offline con hash; no son el código ni los pesos
MATLAB exactos del paper. La tabla del artículo apunta a `fc1000`, así que los
embeddings locales GAP de 2048 se excluyen. Se congeló un protocolo **adaptado**
que concatena `fc1000(RGB)` + `fc1000(YIQ-Y)`, ECOC sparse-random con todas las
decisiones de solver/RNG explícitas y 15 particiones comunes para comparación.
El artículo reporta accuracy FMD 90,15 % ± 1,2; no publica índices/semilla y no
reporta macro-F1. Esta diferencia impide afirmar que se recupera el resultado
publicado, aunque la adaptación permita compararlo en nuestro panel.

Receta, hashes, versiones, filas comunes, scope temporal, límites de fidelidad
y condiciones de despacho están en
`docs/fsc_tex/PROTOCOLO_DEEPLUMINA_ADAPTACION_FMD_2026-11-03.md`. Estado:
**preflight concluido y primitives probados sintéticamente; sin extracción,
fit ni benchmark**. Pasaron 4/4 pruebas unitarias CPU en
`tests/test_deeplumina_adaptation.py`; ver el informe breve en
`results/analysis/deeplumina_recipe_closure_20261103_v1/INFORME.md`. Próximo
paso: implementar/probar runner offline, verificar índices exactos por fila
desde los registros sellados sin editarlos y congelar código/config/modelo/
datos/índices antes de despachar cualquier corrida bajo lock global GPU.

## Neshov FMD paper-like 10x10: consolidación, 03-11-2026

La cola congelada `results/analysis/neshov_paperlike_fmd_10x10_queue_20261102_v1`
ya estaba terminal 100/100 y sin worker activo. La primera auditoría se detuvo
antes de escribir resultados al detectar drift de versiones: se invocó por
error Python del sistema (NumPy 2.5.1) y el manifiesto exige el entorno
confirmatorio (Python 3.12.13, NumPy 2.4.4, PyTorch 2.12.1+cu126,
torchvision 0.27.1+cu126, Pillow 12.2.0; resto de paquetes coincidente).
No se modificó manifiesto ni se repitió ninguna llamada científica; se corrió
solo la consolidación con `.venv-confirmatory/bin/python`, después de validar
que coincidiera el entorno congelado.

Auditoría cerrada: 100/100 condiciones y 10.000 llamadas online de la misma
predicción temporizada; accuracy media por repetición 0,94220 (SD descriptiva
0,00402), macro-F1 media por fold 0,94192 y latencia media por llamada 16,767
ms. El artículo reporta accuracy 0,967; diferencia local −2,48 puntos
porcentuales. El artículo no da macro-F1 ni latencia directamente comparable.
Esto es una **aproximación paper-like**, no reproducción fiel: split/semillas
aproximados, versiones y hardware diferentes; el SD no es intervalo de
confianza porque las repeticiones no son datasets independientes. Evidencia,
provenance y CSV en
`results/analysis/neshov_paperlike_fmd_10x10_consolidated_20261103_v1/`.

Las siguientes etapas del despacho ya constan cerradas en el workspace y no se
repitieron: KTH tercio aproximado, dos métodos completos, 3.168 llamadas por
método, con 44 muestras físicas compartidas entre fit/test; y la extensión
Neshov de cinco datasets, 32/32 condiciones y 33.264 llamadas, cada dataset
consolidado en directorio propio. La auditoría KTH informa HyTex accuracy
0,93908 / macro-F1 0,93944 / 29,070 ms y CellNN accuracy 0,66004 / macro-F1
0,62382 / 32,285 ms. La tabla y reservas de extensión están en
`results/analysis/neshov_batch1_extension_summary_20261103_v1/INFORME.md`;
incluye pérdidas y ganancias frente a las diez cabezas locales y advierte que
la latencia proviene de distintos estados/fechas de hardware. No preparar ni
despachar colas ya terminadas. Próxima acción independiente: continuar el
preflight/implementación adaptada DeepLumina FMD ya especificado, sin medir
hasta tener tests sintéticos, IDs y hashes del manifiesto congelados; OTC12
sigue bloqueado hasta resolver acceso/dataset y el conflicto paper/repo.
