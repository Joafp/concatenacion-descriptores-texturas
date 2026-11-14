# Propuesta concreta de revisión ARS

Estado: **lista para decisión del autor; no aplicada**. Fecha: 13-11-2026, America/Asuncion.

Se mantiene el título y el recorrido Top-k directo → optimización por margen. Se revisaron el texto y sus registros; no se cambiaron resultados ni se ejecutaron modelos.

La corrección principal separa la tasa interna usada para seleccionar la política y la tasa externa que ya utilizan las tablas. El resto mejora explicación, parámetros reproducibles y cierre del argumento.

## Cambios propuestos

| ID | Cambio | Alcance |
|---|---|---|
| REV-01 | Distinguir selección interna y evaluación en las fórmulas de costo | 4 bloques |
| REV-02 | Precisar cómo se eligen la base y el umbral | 1 bloques |
| REV-03 | Añadir un ejemplo real del umbral y de la tasa de activación | 1 bloques |
| REV-04 | Hacer reproducibles los parámetros de los clasificadores | 2 bloques |
| REV-05 | Identificar la política del piloto físico | 1 bloques |
| REV-06 | Explicar la condición que permite ahorrar adquisición | 1 bloques |
| REV-07 | Precisar el aporte sin prometer superioridad universal | 1 bloques |
| REV-08 | Cerrar P2 con resultados, cobertura y alcance del Top-4 fijo | 1 bloques |

Los cambios no repiten experimentos, no eliminan pérdidas, no convierten costos proyectados en tiempos físicos y no declaran Top-4 óptimo universal.

## Texto exacto propuesto

### REV-01: Distinguir selección interna y evaluación en las fórmulas de costo

La ecuación actual define una tasa interna, pero las tablas usan la tasa externa observada. Corregir los símbolos y su explicación conserva todos los resultados.

**Fuente:** `paper/chapters/03_metodologia.tex`, bloque `B0074`.

**Texto de reemplazo**

```latex
\section{Costo incremental y medición física}
Sean \(c_j\) los tiempos históricos por extractor. El costo directo y el incremental del rescate son
\begin{equation}
C_{\mathrm{dir}}=\sum_{j\in S_k}c_j,\qquad
C_{\mathrm{inc}}=\sum_{j\in S_k\setminus\{b\}}c_j.
\label{eq:tk-incremental}
\end{equation}
Un bloque base se reutiliza únicamente si su representación coincide con la que necesita \(h_k\). Se distinguen dos tasas: \(\widehat r_{\mathrm{OOF}}\), observada en las predicciones internas reunidas, y \(\widehat r_V\), observada al aplicar la política fijada al conjunto externo \(V\). Sus adquisiciones medias proyectadas son
\begin{equation}
\begin{aligned}
\widehat C_{\mathrm{sel}} &= c_b+\widehat r_{\mathrm{OOF}}C_{\mathrm{inc}},\\
\widehat C_V &= c_b+\widehat r_VC_{\mathrm{inc}}.
\end{aligned}
\label{eq:tk-cost}
\end{equation}
La primera magnitud se utiliza para seleccionar la política dentro del entrenamiento. La segunda describe su adquisición proyectada en evaluación y es la que reportan las tablas de resultados. Ambas emplean el mismo perfil histórico por extractor; ninguna es un cronometraje nuevo. El umbral y la ruta quedan fijados antes de obtener \(\widehat r_V\).
```

**Fuente:** `paper/chapters/03_metodologia.tex`, bloque `B0075`.

**Texto de reemplazo**

```latex
Las proyecciones de la Ecuación~\ref{eq:tk-cost} no incluyen automáticamente todos los clasificadores, transferencias o sobrecostos de la compuerta. La latencia física cronometra la ruta ejecutada y debe declarar si incluye decodificación, carga de pesos y calentamiento. En un sistema residente, la ruta condicional suma base, compuerta y, cuando corresponde, extracción incremental y clasificador Top-\(k\). La comparación directa ejecuta únicamente su concatenación y su clasificador.
```

**Fuente:** `paper/tesis.tex`, bloque `B0017`.

**Texto de reemplazo**

