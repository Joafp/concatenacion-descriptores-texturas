# Auditoría de recetas de concatenación/fusión, 02-11

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent; pdf para lectura.
- Origin Mode: preparación técnica, no reproducción completa ni evaluación estadística.
- Verification Status: ANALYZED para pasajes leídos y operadores aislados.
- Version Label: recipe_readiness_v1.

## Lectura y procedencia

Fuentes locales aportadas por autor, sin envío externo ni descargas. Sidecars
compact_preflight.json y astexnet_preflight.json: PASS estructural de7/30páginas,
hashes de PDF fijados. Esto no certifica lectura integral humana ni réplica.
Intento WSL initial: UNAVAILABLE por pypdf ausente; no se instaló nada en entorno
experimental congelado. Runtime documental empaquetado resolvió parser en modo
stdout; --output anclado no es compatible conWindows y falló sin alterar PDF.
Los JSON stdout emitidos se conservaron como sidecars, no se inventó PASS.

Texto derivado mediante pdftotext -layout en archivos separados de fuentes.
AsTexNet: método3.1–3.5, protocolo4.2 y disponibilidad; ecuaciones5–9 inspeccionadas
visualmente en imagen astexnet_p8.png. Compact: secciones3/3.1/4/5 y tablas
de dimensionalidad. Extracciones largas truncadas no equivalen a leer todas las
secciones; los pasajes relevantes se consultaron por separado. No se alteró PDF.

## Compact color–texture, DOI10.1016/j.patrec.2014.07.020

Fuente: docs/referencias/1-s2.0-S0167865514002451-main.pdf,
SHA256087aff1a04e093499fc8b0054c359397fd27b00a648fe96c213896e54b6fb9d3.

Sistema descrito: concatenación CLBP/WLD/BGP/LPQ/BSIF,3184componentes; DITC
supervisado por clases de entrenamiento reduce a500; color discriminativo50
se concatena después. Clasificación one-vs-all SVM con kernelchi2 y mayor
respuesta. No sustituir DITC por PCA/SVD ni color discriminativo por RGB simple.
No confundir CLBP con bloqueDRLBP local ni BSIF con un filtro aleatorio propio.

Disponibilidad todavía sin cerrar: filtrosBSIF aprendidos y mapeo de color50,
parámetros exactos de cada descriptor multirradio, implementación DITC y SVM
chi2/regularización. Debe verificarse fuente/código/artefactos antes de considerar
ejecutable. No basta implementar solo histograma concatenado del pool local.
KTH2b publicado usa1muestra train/3test; el panel común3train/1test es adaptación.
FMDpublicado50/50 por clase frente al panel externo80/20; no reutilizaraccuracy
publicada como F1 local ni afirmar identidad de splits.
Estado: RECIPE_DEPENDENCIES_PENDING,0réplicas/0llamadas medidas.

## AsTexNet, DOI10.3390/app16125743

Fuente: docs/referencias/applsci-16-05743-v2.pdf,
SHA256480874d4f1bfa52d07d7ff82284011798201bbee32e48cd16219cd172e0d8f8e.

Sistema:256×256RGB, MobileNetV2ImageNet fijo, original+flip horizontal,
GeM p3/epsilon1e-6, media vistas y L2, PCA ajustado solo en entrenamiento.
Rama local8configuraciones(R,P): (1,8),(2,8),(3,8),(4,8),(2,16),(3,16),(4,16),(5,16).
Cada bloque concatena patrónbinario, magnitudGaussian/Sobel y código central.
HistL1→raíz→L2. Peso por escala es normaFrobenius de coeficientes logistic
multinomial independiente por escala, normalizada por suma. Concatenación
ponderada local y fusiónalpha/beta con PCAprofundo; estandarizacióntraining;
MLP2capas y clasificadorcoseno con escala aprendible, labelsmoothing.1.
Entrenamiento descritoAdam.001/batch32/wd.0001, ReduceOnPlateau, earlystopping,
gradientclipping; decisionesPCA/fusión porCV5foldtraining. No inventar grid.

Incertidumbres relevantes que impiden declarar reproducción fiel:

- U2 se menciona junto aP+2bins e invariancia rotacional; fijar mapeo exacto
  con evidencia/código en lugar de sustituir u2/no-rotación silenciosamente.
- No verificados en pasajes inspeccionados: versión exacta de pesosMobileNet,
  interpolación/bordes/grayscale, configuraciónlogistic, candidatosPCA/fusión y
  regla de desempate por accuracy–compactness, widthsMLP y conexión512D,
  número deépocas, patience/min_delta, schedule/clipping. No asumir defaults.
- Mezcla de precisión se declara en fuente, pero formato/dispositivos locales
  son distintos; FP32 común sería adaptación explícita, no bitparitypublicada.
