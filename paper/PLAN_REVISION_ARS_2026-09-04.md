# Revisión dirigida de tesis y paper: planificación ARS

Fecha: 2026-09-04. Estado: evaluación de los cambios solicitados y propuesta de implementación; no es una revisión integral certificada ni una versión nueva del manuscrito. No se modificaron los LaTeX. La revisión se realizó con los experimentos pausados; véase la actualización de reanudación al final.

## 1. Versiones y problema principal

Fuentes inspeccionadas:

- Paper de trabajo: `paper/articulo/borrador_profesor/main.tex`, modificado el 2 de septiembre. La numeración siguiente se comprobó en su `main.aux`.
- Tesis extensa: `paper/tesis.tex`, que incluye `paper/chapters/01_introduccion.tex` hasta `06_conclusion.tex`. Se revisaron específicamente su resumen, organización y pasajes de resultados/conclusiones afectados por esta solicitud.
- Copia de subida: `overleaf_upload_consolidado/main.tex`, modificada el 28 de agosto; no debe suponerse sincronizada con el paper de septiembre.
- Referente: `docs/2023_7_rgb_pixel_ngrams.pdf`, especialmente la sección 4.4, tablas 6 y 7 y conclusión. Se consultó el texto extraído; no se certificaron anclas de página ni se hizo una auditoría completa del artículo.
- Resultados estadísticos actuales: `results/confirmatory/nonparametric/primary_controltest.tex` y `primary_multipletest.tex`.
- Extensión pausada: `experiments/RGB_NGRAM_MULTIBASE_PLAN.md` y `results/confirmatory/ngram21/`.

Hallazgo prioritario: tesis y paper no describen actualmente el mismo estudio. La tesis conserva 17 extractores base, ampliación a 20, seis datasets, cuatro clasificadores y contrastes sobre folds. Su conclusión todavía afirma hipótesis confirmadas y presenta la validación anidada como trabajo futuro. El paper describe 20 extractores, cuatro datasets, dos clasificadores y evaluación anidada. No se deben trasladar las afirmaciones de significancia de la tesis antigua al protocolo actual.

La armonización necesita separar el estudio exploratorio histórico del estudio anidado actual. No equivale a borrar los experimentos antiguos ni a renombrar sus métodos como si fueran los mismos.

## 2. Mapa de cambios solicitados

Los números son los de la versión inspeccionada; editar por etiqueta LaTeX, porque cambiarán al retirar elementos.