```latex
\chapter*{Siglas y notación}
\addcontentsline{toc}{chapter}{Siglas y notación}
\begin{tabular}{@{}lp{10.6cm}@{}}
Top-\(k\) & Concatenación de los primeros \(k\) bloques de un ranking interno\\
Top-4 & Caso de tamaño fijo \(k=4\), no cuatro identidades universales\\
OOF & Predicciones fuera de pliegue del entrenamiento\\
GFS & Selección secuencial hacia delante de bloques\\
SVD & Descomposición en valores singulares truncada\\
SVM & Máquina de vectores de soporte\\
ResMLP & MLP residual sobre características\\
\(S_k,h_k\) & Bloques seleccionados y clasificador de su concatenación\\
\(h_b,m_b,\tau\) & Clasificador base, margen y umbral\\
\(\widehat r_{\mathrm{OOF}},\widehat r_V\) & Fracciones derivadas interna y externa, respectivamente\\
\(c_j,C_{\mathrm{inc}}\) & Costo por bloque y adquisición incremental\\
P1, P2 & Preguntas de selección Top-k y uso directo/por margen\\
CKA & Similitud entre representaciones, usada en estudios complementarios\\
\end{tabular}
\tableofcontents
\listoffigures
{\emergencystretch=1em\listoftables}
\clearpage
\pagenumbering{arabic}
\input{chapters/01_introduccion}
\input{chapters/02_literatura}
\input{chapters/03_metodologia}
\input{chapters/04_diseno_experimental}
\input{chapters/05_resultados}
\input{chapters/06_discusion}
\input{chapters/07_conclusion}
```

**Fuente:** `paper/chapters/05_resultados.tex`, bloque `B0143`.

**Texto de reemplazo**

```latex
La Tabla~\ref{tab:tm-costos} reporta \(\widehat C_V\): adquisición proyectada con la fracción externa observada después de fijar la política. La selección utilizó \(\widehat C_{\mathrm{sel}}\), calculada con las predicciones internas OOF. Que ambas tasas difieran no implica que se haya vuelto a elegir el umbral con el test. Los porcentajes describen el perfil de extracción por componentes y se mantienen separados de los cronometrajes físicos.
```

### REV-02: Precisar cómo se eligen la base y el umbral

Distinguir macro-F1 OOF reunido del promedio por pliegue empleado para el ranking; expresar la tolerancia en puntos porcentuales y conservar desempates.

**Fuente:** `paper/chapters/03_metodologia.tex`, bloque `B0072`.

**Texto de reemplazo**

```latex
La selección de base compara ResNet-50, SigLIP, BEiT-v2 y ConvNeXt V2-T cuando existen bloque y costo registrado. Para cada base y cuantil, se reúnen las predicciones OOF de todo el entrenamiento externo y se calcula un único macro-F1 de la ruta condicional. Este estimando difiere del promedio de F1 por pliegue utilizado para ordenar los descriptores. Son elegibles las rutas cuyo macro-F1 OOF es al menos el del Top-\(k\) directo menos 0,005, es decir, 0,5 puntos porcentuales. Entre ellas se elige la de menor adquisición proyectada interna; el uso directo siempre es candidato. Los empates favorecen la ruta directa y después ResNet-50. Los mismos registros OOF sirven para comparar y elegir estos candidatos, por lo que su F1 seleccionado no es una evaluación independiente de la elección. La tolerancia constituye una decisión exploratoria, no una garantía poblacional de no inferioridad.
```

### REV-03: Añadir un ejemplo real del umbral y de la tasa de activación

Mostrar con predicciones guardadas que un cuantil interno del 25 % no obliga a derivar el 25 % del test. No se inventan márgenes ni corridas.

**Fuente:** `paper/chapters/03_metodologia.tex`, bloque `B0073`.

**Insertar después del bloque**

```latex
En FMD/SVM, semilla 42 y pliegue externo 0, la selección guardada utiliza SigLIP como base y \(q=0,25\), que produjo \(\tau=0,962190\) al redondear. La regla activa el rescate cuando el margen es menor o igual a ese umbral. En las predicciones externas guardadas se activó para 59 de 200 imágenes: 29,5 \%. El cuantil determina un umbral numérico; la tasa futura depende de los márgenes de las imágenes nuevas. En esa condición, la adquisición proyectada fue 133,966 ms durante la selección OOF y 153,384 ms en evaluación, frente a 457,598 ms del uso directo. Son costos por componentes, no latencias físicas adicionales.
```

