# 6LBP+dCellNN+MLP ADAPTADO: FMD común, versión1

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: adaptación completa autorizada de referencia, prospectiva.
- Origin Date: 2026-11-02.
- Verification Status: fijado antes de features o fits del panel FMD.
- Version Label: cellnn_fmd_adaptation_v1.

Referencia DOI10.1016/j.eswa.2023.122100; implementar el sistema completo
6LBP+dCellNN+MLP, no LBP solo. Versión delautor299502cbb2243ecb78018110236871f261aa92b2
usa mcellnn ycheckpointcompatible. HEAD89fc3d6 incompatible NO se utiliza.
Pesos congelados delautor10.311bytes, SHA256
af56a7e939c93e4ec7b0e2c8af348bff756ac25267af4ca45b52005552fba65f.
No entrenarDRIVE ni modificar red/recurrencias; cargar20tensoresstrict yFP32,
sin strictFalse ni inicializaciones faltantes. Prefijo DataParallelmodule
se elimina de forma exacta; no otros nombres. ContornosGPU, cabezaCPU2hilos.

Adaptación local explícita: decodificar OpenCVBGR, resize128×128INTER_LINEAR,
usar canalB como getHist delautor (no sustituir porY/RGBpromedio). Contornos
reciben normalización porimagen(std→minmax255), CLAHEclip2/tile8×8,gamma1.2;
LBP usa canalBuint8 original redimensionado, no imagenCLAHE. Cualquier imagen
constante/no finita falla, sin epsilon/fallback/omisión. Red normaliza [-1,1],
recurrencias20 con fusiones antes de pasos5/10/15; ceros iniciales,avgpool2,
nearestupsample2,conv3padding1 ymezclas1×1 como fuente. Contornosbinarios
porvalor>media de cada salida. No batching deimágenes por estadísticos globales.

Seisescalas(P,R):(8,1),(16,2),(24,3),(8,3),(12,5),(16,7),skimageLBPuniform.
Fusión4/2/1×(P+2) yhistogramasOpenCV(80,144,208,80,112,144),total768,
countscrudos, sin normalización ni reducción posterior añadida.
Classifier sklearnMLPClassifier(hidden_layer_sizes=(400,),activation=relu,
solver=adam,alpha=0.0001,batch_size=auto,learning_rate=constant,
learning_rate_init=0.001,power_t=0.5,max_iter=10000,shuffle=True,random_state=42,
tol=0.0001,verbose=False,warm_start=False,momentum=0.9,nesterovs_momentum=True,
early_stopping=False,validation_fraction=0.1,beta_1=0.9,beta_2=0.999,
epsilon=1e-8,n_iter_no_change=10,max_fun=15000). Son defaults locales
explicitados de versión congelada ysemilla añadida; no cifraspaperreproducidas.
Unaconfiguración, sinCV/tuning, ajustar solo train yfinalestador retornado.
Si no converge alpresupuesto/valoresnofinitos,error requiere revisión, sinretry.

Antes de datos reales: paridad con versiónautor en entradas sintéticas,
FP32maxabs≤1e-4 para salida flotante yexactitud de tres contornosbinarios e
histogramas768; guardar vectores/errores antes de aceptar. Tolerancia fija,
no cambiar kernels/precisión para forzarpass. Gatefallido requiere revisión.
Constantes constituyen tests negativos con rechazo, no parte del gatepositivo.

FMD: mismas15particiones externas (3semillas×5folds),800train/200test,10clases,
1000imágenes verificadas,3000llamadas. Congelar fuentes,pesos,bibliotecas,
particiones,MLPparams yargv antes defit. Primera auditoría habilita14restantes.
Extractfitbatch1, gateprimer/últimofit reextraído (featuresexactas),train,
online,audit. F1/timing de mismas llamadas individualesfile→features→clase;
guardarpredict_proba con classorder,argmax,predicción,truth yelapsed_ns/ms,
sin llamarlas logits. Cronómetro incluye decode/preproceso,transferencias,
contornos,LBPs,histogramas yMLP, sincronizaciónGPU alinicio/final; excluye
carga depesos/head yhashverificación,cinco warmupsprimerfit excluidos.
No featurescacheonline. Timeout7200/3600/14400/300s,window12h,globalGPUlock,
sin fits/extracciones concurrentes,CPU2hilos ydeterminismoFP32 fijos.

Todo en carpetasnuevas,fuentes/recibos/hash/predicciones/timing/errores.
Fallo requiere revisión, no retry/omitircasos/relajartolerancias/cambiarmétodo.
Consolidar solo15/15 y3000llamadas,comparar ambosheads×cincométodos ymostrar
pérdidas/ganancias. Hardwarecompartido/fechasdistintas, sininferenciaglobal.
No réplica deporcentajes publicados. Mantener reservasKTH/DTD enextensiones,
no repetirpanelpropio niOutex/Neshovrequires_review; noVisTex/manuscrito/commits.