| Solicitud | Elemento identificado | Acción propuesta y condición |
|---|---|---|
| Cambiar figura de concatenación | Figura 1, `fig:pipeline` | Sustituir por imagen → cinco ramas de extracción → vectores → uso individual o concatenación → clasificador. Detalle en sección 3. |
| Referencias enumeradas | `natbib` con `authoryear,longnamesfirst` y `cas-model2-names` | Pasar a citas numéricas compatibles con la clase CAS y revisar las frases con `citet`; no basta con cambiar el estilo bibliográfico. Compilar y verificar orden, enlaces y referencias faltantes. No se ha confirmado una revista destino. |
| Tabla 6: mejor descriptor | `tab:resultados-confirmatorios` | Añadir identidad del descriptor seleccionado por validación interna. Si cambia entre particiones, mostrar el más frecuente con frecuencia explícita o una nota con distribución; no atribuir a un único descriptor la media de distintos seleccionados. No elegirlo por el test externo. |
| Estadística como el referente | `sec:analisis-estadistico`, `sec:replica-paiva` | Organizar en rankings de Friedman/Quade, contrastes globales y comparaciones por pares ajustadas con Holm. Conservar los demás procedimientos en material de respaldo, sin elegir el ajuste por producir significancia. |
| N-gramas general | `tab:ngram-descriptor` y extensión específica de Outex | Integrar un bloque candidato en los cuatro datasets y todas las estrategias; requiere completar y validar la extensión. No presentar las seis condiciones disponibles como resultado multibase. |
| Tabla de valores p | Actualmente dispersos en prosa | Añadir tabla global y matriz triangular de Holm para los diez pares. Esquema y cifras actuales en sección 4. |
| Eliminar gráfico de folds | Figura 3, `fig:protocolo` | Retirar la figura. Conservar en texto la separación entrenamiento/validación/test y el ajuste de transformaciones dentro del entrenamiento. |
| Unificar métodos | Tabla principal, método, estadística y apéndice autónomo | Usar los mismos nombres y definiciones. La tabla principal tiene cuatro estrategias, pero la estadística cinco: incluir Homogénea en la tabla descriptiva si se conserva en la inferencia. No confundir Top-k heredado con autónomo. |
| Eliminar tabla de datasets | Tabla 5, `tab:datasets` | Sustituir por un párrafo que nombre DTD, FMD, CUReT y Outex TC 00013, con citas y protocolo esencial. Retirar la tabla no debe eliminar información necesaria para reproducir el estudio. |
| Eliminar tabla 7 y comparar en general | `tab:sota`, reproducción y concatenación específica en Outex | Retirar del cuerpo principal. Conservar la reproducción como respaldo. La comparación general debe salir del mismo protocolo para todos los datasets, no de reunir exactitudes publicadas incompatibles. |
| Evaluar tabla 8 | `tab:contexto-publicado` | No corresponde como prueba de superioridad: su propio pie admite protocolos distintos. Recomiendo retirarla del cuerpo y conservar antecedentes en prosa o material suplementario claramente contextual. |
| Nombres de pruebas, no programas | Menciones repetidas de ControlTest/MultiPleTest | Encabezar con Friedman, Quade y comparaciones post hoc con Holm. Mencionar los paquetes Java una vez en implementación/reproducibilidad y conservar sus salidas originales. |
| ¿N-gramas cambia conclusión? | Extensión `ngram21` | Pendiente de resultados completos y comparación emparejada biblioteca de 20 frente a 21 candidatos. Distinguir mejora de métrica, cambio de selección y cambio de inferencia. |
| Eliminar tabla 9 | `tab:margen-practico` | Retirar del cuerpo y eliminar referencias colgantes; conservar datos. No convertir la ausencia de significancia en equivalencia. |
| Eliminar tabla 10 | `tab:stability` | Retirar del cuerpo. Jaccard mide estabilidad de selección, no diferencia de rendimiento; no sustituirlo por una interpretación de Holm. |
| Eliminar figura 4 | `fig:random-boxplot` | Retirar gráfico y referencias del cuerpo; conservar resultados de subconjuntos aleatorios como respaldo, sin mezclar su p empírico con el post hoc multibase. |
| Revisar conclusión | `sec:conclusion` y capítulo 6 de la tesis | Reorganizar según objetivo → evidencia principal → resultado estadístico y límites → trabajo futuro. No trasladar la afirmación de superioridad del artículo referente. |

## 3. Diseño de la nueva figura

Cinco ejemplos ilustrativos de la biblioteca, no cinco descriptores nuevos ni toda la biblioteca:

| Rama | Transformación que mostrar | Vector de salida |
|---|---|---|
| LBP, patrones locales | Vecindario y comparaciones con el píxel central; mapa de códigos | Histograma de patrones |
| Gabor, filtros | Ejemplo de filtro orientado y mapa de respuestas | Estadísticos de respuestas |
| GLCM, estadística de segundo orden | Pares de intensidades y matriz de coocurrencia | Propiedades de la matriz |
| ResNet, representación aprendida | Extractor congelado y mapas de activación esquemáticos | Embedding |
| RGB Pixel N-grams, secuencias | Cuantización y ventana que forma una secuencia RGB | Histograma; compresión adicional si esa es la variante adoptada |

