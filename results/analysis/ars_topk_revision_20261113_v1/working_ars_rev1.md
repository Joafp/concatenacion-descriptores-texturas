<!--block:B0001-->
# Manuscrito base para revisión ARS

<!--block:B0002-->
# Source: paper/tesis.tex

<!--block:B0003-->
\documentclass[12pt,a4paper]{report}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[english]{babel}
\usepackage{lmodern}
\usepackage[numbers,sort&compress]{natbib}
\usepackage{placeins,float}
\newenvironment{resulttable}{\begin{table}[!htbp]}{\end{table}}
\renewcommand{\chaptername}{Capítulo}
\renewcommand{\tablename}{Tabla}
\renewcommand{\figurename}{Figura}
\renewcommand{\contentsname}{Contenido}
\renewcommand{\bibname}{Referencias}
\renewcommand{\appendixname}{Anexo}
\addto\captionsenglish{\renewcommand{\chaptername}{Capítulo}\renewcommand{\tablename}{Tabla}\renewcommand{\figurename}{Figura}\renewcommand{\contentsname}{Contenido}\renewcommand{\bibname}{Referencias}\renewcommand{\appendixname}{Anexo}\renewcommand{\listfigurename}{Lista de figuras}\renewcommand{\listtablename}{Lista de tablas}}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{array}
\usepackage{longtable}
\usepackage[margin=1in]{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{listings}
\usepackage{url}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning}
\setlength{\parskip}{0.5em}
\setlength{\parindent}{0pt}
\setlength{\tabcolsep}{5pt}
\setlength{\emergencystretch}{1em}

<!--block:B0004-->
\newcommand{\titulotesis}{Concatenación Top-k de descriptores para clasificar texturas: comparación del uso directo y la activación por margen}
\title{\textbf{\titulotesis}}
\author{Carlos Ayala \and Joaquín Delgado}
\date{Noviembre 2026}
\hypersetup{
pdftitle={Concatenación Top-k de descriptores para clasificar texturas: comparación del uso directo y la activación por margen},
pdfauthor={Carlos Ayala y Joaquín Delgado},
pdfsubject={Concatenación de descriptores, Top-k y clasificación por margen}
}

<!--block:B0005-->
\begin{document}
\hypersetup{pageanchor=false}
\begin{titlepage}
\begin{center}
\vspace*{1.4cm}
{\Large\textbf{Universidad Nacional de Asunción}\par}
\vspace{0.4cm}
{\large Facultad Politécnica\par}
\vspace{1.7cm}
{\LARGE\bfseries\titulotesis\par}
\vspace{1.5cm}
{\large Carlos Ayala\\Joaquín Delgado\par}
\vspace{1.1cm}
{\large Tutor: José Vázquez\par}
\vfill
{\large Noviembre de 2026\par}
\end{center}
\end{titlepage}
\clearpage
\pagenumbering{roman}
\hypersetup{pageanchor=true}

<!--block:B0006-->
\chapter*{Agradecimientos}
A nuestro tutor, José Vázquez, por acompañar la formulación del problema y la revisión del trabajo. A la Facultad Politécnica de la Universidad Nacional de Asunción, y a nuestras familias por su apoyo.

<!--block:B0007-->
\chapter*{Resumen}
\addcontentsline{toc}{chapter}{Resumen}
La concatenación de descriptores permite combinar información para clasificar texturas, pero aumenta la representación y el trabajo de extracción. Esta tesis evalúa dos decisiones: qué bloques concatenar mediante un ranking Top-\(k\), y cuándo ejecutar esa concatenación mediante el margen de un clasificador base. Se estudian seis datasets, SVM lineal y una MLP residual sobre características, distinguiendo bibliotecas de 21 bloques sin N-gramas y la biblioteca consolidada de 22.

<!--block:B0008-->
El barrido exploratorio de uno a 21 bloques contiene 47 condiciones por tamaño y clasificador. Con SVM, Top-4 registra macro-F1 medio equiponderado por dataset de 0,936554, frente al máximo descriptivo de 0,936764 en \(k=10\), utilizando aproximadamente 15,42 \% de las dimensiones del barrido. Con ResMLP, el máximo aparece en \(k=5\). El resultado identifica una alternativa compacta, no un tamaño óptimo universal. Los controles con N-gramas y otras selecciones muestran que relevancia individual y complementariedad no son equivalentes.

<!--block:B0009-->
La comparación directa/por margen reconstruye 27 condiciones SVM y verifica el mismo rescate Top-\(k\) en las imágenes derivadas. La política registra macro-F1 medio 0,983953 frente a 0,982926 del uso directo en FMD, y 0,936950 frente a 0,942574 en Outex. Los costos por componentes proyectan menor adquisición; los pilotos físicos tienen un alcance delimitado y reservas de representación. Las comparaciones externas utilizan adaptaciones identificadas y mantienen DeepLumina bajo revisión por no convergencia y cobertura incompleta.

<!--block:B0010-->
La evidencia es exploratoria y conserva exposición previa a benchmarks, dependencia entre particiones y diferencias entre archivos. Se concluye que una concatenación pequeña puede ofrecer un compromiso útil y que su activación por margen debe evaluarse frente al mismo uso directo, contabilizando la base y separando dimensión, adquisición proyectada y latencia física.

<!--block:B0011-->
\textbf{Palabras clave:} clasificación de texturas, concatenación de descriptores, Top-k, margen, N-gramas, adquisición condicional.

<!--block:B0012-->
\chapter*{Abstract}
\addcontentsline{toc}{chapter}{Abstract}
Descriptor concatenation combines information for texture classification but increases representation size and extraction work. This thesis examines which blocks to concatenate using a Top-\(k\) ranking and when to execute that concatenation using the margin of a base classifier. Six datasets, a linear SVM and a residual feature MLP are studied, distinguishing a 21-block library without N-grams from the consolidated 22-block library.

<!--block:B0013-->
An exploratory sweep from one to 21 blocks includes 47 conditions per size and classifier. For SVM, Top-4 achieves dataset-balanced mean macro-F1 0.936554, compared with the descriptive maximum 0.936764 at \(k=10\), using approximately 15.42 \% of the sweep's feature dimensions. The ResMLP maximum occurs at \(k=5\). This identifies a compact alternative rather than a universally optimal size. Controls with N-grams and other selection methods show that individual relevance and complementarity are different properties.

<!--block:B0014-->
The direct-versus-margin comparison reconstructs 27 SVM conditions and verifies that escalated predictions use the same Top-\(k\) rescue. Mean macro-F1 is 0.983953 versus 0.982926 for direct use on FMD, and 0.936950 versus 0.942574 on Outex. Component profiles project lower acquisition costs; physical pilots have limited scope and unresolved representation reservations. External comparisons use identified adaptations, retaining DeepLumina's nonconvergence and incomplete coverage.

<!--block:B0015-->
The evidence remains exploratory, with prior benchmark exposure, dependent partitions and differences between archives. A small concatenation can provide a useful trade-off, while margin-based activation must be compared with the same direct predictor, accounting for the base and separating feature dimensions, projected acquisition and physical latency.

<!--block:B0016-->
\textbf{Keywords:} texture classification, descriptor concatenation, Top-k, margin, N-grams, conditional acquisition.

<!--block:B0017-->
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

<!--block:B0018-->
\appendix
\input{chapters/A_especificaciones}
\input{chapters/B_procedencia}
\input{chapters/C_resultados_adicionales}
\input{chapters/D_reproducibilidad}
\input{chapters/E_declaraciones}
\input{chapters/F_estudios_complementarios}
\clearpage
\bibliographystyle{unsrtnat}
\setlength{\bibsep}{3pt plus 1pt}
\bibliography{articulo/borrador_profesor/references}
\end{document}


<!--block:B0019-->
# Source: paper/chapters/01_introduccion.tex

<!--block:B0020-->
\chapter{Introducción}\label{sec:introduccion}

<!--block:B0021-->
\section{Problema de investigación}
Una imagen de textura puede describirse por la distribución de intensidades, la organización de patrones locales, las relaciones espaciales o las características aprendidas por una red. Estas representaciones responden de manera diferente a cambios de iluminación, escala y punto de vista. En consecuencia, un descriptor con buen rendimiento individual no necesariamente contiene toda la información útil para clasificar una superficie \citep{liu2019survey,cimpoi2016fisher}.

<!--block:B0022-->
La concatenación permite reunir varios vectores en una única representación y entrenar un clasificador sobre ella. Sin embargo, incorporar más descriptores aumenta la dimensión y exige ejecutar más extractores. Además, la información añadida puede ser redundante o modificar desfavorablemente el ajuste del clasificador. Por ello, la decisión no consiste únicamente en combinar representaciones, sino en determinar cuáles y cuántas conviene utilizar.

<!--block:B0023-->
Esta tesis estudia una regla sencilla: ordenar los descriptores según su desempeño individual dentro del entrenamiento y concatenar los primeros \(k\). A esta estrategia se la denomina Top-\(k\). El estudio compara sus prefijos con la concatenación completa y con otros criterios de selección. Top-4 es un caso de tamaño fijo de especial interés por el compromiso observado entre calidad y dimensión; no se presupone que sea el mejor tamaño para todo conjunto de datos.

<!--block:B0024-->
Una segunda decisión surge durante la clasificación. Aunque se haya seleccionado una concatenación útil, no todas las imágenes necesariamente requieren adquirir sus bloques. Una primera etapa puede resolver una parte de las consultas y utilizar el margen de sus puntuaciones para decidir si ejecutar el Top-\(k\). La comparación relevante mantiene fijo ese Top-\(k\): utilizarlo directamente o activarlo según la decisión de una base. La adquisición condicional tiene antecedentes y se evalúa aquí como una aplicación concreta a una biblioteca heterogénea de texturas \citep{nan2017adaptive,han2021dynamic}.

<!--block:B0025-->
\section{Recorrido: Top-k directo y versión optimizada}
El argumento experimental tiene dos etapas. Primero se construye Top-\(k\), se estudia por qué seleccionar pocos descriptores puede resultar más conveniente que concatenarlos todos y se compara su desempeño con otros métodos. Después se toma esa concatenación como referencia y se optimiza su ejecución mediante la activación por margen: una base atiende cada imagen y el Top-\(k\) se calcula solo cuando la regla aprendida lo requiere. La versión optimizada constituye la segunda parte central del trabajo. Su evaluación debe mostrar cuánto costo evita y qué calidad conserva o pierde frente al uso directo del mismo Top-\(k\).

<!--block:B0026-->
\section{Objetivo general}
Evaluar la concatenación Top-\(k\) de descriptores para clasificar texturas y comparar su uso directo con su activación por margen, distinguiendo calidad predictiva, dimensión de representación, costo de adquisición y latencia física.

<!--block:B0027-->
\section{Objetivos específicos}
\begin{enumerate}
\item Caracterizar la biblioteca de descriptores y el procedimiento de ranking y concatenación, incluyendo el tratamiento de RGB Pixel N-grams y sus transformaciones aprendidas.
\item Examinar el efecto de \(k\), explicar el origen experimental del caso Top-4 y contrastarlo con descriptores individuales, concatenaciones completas y selecciones alternativas.
\item Comparar los resultados con implementaciones adaptadas de métodos de literatura, identificando diferencias de representación, protocolo y métrica.
\item Evaluar el mismo Top-\(k\) como ruta directa y como rescate activado por margen, incluyendo el costo de la base y la reutilización de bloques.
\item Delimitar qué conclusiones respaldan los registros guardados, los pilotos físicos y las comparaciones entre conjuntos, conservando las excepciones y reservas de procedencia.
\end{enumerate}

<!--block:B0028-->
\section{Preguntas y alcance}
El trabajo se organiza alrededor de dos preguntas:
\begin{description}
\item[P1.] ¿Qué compromiso de desempeño y representación permite la concatenación Top-\(k\), y qué evidencia justifica estudiar Top-4 frente a otras concatenaciones y N-gramas?
\item[P2.] ¿Cómo cambia ese compromiso al utilizar directamente el Top-\(k\) o activarlo mediante el margen de una primera etapa?
\end{description}

<!--block:B0029-->
Se utilizan DTD, FMD, CUReT, Outex-TC-00013, SoilOriginal y KTH-TIPS-2b. El estudio estático incluye SVM lineal y una MLP residual sobre características. La comparación histórica directa/por margen utiliza SVM y 27 condiciones; sus tamaños Top-\(k\) proceden de controles archivados y no son siempre cuatro. El barrido ampliado de tamaños contiene 47 condiciones por clasificador y tamaño. El número de condiciones no se interpreta como número de datasets independientes.

<!--block:B0030-->
La biblioteca consolidada contiene 22 bloques, mientras que el barrido principal de \(k\) utiliza 21 sin N-gramas. Se identifican también las bibliotecas intermedias con N-gramas y sin BEiT-v2. Estas diferencias forman parte del diseño y no se ocultan bajo el nombre genérico de concatenación completa.

<!--block:B0031-->
El estudio es exploratorio: resultados externos observados influyeron en decisiones posteriores, incluida la atención prestada a \(k=4\). La separación interna de entrenamiento y prueba evita ciertas fugas dentro de cada ejecución, pero no convierte todo el proceso de investigación en una confirmación ciega. Tampoco se identifica una disminución dimensional con una reducción proporcional del tiempo.

<!--block:B0032-->
\section{Aportes y organización}
El aporte empírico es conectar dos decisiones de un clasificador de texturas: seleccionar una concatenación compacta y decidir para qué imágenes conviene ejecutarla. La primera se estudia mediante el barrido de tamaños y controles de composición; la segunda, manteniendo fijo el rescate y evaluando su activación por margen. El trabajo documenta las condiciones en que esta combinación mejora el compromiso entre calidad y adquisición, junto con sus pérdidas y límites. Su contribución reside en esa comparación trazable sobre la biblioteca y los datasets evaluados; el ranking Top-\(k\) y la adquisición condicional se sitúan respecto de sus antecedentes.

<!--block:B0033-->
Los Capítulos~\ref{sec:trabajos} y~\ref{sec:metodo} presentan antecedentes y método; el Capítulo~\ref{sec:diseno}, el diseño. Los resultados siguen el mismo orden: construcción y comparación de Top-\(k\), N-gramas y literatura, y finalmente uso directo/por margen. La discusión y las conclusiones responden P1 y P2. Los ensambles y la poda desarrollados durante el proyecto se conservan como estudios complementarios en el Anexo~\ref{app:complementarios}, sin atribuirles la identidad del rescate Top-\(k\).


<!--block:B0034-->
# Source: paper/chapters/02_literatura.tex

<!--block:B0035-->
\chapter{Antecedentes y trabajos relacionados}\label{sec:trabajos}

<!--block:B0036-->
\section{Representaciones para clasificar texturas}
Los descriptores clásicos resumen regularidades locales mediante histogramas, filtros, gradientes o estadísticas de coocurrencia. LBP codifica comparaciones vecinales; Gabor caracteriza respuestas a frecuencia y orientación; GLCM resume relaciones entre niveles de intensidad, y HOG organiza orientaciones de gradiente \citep{ojala2002lbp,jain1991gabor,haralick1979glcm,dalal2005hog}. Cada familia destaca propiedades diferentes de la imagen. La invariancia buscada y el tamaño de su salida dependen de la implementación.

<!--block:B0037-->
Las redes preentrenadas ofrecen otra fuente de características. CNN como ResNet y DenseNet, y modelos basados en atención como ViT, generan vectores que pueden utilizarse sin ajustar el backbone a la colección de texturas \citep{he2016resnet,huang2017densenet,dosovitskiy2021vit}. Un clasificador sobre esos vectores permite separar extracción y aprendizaje de la tarea. No obstante, una representación entrenada con otro dominio puede conservar información semántica o de forma que no coincide con la textura que se quiere distinguir.

<!--block:B0038-->
RGB Pixel N-grams representa secuencias de píxeles de color mediante conteos \citep{paiva2023rgb}. Su interés en este trabajo es aportar información cromática y local a representaciones de otras familias. La implementación evaluada comprime sus conteos mediante SVD ajustada dentro del entrenamiento. Esa variante se denomina N-gramas+SVD y no se identifica automáticamente con todas las configuraciones ni los porcentajes del artículo original.

<!--block:B0039-->
\section{Concatenación y selección de bloques}
La concatenación es una fusión a nivel de características: reúne los vectores antes de entrenar el clasificador. Un ensamble, en cambio, combina decisiones o puntuaciones de varios clasificadores. Aunque un miembro de un ensamble pueda recibir una concatenación, ambas operaciones resuelven decisiones distintas.

<!--block:B0040-->
Seleccionar los primeros \(k\) descriptores de un ranking individual ofrece una referencia de baja complejidad conceptual. El ranking estima relevancia individual; no mide necesariamente la complementariedad condicionada a los bloques que ya están presentes. Un descriptor que no ocupa una posición alta puede añadir información útil a otro subconjunto.

<!--block:B0041-->
Los métodos \emph{wrapper} evalúan subconjuntos mediante el clasificador que los utilizará \citep{kohavi1997wrappers,guyon2003feature}. GFS construye el conjunto de manera secuencial, añadiendo bloques según un criterio interno. Frente al ranking Top-\(k\), esto examina más directamente la composición, pero exige más ajustes. La comparación debe informar por separado el número de bloques, la dimensión, el costo de selección y la inferencia.

<!--block:B0042-->
Una selección realizada dentro del entrenamiento no justifica volver a elegir \(k\) mirando los resultados externos y describir esa elección como previa. El análisis de curvas externas es útil para explorar; su función y exposición deben declararse.

<!--block:B0043-->
\section{Métodos de literatura utilizados como comparación}
Neshov et al.\ extraen características de varios niveles de una arquitectura preentrenada y las concatenan antes de una MLP \citep{neshov2025aggregation}. El trabajo permite estudiar agregación entre capas, mientras que nuestro Top-\(k\) selecciona bloques de extractores diferentes. Las dos operaciones pueden relacionarse, pero no tienen el mismo costo ni la misma unidad de selección.

