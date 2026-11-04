# Guion Integral de Defensa de Tesis ante la Mesa Evaluadora (FP-UNA)

* **Título de la Tesis:** *Concatenación sistemática y fusión adaptativa costo-consciente de descriptores visuales para clasificación de texturas: De la selección anidada de bloques a la adquisición secuencial guiada por incertidumbre*
* **Expositores:** Carlos Ayala y Joaquín Delgado
* **Tutor:** Prof. José Vázquez
* **Materiales de la Defensa:**
  * Manuscrito final compilado (71 páginas): [`paper/tesis.pdf`](file:///home/joaquin/tesis_claude/paper/tesis.pdf)
  * Presentación en diapositivas (17 láminas, formato 16:9): [`paper/presentacion_defensa.pdf`](file:///home/joaquin/tesis_claude/paper/presentacion_defensa.pdf)
  * Dossier ejecutivo de tablas y metodología: [`docs/fsc_tex/DOSSIER_REUNION_METODOLOGIA_Y_BENCHMARKS.md`](file:///home/joaquin/tesis_claude/docs/fsc_tex/DOSSIER_REUNION_METODOLOGIA_Y_BENCHMARKS.md)

---

## 1. Distribución de Tiempos y Roles (Duración Estimada: 20 a 22 Minutos)

| Bloque | Diapositivas | Expositor | Contenido Principal | Tiempo |
| :--- | :---: | :--- | :--- | :---: |
| **Apertura y Fase 1** | Láminas 1 a 8 | **Carlos Ayala** | Problema, preguntas, biblioteca de 22 descriptores, protocolo anidado sin fuga, 6 datasets y resultados de concatenación estática (SVM y ResMLP). | ~10 min |
| **Fase 2, Hardware GPU y Comparación SOTA** | Láminas 9 a 16 | **Joaquín Delgado** | Arquitectura FSC-Tex (2 etapas), margen de incertidumbre $m(x)$, calibración OOF de $\tau$, 27 condiciones, benchmark físico en GPU RTX 4060 (612 pares + 94/94 condiciones online), comparación en los 6 datasets contra 4 papers del estado del arte (2022–2026) y discusión. | ~10 min |
| **Cierre y Futuro** | Lámina 17 | **Ambos** | Conclusiones principales, reproducibilidad y líneas de trabajo futuro. | ~2 min |

---

## 2. Guion Palabra por Palabra por Diapositiva (Qué Decir Exactamente)

### PARTE I — Expone: CARLOS AYALA (Láminas 1 a 8)

#### Diapositiva 1: Portada (~45 s)
> *"Buenos días/tardes a los miembros de la Mesa Evaluadora, a nuestro tutor el profesor José Vázquez y a los presentes. Hoy con mi compañero Joaquín Delgado presentamos nuestra tesis de grado titulada: **«Concatenación sistemática y fusión adaptativa costo-consciente de descriptores visuales para clasificación de texturas: De la selección anidada de bloques a la adquisición secuencial guiada por incertidumbre»**."*

#### Diapositiva 2: Estructura de la Presentación (~45 s)
> *"Organizamos la exposición en dos partes que reflejan la evolución natural de nuestra investigación:*
> * *En la **Primera Parte**, presentaré los fundamentos del problema, la biblioteca consolidada de 22 descriptores visuales y la evaluación sistemática de la concatenación estática sobre seis conjuntos de datos.*
> * *En la **Segunda Parte**, Joaquín presentará nuestra propuesta central para resolver el cuello de botella computacional: la **Cascada Adaptativa Costo-Consciente (FSC-Tex)**, su formulación matemática guiada por incertidumbre y su validación física en GPU sobre los seis conjuntos de datos."*

#### Diapositiva 3: Motivación y Problema de Investigación (~1 min 30 s)
> *"¿Por qué es difícil clasificar texturas visuales? Porque las texturas dependen simultáneamente de microestructuras locales, patrones periódicos en frecuencia y propiedades semánticas del material que varían con la escala, la iluminación y el ángulo de cámara.*
>
> *Un único descriptor aislado rara vez captura toda esta riqueza. Cuando combinamos descriptores clásicos con redes convolucionales, Vision Transformers y modelos fundacionales, el poder discriminativo mejora. Sin embargo, al investigar esta fusión nos encontramos con un **doble cuello de botella operativo**:*
> 1. *Primero, la **saturación dimensional**: después de combinar unos pocos extractores fuertes, seguir sumando bloques aporta rendimientos decrecientes.*
> 2. *Segundo, el **costo computacional fijo**: en un esquema estático tradicional, el sistema está obligado a extraer todos los descriptores seleccionados para el **100% de las imágenes**, tardando cientos de milisegundos por muestra, incluso para texturas simples que un solo modelo liviano resolvería sin dificultad."*

#### Diapositiva 4: Preguntas de Estudio y Aportes del Trabajo (~1 min 15 s)
> *"Esto nos llevó a formular dos preguntas centrales de investigación:*
> * *La primera, enfocada en la **concatenación estática**: ¿en qué medida y a qué costo dimensional combinar bloques supera al mejor descriptor individual?*
> * *Y la segunda, enfocada en la **inferencia dinámica**: ¿es posible conservar la calidad predictiva de la concatenación densa reduciendo drásticamente el tiempo de inferencia mediante una regla adaptativa guiada por incertidumbre?*
>
> *Como resultado, la tesis entrega cuatro aportes verificables: (1) un benchmark anidado de cinco estrategias estáticas sobre 22 descriptores y 6 datasets con dos clasificadores; (2) el método de cascada adaptativa evaluado en 27 condiciones canónicas; (3) una validación física pareada en GPU RTX 4060 sobre los 6 datasets con 612 mediciones aleatorizadas; y (4) trazabilidad completa muestra por muestra con 31.984 predicciones persistidas y 60 pruebas unitarias automatizadas."*

#### Diapositiva 5: Espacio de Representación — Biblioteca de 22 Descriptores (~1 min 30 s)
> *"Para que la evaluación sea verdaderamente heterogénea, consolidamos una biblioteca de **22 descriptores visuales que suman 20.652 dimensiones**:*
> * *Por un lado, **6 descriptores clásicos y estadísticos de color** (2.220 dimensiones): LBP multiescala, LBP rotacional, bancos de Gabor, matrices de coocurrencia GLCM, gradientes HOG y secuencias de color RGB Pixel N-grams comprimidas con SVD ajustado estrictamente dentro de cada partición de entrenamiento.*
> * *Por otro lado, **16 modelos profundos y fundacionales congelados** (18.432 dimensiones) divididos en tres familias: 6 redes convolucionales (desde VGG16 y ResNet-50 hasta ConvNeXt V2), 5 Vision Transformers supervisados (incluyendo ViT, Swin, EVA-02 y BEiT-v2) y 5 modelos autosupervisados o multimodales (DINOv2 en tres escalas, MAE y SigLIP).*
> * *Para evitar que un bloque de 4.096 dimensiones domine numéricamente a uno de 18 dimensiones, cada bloque se normaliza individualmente con norma $L_2$ antes de concatenarse."*

#### Diapositiva 6: Estrategias Estáticas Comparadas y Selección Anidada (~1 min 30 s)
> *"En la Fase 1 comparamos cinco estrategias bajo el mismo protocolo anidado:*
> 1. ***Individual**, que elige prospectivamente el mejor bloque único en validación interna;*
> 2. ***Completa-22**, que concatena las 20.652 dimensiones;*
> 3. ***GFS (Greedy Forward Selection)**, una búsqueda wrapper secuencial que agrega en cada paso el bloque que maximiza el macro-F1 interno hasta un máximo de $k=8$ bloques;*
> 4. ***Top-$k$**, que concatena los $k$ mejores descriptores individuales usando el mismo número de bloques $k$ que eligió GFS en esa condición; y*
> 5. ***Homogénea**, que restringe GFS a una sola familia.*
>
> *Un punto metodológico clave de nuestra tesis es el **aislamiento contra fuga de datos (zero test leakage)**: toda selección de bloques, ranking y compresión SVD ocurre exclusivamente dentro de los 4 pliegues internos de entrenamiento; el conjunto de prueba externo jamás se consulta para tomar decisiones."*

#### Diapositiva 7: Conjuntos de Datos y Cobertura Experimental (~1 min)
> *"Evaluamos seis conjuntos de datos de referencia que abarcan condiciones muy distintas: texturas en la naturaleza (**DTD**, 47 clases), materiales cotidianos (**FMD**, 10 clases), reflectancia bajo variaciones de iluminación y pose (**CUReT**, 61 clases), texturas controladas (**Outex13**, 68 clases), suelos agrícolas deduplicados (**SoilOriginal**, 7 clases) y materiales capturados sobre cuatro muestras físicas distintas (**KTH-TIPS-2b**, 11 clases).*
>
> *Además, en la Fase 1 empleamos dos clasificadores con sesgos inductivos diferentes: un clasificador lineal regularizado (**Linear SVM**) y una red neuronal residual multicapa (**ResMLP**)."*

#### Diapositiva 8: Resultados Fase 1 — Concatenación Estática (~1 min 45 s)
> *"En la tabla de la izquierda observamos el macro-F1 medio por dataset. En las 12 configuraciones evaluadas (6 datasets por 2 clasificadores), combinar descriptores supera descriptivamente a usar un descriptor individual.*
>
> *Al aplicar el protocolo estadístico no paramétrico de Demšar de forma desagregada por clasificador ($N=6$ bloques independientes), encontramos un hallazgo importante:*
> * *En **ResMLP**, la selección secuencial **GFS alcanza el primer puesto en el ranking de Friedman (1,667)** y logra una mejora estadísticamente significativa frente al control Individual tras el ajuste de Holm sobre los 10 pares posibles ($p_{\text{Holm}} = \mathbf{0{,}0191}$), reduciendo además entre el **67,1% y el 95,3% de las dimensiones**.*
> * *En **Linear SVM**, Completa y Top-$k$ empatan en el primer lugar del ranking (2,000), con $p_{\text{Holm}} = 0{,}0617$ frente a Individual.*
> * *Sin embargo, persiste el problema práctico: incluso seleccionando un subconjunto Top-$k$ o GFS, un sistema estático sigue ejecutando múltiples redes pesadas para cada imagen. Le cedo la palabra a Joaquín para explicar cómo resolvimos este cuello de botella."*

---

### PARTE II — Expone: JOAQUÍN DELGADO (Láminas 9 a 15)

#### Diapositiva 9: Fase 2 — Cascada Adaptativa Costo-Consciente (FSC-Tex) (~1 min 30 s)
> *"Muchas gracias, Carlos. Partiendo del hallazgo de la Fase 1, nos hicimos una pregunta práctica de ingeniería y ciencia de datos: si una imagen de textura es visualmente clara, ¿por qué obligar a la GPU a ejecutar cinco o seis modelos pesados?*
>
> *Así formulamos la **Cascada Adaptativa Costo-Consciente (FSC-Tex)**, que opera en dos etapas:*
> * *En la **Etapa 1 (Económica)**, extraemos un único descriptor liviano seleccionado en entrenamiento (como SigLIP-B o ResNet-50) y obtenemos las puntuaciones del clasificador lineal. Si el modelo está seguro de su respuesta, emitimos la predicción inmediatamente (**salida temprana**, lo que ocurre en el **74,0% de las imágenes**).*
> * *Solo cuando la muestra presenta ambigüedad o incertidumbre alta (**el 26,0% de los casos**), el sistema activa la **Etapa 2 (Escalamiento Denso)**: calcula los bloques restantes del subconjunto Top-$k$, reutilizando el bloque inicial si ya forma parte de él, y emite la predicción conjunta."*

#### Diapositiva 10: Cálculo del Margen de Incertidumbre y Calibración OOF (~1 min 45 s)
> *"¿Cómo cuantificamos exactamente la incertidumbre de una imagen y cómo fijamos el umbral sin hacer trampa con el conjunto de prueba?*
>
> *1. **Medición muestra por muestra (Margen $m(x)$):** Para cada imagen $x$, el clasificador lineal de la Etapa 1 produce un vector de puntuaciones de decisión $\mathbf{s}(x)$. Ordenamos las puntuaciones y calculamos la diferencia entre la clase más probable $s_{(1)}$ y la segunda clase más probable $s_{(2)}$:*
> $$m(x) = s_{(1)} - s_{(2)}$$
> *Si $m(x)$ es grande, hay una ganadora indiscutible y baja incertidumbre. Si $m(x)$ es cercano a cero, hay un empate técnico entre dos clases y alta incertidumbre.*
>
> *2. **Calibración prospectiva del umbral $\tau$ (Cero Fuga):** Dentro del conjunto de entrenamiento $T_{\text{train}}$, calculamos los márgenes fuera de pliegue (**Out-of-Fold**, OOF). Evaluamos una grilla de presupuestos de escalamiento $B \in \{0{,}25; 0{,}50; 0{,}75\}$ y definimos el umbral $\tau_B$ exactamente como el **cuantil $B$** de los márgenes OOF de entrenamiento. Finalmente, el algoritmo elige automáticamente el par $(\phi_{\text{cheap}}, \tau_B)$ que minimiza el costo computacional proyectado garantizando que el macro-F1 OOF no caiga más de media milésima ($\Delta \le 0{,}005$) respecto a Top-$k$. El conjunto de prueba jamás interviene en esta calibración."*

#### Diapositiva 11: Evaluación Predictiva en 27 Condiciones Canónicas (~1 min 45 s)
> *"Evaluamos esta política en las **27 condiciones canónicas** de los seis conjuntos de datos. La tabla muestra los resultados desglosados dataset por dataset:*
> * *En **DTD**, la cascada empata exactamente con Top-$k$ (**0,8700 vs. 0,8700**) ahorrando un **74,0%** del costo proyectado.*
> * *En **FMD** (**0,9840 vs. 0,9829**) y en **SoilOriginal** (**0,8734 vs. 0,8701**), la cascada incluso supera ligeramente a Top-$k$ al evitar que dimensiones adicionales introduzcan ruido en muestras ya resueltas.*
> * *En **CUReT** (**0,9982 vs. 0,9989**) y **Outex13** (**0,9369 vs. 0,9426**), la diferencia es mínima frente a un ahorro superior al **76%**.*
> * *En **KTH-TIPS-2b**, la cascada alcanza **0,9445** (frente a 0,9400 de la referencia de origen y **0,9445** al completar las 4 particiones del control Top-$k$ con agrupación interna por muestra física).*
>
> *A nivel global en los 6 datasets, la cascada promedia **0,9345** frente a **0,9341** de Top-$k$ con una **reducción proyectada de costo del 75,5%**. En los contrastes no paramétricos de Demšar sobre los 5 conjuntos reconciliados ($N=5$), la cascada empata en el primer lugar del rango medio de Friedman (**2,200**, igual que Completa-22 y por delante de 2,300 de Top-$k$), con $p_{\text{Holm}} = 1{,}0000$."*

#### Diapositiva 12: Frontera de Pareto y Eficiencia de Enrutamiento (~1 min)
> *"Visualmente, en la gráfica izquierda vemos la **Frontera de Pareto calidad–costo**: la Cascada Adaptativa (estrella) se ubica en la esquina superior izquierda, reteniendo la exactitud de los métodos densos a una fracción del tiempo de cómputo. Y en la gráfica derecha vemos cómo en todos los dominios texturales cerca de tres cuartas partes de las consultas se resuelven en la primera etapa."*

#### Diapositiva 13: Protocolo de Validación Física Pareada en GPU (RTX 4060) (~1 min 15 s)
> *"Ahora bien, nosotros no queríamos quedarnos solo con una simulación analítica sobre vectores en caché. Nos propusimos demostrar que el ahorro ocurre físicamente en el reloj de pared sobre los **seis conjuntos de datos**.*
>
> *Para ello construimos un benchmark físico de extremo a extremo sobre una **GPU NVIDIA GeForce RTX 4060**:*
> * *Tomamos una muestra estratificada de 1 imagen de prueba por clase en cada uno de los 6 datasets, sumando **204 imágenes únicas**.*
> * *Para eliminar cualquier sesgo por calentamiento de GPU o caché del sistema operativo, ejecutamos **3 repeticiones pareadas por imagen alternando aleatoriamente el orden** entre Cascada y Top-$k$, totalizando **612 mediciones físicas pareadas** con sincronización explícita de CUDA (`torch.cuda.synchronize()`) y registro individual con hash SHA-256."*

#### Diapositiva 14: Resultados del Benchmark Físico en GPU en los 6 Datasets (~1 min 45 s)
> *"Aquí están los resultados físicos medidos en la GPU RTX 4060 sobre los seis conjuntos de datos:*
> * *En **todos los datasets sin excepción** se verifica un ahorro sustancial de latencia física: **69,4%** en DTD (3,26$\times$), **65,8%** en CUReT (2,92$\times$), **75,5%** en KTH-TIPS-2b (4,09$\times$), **68,5%** en Outex13 (3,18$\times$), **61,5%** en SoilOriginal (2,60$\times$) y **93,7%** en FMD (16,00$\times$).*
> * *En el **agregado global de las 612 inferencias pareadas**, el tiempo medio cae de **291,21 ms a 90,25 ms**, lo que representa una **reducción física real del 69,0% en latencia de reloj de pared** y una **aceleración de 3,23 veces**.*
> * *El **74,0% de las inferencias (453 de 612)** salieron tempranamente en la Etapa 1 (solo un **26,0% de incertidumbre** requirió escalar a la Etapa 2).*
> * *Y lo más importante para la auditoría técnica: la **concordancia funcional entre la ejecución física en GPU y el caché fuera de línea fue del 100,0%** tanto en las rutas tomadas como en las predicciones emitidas."*

#### Diapositiva 15: Comparación en los 6 Datasets con Literatura Reciente (2022–2026) (~1 min 45 s)
> *"Además de nuestros controles internos, adaptamos con fidelidad matemática y de código cuatro arquitecturas recientes de clasificación de texturas por concatenación y las evaluamos en nuestro panel común de los 6 datasets en la GPU RTX 4060 (`batch=1`): **Neshov et al. (2025)**, **DeepLumina de Simon y Uma (2022)**, **HyTexNet de Gupta et al. (2026)** y **6LBP+dCellNN de Chang et al. (2024)**, sumando más de 141.000 inferencias online auditadas.*
> * *Primero, validamos la fidelidad exacta de cada adaptación contra sus papers y repositorios oficiales: **0,000000 de error en punto flotante** en `6LBP+dCellNN` frente al código y pesos oficiales de GitHub; **0,0 de error** en los ejemplos de `HyTexNet`; y replicación de exactitudes publicadas en `DeepLumina` (**90,00%** en FMD 80/20 frente a 90,15% y **98,81%** en CUReT frente a 97,53%).*
> * *Segundo, en el panel común sin fuga de datos sobre los 6 datasets, nuestra política **Adaptive-selection-margin** es simultáneamente **más rápida y mucho más precisa** que `DeepLumina`, `HyTexNet` y `6LBP+dCellNN`, ganando entre **+6,8 y +53,9 puntos de Macro-F1** con latencias de apenas **21,7 a 54,4 ms/img**; y frente al baseline individual `Neshov (2025)`, logra **+3,07 puntos de Macro-F1 en FMD** (0,9727 vs. 0,9420) al mismo costo físico (~21 ms).*
> * *Tercero, nuestra auditoría forense demostró por qué algunos papers reportaban cifras infladas en protocolos particulares: en `6LBP+dCellNN` su script oficial incluía en entrenamiento las primeras 85 imágenes de las iluminaciones de prueba de Outex; y en `HyTexNet` su split aleatorio compartía las mismas 44 muestras físicas de KTH entre entrenamiento y prueba."*

#### Diapositiva 16: Discusión Metodológica y Límites del Estudio (~1 min 15 s)
> *"En el Capítulo 6 discutimos tres aspectos metodológicos fundamentales:*
> 1. ***¿Por qué una cascada de 2 etapas y no una política secuencial profunda paso a paso (tipo MDP o Bellman con horizonte $H \ge 2$)?** Porque al evaluar pilotos multietapa comprobamos que, dado que modelos fundacionales como SigLIP ya resuelven el 74% de las imágenes en el primer paso, evaluar políticas dinámicas complejas paso a paso introduce sobrecarga computacional sin ganancias consistentes de macro-F1. Por el principio de parsimonia, dos etapas resuelven el problema de forma limpia y eficiente.*
> 2. ***Rigor epistémico:** En la tesis declaramos explícitamente que un valor $p_{\text{Holm}} > 0{,}05$ en Demšar significa no rechazar la igualdad de rangos bajo $N=5$, no una prueba algebraica de equivalencia; y distinguimos con total transparencia entre el ahorro proyectado en las 27 condiciones (75,5%) y el ahorro físico medido en las 612 inferencias pareadas en GPU (69,0%).*
> 3. ***Higiene de evaluación frente a la literatura:** Nuestra auditoría demuestra que separar rigurosamente las muestras físicas e iluminaciones de prueba es indispensable para medir la generalización real."*

---

### CIERRE — Exponen: CARLOS AYALA y JOAQUÍN DELGADO (Lámina 17)

#### Diapositiva 17: Conclusiones y Trabajo Futuro (~1 min 30 s)
> **Carlos Ayala:**  
> *"Para concluir: demostramos que si bien la concatenación estática supera a los descriptores individuales y GFS logra reducir hasta el 95,3% de las dimensiones (con ventaja significativa bajo ResMLP, $p_{\text{Holm}} = 0{,}0191$), y nuestras políticas de diversidad (`Ens-diversidad` y `Ens-tombola`) rescatan la ganancia híbrida cuando Top-$k$ sufre interferencia, el paradigma estático sigue atado al costo de extraer múltiples redes para cada imagen."*
>
> **Joaquín Delgado:**  
> *"La Cascada Adaptativa Costo-Consciente resuelve este cuello de botella: mantiene un macro-F1 medio de **0,9345** frente a **0,9341** de Top-$k$ en las 27 condiciones canónicas, demuestra en hardware real sobre los 6 datasets una **reducción del 69,0% en latencia física (3,23$\times$)** y supera en los 6 datasets a las cuatro arquitecturas recientes de concatenación del estado del arte (**Neshov 2025, DeepLumina 2022, HyTexNet 2026 y 6LBP+dCellNN 2024**), dejando abiertos caminos claros hacia la fusión temprana de tokens, el despliegue en dispositivos embebidos Edge AI y la segmentación densa de texturas. Muchas gracias, quedamos atentos a las preguntas de la Mesa Evaluadora."*

---

## 3. Banco de Preguntas Difíciles del Jurado y Respuestas Exactas

### Pregunta 1: *"¿Cómo calculan exactamente el porcentaje de incertidumbre y cómo evitan hacer trampa (data leakage) al elegir el umbral $\tau$?"*
* **Respuesta corta y contundente:**  
  *"Para cada imagen en la Etapa 1, el SVM lineal entrega las puntuaciones de todas las clases. Calculamos el margen $m(x) = s_{(1)} - s_{(2)}$, que es la distancia entre la clase más votada y la segunda más votada. Si esa resta es pequeña, el clasificador está dudando entre dos clases (alta incertidumbre). Para fijar el umbral $\tau$ sin tocar jamás el conjunto de test, usamos validación cruzada interna (Out-of-Fold) solo dentro del conjunto de entrenamiento: probamos los cuantiles 25%, 50% y 75% de los márgenes de entrenamiento y elegimos el umbral que minimiza el costo proyectado manteniendo el macro-F1 interno a menos de 0,005 del Top-$k$. Luego, con ese $\tau$ congelado, medimos en test cuántas imágenes caen por debajo de $\tau$: en el benchmark físico fue el **26,0%** (incertidumbre), mientras que el **74,0%** superó el umbral y salió en la Etapa 1."*

### Pregunta 2: *"En los contrastes estadísticos de la cascada dicen que $p_{\text{Holm}} = 1{,}0000$. ¿Eso significa que demostraron estadísticamente que la cascada es igual a Top-$k$ y a Completa?"*
* **Respuesta rigurosa (que impresionará al jurado):**  
  *"No, y lo destacamos explícitamente en los Capítulos 4, 5 y 6. En estadística frecuentista, no rechazar la hipótesis nula ($p > 0{,}05$) con $N=5$ o $N=6$ conjuntos de datos significa que los datos no muestran diferencias estadísticamente significativas en los rangos medios de Friedman (donde la cascada y Completa empatan en 2,200 y Top-$k$ tiene 2,300), pero no equivale formalmente a una prueba de equivalencia (TOST) ni de no inferioridad. Por eso reportamos con total transparencia las diferencias numéricas exactas: la cascada está a $+0{,}0004$ de Top-$k$ en el promedio de 6 datasets ($-0{,}0004$ en los 5 reconciliados) y a $-0{,}0064$ de Completa-22, a cambio de reducir el 69,0% de la latencia física en GPU."*

### Pregunta 3: *"¿Por qué en la Fase 1 GFS es estadísticamente significativo con ResMLP ($p_{\text{Holm}} = 0{,}0191$) pero con Linear SVM obtiene $p_{\text{Holm}} = 0{,}8028$?"*
* **Respuesta técnica:**  
  *"Por el sesgo inductivo de cada clasificador frente a la alta dimensionalidad. Linear SVM con regularización $L_2$ maneja muy bien espacios de 20.652 dimensiones contrayendo coordenadas colineales; por eso en SVM la concatenación Completa y Top-$k$ rinden muy fuerte y empatan en el rango 2,000. En cambio, ResMLP proyecta la entrada a una capa densa de 256 unidades y se entrena con gradiente estocástico (AdamW); cuando recibe los 22 bloques juntos (20.652 dimensiones), sufre sobreparametrización en datasets medianos. Al usar GFS, que selecciona entre 960 y 6.784 dimensiones informativas eliminando hasta el 95,3% de dimensiones redundantes, ResMLP aprovecha su no linealidad sin sobreajustar."*

### Pregunta 4: *"¿Por qué probaron la cascada física en los 6 datasets con 204 imágenes y 3 repeticiones (612 pares) y no en las 31.984 imágenes de las 27 condiciones?"*
* **Respuesta práctica:**  
  *"Las 31.984 observaciones de las 27 condiciones sí fueron evaluadas al 100% en predicción y tienen sus vectores muestra por muestra persistidos en el repositorio. Para el cronometraje físico de reloj de pared con modelos pesados residentes en VRAM y lote unitario ($\text{batch size}=1$), diseñamos un benchmark estratificado controlado sobre una condición fija por dataset (1 imagen por clase en las 204 clases totales de los 6 datasets) con 3 repeticiones pareadas de orden aleatorizado (612 pares medidos). Esto nos permitió verificar dos cosas cruciales en todos los dominios: primero, que la cascada ahorra entre 61,5% y 93,7% de tiempo real de GPU (69,0% global); y segundo, que las decisiones y predicciones físicas en GPU coinciden al **100,0%** con las predicciones cacheadas de la suite de 27 condiciones."*

### Pregunta 5: *"¿Qué pasó con KTH-TIPS-2b y por qué aparece una nota en la tabla de la cascada?"*
* **Respuesta transparente:**  
  *"En KTH-TIPS-2b las imágenes provienen de 4 muestras físicas por material. Cuando se construyó el archivo original de la cascada, la referencia Top-$k$ provenía del corte previo (con media 0,9400). Posteriormente completamos las 4 particiones del control Top-$k$ exigiendo agrupación estricta por muestra física en los pliegues internos (`innergrp-sample`), obteniendo **0,9445**, que coincide exactamente con el **0,9445** de la cascada. En la tesis reportamos ambos valores con total transparencia y mantenemos el contraste primario de Demšar sobre los 5 conjuntos cuyo archivo de cascada provino del mismo corte."*

### Pregunta 6: *"¿Cómo se comparan sus políticas frente a otros papers recientes de clasificación de texturas por concatenación (2022–2026) y por qué hay diferencias frente a algunas cifras reportadas en esos artículos?"*
* **Respuesta contundente y con evidencia forense:**  
  *"Adaptamos fielmente cuatro arquitecturas recientes (**Neshov et al., 2025; DeepLumina de Simon & Uma, 2022; HyTexNet de Gupta et al., 2026; y 6LBP+dCellNN de Chang et al., 2024**) y ejecutamos más de 141.000 inferencias online en la RTX 4060 sobre los 6 datasets. Primero verificamos que nuestra implementación es matemáticamente exacta: error 0,000000 frente al código y pesos oficiales de GitHub en `6LBP+dCellNN`, error 0,0 en los ejemplos numéricos de `HyTexNet`, y replicación de exactitudes publicadas en `DeepLumina` (90,00% vs. 90,15% en FMD 80/20 y 98,81% vs. 97,53% en CUReT). Luego, al evaluar todos bajo nuestro protocolo común sin fuga de datos en los 6 datasets, nuestra política **Adaptive-selection-margin** supera a las cuatro arquitecturas en calidad y es simultáneamente más rápida que `DeepLumina`, `HyTexNet` y `6LBP+dCellNN`. Finalmente, demostramos con auditoría de código la causa exacta de las cifras infladas en dos artículos previos: en `6LBP+dCellNN` su script oficial (`main_otc12.py`) filtra hacia el entrenamiento las primeras 85 imágenes por secuencia de las iluminaciones de prueba (`t184` y `horizon`), y en `HyTexNet` su partición aleatoria comparte las mismas 44 muestras físicas de KTH-TIPS2b entre entrenamiento y prueba."*

---

## 4. Ficha Rápida de Cifras Clave ("Cheat Sheet" para Tener en la Mano)

* **Biblioteca:** **22 descriptores** = **6 clásicos** (2.220 dims) + **16 profundos/fundacionales** (18.432 dims) = **20.652 dimensiones**.
* **Datasets:** **6 conjuntos** (DTD: 47 clases, FMD: 10, CUReT: 61, Outex13: 68, SoilOriginal: 7, KTH-TIPS-2b: 11 $\rightarrow$ **204 clases en total**).
* **Fase 1 (Estática y Selección por Diversidad):**
  * Reducción dimensional de GFS vs. Completa: entre **67,1% y 95,3%** (960 a 6.784 dims vs. 20.652 dims).
  * Friedman SVM ($N=6$): $p = 0{,}0289$ (Iman–Davenport $p = 0{,}0139$). Mejor rango: Completa y Top-$k$ (**2,000**).
  * Friedman ResMLP ($N=6$): $p = 0{,}0110$ (Iman–Davenport $p = 0{,}0025$). Mejor rango: **GFS (1,667)**; GFS vs. Individual $p_{\text{Holm}} = \mathbf{0{,}0191}$.
  * Rescate en Outex-13 (`Top-4` = 0,9371 con HOG vs. `Top-1` = 0,9427): **`Ens-diversidad` = 0,9374** y **`Ens-tombola` = 0,9387** en Outex-13 (y **0,9422** en KTH-TIPS2b).
* **Fase 2 (Cascada en 27 Condiciones Canónicas y 94/94 Condiciones Online):**
  * Macro-F1 medio global (6 datasets, 27 cond.): **Cascada = 0,9345** | **Top-$k$ = 0,9341** (`+0,0004`) | **Completa-22 = 0,9409** (`-0,0064`).
  * Macro-F1 medio reconciliado ($N=5$, 23 cond.): **Cascada = 0,9325** | **Top-$k$ = 0,9329** (`-0,0004`) | **Completa-22 = 0,9371** (`-0,0046`).
  * Reducción de costo analítico proyectado: **75,5%**.
  * Panel online completo (**94/94 condiciones**, **362.640 llamadas físicas**): latencia media de `Adaptive-selection-margin` entre **21,65 ms y 54,35 ms/img** frente a **73–127 ms/img** del ensamble estático.
* **Benchmark Físico Pareado en GPU (NVIDIA GeForce RTX 4060):**
  * Cobertura: **6 datasets**, **204 imágenes únicas** (1 por clase), **3 repeticiones pareadas con orden aleatorio** = **612 mediciones pareadas**.
  * Latencia media global: **90,25 ms (Cascada)** vs. **291,21 ms (Top-$k$)** $\rightarrow$ **reducción del 69,0% (3,23$\times$)**.
  * Tasa de Salida Temprana (Etapa 1): **74,0%** (453/612) | Incertidumbre (Etapa 2): **26,0%** (159/612) | Fidelidad Físico vs. Caché: **100,0%**.
* **Comparación en los 6 Datasets contra Literatura Reciente (141.584 llamadas online):**
  * **Adaptive-selection-margin:** DTD **0,8606** (54,4 ms) | FMD **0,9727** (21,7 ms) | CUReT **0,9951** (36,6 ms) | Outex13 **0,9168** (45,4 ms) | Soil **0,8642** (39,5 ms) | KTH **0,9236** (25,1 ms).
  * **Neshov (2025) [`BEiT-v2`]:** DTD 0,8397 (22,9 ms) | FMD 0,9420 (21,1 ms) | CUReT 0,9941 (21,2 ms) | Outex13 0,9067 (21,2 ms) | Soil 0,8578 (22,0 ms) | KTH 0,9293 (20,8 ms).
  * **DeepLumina (2022) [ResNet-101 RGB+Y + ECOC]:** DTD 0,7027 (69,6 ms) | FMD 0,8559 (53,3 ms) | CUReT 0,9881 (53,0 ms) | Outex13 0,9073 (53,5 ms) | Soil 0,8050 (57,8 ms) | KTH 0,8744 (51,6 ms).
  * **HyTexNet (2026) [MobileNetV2 + 235D + MLP]:** DTD 0,6363 (31,8 ms) | FMD 0,7652 (29,6 ms) | CUReT 0,9580 (33,5 ms) | Outex13 0,8422 (32,1 ms) | Soil 0,7748 (33,2 ms) | KTH 0,8259 (29,0 ms).
  * **6LBP+dCellNN (2024) [6$\times$LBP + Contorno]:** DTD 0,3427 (33,0 ms) | FMD 0,4329 (29,7 ms) | CUReT 0,9261 (31,2 ms) | Outex13 0,8282 (31,5 ms) | Soil 0,7990 (32,0 ms) | KTH 0,6707 (31,2 ms).
* **Auditoría de Código y Datos:** **31.984 predicciones** persistidas a tolerancia $10^{-12}$, **504.224 inferencias físicas online totales** (362.640 propias + 141.584 externas) y suite de tests unitarios aprobada al 100%.