Composición de izquierda a derecha: una imagen real de textura se ramifica a las cinco transformaciones. Cada transformación termina en un bloque vectorial de color distinto y normalización L2. Después se muestran dos recorridos: un bloque individual hacia el clasificador, o varios bloques unidos extremo con extremo hacia el clasificador. Etiquetar las dimensiones como d1,…,d5; la concatenación tiene dimensión igual a la suma de los bloques utilizados, no a su promedio.

La figura debe mostrar que seleccionar bloques y concatenarlos son operaciones distintas: Completa conserva todos; GFS y Top-k determinan subconjuntos; Homogénea restringe la familia. El ejemplo de cinco ramas ilustra el mecanismo; no implica que todos los subconjuntos dibujados sean admisibles para Homogénea.

No representar todo como «peso asignado a cada píxel». Un histograma cuenta patrones, GLCM cuenta relaciones y un embedding no es una atribución por píxel. Si se dibujan mapas esquemáticos, identificarlos como tales. Para mapas reales, generarlos con el extractor correspondiente sobre la misma imagen. Una reproducción visual explicativa no debe aparentar ser evidencia experimental.

## 4. Presentación estadística propuesta y resultados disponibles

El referente usa Friedman y Quade, rankings medios y una tabla de comparaciones por pares presentada como valores p ajustados con Holm. Podemos adoptar esa estructura. Sus números y sus conclusiones no se transfieren a nuestro estudio. Un contraste global significativo tampoco demostraría que todos los pares difieren.

En nuestro paper actual, macro-F1 es la métrica primaria. Las matrices antiguas de otras métricas no corresponden automáticamente a la evaluación actual; el propio método lo advierte. Para incorporarlas se necesitan predicciones y estrategias compatibles, no copiar tablas históricas.

### Tabla A: rankings del análisis principal, biblioteca de 20

Cifras verificadas en la salida Java `primary_controltest.tex`:

| Estrategia | Friedman | Quade |
|---|---:|---:|
| Individual | 4,750 | 4,800 |
| Completa | 2,500 | 2,400 |
| Top-k | 2,250 | 2,000 |
| GFS | 2,500 | 2,400 |
| Homogénea | 3,000 | 3,400 |

Menor ranking representa mejor desempeño relativo, no puntos de F1 ni significancia por sí mismo.

### Tabla B: contrastes globales

El paper actual reporta Friedman p=0,1586 y Quade p=0,1264 en cuatro bloques independientes por dataset. Ambos superan alfa=0,05. Iman–Davenport (0,1429) y rangos alineados (0,5190) pueden quedar como respaldo para mantener el cuerpo compacto. El criterio no debe ser exigir unanimidad de pruebas: se debe declarar qué análisis se usa y respetarlo.

### Tabla C: comparaciones por pares

Crear una matriz triangular de cinco estrategias con los diez valores p ajustados de Holm. Para destacar la pregunta contra Individual, estas son sus cuatro celdas actuales, verificadas en `primary_multipletest.tex`:

| Comparación | p sin ajustar | p de Holm, familia de diez pares |
|---|---:|---:|
| Top-k frente a Individual | 0,025347 | 0,253473 |
| GFS frente a Individual | 0,044171 | 0,397542 |
| Completa frente a Individual | 0,044171 | 0,397542 |
| Homogénea frente a Individual | 0,117525 | 0,822674 |

Ninguna es significativa a 0,05. La tabla completa debe conservar también los seis pares restantes, aunque no sean significativos. Los valores ajustados mayores que 1 que imprime el Java se presentan acotados a 1, explicando esa normalización de presentación y sin editar los archivos originales. No confundir los umbrales alfa/i con valores p ajustados.

Si se muestran estos pares pese al no rechazo global, aclarar su carácter informativo y la regla de análisis adoptada; no presentarlos como un post hoc habilitado por un Friedman significativo. No cambiar ahora a una familia de cuatro contrastes y conservar silenciosamente el rótulo de la familia original de diez.

La sensibilidad con ocho filas dataset–clasificador debe ir separada y advertir que reutiliza datasets. No sustituye al análisis primario por ofrecer valores menores. Tras integrar N-gramas, las tres tablas se regeneran desde una única matriz completa y trazable.