<!--block:B0044-->
DeepLumina reúne características profundas obtenidas a partir de información RGB y de luminancia \citep{simon2022deeplumina}. HyTexNet combina una codificación local guiada por percentiles con características profundas \citep{gupta2026hytexnet}. El método de Chang et al.\ fusiona LBP multiescala y contornos producidos por CellNN \citep{chang2024cellnn}. Estos casos representan formas concretas de concatenar información complementaria. Las dimensiones, checkpoints y cabezas utilizados en nuestras adaptaciones se identifican en las recetas del proyecto.

<!--block:B0045-->
Scabini et al.\ comparan extractores basados en Vision Transformers y consideran eficiencia junto con calidad \citep{scabini2025survey}. En el proyecto también existen mediciones derivadas de procesamiento por lotes. Su tiempo amortizado por imagen no se intercambia con la latencia individual de una consulta.

<!--block:B0046-->
\begin{table}[!htbp]\centering\small
\caption{Nivel de combinación y relación con la comparación propuesta.}
\label{tab:antecedentes}
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{3.0cm}>{\raggedright\arraybackslash}p{5.4cm}>{\raggedright\arraybackslash}p{4.0cm}@{}}
\toprule
Estrategia & Información combinada & Decisión que se estudia\\\midrule
Top-\(k\) & Bloques mejor valorados internamente & Qué bloques y cuántos\\
GFS & Bloques añadidos según utilidad conjunta & Composición del subconjunto\\
Neshov & Características de varias capas & Agregación dentro de arquitectura\\
DeepLumina & Características RGB/luminancia & Complementariedad cromática\\
HyTexNet / CellNN & Características profundas y patrones locales & Fusión de representaciones\\
Cascada por margen & Base y concatenación Top-\(k\) & Para qué imágenes adquirirla\\
\bottomrule
\end{tabular}
\end{table}

<!--block:B0047-->
\section{Activación condicional y margen}
Las cascadas distribuyen trabajo según decisiones intermedias \citep{viola2001rapid}. La clasificación adaptativa bajo presupuesto incorpora una compuerta para limitar el uso de modelos costosos \citep{nan2017adaptive}. En sistemas con extractores independientes, el costo depende también de qué bloques puede reutilizar la segunda etapa.

<!--block:B0048-->
El margen entre las dos mayores puntuaciones permite ordenar consultas según la separación que produce un clasificador. No es, por sí mismo, una probabilidad calibrada de acierto ni una garantía de que un rescate vaya a corregir el caso. La compuerta puede conservar aciertos de la base o evitar errores del Top-\(k\), pero también descartar una segunda etapa que habría sido útil.

<!--block:B0049-->
Otros enfoques incorporan costo de extracción durante el aprendizaje o adquieren características por información esperada \citep{xu2012greedy,ma2019eddi}. Las salidas tempranas dentro de redes reutilizan activaciones de una misma arquitectura \citep{teerapittayanon2016branchynet,han2021dynamic}. La tesis no reproduce todas estas familias; estudia una regla de dos etapas con margen y una concatenación fijada.

<!--block:B0050-->
\section{Criterio para comparar con un paper}
Se distinguen tres alcances: una reproducción fiel requiere verificar el pipeline y protocolo; una aproximación conserva parte del diseño con supuestos explícitos; una adaptación permite comparar una receta en nuestro panel común. Coincidir en un porcentaje o reproducir una ecuación aislada no acredita identidad de datos, pesos, selección y evaluación.

<!--block:B0051-->
La evaluación empírica utiliza macro-F1, accuracy y tiempos identificados por llamada. Los porcentajes publicados bajo otros repartos se usan como contexto. Para contrastar implementaciones se emparejan muestras y condiciones cuando la evidencia lo permite. Una referencia incompleta o cuyo ajuste exige revisión no se convierte en una media validada por omitir la condición fallida.


<!--block:B0052-->
# Source: paper/chapters/03_metodologia.tex

<!--block:B0053-->
\chapter{Concatenación Top-k y activación por margen}\label{sec:metodo}

<!--block:B0054-->
\section{Bloques y bibliotecas de características}
Sea \(\mathcal B\) una biblioteca de descriptores. El extractor \(j\) transforma la imagen \(x\) en un vector \(\phi_j(x)\in\mathbb R^{d_j}\). La unidad seleccionada es el bloque completo, no cada coordenada. Las características fijas se normalizan por imagen antes de la concatenación:
\begin{equation}
z_j(x)=\frac{\phi_j(x)}{\max(\|\phi_j(x)\|_2,10^{-12})},\qquad
z_S(x)=\mathop{\Vert}_{j\in S} z_j(x),\qquad d_S=\sum_{j\in S}d_j.
\label{eq:tk-concat}
\end{equation}
La concatenación no asigna por sí sola pesos de decisión: estos se aprenden al ajustar el clasificador sobre \(z_S\). La normalización impide identificar automáticamente una mayor norma bruta con mayor importancia.

<!--block:B0055-->
\subsection{Ejemplo concreto: de cuatro vectores a una clase}
En el archivo FMD/SVM, semilla 42 y pliegue externo 0, el prefijo de cuatro bloques es SigLIP-base (768 valores), DINOv2-large (1.024), EVA02-base (768) y DINOv2-base (768). Para una misma imagen se obtienen esos cuatro vectores, se normaliza cada uno con la Ecuación~\ref{eq:tk-concat} y se colocan consecutivamente:
\begin{equation}
z_{S_4}(x)=[z_{\mathrm{SigLIP}}(x)\Vert z_{\mathrm{DINO\,L}}(x)
\Vert z_{\mathrm{EVA02}}(x)\Vert z_{\mathrm{DINO\,B}}(x)]
\in\mathbb R^{3328}.
\end{equation}
Las filas de los cuatro bloques deben representar la misma imagen. Un único SVM se ajusta con estos vectores de 3.328 coordenadas y las etiquetas del entrenamiento. Para una imagen nueva se construye el vector en el mismo orden y el SVM entrega la clase de textura. La concatenación une características; el clasificador aprende cómo utilizarlas. Este ejemplo identifica una condición real, sin convertir sus cuatro nombres en una selección universal para todos los datasets.

<!--block:B0056-->
El proyecto contiene bibliotecas relacionadas, pero diferentes. Sea \(\mathcal B_{20}\) la biblioteca previa sin N-gramas ni el bloque final BEiT-v2. La incorporación de cada uno genera dos bibliotecas de 21 bloques:
\begin{equation}
\mathcal B_{21}^{Ng}=\mathcal B_{20}\cup\{Ng\},\quad
\mathcal B_{21}^{B}=\mathcal B_{20}\cup\{\mathrm{BEiT}\},\quad
\mathcal B_{22}=\mathcal B_{20}\cup\{Ng,\mathrm{BEiT}\}.
\label{eq:tk-libraries}
\end{equation}
El barrido de tamaños utiliza 21 bloques sin N-gramas. Por tanto, su prefijo \(k=21\) no es la concatenación completa de 22. Las etiquetas de carpetas históricas no sustituyen esta identificación de candidatos.

<!--block:B0057-->
La biblioteca consolidada reúne operadores clásicos, N-gramas y representaciones aprendidas congeladas. El Anexo~\ref{app:especificaciones} conserva parámetros y dimensiones. La SVD de N-gramas se aprende en cada entrenamiento pertinente; no se ajusta una proyección con todas las imágenes antes de separar prueba.

<!--block:B0058-->
\section{Ranking individual y construcción de Top-k}
Para una partición externa, \(T\) contiene el entrenamiento y \(V\) la evaluación. Dentro de \(T\), los pliegues \(T_\ell^{fit}\), \(T_\ell^{val}\) respetan los grupos de dependencia. Cada descriptor se puntúa individualmente con el clasificador que se estudiará:
\begin{equation}
a_j=\frac{1}{L}\sum_{\ell=1}^{L}
 F_{1,\mathrm{macro}}\!\left(y_{T_\ell^{val}},
 f_{j,\ell}(z_j(T_\ell^{val}))\right).
\label{eq:tk-ranking}
\end{equation}
Se ordenan los bloques por \(a_j\) decreciente. En el barrido, los empates se resuelven por nombre. El prefijo de tamaño \(k\) es
\begin{equation}
S_k=\{j_{(1)},\ldots,j_{(k)}\},\qquad
h_k=\mathrm{Ajustar}\bigl(z_{S_k}(T),y_T\bigr).
\label{eq:tk-subset}
\end{equation}
Una vez fijado \(S_k\), se reajusta el clasificador con todo \(T\) y se evalúa en \(V\). El ranking puede cambiar entre datasets, clasificadores y particiones. Top-4 fija el número de bloques, no cuatro identidades universales.

<!--block:B0059-->
\begin{figure}[!htbp]\centering
\begin{tikzpicture}[node distance=0.65cm,
box/.style={draw,rounded corners,align=center,text width=10.7cm,minimum height=0.85cm,font=\small},
arr/.style={-{Latex},thick}]
\node[box] (a) {Separar entrenamiento externo \(T\) y evaluación \(V\)};
\node[box,below=of a] (b) {En \(T\): ajustar y puntuar cada descriptor por validación interna agrupada};
\node[box,below=of b] (c) {Ordenar descriptores y fijar el prefijo \(S_k\)};
\node[box,below=of c] (d) {Concatenar sus vectores y reajustar un clasificador con todo \(T\)};
\node[box,below=of d] (e) {Evaluar el modelo fijado en \(V\); guardar predicciones y procedencia};
\draw[arr] (a)--(b);\draw[arr] (b)--(c);\draw[arr] (c)--(d);\draw[arr] (d)--(e);
\end{tikzpicture}
\caption{Construcción de una concatenación Top-\(k\). Evaluar varios tamaños externos es una exploración; escoger uno después de observarlos no constituye selección interna de ese tamaño.}
\label{fig:tk-training}
\end{figure}

<!--block:B0060-->
\section{Barrido de tamaños y origen del caso Top-4}
El barrido ejecuta los prefijos \(k=1,\ldots,21\) del mismo orden interno. Cada punto permite examinar la relación entre calidad y representación. Se conserva también el descriptor añadido y el tamaño de la concatenación.

<!--block:B0061-->
Hay dos controles distintos. En Top-4 se fija \(k=4\). En el Top-\(k\) histórico de igual tamaño que GFS, \(k\) se hereda del GFS archivado para esa condición y después se eligen los primeros bloques del ranking individual. Este control compara composiciones a un tamaño vinculado al otro procedimiento; no debe utilizarse para afirmar que cuatro fue el tamaño elegido en todas las condiciones.

<!--block:B0062-->
La atención a Top-4 surgió al observar una región de la curva con buen compromiso de calidad y dimensión. Esa elección es exploratoria. Los máximos por dataset o clasificador son descripciones del barrido, no tamaños elegidos ciegamente para despliegue. La evaluación de Top-4 conserva también los casos en que tamaños mayores o la biblioteca completa obtienen mejor macro-F1.

<!--block:B0063-->
\section{Controles de concatenación y papel de N-gramas}
El mejor individual se selecciona dentro del entrenamiento. Completa utiliza todos los bloques de la biblioteca identificada. GFS valora adiciones conjuntas y devuelve el mejor paso según su regla interna; la selección homogénea compara familias. Los ensambles de tómbola y diversidad combinan decisiones de varios miembros y se utilizan como controles complementarios.

<!--block:B0064-->
El aporte de N-gramas se examina mediante versiones emparejadas de la biblioteca y el procedimiento de selección. Añadirlo a Completa mantiene el resto de los bloques; ofrecerlo a GFS o Top-\(k\) puede cambiar el subconjunto y su tamaño. Esta última comparación mide el efecto de ampliar la biblioteca y reseleccionar, no una ablación con todos los demás componentes fijos.

<!--block:B0065-->
Un buen ranking individual no garantiza complementariedad: que N-gramas no aparezca entre los cuatro primeros no demuestra que añadirlo al Top-4 sea inútil. Si no existe ese control específico bajo el mismo protocolo, no se sustituye por otra comparación.

<!--block:B0066-->
\section{Uso directo y versión optimizada por margen}
La optimización estudiada en esta segunda etapa modifica cuándo se ejecuta la concatenación seleccionada. Conserva el clasificador Top-\(k\) como rescate y añade una decisión de adquisición por imagen. Por ello se evalúa frente a su propio uso directo, además de las comparaciones estáticas de la primera etapa.

<!--block:B0067-->
La ruta directa calcula \(z_{S_k}(x)\) y devuelve \(h_k(x)\) para todas las imágenes. No necesita ejecutar un clasificador base adicional.

<!--block:B0068-->
La ruta condicional incorpora una base \(h_b\), un bloque base \(b\) y un umbral \(\tau\). Para SVM multiclase, el margen es la diferencia entre las dos mayores puntuaciones de su función de decisión:
\begin{equation}
m_b(x)=s_{b,(1)}(x)-s_{b,(2)}(x).
\label{eq:tk-margin}
\end{equation}
En clasificación binaria, la implementación utiliza el valor absoluto de la función de decisión. El margen no es una probabilidad calibrada.

<!--block:B0069-->
La implementación histórica de esta cascada usa la regla
\begin{equation}
h_{\mathrm{margen}}(x)=
\begin{cases}
h_b(x),&m_b(x)>\tau,\\
h_k(x),&m_b(x)\leq\tau .
\end{cases}
\label{eq:tk-rule}
\end{equation}
Cuando se activa el rescate, su predicción reemplaza a la base. No se añade un voto ni se entrenan pesos de mezcla diferentes para la ruta directa y la condicional.

<!--block:B0070-->
\begin{figure}[!htbp]\centering
\begin{tikzpicture}[node distance=0.65cm,
box/.style={draw,rounded corners,align=center,text width=4.1cm,minimum height=0.9cm,font=\small},
arr/.style={-{Latex},thick}]
\node[box] (base) {Imagen nueva: extraer la base\\y obtener \(h_b(x)\) y \(m_b(x)\)};
\node[box,below=of base] (gate) {Comparar \(m_b(x)\) con el\\umbral \(\tau\) fijado en entrenamiento};
\node[box,below left=1cm and 0.45cm of gate] (early) {Si \(m_b(x)>\tau\):\\entregar \(h_b(x)\)};
\node[box,below right=1cm and 0.45cm of gate] (rescue) {Si \(m_b(x)\leq\tau\):\\extraer bloques adicionales de \(S_k\)};
\node[box,below=of rescue] (late) {Reutilizar bloques compartidos\\y entregar el mismo \(h_k(x)\)};
\draw[arr] (base)--(gate);\draw[arr] (gate)--(early);\draw[arr] (gate)--(rescue);\draw[arr] (rescue)--(late);
\end{tikzpicture}
\caption{Clasificación por margen. La ruta directa de comparación ejecuta \(h_k\) sin base. La condición de margen no utiliza la etiqueta verdadera de la imagen nueva.}
\label{fig:tk-inference}
\end{figure}

<!--block:B0071-->
\section{Cómo se aprenden la base y el umbral}
El umbral se obtiene de márgenes fuera de pliegue del entrenamiento externo. Para cada base candidata se consideran cuantiles \(q\in\{0,25;0,50;0,75\}\), utilizando la notación decimal de esos valores. El cuantil produce un umbral numérico y permite estimar la fracción derivada dentro del entrenamiento.

<!--block:B0072-->
La selección de base compara ResNet-50, SigLIP, BEiT-v2 y ConvNeXt V2-T cuando existen bloque y costo registrado. Para cada base y cuantil, se reúnen las predicciones OOF de todo el entrenamiento externo y se calcula un único macro-F1 de la ruta condicional. Este estimando difiere del promedio de F1 por pliegue utilizado para ordenar los descriptores. Son elegibles las rutas cuyo macro-F1 OOF es al menos el del Top-\(k\) directo menos 0,005, es decir, 0,5 puntos porcentuales. Entre ellas se elige la de menor adquisición proyectada interna; el uso directo siempre es candidato. Los empates favorecen la ruta directa y después ResNet-50. Los mismos registros OOF sirven para comparar y elegir estos candidatos, por lo que su F1 seleccionado no es una evaluación independiente de la elección. La tolerancia constituye una decisión exploratoria, no una garantía poblacional de no inferioridad.

<!--block:B0073-->
Finalmente se reajustan los modelos seleccionados con todo el entrenamiento externo y se conserva el umbral numérico. El porcentaje de imágenes nuevas que activa el rescate puede ser distinto del cuantil nominal. No se recalcula el umbral utilizando etiquetas ni márgenes de todo el test.

<!--block:B0312-->
En FMD/SVM, semilla 42 y pliegue externo 0, la selección guardada utiliza SigLIP como base y \(q=0,25\), que produjo \(\tau=0,962190\) al redondear. La regla activa el rescate cuando el margen es menor o igual a ese umbral. En las predicciones externas guardadas se activó para 59 de 200 imágenes: 29,5 \%. El cuantil determina un umbral numérico; la tasa futura depende de los márgenes de las imágenes nuevas. En esa condición, la adquisición proyectada fue 133,966 ms durante la selección OOF y 153,384 ms en evaluación, frente a 457,598 ms del uso directo. Son costos por componentes, no latencias físicas adicionales.

<!--block:B0074-->
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

<!--block:B0075-->
Las proyecciones de la Ecuación~\ref{eq:tk-cost} no incluyen automáticamente todos los clasificadores, transferencias o sobrecostos de la compuerta. La latencia física cronometra la ruta ejecutada y debe declarar si incluye decodificación, carga de pesos y calentamiento. En un sistema residente, la ruta condicional suma base, compuerta y, cuando corresponde, extracción incremental y clasificador Top-\(k\). La comparación directa ejecuta únicamente su concatenación y su clasificador.

<!--block:B0076-->
La compacidad del vector, la extracción de bloques, el tiempo de selección, el entrenamiento y la latencia por consulta son magnitudes distintas. El diseño experimental y los resultados mantienen separadas sus unidades.


<!--block:B0077-->
# Source: paper/chapters/04_diseno_experimental.tex

