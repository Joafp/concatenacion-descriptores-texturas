# Estado de comparadores externos, 2026-11-02, 13:46 UTC

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: cierre técnico de datasets completos; no inferencia estadística.
- Verification Status: llamadas reagregadas con hashes y recibos por dataset.
- Version Label: external_comparison_status_1346.

El panel propio permanece cerrado94/94, sin repetir. Esta tabla contiene un
sistema completo ADAPTADO de HyTexNet, no cinco métodos externos ni una
reproducción de sus porcentajes publicados. No hay media global de seis datasets.

| Dataset | Condiciones completas | Llamadas | F1 macro medio de condiciones | Media ms por llamada |
|---|---:|---:|---:|---:|
| FMD | 15/15 | 3000 | 0,741416822 | 31,180760 |
| CUReT | 2/2 | 5612 | 0,983066810 | 32,412854 |
| DTD | 10/10 | 18800 | 0,624152671 | 33,512065 |
| SoilOriginal | 15/15 | 3420 | 0,787961802 | 33,114365 |
| KTHTIPS2b | 4/4 | 4752 | 0,825855669 | 30,977042 |
| Outex13Official1360 | 0/1 | 0 | No medido | No medido |

46condiciones completas en cinco datasets,35584llamadas. Faltan680llamadas
Outex para el panel de47condiciones/36264llamadas; NO declarar completo.
Cada resultado anterior posee condition_metrics.csv,comparison_by_condition.csv,
comparison_dataset.csv yprovenance.json en results/analysis/
hytex_{fmd,curet,dtd,soil,kth}_external_summary_20261102_v1, respectivamente.
Comparaciones completas incluyen ambos heads×cinco métodos, con pérdidas.
F1 ytiempos proceden de las mismas llamadas. Hardwarecompartido/fechas distintas;
reserva física DTD/SVM, reserva histórica KTH y representaciónDeiT corregida
Outex/Soil se conservan. No inferencia de independencia entre seeds/folds.

KTH completó4auditorías a13:46:14 UTC. SummarySHA256
b988d2c5fc1768e4998c7bbba99ddbee9ac0573ca126987f28ca3d7446536edd.
Su adaptativoSVMlocal0,938996502/30,953839555ms frente aHyTex0,825855669/
30,977041997ms tiene mayorF1 y medias de tiempo muy próximas; una diferencia
de0,0232ms no prueba ventaja física reproducible bajo este hardware compartido.
AdaptativoResMLPlocal0,939089669/32,162136261ms: mayorF1 y mayortiempo medio.

## Intentos en revisión, no reintentar

- Neshov FMD: discrepancia de features sobre tolerancia1e-4; primera condición
  requiere revisión,14dependientes bloqueadas, cero llamadas externas. No ajustar
  kernels,precisión,tolerancia ni método para aceptar un resultado diferente.
- HyTex Outex: falta checkpoint_sha256 enpreflight, antes de cargar modelo;
  cero llamadas y evidencia íntegra, requires_review. No repetir bajo instrucción
  vigente de reanudar solo nunca ejecutados. No confundir con fallo científico.

## Otros papers: búsqueda primaria acotada

Consultas AsTexNetcode/github,DeepLuminagithub,CompactDITCcode no verificaron
repositorio oficial; esto NO prueba inexistencia. No se descargaron pesos,
software ni datasets, ni se contactaron autores.

AsTexNet: resultado indexado de editor accesible; apertura directa429, no
insistir ni eludir límite. Parámetros faltantes siguen en RECIPE_READINESS.md.
Fuente: https://www.mdpi.com/2076-3417/16/12/5743

DeepLumina: página del editor abierta inicialmente con métodoRGB+luminancia,
ResNet101 ySVM, pero consultas posteriores de localizadores devolvieron403.
No se verificó código/receta completa ni se aceptaron esos errores como éxito.
Fuente: https://onlinelibrary.wiley.com/doi/10.1155/2022/9510987

Compact: fuente editor confirma fusión de descriptores ycompresiónDITC;
faltan artefactos/implementación verificables. No sustituir por PCA ni un
descriptor distinto. ProtocoloKTH debe verificarse por apartado/dataset,
sin generalizar descripciónKTH2a aKTH2b.
Fuente: https://www.sciencedirect.com/science/article/abs/pii/S0167865514002451

Siguiente acción: continuar auditoría local de recetas de los demás PDFs y
artefactos oficiales; fijar cualquier adaptación completa prospectivamente,
con presupuesto explícito ytests, antes de nuevos fits. No presentar operadores
aislados deAsTexNet como método completo. Sin cambios almanuscrito/commits/push.