## 5. N-gramas: decisión pendiente antes de cerrar el método

Estado observado: seis checkpoints completos, todos de DTD (ResMLP splits oficiales 1–4 y SVM 1–2). CSV con 24 filas de resultados. El plan multibase exige 56 condiciones; no está completo. Esta revisión no lanzó ni reanudó ejecuciones.

La variante planificada no es el histograma original: códigos módulo 8192, suma de colisiones, TruncatedSVD hasta 256 componentes y normalización L2. Debe ajustarse SVD exclusivamente con entrenamiento en cada partición interna y externa. La reproducción con histogramas originales de Outex permanece separada.

Decisión del autor pendiente: ¿el descriptor general que se quiere estudiar es RGB Pixel N-grams original, o se acepta la variante comprimida denominada RGB Pixel N-grams + SVD? Esa elección afecta método, cómputo y qué puede concluirse sobre el descriptor. No cambiarla después de observar cuál obtiene mejores resultados.

Para evaluar si cambia la conclusión: completar las mismas condiciones con el bloque adoptado; verificar cobertura e identidades; regenerar Top-k y Homogénea bajo la misma biblioteca; comparar métricas y dimensiones contra la biblioteca de 20 en condiciones coincidentes; registrar cuándo se selecciona N-gramas; reconstruir matrices multibase y ajustes. Un cambio numérico o un cruce aislado de 0,05 no prueba por sí solo un beneficio general del descriptor.

## 6. Orden de trabajo y criterios de aceptación

1. Resolver la variante de N-gramas y dejar explícito qué estudio es principal y cuál histórico en la tesis. La línea solicitada por el usuario es concatenación de descriptores; no se propone aquí una nueva afirmación de contribución.
2. Aplicar limpieza editorial por etiquetas: retiros solicitados, citas numéricas, nombres consistentes y nueva figura. Conservar versiones anteriores y datos; revisar todos los cruces LaTeX tras la renumeración.
3. Incorporar las tablas estadísticas actuales, claramente identificadas como biblioteca de 20, sin afirmar que incluyen N-gramas. Añadir la identidad del individual desde los registros de selección y Homogénea si sigue en los contrastes.
4. Cuando el usuario reanude los experimentos, completar la biblioteca ampliada. No reemplazar medias completas con resultados parciales.
5. Actualizar método, tablas, resumen y conclusión conjuntamente; sincronizar después la carpeta de subida. Compilar y revisar visualmente: citas numéricas, tablas legibles, figura sin solapamientos, referencias resueltas y ausencia de afirmaciones estadísticas antiguas incompatibles.

Checkpoint ARS: evaluación dirigida y decisiones de presentación preparadas. No se declara diálogo por capítulos completado, contribución nueva aprobada, manuscrito listo para enviar ni conformidad con una revista específica. La siguiente decisión material es la variante de N-gramas; la reanudación de cómputo continúa pendiente del aviso del usuario.

## Actualización: reanudación solicitada durante esta revisión

El usuario pidió dejar ejecutando los experimentos. El 4 de septiembre a las 23:45 (America/Asuncion) se iniciaron dos sesiones persistentes mediante `scripts/run_rgb_ngram_queue.sh`: SVM (sesión 86027) y ResMLP (11285). Ambas omitieron los checkpoints terminados: SVM 1–2 y ResMLP 1–4 de DTD. Continúan la variante comprimida ya iniciada, sin modificar su protocolo. SVM conserva CPU y ResMLP acceso GPU. Cada cola programa DTD → FMD → CUReT → Outex y después los controles Top-k de los cuatro datasets; se detiene si una etapa falla. Un intento previo con nohup no permaneció activo y fue sustituido por estas sesiones, sin experimentos duplicados observados. Esta reanudación reemplaza el estado de pausa mencionado en las secciones anteriores; no significa que los resultados estén completos ni que se haya decidido la redacción definitiva sobre N-gramas.