<!--block:B0078-->
\chapter{Diseño experimental}\label{sec:diseno}

<!--block:B0079-->
\section{Recorrido de las pruebas hasta Top-4 y su optimización}
El estudio avanzó por una secuencia de preguntas. Los pasos siguientes reconstruyen ese recorrido experimental; los registros ampliados y las bibliotecas correspondientes se identifican después para evitar tratarlos como una única corrida.
\begin{enumerate}
\item \textbf{Establecer referencias individuales.} Se evaluaron los descriptores por separado y se calculó un ranking mediante validación interna del entrenamiento. Esto permite conocer qué representación funciona bien sola y definir el punto de partida de una selección.
\item \textbf{Probar la concatenación completa.} Se entrenó un clasificador con todos los bloques de la biblioteca de cada corte. La comparación con Individual permitió examinar si añadir toda la información disponible compensa su mayor dimensión.
\item \textbf{Comparar maneras de elegir bloques.} GFS construye combinaciones valorando las adiciones; Homogénea restringe familias; el control Top-\(k\) toma los primeros del ranking con el mismo número de bloques que el GFS de esa condición. Este control separa la cantidad seleccionada de la composición.
\item \textbf{Recorrer todos los tamaños.} Un solo tamaño heredado no explica cuántos descriptores hacen falta. El barrido pasó a evaluar los 21 prefijos del ranking. El registro inicial SVM contenía 27 condiciones con semilla 42; los CSV ampliados contienen 47 por tamaño y clasificador, incluyendo ResMLP y más semillas FMD/Soil. La tesis utiliza la cobertura ampliada en sus curvas principales.
\item \textbf{Examinar el aporte marginal.} Se compararon la calidad y la dimensión al pasar de uno a dos, tres, cuatro y más bloques. La zona de buen rendimiento con pocos bloques motivó prestar atención a Top-4. El máximo observado y las pérdidas por dataset se conservan, en lugar de imponer cuatro como ganador de todas las curvas.
\item \textbf{Examinar alternativas y ampliaciones.} Los archivos exploratorios también incluyen reglas internas para elegir \(k\), SFFS y selecciones aleatorias; su cobertura no es la del barrido ampliado. Las comparaciones emparejadas con N-gramas estudian qué cambia al ampliar la biblioteca. Estos estudios contextualizan la elección sencilla por ranking, sin atribuirles una validación ciega de \(k=4\).
\item \textbf{Contrastar con métodos externos.} Se comparó Top-4 con adaptaciones de métodos de literatura y se midieron predicción y tiempo de las mismas llamadas. Se conservaron por separado porcentajes publicados, recetas adaptadas y resultados locales.
\item \textbf{Optimizar cuándo ejecutar Top-\(k\).} Se tomó el uso directo como referencia y se estudió una base que activa el mismo rescate según su margen. Esta segunda parte compara calidad y adquisición por imagen, y utiliza los pilotos físicos dentro de su alcance.
\end{enumerate}
La elección de Top-4 fue posterior a observar resultados del barrido. El ranking interno y la decisión exploratoria sobre un tamaño global son decisiones distintas. La secuencia documenta cómo surgió la opción compacta, sin presentarla como una regla derivada antes de ver toda la evidencia.

<!--block:B0080-->
\section{Experimentos y unidades de análisis}
La evaluación reúne tres archivos con funciones distintas. El barrido permite estudiar \(k\); el benchmark de selección compara estrategias sobre una biblioteca consolidada; la cascada contrasta el mismo Top-\(k\) directo y por margen. Un cuarto archivo físico permite describir las llamadas de Top-4 y de los comparadores externos. Sus cifras no se mezclan para construir una media nueva.

<!--block:B0081-->
\begin{table}[!htbp]\centering\small
\caption{Cobertura de los bloques experimentales utilizados en la tesis.}
\label{tab:cobertura}
\begin{tabular}{@{}lrrr@{}}\toprule
Conjunto & Barrido por k/clasif. & Estático por clasif. & Directo/margen SVM\\\midrule
DTD & 10 & 10 & 10\\
FMD & 15 & 15 & 5\\
CUReT & 2 & 2 & 2\\
Outex13 & 1 & 1 & 1\\
SoilOriginal & 15 & 15 & 5\\
KTH-TIPS2b & 4 & 4 & 4\\\midrule
Total & 47 & 47 & 27\\
\bottomrule\end{tabular}
\end{table}

<!--block:B0082-->
El barrido contiene 21 tamaños por clasificador: 987 filas SVM y 987 ResMLP. Cada tamaño conserva las mismas 47 condiciones de su clasificador. Las 27 condiciones de cascada utilizan solo la semilla 42 en FMD y Soil, frente a tres semillas en los archivos ampliados. Las particiones oficiales DTD, las mitades complementarias de CUReT y las semillas repetidas comparten imágenes; sus condiciones no son réplicas independientes.

<!--block:B0083-->
El panel online previo incluye cinco estrategias locales y dos clasificadores sobre 94 condiciones. La tesis extrae la evidencia de Top-4 de ese panel y la mantiene separada de sus otras políticas. Las 362.640 llamadas primarias del panel completo no son 362.640 llamadas de Top-4 ni una nueva medición del sistema directo/por margen.

<!--block:B0084-->
\section{Colecciones y particiones}
Se utilizaron manifiestos para comprobar etiquetas, orden, dimensiones y valores finitos de los vectores. Los hashes y grupos permiten detectar duplicados y separar unidades relacionadas. La existencia de una separación externa dentro de una corrida no elimina la exposición de sus resultados durante el desarrollo.

<!--block:B0085-->
DTD contiene 47 clases y diez particiones oficiales \citep{cimpoi2014dtd}. El estudio estático selecciona dentro de la unión de entrenamiento y validación de cada partición; la prueba de esa ejecución permanece fuera del ajuste. Los duplicados byte-idénticos que cruzaban roles se retiraron del entrenamiento. La reserva física de una condición del panel online se conserva en su documentación y no se interpreta como una validación nueva de todas las representaciones.

<!--block:B0086-->
FMD contiene 1.000 imágenes y diez categorías \citep{sharan2013fmd}. Se usan cinco pliegues estratificados y agrupados con semillas 42, 123 y 2026. Cada imagen se identifica mediante un hash; la cascada utiliza los cinco pliegues de la semilla 42.

<!--block:B0087-->
CUReT se basa en la distribución gris recortada de 61 materiales y 92 condiciones por clase \citep{varma2003filter}. Se fijaron dos mitades de 46 condiciones y ambas direcciones de entrenamiento/prueba. Las condiciones de adquisición se agrupan para no cruzar una misma configuración. Este reparto no identifica el subconjunto histórico exacto de cada paper y sus direcciones son dependientes.

<!--block:B0088-->
Outex-TC-00013 contiene 1.360 imágenes de 68 clases y una partición oficial de 680/680 \citep{ojala2002outex}. Se comprobaron imágenes RGB legibles, IDs y ausencia de duplicados exactos. Existe una alerta de correspondencia de filas y bloques de características cuyo rastreo se conserva como reserva; la enmienda DeiT del panel no se atribuye automáticamente a todos los archivos históricos.

<!--block:B0089-->
SoilOriginal utiliza solo imágenes originales de la versión 1 de la colección \emph{Comprehensive Soil Classification Datasets}. Tras deduplicación exacta se conservaron 1.140 imágenes, siete clases y 962 grupos conservadores por familia de nombre dentro de clase. No existe un split oficial utilizado en esta evaluación. Se aplican cinco pliegues agrupados y tres semillas en el archivo ampliado; la cascada conserva la semilla 42.

<!--block:B0090-->
KTH-TIPS2b tiene 11 clases y cuatro muestras físicas por clase. El estudio mantiene cuatro particiones invertidas, con tres muestras para entrenar y una para probar. Algunos controles históricos difieren en agrupación interna y procedencia de representaciones. No se sustituye una media por la de otro control para dar por reconciliada toda la ruta. KTH se muestra descriptivamente y se excluye del contraste conjunto histórico de la cascada. Las aproximaciones al reparto de un tercio de algunos papers, con 44 muestras físicas compartidas entre entrenamiento y prueba, son otra evaluación y no se mezclan con este panel.

<!--block:B0091-->
\section{Clasificadores y transformaciones}
La SVM lineal CPU utiliza \texttt{LinearSVC}, \(C=1\), clases balanceadas, pérdida \emph{squared hinge}, regularización \(L_2\), estrategia uno-contra-el-resto, \texttt{dual=auto}, tolerancia \(10^{-4}\) y máximo de 10.000 iteraciones. El estado aleatorio sigue la semilla de la condición; la cascada histórica con base seleccionada utiliza 42. El código conserva los parámetros y el estado del ajuste. Los avisos de convergencia se informan sin cambiar retrospectivamente el solver para recuperar una cifra deseada.

<!--block:B0092-->
ResMLP es una MLP residual sobre vectores de características. Proyecta a 256 unidades y utiliza tres bloques residuales, normalización de capa, GELU y \emph{dropout} de 0,1. Se ajusta con AdamW, tasa de aprendizaje \(10^{-3}\), decaimiento de pesos \(10^{-4}\), lotes de 256 y máximo de 100 épocas. La parada usa paciencia de diez épocas y una mejora mínima de \(10^{-4}\) en la pérdida media de entrenamiento; al finalizar restaura el mejor estado registrado. Esta regla no utiliza el test para elegir una época y no equivale a una parada basada en pérdida de validación.

<!--block:B0093-->
La búsqueda interna utiliza pliegues estratificados y agrupados, limitada por disponibilidad de grupos. Las redes de extracción permanecen congeladas. Las transformaciones aprendidas, como SVD, se ajustan con el entrenamiento del pliegue correspondiente. Cuando se cambia la biblioteca o el clasificador, la selección se repite dentro de su protocolo; no se reutiliza un ranking de otro modelo como si fuera una nueva selección interna.

<!--block:B0094-->
\section{Cómo se comparan los prefijos y las bibliotecas}
En cada condición del barrido se mantiene un ranking y se evalúan sus prefijos de uno a 21 bloques. Se comprueba cobertura íntegra para cada \(k\), ausencia de duplicados de dataset/semilla/pliegue/tamaño y correspondencia con los resúmenes guardados. Esta evaluación no incluye N-gramas.

<!--block:B0095-->
El estudio de N-gramas utiliza sus bibliotecas emparejadas y condiciones comunes. Las tablas de 20 frente a 21 bloques corresponden a un corte anterior a la incorporación final de BEiT-v2. Las tablas consolidadas de 22 y el barrido sin N-gramas responden a otro corte. La comparación no utiliza los nombres de las carpetas como prueba de identidad de bibliotecas.

<!--block:B0096-->
Las medias principales se calculan dentro de cada dataset y luego se equiponderan los seis datasets:
\begin{equation}
\overline F=\frac{1}{D}\sum_{d=1}^{D}
\left(\frac{1}{n_d}\sum_{r=1}^{n_d}F_{d,r}\right).
\label{eq:tk-aggregation}
\end{equation}
Este estimando difiere de reunir todas las predicciones y calcular un único F1. Las tablas indican cuando muestran una media por condición, un valor por llamada o un promedio OOF reunido.

<!--block:B0097-->
\section{Contraste del mismo Top-k directo y por margen}
Cada condición conserva el subconjunto Top-\(k\) archivado, ajusta su clasificador con el entrenamiento externo y utiliza ese mismo resultado como referencia de la ruta condicional. La selección de base y umbral usa únicamente sus predicciones internas fuera de pliegue. Se conserva la alternativa Top-\(k\) directo si la cascada no resulta elegida.

<!--block:B0098-->
Para la revisión final se reconstruyeron las métricas de las 27 condiciones desde sus JSON de predicción. Se verificaron identidad de dataset/protocolo, unicidad de índices dentro de cada prueba, longitud de arrays, macro-F1, fracción activada, bloques del rescate y hash del archivo de origen. Para cada imagen derivada se exigió que la predicción condicional coincidiera con la del Top-\(k\) directo. Esta comprobación atribuye las diferencias a conservar la base en las otras imágenes, y no a utilizar otro rescate.

<!--block:B0099-->
La auditoría cubre 31.984 observaciones externas, no ese número de imágenes independientes. Reconstruye las decisiones guardadas sin volver a ajustar modelos. La coincidencia con el registro es una prueba de consistencia del archivo, no una reproducción independiente desde RGB.

<!--block:B0100-->
\section{Métricas y costos}
Para \(C\) clases se usa
\begin{equation}
F_{1,\mathrm{macro}}=\frac1C\sum_{c=1}^{C}
\frac{2TP_c}{2TP_c+FP_c+FN_c},\qquad
\mathrm{accuracy}=\frac{1}{n}\sum_{i=1}^{n}\mathbb I[\widehat y_i=y_i].
\label{eq:tk-metrics}
\end{equation}
Se aplica la convención registrada de valor cero ante denominador nulo. Un aumento de accuracy no implica necesariamente el mismo cambio de macro-F1.

<!--block:B0101-->
Se informan también bloques, dimensión, tiempo de selección y ajuste, fracción derivada y costo incremental. Un porcentaje de dimensiones se refiere a su biblioteca de comparación. Un porcentaje de adquisición se refiere al modelo analítico de componentes. Ninguno se denomina automáticamente ahorro de latencia.

<!--block:B0102-->
Los perfiles históricos de adquisición se midieron con imágenes de entrenamiento y se trasladaron como proxies entre dominios. El piloto físico de la cascada utiliza una condición por dataset, una imagen por clase y tres repeticiones pareadas, con modelos residentes e imágenes decodificadas. Sus 612 parejas corresponden a 204 imágenes. No se presentan como toda la prueba externa de cada dataset ni como latencia de arranque en frío.

<!--block:B0103-->
El panel online posterior conserva predicción y tiempo de cada llamada batch1. Los tiempos de métodos diferentes proceden de fechas/estados de hardware distintos y tienen alcance descriptivo. Los tiempos amortizados de lotes de 32 pertenecen a otro régimen y no se incorporan a esas tablas.

<!--block:B0104-->
\section{Comparadores externos y controles estadísticos}
Se utilizan las adaptaciones Neshov BEiTv2+MLP, HyTexNet y 6LBP+dCellNN con 47 condiciones completas cada una. DeepLumina mantiene 46 condiciones terminadas, avisos de no convergencia en todas y una condición DTD interrumpida. La tabla DTD no tiene una media completa de ese método. El protocolo aproximado Neshov FMD 10 por 10 es una comprobación separada, no el panel común.

<!--block:B0105-->
Los contrastes agregados por dataset se separan por clasificador y familia de comparación. Friedman y los post-hoc archivados comparan las estrategias de su benchmark; no prueban que Top-4 fijo sea el mejor tamaño del barrido. En la cascada se mantiene la sensibilidad que excluye KTH. El no rechazo no demuestra equivalencia ni no inferioridad \citep{demsar2006statistical,garcia2008extension}.

<!--block:B0106-->
\section{Reglas de cierre y reproducibilidad}
Toda condición nueva requiere congelar receta, versiones, pesos, semillas, partición y presupuesto antes de medir. Se conserva un benchmark GPU, CPU a dos hilos y lock global, sin ajuste o extracción concurrente con el cronometraje. No se repiten paneles cerrados para sustituir resultados desfavorables. Los fallos científicos mantienen evidencia y revisión, sin omisión de casos ni cambios silenciosos de método.

<!--block:B0107-->
La actualización de este manuscrito añade auditorías y tablas reconstruidas; no ejecuta un nuevo barrido ni afirma una nueva campaña física. Los estudios de ensamble, poda y réplicas OOF permanecen en los anexos con su propio alcance.


<!--block:B0108-->
# Source: paper/chapters/05_resultados.tex

<!--block:B0109-->
\chapter{Resultados experimentales}\label{sec:resultados-experimentales}

<!--block:B0110-->
Los resultados responden primero cómo se construye y se compara Top-\(k\), y después qué cambia al activarlo por margen. Se conservan separados el archivo de características, el panel online y los pilotos físicos. Las tablas generadas para esta revisión se vinculan con 124 fuentes mediante hashes y no añaden ajustes ni mediciones.

<!--block:B0111-->
\section{P1: del descriptor individual a la concatenación}\label{sec:resultados-fase1}
El benchmark consolidado compara Individual, Completa, Top-\(k\), GFS y Homogénea sobre seis datasets y dos clasificadores. Individual designa la mejor alternativa seleccionada internamente, no el máximo externo de todos los descriptores. El Top-\(k\) de esta primera tabla hereda su tamaño del control GFS; su nombre no significa Top-4 fijo.

<!--block:B0112-->
\input{articulo/borrador_profesor/generated/baseline_f1.tex}
\input{articulo/borrador_profesor/generated/dimensions_primary.tex}

<!--block:B0113-->
Las medias muestran que una concatenación puede mejorar al mejor individual seleccionado, pero añadir indiscriminadamente bloques también puede empeorar. En FMD/SVM, Completa registra aproximadamente 0,9647, frente a 0,9726 de Individual y 0,9820 del Top-\(k\) del control. En Outex/SVM, en cambio, Completa alcanza aproximadamente 0,9656. Las diferencias entre datasets impiden definir una regla uniforme a partir del número de bloques.

<!--block:B0114-->
La dimensión seleccionada y la calidad se reportan conjuntamente. La reducción de entrada al clasificador es informativa para almacenamiento y ajuste, pero no determina qué extractores dominan el tiempo de una consulta. Los contrastes del benchmark estático y su sensibilidad sin KTH se conservan en el Anexo~\ref{app:resultados-adicionales}. Su alcance no se extiende a los tamaños fijos nuevos por un cambio de etiqueta.

<!--block:B0115-->
\section{Barrido de k y justificación del caso Top-4}
La reconstrucción del barrido verifica 47 condiciones para cada tamaño de uno a 21 y cada clasificador. Las Tablas~\ref{tab:tm-curva}--\ref{tab:tm-top4-resmlp} y la Figura~\ref{fig:tm-curve} describen ese archivo ampliado. El README inicial del barrido corresponde a menos condiciones y no sustituye sus CSV ampliados.