### REV-04: Hacer reproducibles los parámetros de los clasificadores

Sustituir referencias vagas a parámetros registrados por los valores ya presentes en el código, sin cambiar ningún ajuste.

**Fuente:** `paper/chapters/04_diseno_experimental.tex`, bloque `B0091`.

**Texto de reemplazo**

```latex
\section{Clasificadores y transformaciones}
La SVM lineal CPU utiliza \texttt{LinearSVC}, \(C=1\), clases balanceadas, pérdida \emph{squared hinge}, regularización \(L_2\), estrategia uno-contra-el-resto, \texttt{dual=auto}, tolerancia \(10^{-4}\) y máximo de 10.000 iteraciones. El estado aleatorio sigue la semilla de la condición; la cascada histórica con base seleccionada utiliza 42. El código conserva los parámetros y el estado del ajuste. Los avisos de convergencia se informan sin cambiar retrospectivamente el solver para recuperar una cifra deseada.
```

**Fuente:** `paper/chapters/04_diseno_experimental.tex`, bloque `B0092`.

**Texto de reemplazo**

```latex
ResMLP es una MLP residual sobre vectores de características. Proyecta a 256 unidades y utiliza tres bloques residuales, normalización de capa, GELU y \emph{dropout} de 0,1. Se ajusta con AdamW, tasa de aprendizaje \(10^{-3}\), decaimiento de pesos \(10^{-4}\), lotes de 256 y máximo de 100 épocas. La parada usa paciencia de diez épocas y una mejora mínima de \(10^{-4}\) en la pérdida media de entrenamiento; al finalizar restaura el mejor estado registrado. Esta regla no utiliza el test para elegir una época y no equivale a una parada basada en pérdida de validación.
```

### REV-05: Identificar la política del piloto físico

Aclarar que los tiempos corresponden a la política con base seleccionada, preservando las seis cifras y todas sus reservas.

**Fuente:** `paper/chapters/05_resultados.tex`, bloque `B0144`.

**Texto de reemplazo**

```latex
\begin{table}[!htbp]\centering\fontsize{8}{10}\selectfont
\caption{Piloto físico de la política con base seleccionada, una condición por dataset. Modelos residentes e imágenes decodificadas; una imagen por clase y tres repeticiones pareadas.}
\label{tab:gpu-benchmark}
\begin{tabular}{@{}lrrrrl@{}}\toprule
Dataset & Imágenes & Pares & Margen ms & Directo ms & Reserva\\\midrule
DTD & 47 & 141 & 90,57 & 295,55 & alcance del piloto\\
FMD & 10 & 30 & 13,01 & 208,08 & alcance del piloto\\
CUReT & 61 & 183 & 92,52 & 270,60 & representación\\
Outex13 & 68 & 204 & 111,47 & 354,31 & alcance del piloto\\
Soil & 7 & 21 & 41,99 & 109,10 & representación\\
KTH-TIPS2b & 11 & 33 & 46,08 & 188,33 & variante histórica\\
\bottomrule\end{tabular}
\end{table}
```

### REV-06: Explicar la condición que permite ahorrar adquisición

Conectar el método optimizado con su condición algebraica, sin convertirla en promesa de latencia.

**Fuente:** `paper/chapters/06_discusion.tex`, bloque `B0157`.

**Texto de reemplazo**

```latex
\section{Cuándo tiene sentido la activación por margen}
La ruta condicional reduce adquisición proyectada cuando el trabajo evitado compensa ejecutar la base. Para \(C_{\mathrm{inc}}>0\), las definiciones del método dan
\begin{equation}
\widehat C_V<C_{\mathrm{dir}}
\quad\Longleftrightarrow\quad
\widehat r_V<\frac{C_{\mathrm{dir}}-c_b}{C_{\mathrm{inc}}}.
\end{equation}
La desigualdad explica por qué importan tanto la base elegida como la fracción activada. Si \(c_b\geq C_{\mathrm{dir}}\), el perfil de componentes no permite un ahorro estricto mediante esa base. Si \(C_{\mathrm{inc}}=0\), se comparan directamente los costos sin dividir por cero. En todos los casos, el ahorro de latencia física exige contabilizar y medir los clasificadores, la compuerta y los demás sobrecostos de la implementación.
```