- Pesos de escala antes de estandarización por coordenada requieren conservar
  el orden exacto. No usar comparaciones de magnitudes para alterar la receta.
- Disponibilidad del artículo remite datos procesados/detalles al autor; no se
  enviaron solicitudes. Una ausencia de código verificado no prueba inexistencia.

Componentes aislados implementados en src/astexnet_formula_components.py,
13tests pasan. Solo eq8–12/16–18: cuantizaciónmagnitud, código75percentil,
Hellinger/L2, pesosFrobenius y concatenación ponderada. No contiene extractor
completo, CNN, selecciónPCA/logistic, MLP ni entrenamiento del sistemaAsTexNet.
NumPypercentile lineal es decisión de implementación declarada. Divisor0 falla
explícitamente sin epsilon no documentado. No experimentar sobre test ni tomar
los operadores como un benchmark completo.
Estado: FORMULA_COMPONENTS_TESTED_FULL_RECIPE_PENDING,0réplicas/0llamadas.

## Siguiente acción independiente

Buscar código/artefactos oficiales y detalles faltantes mediante fuentes primarias
sin contactos/autodescargas; continuar fichasHyTexNet, DeepLumina y multiescala.
Si solo procede una adaptación, fijar todas las diferencias antes de entrenar y
rotularla como tal; no improvisar receta dentro del runner para ejecutar más.
Neshov sigue requires_review, sin retries; panel local94 y manuscrito intactos.

## Segunda lectura: HyTexNet y DeepLumina

HyTexNetPDF19páginas, hash28169c0ec5d14654fffd347282c18caee99026bdf856149ffb3a46ae3f845e53;
DeepLumina16páginas, hash9458ecb383ea50142d2de144e97e7d8a3caabfe19d160e5754e4be0c0ebdb879.
Preflightestructural stdout del runtime documental:PASS19/16 sinwarnings,
2026-11-02T11:03:04.226804UTC /11:03:03.648628UTC. No declaración de lectura
humana íntegra. Métodos/protocolos/tablas pertinentes leídos; HyTexpage4
renderizada e inspeccionada, ecuaciones1–6 y Tabla1.

HyTexNet: ramaCNN1024+HyTex514 concat1538; FC256/ReLU/dropout.5/FC(K),
Adam/CE descritos. Signo/magnitud/centro tienen criterios≥, percentilCDFempírica
75% (sexta estadística de8), centroglobalmean por eq7–8. No usar interpolación
lineal de NumPy paraT75: rompe los ejemplos deTabla1. No cambiar globalmean
por media3×3 a partir de la figura ilustrativa. No verificados pesos exactos,
resize/bordes/grayscale y detalles de entrenamiento; frozenbackbone en descripción
frente a end-to-end en sección3.5 es ambigüedad que debe declararse.
Código/datosprocesados remiten a solicitud razonable, no se contactó autores.

Implementados descriptor y cabeza no entrenada en src/hytex_reference.py.
9tests nuevos,22en conjunto con componentesAsTexNet pasan. Incluyen los5casos
numéricosTabla1, empates, normalización, umbralglobal, dimensiones y orden de
fusión. No CNNcompleto ni nuevas llamadas/reproducción de métricas.
Para hacer ejecutable una comparación honesta se fijó protocolo ADAPTADO
docs/fsc_tex/PROTOCOLO_HYTEX_ADAPTACION_FMD_2026-11-02.md, con todas las elecciones
locales separadas de lo descrito por fuente; runner/preflight pendientes.
CheckpointDenseNet local verificado32334434bytes hash
c894c6d9caa317a8ca1942986dee7a16a86c77734a4d691d2abe05389cfef358, sin descarga.

DeepLumina: RGB+YdeYIQ,ResNet101dosrutas y concatenación;Tabla3 especifica
fc1000, no embeddingGAP2048. ClasificadorlinealECOC con codificación sparse-random
en MATLAB; no sustituir por nuestroSVCmulticlase/RBF sinadaptación explícita.
La discusión de entrenamiento5–20épocas/SGDM/batch8 aparece en el contexto de
comparadoresCNN, mientras sección4.1 da batch27 paraDeepLumina. No mezclarlo
como una receta de entrenamiento única resuelta. Pesos/capa/preprocess/ECOC
exactos pendientes;0réplicas externas,0latencias.

Búsquedaweb acotada de código (HyTexNetgithub/Compactcode) no verificó repo
oficial; no prueba inexistencia. Página primariaWiley deDeepLumina localizada
https://onlinelibrary.wiley.com/doi/10.1155/2022/9510987 yElsevierHyTexNet
https://www.sciencedirect.com/science/article/pii/S095070512600225X.
Esta búsqueda no es auditoría integral de retractaciones ni certificado editorial.