<!--block:B0116-->
\input{generated_topk_margin/curva_k.tex}
\begin{figure}[!htbp]\centering
\includegraphics[width=\textwidth]{generated_topk_progression/ganancias_k.pdf}
\caption[Calidad y ganancia marginal al aumentar el número de descriptores.]{Calidad al aumentar el número de descriptores y ganancia de cada bloque adicional. Los círculos abiertos y la línea vertical señalan Top-4. Cada punto promedia primero dentro del dataset y después entre datasets. Una barra negativa indica pérdida al añadir ese bloque. Se muestran todos los tamaños, incluidos los máximos posteriores a cuatro.}
\label{fig:tm-curve}
\end{figure}

<!--block:B0117-->
Con SVM, Top-4 obtiene 0,936554 y el máximo descriptivo aparece en \(k=10\), con 0,936764. La diferencia es 0,000210 de macro-F1, mientras el porcentaje dimensional medio es aproximadamente 15,42 para cuatro bloques y 45,17 para diez, respecto a 21. Esto identifica una alternativa compacta cercana al máximo observado, no una prueba de equivalencia.

<!--block:B0118-->
Con ResMLP, Top-4 registra 0,933077 y el máximo del barrido aparece en \(k=5\), con 0,935195. Por tanto, la elección de cuatro no maximiza todas las curvas. Tampoco puede reducirse la decisión al promedio global: la composición y la respuesta a \(k\) dependen del dataset y del clasificador.

<!--block:B0119-->
\subsection{Por qué estudiar cuatro: ganancia frente a crecimiento del vector}
El eje horizontal representa el número de descriptores concatenados. Se trata de una curva de desempeño frente al tamaño de la representación; el número de imágenes de entrenamiento y las épocas no varían en ese eje. Para explicar la contribución incremental se calcula
\begin{equation}
g_k=100\,[\overline F(k)-\overline F(k-1)],\qquad k=2,\ldots,21,
\end{equation}
en puntos porcentuales de macro-F1. La Figura~\ref{fig:tm-curve} muestra cada incremento, incluidos los negativos.

<!--block:B0120-->
Con SVM, pasar de uno a cuatro bloques aumenta el macro-F1 medio de 0,917448 a 0,936554: una ganancia de 1,911 puntos porcentuales. Pasar de cuatro al máximo observado en diez aporta solo 0,021 puntos adicionales, mientras la dimensión media relativa aumenta de 15,42 a 45,17 \%. Cuatro concentra aproximadamente el 98,91 \% de la mejora observada entre uno y el máximo del barrido. Esta proporción describe la ganancia de F1, no el porcentaje de imágenes clasificadas correctamente ni un intervalo de equivalencia.

<!--block:B0121-->
Así, Top-4 resulta una elección compacta con buena calidad media y una regla de tamaño fácil de explicar. Después de cuatro se observan ocho pasos negativos y nueve positivos con SVM: el rendimiento fluctúa, en lugar de disminuir siempre. Con ResMLP, cinco aporta 0,212 puntos más que cuatro. La conclusión sustentada es que las ganancias posteriores pueden ser pequeñas frente al crecimiento de representación; identificar un mejor compromiso exige declarar qué calidad y costo se priorizan.

<!--block:B0122-->
\input{generated_topk_margin/top4_svm.tex}
\input{generated_topk_margin/top4_resmlp.tex}

<!--block:B0123-->
En FMD, cuatro es el máximo medio del barrido para ambos clasificadores y supera a concatenar toda la biblioteca. En Soil, cuatro también maximiza la curva SVM; con ResMLP el máximo aparece en ocho. Outex constituye una excepción relevante: la representación completa conserva una ventaja de calidad frente a cuatro. CUReT se encuentra cerca del techo de la métrica, donde diferencias pequeñas merecen una interpretación prudente. Los resultados KTH de este archivo conservan su variante histórica y no se utilizan para borrar la reserva de otra evaluación.

<!--block:B0124-->
\begin{figure}[!htbp]\centering
\includegraphics[width=\textwidth]{generated_topk_progression/curvas_por_dataset.pdf}
\caption[Barrido de tamaños en los seis datasets.]{Barrido de tamaños en los seis datasets. Cada panel muestra SVM y ResMLP con medias de las condiciones del dataset. La línea vertical y los círculos abiertos señalan cuatro. Las escalas verticales se ajustan por panel para mostrar las variaciones; KTH mantiene su reserva de procedencia.}
\label{fig:tm-per-dataset-curves}
\end{figure}

<!--block:B0125-->
\section{Qué aportan N-gramas y las ampliaciones de biblioteca}
Las tablas previas distinguen 21 bloques sin N-gramas de la biblioteca de 22. El control histórico emparejado de 20 frente a 21 con N-gramas examina otra ampliación, anterior a BEiT-v2. Se conserva en la Tabla~\ref{tab:ngram-svm} para SVM y en el Anexo~\ref{app:resultados-adicionales} para ResMLP.

<!--block:B0126-->
\input{articulo/borrador_profesor/generated/ngram_svm.tex}

<!--block:B0127-->
En ese control, añadir N-gramas a Completa en Outex cambia el macro-F1 de aproximadamente 0,9572 a 0,9674. La ampliación también puede cambiar qué subconjunto elige GFS o el Top-\(k\) de tamaño heredado. En DTD, Completa no mejora con la incorporación del bloque. El aporte no es uniforme y el resultado de una ampliación no se extrapola a todas las bibliotecas.

<!--block:B0128-->
El ranking individual y la complementariedad responden preguntas distintas. La ausencia de N-gramas entre cuatro bloques mejor puntuados individualmente no demuestra que su combinación con ellos no sea útil. La tesis no presenta como ejecutado un control Top-4 más N-gramas que no tenga evidencia emparejada y cobertura identificada.

<!--block:B0129-->
\section{Comparación externa de Top-4 en llamadas online}\label{sec:resultados-panel-online-sota}
Las Tablas~\ref{tab:tm-externos-f1} y~\ref{tab:tm-externos-ms} extraen Top-4/SVM del panel físico auditado y lo comparan con las adaptaciones externas sobre las mismas imágenes de cada condición. Las métricas de cada método se reconstruyeron con predicción y tiempo de las mismas llamadas. No se reutiliza aquí el F1 del barrido histórico con un tiempo medido después.

<!--block:B0130-->
\input{generated_topk_margin/externos_f1.tex}
\input{generated_topk_margin/externos_ms.tex}

<!--block:B0131-->
En FMD, Top-4 alcanza aproximadamente 0,98230 frente a 0,94213 de la adaptación Neshov con MLP. Requiere más tiempo en las mediciones observadas. En Soil, Top-4 queda en 0,85940 frente a 0,86310 de Neshov, y su media temporal es mayor. Este caso desfavorable se conserva. Las mediciones de fechas distintas describen el archivo disponible y no identifican por sí solas una ventaja temporal causal.

<!--block:B0132-->
Los valores Top-4 del panel online no se presentan como reproducción exacta de toda fila del barrido. Por ejemplo, Soil/SVM registra aproximadamente 0,88639 en el archivo de tamaños y 0,85940 en este panel. La discrepancia entre archivos requiere trazabilidad de selección, representación y ajuste; no se atribuye a una causa no demostrada ni se escoge el mayor número para una tabla final. Las conclusiones del barrido y las comparaciones por llamadas se mantienen dentro de sus archivos.

<!--block:B0133-->
DeepLumina conserva una reserva científica: las 46 condiciones terminadas contienen avisos de no convergencia y la inspección de modelos encontró 1.653 de 2.441 clasificadores binarios en el límite de iteraciones. DTD contiene nueve de diez condiciones terminadas y no se informa una media completa. La existencia de predicciones no convierte esos ajustes en una réplica validada.

<!--block:B0134-->
La aproximación separada Neshov FMD de 100 condiciones y 10.000 llamadas registra accuracy 94,22 \%, frente a 96,7 \% publicado. La diferencia no se oculta ni se transforma en un cambio de receta para forzar coincidencia. Se trata de una aproximación con diferencias de partición y entorno. Los porcentajes de otros artículos se interpretan de igual modo según sus protocolos.

<!--block:B0135-->
\section{P2: optimización mediante activación por margen}\label{sec:resultados-cascada}
La auditoría reconstruye 27 condiciones SVM y 31.984 observaciones de prueba a partir de las predicciones guardadas. Verifica que, en todas las imágenes derivadas, el resultado condicional es el del mismo Top-\(k\) directo. Los tamaños del rescate van de uno a ocho: cinco condiciones usan cuatro. Son una evaluación de Top-\(k\) por condición, no 27 experimentos Top-4 fijo.

<!--block:B0136-->
\input{generated_topk_margin/cascada_calidad.tex}

<!--block:B0137-->
Se identificaron además las cinco condiciones cuyo rescate tiene cuatro bloques y coincide exactamente con el subconjunto Top-4 del barrido de esa partición. La Tabla~\ref{tab:tm-fixed4-margin} conserva sus aumentos, pérdidas y empates. El subconjunto se define por identidad de bloques y tamaño, no por favorecer la activación. No representa cobertura Top-4 por margen en los seis datasets.

<!--block:B0138-->
\input{generated_topk_margin/top4_margin_subset.tex}

<!--block:B0139-->
Se selecciona cascada en 26 condiciones y uso directo en una. Las bases de las rutas condicionales son SigLIP en veinte condiciones, BEiT-v2 en cinco y ResNet-50 en una. Estas elecciones provienen del criterio interno identificado en el método; no se escoge una base por el mayor F1 externo.

<!--block:B0140-->
En FMD, el uso directo registra macro-F1 medio 0,982926 y la política por margen 0,983953. En Outex, la política condicional baja de 0,942574 a 0,936950. CUReT presenta una pérdida pequeña; DTD queda muy próximo en promedio. Soil y el KTH histórico muestran aumentos. La compuerta no produce una mejora uniforme.

<!--block:B0141-->
La ruta condicional puede superar a Top-\(k\) porque conserva la predicción base en las imágenes que no deriva. Top-\(k\) directo no es un techo matemático de esa combinación. Del mismo modo, un margen alto puede conservar un error que la segunda etapa habría corregido. La auditoría guarda ambos conteos, junto con los cambios de clase.

<!--block:B0142-->
\section{Adquisición proyectada y pilotos físicos}\label{sec:resultados-gpu}
\input{generated_topk_margin/cascada_costos.tex}
\begin{figure}[!htbp]\centering
\includegraphics[width=\textwidth]{generated_topk_margin/directo_margen.pdf}
\caption{Comparación por dataset del uso directo y por margen: calidad a la izquierda y adquisición proyectada a la derecha. La diagonal indica igualdad de la magnitud; el panel de costo no es un cronometraje físico nuevo. KTH conserva su reserva.}
\label{fig:tm-direct-margin}
\end{figure}

<!--block:B0143-->
La Tabla~\ref{tab:tm-costos} reporta \(\widehat C_V\): adquisición proyectada con la fracción externa observada después de fijar la política. La selección utilizó \(\widehat C_{\mathrm{sel}}\), calculada con las predicciones internas OOF. Que ambas tasas difieran no implica que se haya vuelto a elegir el umbral con el test. Los porcentajes describen el perfil de extracción por componentes y se mantienen separados de los cronometrajes físicos.

<!--block:B0144-->
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

<!--block:B0145-->
El piloto reúne 204 imágenes y 612 parejas, no 612 imágenes independientes. Los tiempos observados favorecen la ruta condicional en esas condiciones. Sin embargo, CUReT y Soil mantienen discrepancias entre los vectores físicos y cacheados; sus cosenos mínimos fueron aproximadamente -0,0707 y 0,0085. Coincidir en clase o ruta no demuestra identidad de representación. Los tiempos no cierran esa reserva ni acreditan reducción general en los seis conjuntos.

<!--block:B0146-->
El control físico KTH con salida directa justa documentó también que una cascada puede ser más lenta cuando Top-\(k\) ya es barato. La posibilidad de elegir uso directo forma parte de la decisión estudiada, no constituye un caso que se deba omitir.

<!--block:B0147-->
\section{Síntesis de evidencia}
P1 queda respaldada por un barrido amplio y por comparaciones que identifican tanto ventajas de compactar como pérdidas frente a representaciones mayores. P2 dispone de una comparación por predicciones del mismo Top-\(k\), costos analíticos y pilotos físicos delimitados. La cobertura completa de las predicciones no convierte automáticamente los costos en latencias físicas completas.

<!--block:B0148-->
Los experimentos de ensamble y poda permiten otras preguntas y se conservan en el Anexo~\ref{app:complementarios}. No se utilizan sus porcentajes de ahorro para atribuir un resultado al Top-\(k\) directo/por margen del cuerpo principal.


<!--block:B0149-->
# Source: paper/chapters/06_discusion.tex

<!--block:B0150-->
\chapter{Discusión}\label{sec:discusion}

<!--block:B0151-->
\section{Qué justifica estudiar Top-4}
El barrido muestra una mejora importante al pasar de una representación individual a concatenaciones pequeñas. Después aparece una región de variaciones menores, sin una ganancia monótona al añadir bloques. Con SVM, cuatro se encuentra cerca del máximo medio observado con una fracción reducida de dimensiones. Esto justifica estudiarlo como un compromiso práctico y explicable.

<!--block:B0152-->
La conclusión no es que cuatro constituya una constante óptima de la clasificación de texturas. Con ResMLP, el máximo descriptivo del barrido aparece en cinco. Outex se beneficia de una representación mayor; otras colecciones tienen márgenes pequeños de mejora o se aproximan al techo de la métrica. El promedio global no reemplaza estas diferencias.

<!--block:B0153-->
El origen de la elección también importa. Top-4 se destacó después de observar curvas externas, aunque los rankings de cada corrida se calcularan dentro del entrenamiento. Esa cronología permite una conclusión exploratoria sobre el archivo y una hipótesis para otra evaluación; no demuestra selección ciega de \(k\).

<!--block:B0154-->
\section{Relevancia individual y complementariedad}
Top-\(k\) ordena descriptores por cómo funcionan solos. Una concatenación, sin embargo, utiliza la información conjunta. Dos bloques individualmente fuertes pueden ser redundantes, y un bloque menos destacado puede corregir una limitación común de los primeros.

<!--block:B0155-->
N-gramas es relevante para interpretar esa diferencia. Su información cromática y local puede cambiar una concatenación aunque no encabece el ranking individual. Los controles con/sin el bloque muestran beneficios en algunos casos y pérdidas en otros. La explicación no debe reducirse a que una familia sea intrínsecamente superior: cambian biblioteca, combinación, clasificador y dominio.

<!--block:B0156-->
GFS permite examinar adiciones condicionadas al subconjunto, pero tiene una búsqueda más costosa y tampoco garantiza un óptimo global. El control que hereda su tamaño ayuda a separar composición y cantidad, siempre que se mantenga identificado como otra regla. Los ensambles permiten agregar decisiones, pero su ventaja no demuestra una mejora de la concatenación de un único vector.

<!--block:B0157-->
\section{Cuándo tiene sentido la activación por margen}
La ruta condicional reduce adquisición proyectada cuando el trabajo evitado compensa ejecutar la base. Para \(C_{\mathrm{inc}}>0\), las definiciones del método dan
\begin{equation}
\widehat C_V<C_{\mathrm{dir}}
\quad\Longleftrightarrow\quad
\widehat r_V<\frac{C_{\mathrm{dir}}-c_b}{C_{\mathrm{inc}}}.
\end{equation}
La desigualdad explica por qué importan tanto la base elegida como la fracción activada. Si \(c_b\geq C_{\mathrm{dir}}\), el perfil de componentes no permite un ahorro estricto mediante esa base. Si \(C_{\mathrm{inc}}=0\), se comparan directamente los costos sin dividir por cero. En todos los casos, el ahorro de latencia física exige contabilizar y medir los clasificadores, la compuerta y los demás sobrecostos de la implementación.

<!--block:B0158-->
La compuerta conserva dos posibles beneficios: evitar adquirir información innecesaria y mantener aciertos de la base que Top-\(k\) no comparte. También introduce dos riesgos: descartar un rescate útil y ejecutar un rescate que empeora la predicción. Por eso, una fracción baja de derivación no basta para evaluar el método; se requieren calidad y costo en las mismas rutas.

<!--block:B0159-->
La tolerancia interna de 0,005 limita el conjunto de candidatos del procedimiento registrado. No garantiza una pérdida externa menor a ese valor, ni tiene por sí sola el significado de una prueba de no inferioridad. El traslado del umbral al modelo reajustado puede cambiar la escala de márgenes y la tasa de rescate.

<!--block:B0160-->
\section{Qué permite afirmar el tiempo medido}
La dimensión del vector es una propiedad de la representación. La latencia depende de extractores, hardware, preprocesamiento, residencia, transferencia y clasificadores. Cuatro bloques pueden incluir redes costosas; una representación de más coordenadas puede provenir de un extractor económico. No corresponde convertir el 15 \% de dimensiones de un punto en un 85 \% de ahorro temporal.

<!--block:B0161-->
Los perfiles analíticos sirven para comparar candidatos bajo constantes comunes y seleccionar antes de evaluar. Los pilotos físicos comprueban comportamiento de una implementación y de una muestra de imágenes. El panel online posterior permite asociar F1 y tiempo de cada llamada, pero sus diferencias entre fechas no son un experimento pareado simultáneo de todos los métodos.

<!--block:B0162-->
Las discrepancias de representación de CUReT y Soil impiden cerrar el vínculo entre algunos embeddings y la ejecución física. La identidad de predicciones no resuelve esa diferencia. Se necesita una reconciliación de capa, transformación, checkpoint y muestras antes de extender el alcance, no una explicación causal elegida a partir de una coincidencia parcial.