### REV-07: Precisar el aporte sin prometer superioridad universal

Expresar la contribución como dos decisiones concretas, selección de representación y adquisición por imagen, conservando el alcance exploratorio.

**Fuente:** `paper/chapters/01_introduccion.tex`, bloque `B0032`.

**Texto de reemplazo**

```latex
\section{Aportes y organización}
El aporte empírico es conectar dos decisiones de un clasificador de texturas: seleccionar una concatenación compacta y decidir para qué imágenes conviene ejecutarla. La primera se estudia mediante el barrido de tamaños y controles de composición; la segunda, manteniendo fijo el rescate y evaluando su activación por margen. El trabajo documenta las condiciones en que esta combinación mejora el compromiso entre calidad y adquisición, junto con sus pérdidas y límites. Su contribución reside en esa comparación trazable sobre la biblioteca y los datasets evaluados; el ranking Top-\(k\) y la adquisición condicional se sitúan respecto de sus antecedentes.
```

### REV-08: Cerrar P2 con resultados, cobertura y alcance del Top-4 fijo

Reforzar la respuesta a la segunda pregunta y diferenciar la auditoría de identidad del rescate de una demostración de superioridad.

**Fuente:** `paper/chapters/07_conclusion.tex`, bloque `B0177`.

**Texto de reemplazo**

```latex
Para P2, la comparación de 27 condiciones SVM muestra que activar por margen el mismo Top-\(k\) puede mejorar o empeorar la calidad frente a ejecutarlo siempre: FMD mejora en promedio y Outex pierde macro-F1. La auditoría verifica que las imágenes derivadas reciben la predicción del mismo rescate directo, por lo que los cambios provienen de conservar la base en las restantes. Cinco condiciones coinciden en tamaño y bloques con el Top-4 del barrido; los demás rescates utilizan otros valores de \(k\). La evidencia respalda estudiar cuándo activar una concatenación fijada y conserva esa diferencia de cobertura al interpretar la versión optimizada.
```

## Revisión y límites

`criteria_binding_unavailable`; `calibration_status: NOT_CALIBRATED`.

Revisión local y acotada, con un revisor de código y síntesis editorial en el mismo trabajo. No es revisión ciega ni evaluación institucional. Las cinco dimensiones se examinaron cualitativamente: originalidad no reevaluada como novedad; rigor y coherencia requieren la precisión del costo; evidencia suficiente para los resultados descriptivos auditados; escritura mejorable mediante estos cambios concretos.

Se verificó que el piloto físico sí corresponde a la política con base seleccionada; no existe el supuesto error de variante. Se conservan las reservas KTH, CUReT/Soil, diferencias histórico/online y DeepLumina/DTD. La atribución individual CRediT y la aprobación académica siguen siendo decisiones de los autores; no se inventaron.

Contraste acotado de antecedentes existentes: [Neshov et al.](https://www.mdpi.com/2079-9292/14/23/4779) respalda la agregación entre capas; [Nan y Saligrama](https://proceedings.neurips.cc/paper_files/paper/2017/hash/d9ff90f4000eacd3a6c9cb27f78994cf-Abstract.html) respalda la adquisición condicional bajo costo; [Scabini et al.](https://www.mdpi.com/2313-433X/11/9/304) aporta el contexto de evaluación de calidad y eficiencia de extractores. Esta comprobación no es una revisión sistemática ni una certificación de toda la bibliografía.

## Decisión necesaria

Para aplicar la ronda ARS actual, el autor debe elegir explícitamente los cambios y sus bloques. Aprobar todos corresponde exactamente a REV-01 a REV-08 y a las operaciones mostradas, sin ampliar el alcance. También se puede autorizar un subconjunto por ID.

El flujo instalado exige una adjudicación explícita del autor: [WORKFLOW.md, Revision Mode Patch Protocol](</mnt/c/Users/Joaquin/.codex/skills/academic-research-suite/ars/academic-paper/WORKFLOW.md>) y [revision_patch_protocol.md](</mnt/c/Users/Joaquin/.codex/skills/academic-research-suite/ars/academic-paper/references/revision_patch_protocol.md>). La propuesta y su hoja de ruta no autorizan por sí solas una modificación.