<!--block:B0163-->
\section{Interpretación de la comparación con papers}
La tabla externa responde cómo se comportaron adaptaciones en el panel local. No demuestra que nuestras recetas reproduzcan íntegramente los artículos ni que las cifras publicadas sean incorrectas. El protocolo aproximado Neshov, por ejemplo, conserva una diferencia observada de accuracy respecto del porcentaje publicado.

<!--block:B0164-->
DeepLumina exige una reserva adicional de ajuste. No conocer el impacto de la no convergencia sobre F1 impide atribuir toda una diferencia a la calidad de su idea de concatenación. Una tabla con datos disponibles puede ser informativa si mantiene esa condición y la cobertura incompleta, pero no debe utilizarse como prueba definitiva de superioridad sobre el método del paper.

<!--block:B0165-->
Top-4 también presenta pérdidas: Soil frente a Neshov en el panel online es un ejemplo. La selección de un método exige decidir qué calidad y costo son aceptables para una aplicación; una clasificación global de ganadores ocultaría ese compromiso.

<!--block:B0166-->
\section{Amenazas a la validez y alcance}
La primera amenaza es la exposición acumulada a benchmarks durante el desarrollo. Separar pliegues sigue siendo necesario, pero no elimina la influencia de resultados anteriores sobre nuevas decisiones. Las bibliotecas intermedias y los distintos regímenes de medición constituyen otra fuente de confusión si no se identifican.

<!--block:B0167-->
La segunda es la dependencia: semillas, particiones y repeticiones físicas reutilizan imágenes. Aumentar su número no equivale a incorporar nuevos dominios. Las desviaciones entre pliegues no son intervalos de generalización universal; el no rechazo estadístico no acredita igualdad.

<!--block:B0168-->
La tercera es la conciliación entre archivos. El barrido, el benchmark estático y el panel online no se intercambian automáticamente. Las diferencias Top-4 de Soil y las variantes KTH requieren trazabilidad adicional antes de atribuir identidad de modelo y representación. Esta tesis conserva los archivos y no selecciona entre cifras según cuál favorece la hipótesis.

<!--block:B0169-->
Finalmente, faltan controles específicos para algunas preguntas secundarias, como Top-4 más N-gramas bajo determinadas bibliotecas y una campaña física íntegra del mismo Top-\(k\) directo/condicional con todas sus representaciones reconciliadas. Su ausencia limita esas afirmaciones, pero no invalida la comparación descriptiva que sí dispone de predicciones y procedencia.

<!--block:B0170-->
\section{Implicación para el diseño de un clasificador}
El recorrido permite plantear una decisión ordenada: elegir primero una biblioteca y un clasificador, evaluar la representación pequeña frente a referencias y solo después estudiar si una base aporta ventaja de adquisición. Esa secuencia evita introducir una compuerta para compensar una concatenación que no fue comparada adecuadamente.

<!--block:B0171-->
La contribución de la tesis es documentar ese recorrido con sus resultados y límites. No depende de que Top-4 gane todos los datasets, de que el margen siempre mejore F1 o de que se igualen porcentajes publicados.


<!--block:B0172-->
# Source: paper/chapters/07_conclusion.tex

<!--block:B0173-->
\chapter{Conclusiones y trabajo futuro}\label{sec:conclusion}

<!--block:B0174-->
\section{Respuesta a las preguntas de investigación}
Esta tesis estudió primero la construcción y el uso directo de la concatenación Top-\(k\) de descriptores para clasificar texturas y después la optimización de su ejecución mediante activación por margen. Ambas etapas forman parte del aporte: seleccionar una representación útil y decidir para qué imágenes compensa adquirirla.

<!--block:B0175-->
Para P1, el barrido de uno a 21 bloques, con 47 condiciones por tamaño y clasificador, mostró que aumentar la representación no mejora uniformemente el macro-F1. Top-4/SVM alcanzó una media equiponderada por dataset de 0,936554, frente al máximo descriptivo de 0,936764 en \(k=10\), utilizando aproximadamente 15,42 \% de las dimensiones de la biblioteca sin N-gramas. Con ResMLP, el máximo observado correspondió a cinco. Los datos respaldan estudiar Top-4 como alternativa compacta, no declararlo óptimo universal ni equivalente estadísticamente al máximo.

<!--block:B0176-->
La comparación por dataset conserva situaciones donde concatenar más información resulta útil. N-gramas mostró que relevancia individual y complementariedad no son intercambiables. Sus variantes con SVD y las bibliotecas intermedias deben identificarse para no atribuir a la selección un efecto producido por cambiar los candidatos. Las adaptaciones de papers ofrecen contexto empírico, con diferencias de receta y reservas explícitas.

<!--block:B0177-->
Para P2, la comparación de 27 condiciones SVM muestra que activar por margen el mismo Top-\(k\) puede mejorar o empeorar la calidad frente a ejecutarlo siempre: FMD mejora en promedio y Outex pierde macro-F1. La auditoría verifica que las imágenes derivadas reciben la predicción del mismo rescate directo, por lo que los cambios provienen de conservar la base en las restantes. Cinco condiciones coinciden en tamaño y bloques con el Top-4 del barrido; los demás rescates utilizan otros valores de \(k\). La evidencia respalda estudiar cuándo activar una concatenación fijada y conserva esa diferencia de cobertura al interpretar la versión optimizada.

<!--block:B0178-->
Los costos por componentes proyectan menor adquisición en las rutas elegidas; los pilotos físicos aportan observaciones favorables de tiempo en condiciones delimitadas. Las discrepancias de representación, las variantes KTH y el alcance de los cronometrajes impiden concluir ahorro físico universal o equivalencia predictiva. La complejidad del vector y la latencia son magnitudes que deben medirse por separado.

<!--block:B0179-->
\section{Contribución y límites del cierre}
El aporte consiste en un estudio trazable de selección, concatenación y adquisición por imagen: identifica cómo se obtiene el subconjunto, qué evidencia motiva un tamaño compacto y cuándo se utiliza una primera etapa para decidir su ejecución. Se conservan tanto mejoras como pérdidas y se separan archivos históricos, llamadas online y experimentos complementarios.

<!--block:B0180-->
Las comparaciones externas no se presentan como reproducción fiel de todos los porcentajes publicados. DeepLumina permanece bajo revisión por no convergencia e incompletitud DTD. Las discrepancias entre archivos Top-4 tampoco se resuelven escogiendo la cifra más favorable. Las conclusiones son las de una investigación exploratoria con evidencia localizada, no las de una confirmación ciega de superioridad.

<!--block:B0181-->
\section{Trabajo futuro delimitado}
Las prioridades son conciliar las variantes pendientes de representación y procedencia; completar controles específicos de complementariedad con N-gramas; y medir de manera pareada el sistema directo/por margen bajo un régimen físico explícito. Toda condición nueva deberá fijar receta y criterio antes de evaluar, conservando los datos ya observados como tales.

<!--block:B0182-->
También es pertinente examinar bases y tamaños seleccionados con otros dominios de evaluación. Una compuerta más compleja o un rescate de ensamble constituye otra hipótesis y requiere controles propios. El estudio aquí presentado muestra que la pregunta útil no es cuántos descriptores se pueden concatenar, sino qué combinación aporta calidad y para qué imágenes compensa adquirirla.


<!--block:B0183-->
# Source: paper/chapters/A_especificaciones.tex

<!--block:B0184-->
\chapter{Especificaciones de representación y selección}\label{app:especificaciones}
Este anexo conserva la parametrización necesaria para reproducir las representaciones y comparadores. Su extensión no implica que todos los bloques se adquieran para cada imagen de una ruta condicional.

<!--block:B0185-->
La biblioteca de 21 bloques del barrido excluye N-gramas y tiene 20.396 dimensiones nominales. No es la biblioteca intermedia de 21 con N-gramas y sin BEiT-v2, de 19.884 dimensiones. La biblioteca consolidada de 22 suma 20.652. Se conserva esta distinción al interpretar los porcentajes de compacidad.

<!--block:B0186-->
\section{Espacio de descriptores}

<!--block:B0187-->
La biblioteca contiene cinco operadores clásicos, RGB N-gramas con SVD y 16 extractores aprendidos congelados. Cada uno constituye un bloque candidato sujeto al mismo criterio de selección. Las
Tablas~\ref{tab:extractores-clasicos} y~\ref{tab:extractores-aprendidos}
identifican la parametrización, los checkpoints y la dimensionalidad de cada
bloque. Las redes preentrenadas se ejecutaron en modo evaluación y sin
ajuste de pesos. En los modelos cargados mediante \texttt{timm} se eliminó la
capa clasificadora (\texttt{num\_classes=0}) y se aplicó el preprocesamiento
asociado al checkpoint. Para ViT, DeiT, Swin, MAE y SigLIP se utilizó la salida
\emph{pooler} cuando estaba disponible y, en caso contrario, el token de
clasificación. Todas las imágenes se convirtieron a RGB.

<!--block:B0188-->
Los descriptores clásicos se basan en operadores LBP,
Gabor, GLCM y HOG \citep{ojala2002lbp,mehta2016drlbp,jain1991gabor,haralick1979glcm,dalal2005hog}.
Las CNN corresponden a VGG16, ResNet, DenseNet, EfficientNet y ConvNeXt V2
\citep{simonyan2015vgg,he2016resnet,huang2017densenet,tan2019efficientnet,woo2023convnextv2}.
El grupo Transformer incluye ViT, DeiT, Swin y EVA-02
\citep{dosovitskiy2021vit,touvron2021deit,liu2021swin,fang2024eva02}; las
representaciones con preentrenamiento autosupervisado o multimodal se basan en
DINOv2, MAE y SigLIP \citep{oquab2024dinov2,he2022mae,zhai2023siglip}.

<!--block:B0189-->
\begin{table}[!ht]
\centering
\caption{Seis descriptores basados en patrones, filtros, gradientes y conteos incluidos en la biblioteca. Cada fila constituye un bloque completo.}
\label{tab:extractores-clasicos}
\fontsize{9}{11}\selectfont
\begin{tabular}{@{}l>{\raggedright\arraybackslash}p{7.0cm}>{\raggedright\arraybackslash}p{3.2cm}r@{}}
\toprule
Descriptor & Parametrización & Salida & Dim. \\
\midrule
LBP & multiescala $(P,R)=(8,1),(16,2),(24,3)$; mapeo \texttt{uniform} & histogramas normalizados & 54 \\
LBP-rot & $P=8$, $R=1$; ocho rotaciones; códigos limitados a $[0,10]$ & histogramas $10\times 8$ & 80 \\
Gabor & cuatro frecuencias 0,1--0,8; seis orientaciones & media y desv. de respuesta real & 48 \\
GLCM & 256 niveles; distancias 1--3; cuatro ángulos; seis propiedades & promedios sobre ángulos & 18 \\
HOG & nueve orientaciones; celda $16^2$; bloque $2^2$; norma L2-Hys & vector HOG & 1.764 \\
N-gramas & ventana vertical $2\times1$; cuantización RGB por 12; 8.192 bins; SVD & vector normalizado & 256 \\
\bottomrule
\end{tabular}
\end{table}

<!--block:B0190-->
\begin{table}[!ht]
\centering
\caption{Representaciones aprendidas congeladas incluidas en la biblioteca (16 extractores profundos y de modelos fundacionales). ``Preclas.'' designa la salida inmediatamente anterior al clasificador del backbone.}
\label{tab:extractores-aprendidos}
\fontsize{9}{11}\selectfont
\begin{tabular}{@{}ll>{\raggedright\arraybackslash}p{6.5cm}lr@{}}
\toprule
Familia & Descriptor & Checkpoint & Salida & Dim. \\
\midrule
CNN & VGG16 & \texttt{vgg16.tv\_in1k} & preclas. & 4.096 \\
 & ResNet-50 & \texttt{resnet50.a1\_in1k} & preclas. & 2.048 \\
 & ResNet-101 & \texttt{resnet101.a1\_in1k} & preclas. & 2.048 \\
 & DenseNet-121 & \texttt{densenet121.tv\_in1k} & preclas. & 1.024 \\
 & EfficientNet-B0 & \texttt{efficientnet\_b0.ra\_in1k} & preclas. & 1.280 \\
 & ConvNeXt V2-T & \texttt{convnextv2\_tiny.fcmae\_ft\_in22k\_in1k} & preclas. & 768 \\
\midrule
Transformer & ViT-B/16 & \texttt{google/vit-base-patch16-224} & pooler/CLS & 768 \\
 & DeiT-S & \texttt{facebook/deit-small-patch16-224} & pooler/CLS & 384 \\
 & Swin-T & \texttt{microsoft/swin-tiny-patch4-window7-224} & pooler & 768 \\
 & EVA-02 base & \texttt{eva02\_base\_patch14\_224} & preclas. & 768 \\
 & BEiT-v2-B$^\dagger$ & \texttt{beitv2\_base\_patch16\_224.}\allowbreak\texttt{in1k\_ft\_in22k\_in1k} & preclas. & 768 \\
\midrule
Autosup./multimodal & DINOv2-S & \texttt{vit\_small\_patch14\_dinov2.lvd142m} & preclas. & 384 \\
 & DINOv2-B & \texttt{vit\_base\_patch14\_dinov2.lvd142m} & preclas. & 768 \\
 & DINOv2-L & \texttt{vit\_large\_patch14\_dinov2.lvd142m} & preclas. & 1.024 \\
 & MAE-B & \texttt{facebook/vit-mae-base} & pooler/CLS & 768 \\
 & SigLIP-B & \texttt{google/siglip-base-patch16-224} & pooler/CLS & 768 \\
\bottomrule
\multicolumn{5}{l}{\footnotesize $^\dagger$BEiT-v2-B (768d) consolida la biblioteca en 22 extractores (20.652 dimensiones conjuntas).}
\end{tabular}
\end{table}

<!--block:B0191-->
Los descriptores clásicos se calcularon en escala de grises con la implementación de scikit-image: LBP, LBP-rot, Gabor y GLCM sobre imágenes redimensionadas a $256\times256$, y HOG sobre $128\times128$. LBP-rot designa la implementación propia registrada como \texttt{drlbp} en los archivos experimentales: aplica LBP con mapeo \texttt{ror} a ocho rotaciones y concatena diez bins por rotación en el intervalo $[0,10]$. Los códigos fuera de ese intervalo se descartan; por tanto, es un histograma restringido, no una reproducción del DRLBP de Mehta y Egiazarian \citep{mehta2016drlbp}.

<!--block:B0192-->
La biblioteca consolidada del estudio comprende 22 descriptores (cinco operadores clásicos, N-gramas con SVD y 16 extractores aprendidos), cuyos vectores concatenados suman 20.652 dimensiones (19.884 dimensiones correspondientes al conjunto preliminar de 21 descriptores más 768 componentes aportadas por BEiT-v2-B). Las características fijas y los conteos por imagen se almacenaron junto con etiquetas, orden de muestras y hashes de procedencia; las transformaciones aprendidas se ajustaron dentro de cada partición de entrenamiento. El estudio evalúa la selección y concatenación de bloques con extractores de imagen congelados y transformaciones ajustadas dentro del entrenamiento; no compara estrategias de \emph{fine-tuning}.

<!--block:B0193-->
RGB Pixel N-grams \citep{paiva2023rgb} utiliza ventanas verticales de $2\times1$ píxeles con paso 1 sobre la imagen RGB en su resolución original. Cada canal se cuantiza mediante $q(v)=\lfloor v/12\rfloor$; los seis valores se codifican en base 22, recorriendo las dos posiciones de R, G y B. Los conteos se agrupan por el resto del código dividido por 8.192 y se comprimen mediante TruncatedSVD aleatorizado (256 componentes, cinco iteraciones y semilla de la condición). SVD se ajusta exclusivamente con el entrenamiento de cada partición interna y se reajusta sobre el entrenamiento externo para la evaluación final. El vector se normaliza con $L_2$ antes de concatenarlo. Esta parametrización comprimida se identifica como N-gramas + SVD y constituye una familia propia para la selección Homogénea.

<!--block:B0194-->
\section{Greedy Forward Selection}

<!--block:B0195-->
GFS se utiliza como un método \emph{wrapper}: los subconjuntos se valoran mediante el propio clasificador y exclusivamente dentro de la validación interna, como requieren los diseños de selección que separan búsqueda y evaluación externa \citep{kohavi1997wrappers,guyon2003feature}. La búsqueda comienza con un conjunto vacío. En el paso $t$, evalúa cada descriptor aún no seleccionado al añadirlo al subconjunto vigente y elige el candidato con mayor macro-F1 medio en la validación interna:
\begin{equation}
 j_t=\arg\max_{j\notin S_{t-1}}\widehat{F}_{1,\mathrm{inner}}(S_{t-1}\cup\{j\}),
 \qquad S_t=S_{t-1}\cup\{j_t\}.
 \label{eq:gfs}
\end{equation}
La búsqueda se limita a $k\leq 8$. Se detiene cuando la mejora respecto del paso anterior es menor que 0,001 durante dos pasos consecutivos, pero devuelve el mejor paso histórico, no necesariamente el último. Los empates se resuelven de forma determinista mediante el nombre del extractor. Todas las evaluaciones candidatas utilizan únicamente muestras pertenecientes al entrenamiento externo.

<!--block:B0196-->
La Figura~\ref{fig:gfs-pasos} representa el mecanismo general de GFS. En cada ronda se comparan únicamente los bloques aún disponibles dentro de los folds internos; el bloque elegido se incorpora al subconjunto y el test externo permanece fuera de esa decisión.

<!--block:B0197-->
\begin{figure}[!ht]
\centering
\includegraphics[width=\textwidth]{articulo/borrador_profesor/figures/gfs_pasos.pdf}
\caption{Mecanismo de Greedy Forward Selection sobre bloques completos. En cada paso se elige el bloque que maximiza el macro-F1 medio de la validación interna; el test externo se utiliza únicamente tras cerrar el subconjunto.}
\label{fig:gfs-pasos}
\end{figure}
\FloatBarrier

<!--block:B0198-->
La Tabla~\ref{tab:config-gfs} concentra los parámetros de búsqueda, comunes a ambos clasificadores.

<!--block:B0199-->
\begin{table}[!htbp]
\centering
\caption{Configuración de la selección GFS en el flujo general.}
\label{tab:config-gfs}
\fontsize{9}{11}\selectfont
\begin{tabular}{lp{8.4cm}}
\toprule
Elemento & Configuración \\
\midrule
Unidad de selección & Bloque completo generado por un extractor \\
Candidatos & Hasta 22 bloques candidatos \\
Criterio interno & Macro-F1 medio en cuatro folds estratificados y agrupados \\
Presupuesto & Hasta $k=8$ bloques \\
Parada & Dos mejoras consecutivas menores que 0,001; se devuelve el mejor paso histórico \\
Empates & Nombre del extractor, en orden determinista \\
Información excluida & Test externo y sus etiquetas durante toda la selección \\
\bottomrule
\end{tabular}
\end{table}
\FloatBarrier



<!--block:B0200-->
\section{Perfil numérico de costos del piloto}
\input{generated_editorial/perfil_costos.tex}
El perfil es una colección de constantes archivadas, no una medición de extremo a extremo del híbrido. Incluye un sobrecosto fijo de política de 0,45 ms cuando existe rescate y excluye la latencia completa de sus múltiples SVM, transferencias y régimen de carga/residencia. Las mediciones de la cascada anterior no se transfieren automáticamente a esta implementación.


<!--block:B0201-->
# Source: paper/chapters/B_procedencia.tex

<!--block:B0202-->
\chapter{Protocolos y variantes de referencia}\label{app:procedencia}

<!--block:B0203-->
\section{Separación de evaluaciones}
Las 47 condiciones estáticas por clasificador incluyen tres semillas en FMD y Soil. El panel canónico de 27 conserva solo la semilla 42 en esos conjuntos. Las medias de ambos paneles pueden diferir sin que una tabla reemplace a la otra. El piloto híbrido produce predicciones OOF de las 680 imágenes del entrenamiento oficial de Outex y mantiene fuera su test oficial.

<!--block:B0204-->
En los experimentos de desarrollo anteriores de DTD se utilizó también una partición SGKF de 4.512/1.128 imágenes. Su entrenamiento incluye 1.501 imágenes del test oficial 1, por lo que esas exploraciones no se presentan como evaluación oficial ciega ni como controles directos del benchmark. No se mezclan sus métricas con las tablas principales.

<!--block:B0205-->
\section{Procedencia de KTH}
Las tablas estáticas conservan los resultados archivados de 22 bloques. El Top-$k$ SVM de origen registra macro-F1 medio aproximado de 0,9400; el control corregido con agrupación interna por muestra registra aproximadamente 0,9445. La cascada se construyó con el rescate anterior. Coincidir en una media no acredita que selecciones, transformaciones y predicciones sean idénticas.

<!--block:B0206-->
Los contrastes estáticos sobre seis conjuntos describen el archivo indicado; no certifican que todos sus controles correspondan a la variante KTH corregida. La inferencia conjunta de la cascada excluye KTH hasta reconciliar su ruta completa. Tampoco se sustituye solo una cifra en el análisis para resolver esta reserva.

<!--block:B0207-->
\section{Fidelidad de los pilotos físicos}
El piloto de una condición por conjunto se documenta con registros por imagen y repetición. La coincidencia de rutas o clases no basta para establecer identidad del vector extraído. CUReT y Soil mantienen cosenos mínimos aproximados de -0,0707 y 0,0085 respecto al caché. No se atribuye la diferencia a una capa, interpolación o normalización concreta sin diagnóstico controlado.

<!--block:B0208-->
\section{Particiones y multiplicidades del piloto híbrido}
El desarrollo utiliza únicamente las 680 imágenes del entrenamiento oficial de Outex. Los pliegues productores estratificados y agrupados usan semilla 142; los internos, semilla 42. Cada ensamble contiene 15 votos, pero un subconjunto repetido reutiliza el mismo modelo y conserva su multiplicidad en la agregación.

<!--block:B0209-->
\begin{table}[!htbp]
\centering\small
\caption{Tamaños y modelos únicos del control de diversidad permanente en cada pliegue productor. No son nuevas réplicas ni 15 ejecuciones distintas por imagen.}
\label{tab:producer-folds}
\begin{tabular}{@{}lrrrr@{}}
\toprule
Pliegue & Entrenamiento & Validación & Votos & Modelos únicos\\
\midrule
0 & 453 & 227 & 15 & 9\\
1 & 453 & 227 & 15 & 11\\
2 & 454 & 226 & 15 & 12\\
\bottomrule
\end{tabular}
\end{table}

<!--block:B0210-->
El sorteo de diversidad usa las semillas 4.200.009, 4.200.019 y 4.200.029, derivadas de la semilla de desarrollo y del índice productor. Las particiones y miembros se conservan en los registros por pliegue. Un modelo único del rescate no equivale a un extractor único: su costo depende de la unión de los cuatro bloques de cada miembro, descontando la base cuando ya está adquirida.

<!--block:B0211-->
\section{Figuras de la cascada de referencia}
\begin{figure}[!htbp]
\centering
\includegraphics[width=0.85\textwidth]{figures/pareto_frontier_adaptive_cascade.pdf}
\caption{Comparación histórica calidad--costo bajo su perfil analítico. No representa el rescate de diversidad ni una medición física de todas las rutas.}
\label{fig:pareto-cascade}
\end{figure}
\begin{figure}[!htbp]
\centering
\includegraphics[width=0.85\textwidth]{figures/cascade_routing_efficiency.pdf}
\caption{Enrutamiento de la cascada histórica según los artefactos archivados. Las proporciones no garantizan una tasa de salida para imágenes nuevas.}
\label{fig:routing-efficiency}
\end{figure}


<!--block:B0212-->
\FloatBarrier


<!--block:B0213-->
# Source: paper/chapters/C_resultados_adicionales.tex

<!--block:B0214-->
\chapter{Resultados secundarios y variabilidad}\label{app:resultados-adicionales}

<!--block:B0215-->
\section{Exactitud y dispersión del benchmark estático}
\input{articulo/borrador_profesor/generated/baseline_accuracy.tex}
\input{generated_editorial/variabilidad_estatica.tex}
Las desviaciones entre condiciones no son intervalos de generalización a otros dominios. Semillas y particiones pueden compartir imágenes; no se tratan como réplicas independientes. Outex tiene un único split, por lo que no se estima dispersión entre splits.

<!--block:B0216-->
\section{Rankings y contrastes completos por clasificador}
\input{articulo/borrador_profesor/generated/classifier_rankings.tex}
\input{articulo/borrador_profesor/generated/classifier_global.tex}
\input{articulo/borrador_profesor/generated/classifier_holm.tex}
Los post-hoc aplican diferencias de rangos de Friedman y Holm por familia de diez pares. Sus valores no son Wilcoxon exactos ni contrastes del híbrido.
\FloatBarrier

<!--block:B0217-->
\subsection{Sensibilidad del benchmark sin KTH}
Se conservan todos los pares del análisis sobre DTD, FMD, CUReT, Outex y SoilOriginal, con una media por dataset y clasificador. Las familias de Holm son separadas para SVM y ResMLP. Este recálculo no corrige la variante KTH archivada ni aumenta el número de datasets independientes.
\input{generated_mesa_r2/kth_sensibilidad_global.tex}
\input{generated_mesa_r2/kth_sensibilidad_holm.tex}
\FloatBarrier

<!--block:B0218-->
\section{N-gramas con ResMLP y ampliación de biblioteca}
\input{articulo/borrador_profesor/generated/ngram_resmlp.tex}
Esta comparación conserva la biblioteca de 20 frente a 21 con N-gramas de su corte histórico; no equivale al barrido sin N-gramas de 21 ni a una prueba de Top-4 más N-gramas.

<!--block:B0219-->
\subsection{N-gramas en el estudio complementario de rescate}
El pool corregido conserva candidatos estáticos, sorteos, particiones y scores comunes al ofrecer versiones con y sin N-gramas. En marginal/B120, permitir color y reseleccionar cambia $0{,}900563/97{,}245$ ms a $0{,}906690/83{,}772$ ms. Cambia la ruta: no es una ablación de ruta fija. El rescate de diversidad utiliza otro pool, por lo que sus diferencias no se atribuyen únicamente al color.


<!--block:B0220-->
\section{Barrido del control de poda y compuerta}\label{sec:anexo-p0}
La Tabla~\ref{tab:p0-barrido} conserva las doce configuraciones, incluidas las cuatro sin rescate. Se calcula macro-F1 sobre las 680 predicciones reunidas; los costos se ponderan por imagen. Las comparaciones comparten imágenes y no constituyen doce datasets ni réplicas independientes.

<!--block:B0221-->
\input{generated_p0/barrido_p0.tex}
\FloatBarrier

<!--block:B0222-->
La base es la seleccionada en cada política. El rescate permanente conserva exactamente miembros y multiplicidades, omite una base innecesaria y no se reoptimiza para el presupuesto indicado. La ruta forzada, no mostrada en este barrido, tiene las mismas predicciones del rescate permanente y conserva base y sobrecosto de política; se distingue en la Tabla~\ref{tab:p0-b60}. Los cuatro casos sin rescate mantienen la base en todas las vistas.

<!--block:B0223-->
\section{Réplica del rescate por condición y regla}\label{sec:anexo-replica}
La réplica conserva cinco condiciones nuevas: FMD/42, FMD/123, FMD/2026, Outex/123 y Outex/2026. Outex/42 permanece en las tablas del piloto y no integra las medias nuevas. Las Tablas~\ref{tab:replica-barrido} y~\ref{tab:replica-referencias} mantienen los presupuestos completos y las referencias del mismo protocolo de desarrollo. No se escoge una regla por su F1 de validación productora.

<!--block:B0224-->
\input{generated_replication/replica_barrido.tex}
\input{generated_replication/replica_referencias.tex}
\FloatBarrier

<!--block:B0225-->
\subsection{Activación del mismo rescate en la réplica}
La Tabla~\ref{tab:replica-p0} compara las mismas políticas con su rescate permanente, conservando miembros y puntuaciones. Las medias se calculan primero por condición y luego entre semillas del mismo dataset. En los casos sin rescate ambas vistas son la base. Las diferencias de calidad pueden ser positivas o negativas; no se traslada a estas condiciones la conclusión de ausencia de mejora de F1 del piloto Outex/42. El archivo de análisis conserva además las sesenta filas individuales por condición, regla y presupuesto.

<!--block:B0226-->
\input{generated_replication/replica_p0.tex}
\FloatBarrier

<!--block:B0227-->
\section{Alcance de las exploraciones secundarias}
Las exploraciones de proyecciones, residuos y políticas de más etapas pertenecen al desarrollo del proyecto. No se les atribuye aquí una pérdida general frente a concatenación, ni se usa la falta de un resultado reconciliado para refutar una familia metodológica. Solo un contraste con particiones, selección y medición compatibles permitiría esa conclusión.

<!--block:B0228-->
Los registros de desarrollo conservan variantes con distintos protocolos y estimandos. Las tablas de este manuscrito incluyen resultados con fuentes identificadas y separan las comparaciones no reconciliadas. Así se evita atribuir a una misma evaluación cifras procedentes de diseños distintos.


<!--block:B0229-->
# Source: paper/chapters/D_reproducibilidad.tex

<!--block:B0230-->
\chapter{Reproducibilidad y disponibilidad}\label{app:reproducibilidad}

<!--block:B0231-->
\section{Fuentes y versiones}
El proyecto organiza código, manifiestos, decisiones de selección, predicciones y registros físicos. El código se conserva en el \href{https://github.com/Joafp/concatenacion-descriptores-texturas}{repositorio público del proyecto}. Un commit y los cambios locales deben identificarse al reproducir una versión; la existencia de un archivo público no demuestra que incluya pesos, imágenes y entornos locales.

<!--block:B0232-->
La revisión del 13 de noviembre reconstruye las curvas de tamaño y la comparación directa/por margen mediante \path{scripts/build_topk_margin_thesis_20261113.py}. Sus salidas están en \path{results/analysis/topk_margin_rewrite_20261113_v1/} y las tablas y figuras del manuscrito en \path{paper/generated_topk_margin/}. El resumen registra 124 fuentes ligadas por SHA-256, la cobertura y la ausencia de nuevos fits, predicciones o tiempos.

<!--block:B0233-->
El barrido se reconstruye desde seis CSV por clasificador. La auditoría de cascada utiliza los 27 resultados, sus decisiones pretest, predicciones y archivos Top-\(k\) de origen. El panel externo procede de \path{results/analysis/reconciliation_full_panel_20261104_v1/}. Las referencias bibliográficas corregidas se contrastaron con los metadatos del DOI y se registraron en \path{reference_metadata.json} del directorio de auditoría.

<!--block:B0234-->
Las figuras de ganancias y por dataset (252 puntos) se reconstruyen con \path{scripts/build_topk_progression_20261113.py}. Los cinco rescates con los bloques Top-4 del barrido se verifican con \path{scripts/audit_top4_margin_subset_20261113.py}. Ambos leen resultados existentes y conservan fuentes y hashes.

<!--block:B0235-->
\section{Reconstrucción sin ejecutar modelos}\label{sec:trazabilidad}
El siguiente comando utiliza salidas nuevas y rechaza sobreescribir el directorio de auditoría:
\begin{lstlisting}[basicstyle=\ttfamily\scriptsize,breaklines=true]
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 \
.venv-confirmatory/bin/python \
scripts/build_topk_margin_thesis_20261113.py \
  --audit results/analysis/topk_margin_rebuild_v1 \
  --generated output/topk_margin_rebuild
\end{lstlisting}
La reconstrucción recalcula agregados y métricas guardadas; no reextrae imágenes ni reentrena. Sus tablas no deben confundirse con una nueva validación física. El directorio generado alternativo permite comparar resultados sin alterar los utilizados por el manuscrito.

<!--block:B0236-->
Las pruebas de software verifican cobertura, integridad de fuentes y correspondencia entre predicciones derivadas y el mismo rescate. Las verificaciones de cortes anteriores, incluidas las auditorías del rescate de ensamble, se conservan con sus fechas. No se suman conteos de tests históricos para afirmar que toda la versión actual fue validada en una ejecución única.

<!--block:B0237-->
\section{Datos, pesos y portabilidad}
La disponibilidad y redistribución de imágenes, embeddings y pesos dependen de sus proveedores. El archivo público no incluye necesariamente los datasets, las características cacheadas o los modelos entrenados. Reproducir desde RGB exige checkpoints, capa y preprocesamiento de cada bloque, y ajustar las transformaciones aprendidas exclusivamente en el entrenamiento correspondiente.

<!--block:B0238-->
Los nombres de diez artefactos CUReT se normalizaron sustituyendo dos puntos por doble guion bajo para permitir su descarga en Windows. El contenido y los identificadores de protocolo internos permanecieron iguales. Los generadores y lectores se actualizaron; las rutas absolutas históricas dentro de registros se interpretan con su mapeo, no como autorización para modificar resultados sellados.

<!--block:B0239-->
Para Soil se conserva el archivo de la versión auditada y los manifiestos con los hashes de las 1.140 imágenes. Las agrupaciones por nombre son conservadoras y no acreditan conocer toda dependencia física. Las reservas KTH, Outex, CUReT/Soil y DeepLumina forman parte de los materiales y no desaparecen al empaquetar el PDF.

<!--block:B0240-->
\section{Compilación y alcance de la entrega}
La fuente principal es \path{paper/tesis.tex}, con siete capítulos y anexos. Las tablas históricas y las nuevas están incluidas por rutas explícitas. La bibliografía activa se encuentra en \path{paper/articulo/borrador_profesor/references.bib}. La compilación local utiliza Tectonic o un flujo LaTeX/BibTeX compatible; el registro de construcción identifica el resultado entregado.

<!--block:B0241-->
Una compilación correcta y una auditoría de predicciones no constituyen aprobación académica ni certifican identidad completa de todos los pipelines físicos. La entrega distingue el manuscrito escrito de las comprobaciones científicas que continúan abiertas.


<!--block:B0242-->
# Source: paper/chapters/E_declaraciones.tex

<!--block:B0243-->
\chapter*{Declaraciones}
\addcontentsline{toc}{chapter}{Declaraciones}

<!--block:B0244-->
\section*{Financiación}
Los autores declaran que no hubo financiación externa para este trabajo.

<!--block:B0245-->
\section*{Conflictos de interés}
Los autores declaran que no existen conflictos de interés.

<!--block:B0246-->
\section*{Datos y consideraciones éticas}
El estudio utiliza colecciones de imágenes preexistentes y no incorpora reclutamiento ni intervención sobre participantes. La disponibilidad de datos, código y registros se describe en el Anexo~\ref{app:reproducibilidad}. El acceso y la eventual redistribución de imágenes, características y pesos están sujetos a las condiciones de sus proveedores.

<!--block:B0247-->
\section*{Asistencia en la revisión}
Se utilizó asistencia de inteligencia artificial para reorganizar y redactar este borrador, revisar la argumentación y construir scripts de auditoría y presentación de resultados. Esa asistencia no se considera autora, fuente científica ni evidencia de validez experimental. Las afirmaciones y referencias deben ser revisadas por los autores, quienes conservan la responsabilidad de la entrega. Los resultados se vinculan con sus archivos de procedencia y se distinguen las verificaciones automáticas de una reproducción independiente.


<!--block:B0248-->
# Source: paper/chapters/F_estudios_complementarios.tex

<!--block:B0249-->
\chapter{Estudios complementarios de rescate de ensamble}\label{app:complementarios}

<!--block:B0250-->
Este anexo conserva el estudio de ensambles y poda desarrollado durante el proyecto. Su rescate contiene varios clasificadores sobre subconjuntos y no equivale a ejecutar la misma concatenación Top-k del cuerpo principal. Sus resultados OOF, presupuestos y réplicas no se atribuyen automáticamente a la comparación directa/por margen de esta tesis. Se preservan como evidencia complementaria, incluidos los casos desfavorables y las reservas de costo proyectado.


<!--block:B0251-->
\section{Bloques, miembros y política de adquisición}
Sea $\mathcal B=\{1,\ldots,M\}$ una biblioteca de extractores congelados. El bloque $j$ transforma una imagen $x_i$ en $\mathbf z_{ij}\in\mathbb R^{d_j}$. Para un subconjunto $S\subseteq\mathcal B$, se utiliza
\begin{equation}
\mathbf z_{i,S}=\mathop{\Vert}_{j\in S}
\frac{\mathbf z_{ij}}{\max(\lVert\mathbf z_{ij}\rVert_2,10^{-12})},
\qquad d_S=\sum_{j\in S}d_j .
\label{eq:concat}
\end{equation}
Cada miembro $f_S$ es una SVM entrenada sobre una concatenación de bloques; distintos votos pueden corresponder al mismo modelo. Una política $\pi=(b,E,\tau)$ consta de un bloque base $b$, una lista de miembros de rescate $E$ y un umbral $\tau$. El ensamble completo puede contener miembros repetidos con efecto en el voto, aunque cada modelo único se ejecute una sola vez.

<!--block:B0252-->
La biblioteca comprende 22 bloques y 20.652 dimensiones nominales. Los descriptores fijos se almacenan por imagen, mientras que la proyección SVD de N-gramas se aprende con el entrenamiento del ajuste pertinente. Los detalles de extracción, checkpoints y dimensiones se conservan en el Anexo~\ref{app:especificaciones}. La selección actúa sobre bloques completos, no sobre coordenadas individuales.

<!--block:B0253-->
Se denomina entrenamiento productor al conjunto utilizado para construir candidatos, seleccionar la política y reajustar los modelos. Dentro de él se obtienen predicciones OOF internas para la selección. La validación productora permanece fuera de esas decisiones y evalúa la política elegida. El Capítulo~\ref{sec:diseno} detalla ambos niveles de partición.

<!--block:B0254-->
\section{Generación del ensamble de subconjuntos}
Se construye un ensamble de 15 miembros, cada uno con cuatro bloques. La relevancia $R_j$ se obtiene normalizando $a_j$, la media aritmética del macro-F1 individual entre los pliegues internos:
\begin{equation}
R_j=\frac{a_j-a_{\min}}{a_{\max}-a_{\min}},
\label{eq:relevance}
\end{equation}
con denominador uno cuando todos los valores coinciden. La frontera de bases y las ganancias de poda, en cambio, usan macro-F1 sobre las predicciones OOF internas reunidas. Ambas agregaciones pueden producir ordenamientos diferentes. La similitud entre dos matrices de características centradas por columna, $X$ e $Y$, se calcula mediante CKA lineal \citep{kornblith2019similarity}:
\begin{equation}
\operatorname{CKA}(X,Y)=
\frac{\lVert Y^\top X\rVert_F^2}
{\lVert X^\top X\rVert_F\,\lVert Y^\top Y\rVert_F}.
\label{eq:cka}
\end{equation}
Si el denominador es cero, la implementación devuelve cero. Se usa únicamente el entrenamiento productor, es decir, las imágenes disponibles para construir y seleccionar la ruta antes de evaluar su pliegue de validación.

<!--block:B0255-->
Dado el conjunto parcial $S$, la utilidad de un candidato es
\begin{equation}
u_j(S)=R_j-\lambda\,|S|^{-1}\sum_{\ell\in S}\operatorname{CKA}(j,\ell);
\qquad u_j(\varnothing)=R_j .
\label{eq:utility}
\end{equation}
Los candidatos se ordenan por utilidad decreciente y nombre en caso de empate. Si quedan $n$ candidatos y $r_j=1$ identifica el mejor, el sorteo utiliza
\begin{equation}
p(j\mid S)=\frac{(n-r_j+1)^\beta}{\sum_{\ell=1}^{n}\ell^\beta}.
\label{eq:lottery}
\end{equation}
Cada bloque elegido se retira del sorteo del mismo miembro. Entre miembros sí pueden repetirse subconjuntos. En el piloto se fijaron $\beta=8$ y $\lambda=0{,}25$, procedentes de la configuración archivada del ensamble. No se presentan como hiperparámetros óptimos universales.

<!--block:B0256-->
\section{Puntuaciones y agregación}
Cada SVM produce un vector de puntuaciones $s_S(x)\in\mathbb R^C$, con el mismo orden de clases. Su escala $\sigma_S$ es la desviación estándar poblacional de todas las puntuaciones de sus imágenes de entrenamiento, agrupando filas y clases. Se fija en uno si no es positiva o finita. La puntuación normalizada es
\begin{equation}
\widetilde s_S(x)=s_S(x)/\sigma_S,\qquad
\widehat y_E(x)=\arg\max_c\frac{1}{|E|}
\sum_{S\in E}\widetilde s_{S,c}(x).
\label{eq:ensemble}
\end{equation}
La escala permanece congelada en validación; no se recalcula con el lote evaluado. Esta operación no convierte las puntuaciones en probabilidades calibradas. Los miembros repetidos conservan su multiplicidad en la suma del ensamble completo. El rescate podado, en cambio, usa pesos uniformes sobre modelos únicos seleccionados.

<!--block:B0257-->
\section{Base y compuerta}
Las bases candidatas pertenecen a la frontera no dominada de macro-F1 individual interno y costo proyectado. Una base se excluye si otra no es peor en calidad ni costo y la mejora estrictamente en al menos uno. Es una restricción del espacio de búsqueda: no demuestra que una base dominada individualmente carezca de utilidad para enrutamiento.

<!--block:B0258-->
El margen de la base es la diferencia entre sus dos puntuaciones más altas:
\begin{equation}
m_b(x)=\widetilde s_{b,(1)}(x)-\widetilde s_{b,(2)}(x).
\label{eq:margin}
\end{equation}
Para cada base se consideran cuantiles $q\in\{0{,}1;0{,}25;0{,}5\}$ de márgenes OOF internos. Un umbral $\tau_{b,q}$ define la regla
\begin{equation}
\widehat y_\pi(x)=
\begin{cases}
\widehat y_b(x),& E=\varnothing\ \text{o}\ m_b(x)\ge\tau_{b,q},\\
\widehat y_E(x),& m_b(x)<\tau_{b,q}.
\end{cases}
\label{eq:decision-rule}
\end{equation}
Cuando se activa el rescate, su predicción reemplaza a la base; esta no se añade como voto adicional. El margen ordena las muestras para esta regla de parada, pero no es una probabilidad de acierto. Tras reajustar la base con todo el entrenamiento productor, su escala se vuelve a estimar únicamente con ese entrenamiento y se conserva el valor numérico del umbral OOF. No se recalcula el cuantil con la validación productora. Por ello, el cuantil seleccionado no fija una fracción exacta de derivación al evaluar.

<!--block:B0259-->
\section{Costo compartido y presupuesto}
Sea $U(E)$ la unión de bloques de los miembros y $c_j$ el costo por extractor del perfil fijado. Para la fracción interna derivada $\widehat r$, se estima
\begin{equation}
\widehat C(b,E)=
\begin{cases}
c_b,&E=\varnothing,\\
c_b+c_{\mathrm{pol}}+\widehat r
\displaystyle\sum_{j\in U(E)\setminus\{b\}}c_j,&E\ne\varnothing.
\end{cases}
\label{eq:cost-hybrid}
\end{equation}
Los bloques compartidos se contabilizan una vez y la representación base se reutiliza. El piloto fija $c_{\mathrm{pol}}=0{,}45$ ms como sobrecosto del perfil. Este valor no constituye un cronometraje de todos los clasificadores del híbrido. El Anexo~\ref{app:especificaciones} registra las constantes utilizadas.

<!--block:B0260-->
Los presupuestos $B\in\{15,30,60,120\}$ ms restringen la media proyectada de selección, no el costo de cada imagen ni una media futura. La fracción derivada puede cambiar al evaluar. También se registra el número esperado de llamadas:
\begin{equation}
\widehat L=1+\widehat r\,|\operatorname{unique}(E)|.
\end{equation}
Menos llamadas no implica por sí solo una reducción física proporcional.

<!--block:B0261-->
\subsection{Interpretación del costo de adquisición}
Para una política no vacía, sea $A_{b,E}=\sum_{j\in U(E)\setminus\{b\}}c_j$ el costo adicional del rescate. El modelo por imagen es
\begin{equation}
C_\pi(x)=c_b+c_{\mathrm{pol}}+
\mathbb I[m_b(x)<\tau]\,A_{b,E}.
\end{equation}
La media de esta expresión da la Ecuación~\ref{eq:cost-hybrid}. El sobrecosto fijo se aplica a todas las imágenes cuando existe rescate, no solo a las derivadas.

<!--block:B0262-->
Una referencia que extrae permanentemente la misma unión tiene costo de adquisición $C_E=\sum_{j\in U(E)}c_j$, sin incluir latencia de clasificadores. Si $A_{b,E}>0$, la política condicional reduce ese costo estimado únicamente cuando
\begin{equation}
\widehat r < \frac{C_E-c_b-c_{\mathrm{pol}}}{A_{b,E}}.
\label{eq:break-even}
\end{equation}
La condición muestra dos efectos distintos: podar puede reducir $U(E)$ y enrutar puede reducir $\widehat r$. Una base fuera de la unión añade un costo que debe compensarse; el umbral también puede derivar demasiadas imágenes para que la adquisición resulte ventajosa. Esta identidad del modelo de costos no es una garantía de latencia física. Además, comparar un rescate podado condicional con un ensamble completo permanente cambia ambos mecanismos, por lo que no aísla el aporte de la compuerta.

<!--block:B0263-->
\section{Selección completa y poda del rescate}
Sea $\mathcal P_B$ la familia restringida de políticas visitadas a partir de las bases candidatas, los cuantiles y la búsqueda de rescates para el presupuesto $B$. Se selecciona
\begin{equation}
\widehat\pi_B\in
\underset{\pi\in\mathcal P_B:\,\widehat C(\pi)\le B}
{\operatorname{arg\,max}}\;
\widehat F_{1,\mathrm{OOF}}(\pi),
\label{eq:policy-selection}
\end{equation}
donde el macro-F1 se calcula sobre las puntuaciones internas reunidas. El desempate favorece menor costo, menos miembros y, finalmente, los identificadores deterministas de la implementación. La optimalidad se refiere solo a los puntos visitados en $\mathcal P_B$; no a todos los subconjuntos posibles. Si ninguna base cabe en el presupuesto, la configuración se registra como inviable.

<!--block:B0264-->
El criterio operativo de este estudio es maximizar calidad interna dentro de un presupuesto de adquisición fijado, no aceptar una pérdida de F1 elegida después de observar validación. Al evaluar se informan conjuntamente $\Delta F_1$, costo y cumplimiento del presupuesto frente a controles factibles para el mismo $B$. Una política domina descriptivamente a otra si no empeora ninguna de las dos magnitudes y mejora al menos una; de otro modo se conserva el compromiso, sin agregarlo en una puntuación arbitraria. No se escoge un presupuesto de despliegue ni se establece un margen retrospectivo de no inferioridad. Una excedencia en validación se registra como incumplimiento observado, aunque la selección interna fuera factible.

<!--block:B0265-->
El rescate completo compara la base sola con los 15 votos para cada base, cuantil y presupuesto factibles. La poda empieza sin miembros y añade hasta tres modelos únicos del mismo ensamble. Cada adición debe mejorar el macro-F1 interno de la ruta y cumplir $\widehat C\le B$. Se comparan dos méritos:
\begin{equation}
h_{\mathrm{rel}}=\Delta F_1,\qquad
h_{\mathrm{marg}}=\Delta F_1/\Delta\widehat C .
\end{equation}
Aquí $\Delta F_1$ es el cambio de macro-F1 de la ruta completa sobre las imágenes internas reunidas, manteniendo base y umbral; no el F1 aislado del candidato ni el F1 de las imágenes derivadas solamente. $\Delta\widehat C$ es la diferencia de costo de adquisición al añadir ese miembro a los ya elegidos.
El primer criterio se denomina \emph{relevancia} en los registros, pero su mérito es la ganancia de macro-F1 de la ruta, no la relevancia individual $R_j$ usada para generar el ensamble. Solo se aceptan ganancias mayores que $10^{-12}$. En el criterio marginal, una ganancia positiva con costo incremental no mayor que $10^{-12}$ tiene prioridad sobre razones finitas; el criterio de relevancia ordena por ganancia sin utilizar ese cociente. Los desempates consideran ganancia, costo y nombre del miembro. Se conserva el mejor punto interno visitado, incluida base sola.

<!--block:B0266-->
Esta es una búsqueda heurística sobre candidatos generados, no una solución global del problema combinatorio. La relevancia y la razón marginal usan el mismo pool, bases y cuantiles; cambiar ese pool constituiría otra comparación.

<!--block:B0267-->
\begin{table}[H]
\centering
\caption{Procedimiento de selección dentro de un entrenamiento productor. La validación productora no interviene en estos pasos.}
\label{tab:algoritmo-entrenamiento}
\begin{minipage}{0.95\textwidth}\small
\begin{enumerate}
\item Recibir entrenamiento productor, biblioteca, grupos, semilla y perfil de costos.
\item Calcular ranking individual y CKA; generar 15 subconjuntos de cuatro bloques.
\item Obtener puntuaciones OOF internas de bases y miembros, ajustando SVD y escalas dentro de cada ajuste pertinente.
\item Construir la frontera de bases; para cada presupuesto y cuantil, evaluar base sola y rescate completo o la secuencia de poda.
\item Conservar la política de mayor macro-F1 interno bajo el presupuesto y los desempates especificados.
\item Reajustar los modelos necesarios con el entrenamiento productor; congelar escalas y umbral. Guardar selección e índices antes de evaluar la validación productora.
\end{enumerate}
\end{minipage}
\end{table}

<!--block:B0268-->
\begin{table}[H]
\centering
\caption{Especificación de inferencia de la política seleccionada. El piloto la evalúa sobre puntuaciones guardadas; la ejecución física completa del híbrido no ha sido medida.}
\label{tab:algoritmo-inferencia}
\begin{minipage}{0.95\textwidth}\small
\begin{enumerate}
\item Extraer y normalizar la base; calcular su predicción y margen.
\item Si no hay rescate o el margen es al menos el umbral, devolver la predicción base.
\item En otro caso, adquirir $U(E)\setminus\{b\}$, reutilizando cada bloque ya disponible.
\item Evaluar cada modelo único del rescate; agregar puntuaciones con sus escalas y multiplicidades fijadas. Devolver la clase de mayor puntuación.
\end{enumerate}
\end{minipage}
\end{table}
\FloatBarrier

<!--block:B0269-->
\input{figures/hibrido_flujo.tex}

<!--block:B0270-->
\section{Referencias estáticas y cascada de comparación}
\label{sec:comparadores}
Las estrategias estáticas son: Individual, mejor descriptor interno; Completa, los 22 bloques; GFS, selección secuencial; Top-$k$, los primeros del ranking individual con $k$ heredado de GFS; y Homogénea, GFS restringido a una familia con el límite de tamaño del GFS heterogéneo. Top-$k$ controla composición bajo igual número de bloques, no una elección independiente de $k$.

<!--block:B0271-->
GFS inicia vacío y añade el bloque que maximiza macro-F1 interno, hasta ocho bloques. Se detiene tras dos mejoras consecutivas menores que 0,001 y devuelve el mejor paso visitado. Sus detalles y esquema se conservan en el Anexo~\ref{app:especificaciones}.

<!--block:B0272-->
La cascada de referencia usa una base y una concatenación Top-$k$ archivada como rescate. Su compuerta deriva si $m(x)\le\tau$, mientras el híbrido usa $m(x)<\tau$. El umbral se seleccionó entre cuantiles 0,25/0,50/0,75 minimizando costo bajo tolerancia interna de F1 de 0,005. La ruta Top-$k$ no se reconstruyó dentro de cada pliegue productor OOF; esta dependencia se mantiene como límite de esa referencia. Si ninguna ruta cumple, se elige Top-$k$ directo.

<!--block:B0273-->
En la referencia se consideraron ResNet-50, SigLIP, BEiT-v2 y ConvNeXt V2; KTH utilizó solo ResNet-50 y BEiT-v2. No se confunde este conjunto acotado de bases con la frontera individual del híbrido.

<!--block:B0274-->
\section{Piloto de rescate de ensamble}
Sea $D_{\mathrm{dev}}$ el entrenamiento oficial de Outex. Cada pliegue productor $h$ lo divide en entrenamiento $T_h$ y validación $V_h$, sin grupos compartidos. A su vez, $T_h$ se divide en tres pliegues internos. Se distinguen cuatro operaciones:
\begin{enumerate}
\item Construir el ranking, calcular CKA y generar los subconjuntos utilizando $T_h$.
\item Reunir puntuaciones OOF internas de las imágenes de $T_h$ y seleccionar base, umbral y rescate mediante la Ecuación~\ref{eq:policy-selection}.
\item Reajustar los modelos elegidos con $T_h$, estimar sus escalas y conservar el umbral numérico seleccionado.
\item Predecir las imágenes de $V_h$ sin modificar la política a partir de sus etiquetas.
\end{enumerate}
Al reunir las tres validaciones $V_h$ se obtienen las 680 predicciones OOF de desarrollo, una por imagen y política. Esas predicciones son distintas de las puntuaciones OOF internas que guiaron la selección.

<!--block:B0275-->
La biblioteca de candidatos se construye a nivel de $T_h$; no se genera de nuevo dentro de cada pliegue interno. Las puntuaciones internas, por tanto, sirven como criterio de selección dentro de una búsqueda adaptada a $T_h$, no como evaluación independiente del procedimiento completo. La evaluación productora conserva separadas las imágenes de $V_h$. La semilla de partición productora es 142 y la interna, 42; el Anexo~\ref{app:procedencia} registra tamaños y multiplicidades.

<!--block:B0276-->
El piloto reutiliza puntuaciones de validación productora de los miembros del control de diversidad previamente auditado. Se ajustaron las puntuaciones internas faltantes y las bases necesarias, comprobando igualdad de particiones y procedencia. Los parámetros del ensamble, presupuestos y cuantiles se fijaron desde la configuración de desarrollo; no son una preespecificación ciega de toda la investigación.

<!--block:B0277-->
Los controles del mismo piloto incluyen mejor individual interno, Top-3/4/5, Completa-22 y ensamble de diversidad permanente. Top-3/4/5 son tamaños fijos; no equivalen al Top-$k$ del benchmark que hereda $k$ de GFS. Se añadió un ensamble estático seleccionado bajo cada presupuesto, definido a continuación; no se dispone de GFS concatenado reajustado para este protocolo.

<!--block:B0278-->
\subsection{Ablación del mismo rescate con y sin compuerta}\label{sec:diseno-p0}
Se reconstruyeron cuatro vistas de cada una de las doce políticas a partir de puntuaciones y predicciones de validación productora guardadas: base sola, mismo rescate permanente, ruta forzada y ruta condicional. Se conservaron los miembros, multiplicidades, pesos, escalas, modelos y particiones; no se reentrenó ni se utilizó el test oficial. La base de cada vista es la elegida para esa política, no el mejor individual global.

<!--block:B0279-->
El rescate permanente predice todas las imágenes con los miembros fijados y contabiliza únicamente la unión $U(E)$, sin extraer una base innecesaria. La ruta forzada conserva además la base y el sobrecosto de política, pero activa el mismo rescate en todas las imágenes. Ambas producen las mismas clases; la segunda tiene otra contabilidad de costo y llamadas. La vista condicional conserva la decisión archivada de la compuerta. Si el rescate es vacío, las cuatro vistas se reducen a la base; esos casos no aportan evidencia sobre enrutamiento.

<!--block:B0280-->
El contraste entre rescate permanente y condicional aísla la activación para los modelos fijados en este archivo de desarrollo. No evalúa el mejor rescate estático posible: sus miembros fueron seleccionados conjuntamente con la compuerta. Las doce configuraciones reutilizan las mismas 680 imágenes y son dependientes. Se informan cambios predictivos, costos y llamadas, sin atribuirles significancia confirmatoria ni equivalencia poblacional.

<!--block:B0281-->
\subsection{Control estático bajo presupuesto}\label{sec:diseno-estatico-presupuesto}
En cada entrenamiento productor se reúnen los 22 clasificadores individuales y los modelos únicos del ensamble de diversidad, con las puntuaciones OOF internas guardadas. Se enumeran todos los ensambles de uno a tres miembros únicos de ese pool, con igual peso y sin repetición. Para cada presupuesto 15, 30, 60 y 120 ms se elige el mayor macro-F1 interno cuya unión de bloques sea factible. Los desempates favorecen menor costo, menos modelos y orden léxico. No se añade una base ni una compuerta al costo del control permanente.

<!--block:B0282-->
Las doce decisiones se guardaron antes de calcular sus predicciones de validación productora. Se reutilizaron nueve modelos disponibles y se reajustaron nueve con la misma receta SVM y el mismo entrenamiento productor. La enumeración es exhaustiva dentro de ese pool y límite de tres miembros, no sobre todas las concatenaciones o ponderaciones posibles. Se conservan los mismos pliegues y constantes del híbrido; el control no sustituye una ejecución GFS bajo presupuesto.

<!--block:B0283-->
Este análisis se diseñó después de conocer el piloto y P0. Su regla se fijó antes de obtener las nuevas predicciones, pero no constituye una preinscripción ciega. Se conserva todo el barrido y no se usa el test oficial ni se reajusta el híbrido a partir del resultado del control.

<!--block:B0284-->
\subsection{Réplica en FMD y semillas adicionales}\label{sec:diseno-replica}
La réplica conserva la biblioteca de 22 bloques, SVM, tres pliegues productores y tres internos, presupuestos 15/30/60/120 ms y cuantiles 0,10/0,25/0,50. Mantiene cinco sorteos de candidatos de tamaño cuatro, hasta tres miembros podados y el ensamble de quince votos con $\beta=8$ y $\lambda=0{,}25$. No se modificaron estos parámetros a partir de sus resultados. Las cinco condiciones y los comandos se fijaron antes de ejecutar la cola, después de conocer el piloto; no constituyen una preinscripción ciega de la investigación.

<!--block:B0285-->
En FMD se reserva el pliegue externo 0 de la partición estratificada y agrupada de cada semilla 42, 123 y 2026: 800 imágenes forman $D_{\mathrm{dev}}$ y las 200 restantes quedan excluidas. En Outex se mantiene el entrenamiento oficial de 680 imágenes y se añaden las semillas 123 y 2026, sin evaluar las 680 imágenes de test. El piloto Outex/42 se conserva por separado. Las semillas alteran particiones, sorteos y transformaciones; no aíslan solamente el efecto de la inicialización. La partición productora usa semilla $s+100$ y la interna, $s$.

<!--block:B0286-->
Cada condición evalúa referencias individuales, Top-3/4/5, Completa-22, ensambles permanentes, las tres reglas híbridas y el rival estático bajo presupuesto. La vista P0 vuelve a aplicar permanentemente exactamente el rescate seleccionado, sin reoptimizarlo. La cobertura se audita por imagen, grupo y transformación, manteniendo el test externo excluido. El perfil de costos es el mismo del piloto Outex, no una medición nueva de extracción en FMD. Las reglas completas y el detalle por semilla se conservan en el Anexo~\ref{sec:anexo-replica}.

<!--block:B0287-->
\section{Resultados del rescate de ensamble en desarrollo Outex}\label{sec:resultados-hibrido}

<!--block:B0288-->
El piloto usa las 680 imágenes del entrenamiento oficial de Outex, semilla 42, tres folds productores y tres internos. El test oficial no fue evaluado. La Tabla~\ref{tab:hybrid-oof} muestra todas sus políticas; no se comparan directamente con el F1 de test de la Tabla~\ref{tab:tm-cascada}.

<!--block:B0289-->
\input{generated_editorial/controles_hibrido.tex}

<!--block:B0290-->
\begin{figure}[!htbp]
\centering
\includegraphics[width=\textwidth]{figures/hibrido_calidad_costo.pdf}
\caption{Políticas del piloto Outex y controles del mismo protocolo. Se muestran los cuatro presupuestos de cada variante, incluidos puntos coincidentes. El eje horizontal es costo proyectado en escala logarítmica, no latencia física; las líneas no representan una frontera óptima.}
\label{fig:hibrido-calidad-costo}
\end{figure}
\FloatBarrier

<!--block:B0291-->
\begin{table}[!htbp]
\centering\small
\caption{Piloto híbrido de Outex: macro-F1 OOF de desarrollo y costo proyectado. $B$ es el presupuesto de selección en ms; los costos no son latencias físicas.}
\label{tab:hybrid-oof}
\begin{tabular}{@{}lrrr@{}}
\toprule
Ruta & $B$ & Macro-F1 & Costo proyectado ms\\
\midrule
Diversidad15 permanente & -- & 0,914389 & 365,196\\
Completo como rescate & 15 & 0,858056 & 12,220\\
Podado marginal & 15 & 0,858056 & 12,220\\
Podado relevancia & 15 & 0,858056 & 12,220\\
Completo como rescate & 30 & 0,854129 & 20,485\\
Podado marginal & 30 & 0,893488 & 25,394\\
Podado relevancia & 30 & 0,893488 & 25,394\\
Completo como rescate & 60 & 0,891759 & 57,839\\
Podado marginal & 60 & 0,905140 & 55,365\\
Podado relevancia & 60 & 0,910742 & 53,316\\
Completo como rescate & 120 & 0,908603 & 104,660\\
Podado marginal & 120 & 0,908781 & 84,018\\
Podado relevancia & 120 & 0,909396 & 78,938\\
\bottomrule
\end{tabular}
\end{table}

<!--block:B0292-->
El punto podado por relevancia/B60 obtiene $0{,}910742$, frente a $0{,}914389$ de diversidad permanente, con 85,40\% menos costo estimado y una diferencia de F1 de $-0{,}003646$ (aproximadamente $-0{,}365$ puntos porcentuales). Top-5 obtiene $0{,}900824/288{,}435$ ms y Completa-22 $0{,}913957/1706{,}420$ ms. El híbrido supera numéricamente Top-5, pero no a Completa ni al ensamble permanente en calidad. B60 es un punto observado dentro del barrido de desarrollo, no un presupuesto validado de forma independiente después de su selección.

<!--block:B0293-->
Ese punto deriva 278/680 imágenes: corrige 52 errores de las bases y perjudica cinco aciertos. El saldo de 47 aciertos adicionales describe exactitud, no una diferencia de macro-F1, que depende de la distribución de errores por clase. Sus bases son DINOv2-small, BEiT-v2-final y VGG16, con dos, dos y un modelos de rescate únicos. Las llamadas medias son 1,654 frente a 10,665 del ensamble permanente. El resto de las imágenes sale por la base; el Anexo~\ref{app:procedencia} aclara la diferencia entre votos y modelos ejecutados.

<!--block:B0294-->
A presupuesto 15 se elige base sola; el rescate completo/B30 tampoco se activa. Relevancia supera a marginal en calidad y costo en los puntos de 60 y 120 ms. Los 36 presupuestos internos se cumplen, pero completo/B60/fold1 registra 70,019604 ms proyectados en validación frente a 59,602804 internos. Se conservan esa excedencia y la falta de monotonía del F1 con el presupuesto.


<!--block:B0295-->
La Tabla~\ref{tab:controles-hibrido} y la Figura~\ref{fig:hibrido-calidad-costo} permiten comparar referencias sin trasladar cifras de test externo. El primer control siguiente mantiene fijo el rescate; el segundo lo compara con una selección estática propia bajo presupuesto. GFS concatenado sigue sin evaluarse en este protocolo. El análisis emparejado de N-gramas se conserva como evidencia secundaria en el Anexo~\ref{app:resultados-adicionales}.

<!--block:B0296-->
\subsection{Separación de poda y activación condicional}\label{sec:resultados-p0}
La Tabla~\ref{tab:p0-b60} descompone el punto relevancia/B60 con el control de la Sección~\ref{sec:diseno-p0}. Son las mismas 680 imágenes y los mismos modelos del piloto; el recálculo no constituye otra evaluación independiente.

<!--block:B0297-->
\input{generated_p0/descomposicion_b60.tex}

<!--block:B0298-->
La poda cambia el ensamble permanente de $0{,}914389/365{,}196$ ms a $0{,}911993/110{,}421$ ms: reduce la adquisición proyectada en 69,76\%, con $\Delta\mathrm{F1}=-0{,}002395$. Activar condicionalmente ese mismo rescate reduce otros 51,72\% respecto de su ejecución permanente, hasta $53{,}316$ ms, con $\Delta\mathrm{F1}=-0{,}001251$. Las reducciones se aplican sucesivamente y no se suman; el descenso total frente al ensamble completo es 85,40\%. La ruta forzada retiene la base y tiene costo $110{,}871$ ms; se distingue de la referencia permanente eficiente, que omite ese trabajo.

<!--block:B0299-->
Frente al mismo rescate permanente, la compuerta cambia tres clases predichas: corrige una y perjudica dos. La exactitud pasa de $0{,}914706$ a $0{,}913235$. Es un contraste distinto del balance de 52 errores corregidos y cinco aciertos perjudicados frente a las bases. Las llamadas medias apenas disminuyen un 0,79\% respecto del rescate podado permanente, de $1{,}668$ a $1{,}654$. La gran reducción de llamadas frente al ensamble completo corresponde principalmente a la poda, no a la compuerta.

<!--block:B0300-->
En marginal/B60, las 680 predicciones condicionales coinciden exactamente con las del mismo rescate permanente: macro-F1 $0{,}905140$ y exactitud $0{,}907353$. Su costo proyectado pasa de $97{,}282$ a $55{,}365$ ms, una reducción de 43,09\%. Sin embargo, las llamadas aumentan de $1{,}334$ a $1{,}672$, un 25,36\%, porque la ruta también calcula la base. Menor adquisición proyectada puede coexistir con más evaluaciones de clasificadores; la coincidencia de clases en estas imágenes no prueba equivalencia poblacional.

<!--block:B0301-->
El barrido completo, incluida la base sola, se presenta en la Tabla~\ref{tab:p0-barrido}. En ocho configuraciones existe rescate: la compuerta reduce F1 en siete y conserva las predicciones en marginal/B60; no mejora F1 en ninguna. Las otras cuatro se reducen a la base. Los rescates permanentes de ambos criterios en B60 superan 60 ms proyectados, mientras sus rutas condicionales quedan por debajo en la media reunida. Esto no descarta una alternativa estática distinta que cumpla el mismo presupuesto. La excedencia del rescate completo/B60 en un pliegue sigue vigente. Para esta ablación no se calcularon valores $p$ ni se midió latencia física.

<!--block:B0302-->
\subsection{Comparación con selección estática bajo presupuesto}\label{sec:resultados-estatico-presupuesto}
El control de la Sección~\ref{sec:diseno-estatico-presupuesto} cumple su presupuesto en las doce combinaciones de pliegue y presupuesto. Los pools contienen 31, 33 y 34 candidatos. En B60 se examinan 617 combinaciones factibles por pliegue; en B120, entre 1.287 y 1.701. La elección usa únicamente macro-F1 OOF interno. La Tabla~\ref{tab:estatico-presupuesto} conserva los cuatro presupuestos frente a relevancia, sin recomendar uno retrospectivamente.

<!--block:B0303-->
\input{generated_mesa_r2/estatico_presupuesto.tex}

<!--block:B0304-->
En B30, el híbrido por relevancia tiene mayor F1 observado y menor costo proyectado que el control: $0{,}893488/25{,}394$ ms frente a $0{,}861264/28{,}463$ ms. En B60 obtiene $0{,}910742$ frente a $0{,}892923$, pero también adquiere más información estimada: $53{,}316$ frente a $44{,}831$ ms. Ambos cumplen 60 ms en la media reunida; no son puntos de idéntico costo.

<!--block:B0305-->
En B15, el estático tiene mayor F1 ($0{,}859690$ frente a $0{,}858056$) y mayor costo ($13{,}752$ frente a $12{,}220$ ms). En B120 también obtiene mayor F1 ($0{,}909612$ frente a $0{,}909396$) con mayor costo ($103{,}040$ frente a $78{,}938$ ms). Por tanto, la comparación no muestra superioridad uniforme de la adquisición condicional. La ventaja predictiva observada dentro de B60 corresponde a este pool, semilla y protocolo de desarrollo; no establece optimalidad global, significancia entre dominios ni aceleración física.
\FloatBarrier

<!--block:B0306-->
\section{Réplica del rescate en dos datasets}\label{sec:resultados-replica}
Las cinco condiciones nuevas de la Sección~\ref{sec:diseno-replica} completaron sus etapas y la auditoría de índices, selecciones y predicciones. Las medias de la Tabla~\ref{tab:replica-medias} no incluyen el piloto Outex/42: resumen tres semillas FMD y dos semillas Outex. Se conserva relevancia como referencia de la discusión del piloto, sin cambiar la regla para escoger retrospectivamente el mejor resultado de cada fila. Las tres reglas completas y las referencias emparejadas figuran en las Tablas~\ref{tab:replica-barrido} y~\ref{tab:replica-referencias}.

<!--block:B0307-->
\input{generated_replication/replica_medias.tex}
\FloatBarrier

<!--block:B0308-->
En B60, relevancia alcanza en FMD macro-F1 medio $0{,}977489$ y adquisición proyectada $35{,}689$ ms, frente a $0{,}974600/41{,}888$ ms del estático. En las dos semillas nuevas de Outex obtiene $0{,}905991/40{,}750$ ms frente a $0{,}889152/49{,}047$ ms. Son comparaciones bajo un mismo presupuesto de selección, no a idéntico costo realizado ni pruebas de significancia entre dominios. En FMD/B30 el mayor F1 del híbrido requiere más costo; en FMD/B120 las medias de F1 casi coinciden, sin demostrar equivalencia. En Outex/B15 el estático conserva mayor F1 a cambio de mayor adquisición.

<!--block:B0309-->
El promedio FMD/B60 oculta diferencias importantes entre semillas. En la semilla 42, el estático supera al híbrido en calidad y costo: $0{,}978772/35{,}078$ ms frente a $0{,}977506/38{,}282$ ms. En 123, el híbrido pierde $0{,}000042$ de F1 con menor costo ($35{,}869$ frente a $52{,}565$ ms); en 2026 lo supera en ambas medidas. Tampoco se conserva una dominancia general de relevancia sobre marginal: en FMD/123/B30, marginal obtiene $0{,}975051/15{,}770$ ms frente a $0{,}973800/17{,}771$ ms. Las reglas compiten según condición y presupuesto.

<!--block:B0310-->
La comparación del mismo rescate con y sin compuerta también cambia de signo entre dominios. En relevancia/B60, el promedio FMD pasa de $0{,}974596/281{,}061$ ms permanente a $0{,}977489/35{,}689$ ms condicional; en las semillas nuevas de Outex pasa de $0{,}912135/134{,}273$ ms a $0{,}905991/40{,}750$ ms. La compuerta puede conservar aciertos de la base que el rescate perdería, pero no mejora siempre la calidad. La Tabla~\ref{tab:replica-p0} presenta todos los presupuestos y reglas, incluidos los casos sin rescate. La referencia permanente no es un rival reoptimizado para cumplir el presupuesto del híbrido.

<!--block:B0311-->
La réplica amplía la evidencia del piloto, pero sigue siendo desarrollo sobre benchmarks previamente observados. No valida una política única de despliegue, ni el híbrido en los seis conjuntos, ni el ahorro físico. GFS y Top-$k$ con tamaño seleccionado requieren ajustes propios bajo este protocolo; no se sustituyen por Top-3/4/5 ni por cifras de test externo.
\FloatBarrier



