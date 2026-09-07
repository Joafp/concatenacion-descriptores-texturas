# Dictamen editorial independiente — 2026-08-15

Manuscrito: *Selección y concatenación de descriptores heterogéneos para la
clasificación de texturas*  
Modalidad: ARS `academic-paper-reviewer`, revisión completa.  
Panel simulado: adecuación editorial, metodología/estadística, dominio,
perspectiva externa y abogado del diablo, seguido de síntesis editorial.  
Procedencia: evaluación local con una única familia de modelo; no se remitió el
manuscrito a un proveedor externo.  
Criterios de revista: `criteria_binding_unavailable`. No se indicó una revista o
conferencia objetivo confirmada por los autores; el dictamen evalúa validez y
preparación general, no cumplimiento de una guía editorial específica.

## Decisión

**MINOR REVISION para el borrador de tesis; todavía no “Accept” para envío a una
revista.**

La pregunta de investigación, el diseño anidado, los comparadores y la lectura
estadística forman ahora una cadena lógica coherente. No se detectó un defecto
crítico que invalide los resultados ni una necesidad inmediata de repetir el
bloque experimental. Las revisiones pendientes se concentran en la presentación
tabular, la jerarquía de evidencia y la calibración visual de las comparaciones
publicadas. Antes de una presentación externa también debe reemplazarse la URL
pendiente del código por una versión pública y archivada.

## Configuración del panel

| Asiento | Perspectiva aplicada | Pregunta principal |
|---|---|---|
| EIC | Editor de visión por computador aplicada | ¿La contribución y su alcance se entienden sin sobrepromesas? |
| R1 | Metodología y estadística de aprendizaje automático | ¿La selección permanece aislada del test y la incertidumbre se interpreta correctamente? |
| R2 | Reconocimiento y clasificación de texturas | ¿La literatura, los baselines y la contribución respecto de RGB Pixel N-grams son técnicamente pertinentes? |
| R3 | Reproducibilidad y comunicación científica | ¿Puede un lector reconstruir el estudio y distinguir evidencia directa de contexto? |
| DA | Abogado del diablo | ¿Qué explicación alternativa debilita más la tesis y está correctamente reconocida? |

## Informes independientes

### EIC — adecuación editorial

**Fortalezas.** El título corresponde al objeto estudiado; las tres
contribuciones son concretas; la conclusión sigue la secuencia propuesta,
evaluación, resultados y trabajo futuro. El resumen ya evita afirmar una
superioridad estadística inexistente en Outex.

**Hallazgo menor EIC-1.** La tabla principal concede el mismo peso visual a seis
cantidades distintas. El lector no identifica de inmediato qué comparación
responde la pregunta primaria y cuál representa costo. Remedio mínimo: separar
desempeño de presupuesto/dimensionalidad y mostrar explícitamente las diferencias
de GFS respecto del individual y de la concatenación completa.

**Recomendación:** Minor Revision.

### R1 — metodología y estadística

**Fortalezas.** El test externo queda excluido de la selección; DTD/FMD, CUReT y
Outex reciben interpretaciones compatibles con su distinta estructura de
particiones; Wilcoxon e intervalos sobre splits reutilizados se declaran
descriptivos; el análisis pareado de Outex usa predicciones por imagen y no
simula réplicas inexistentes. El margen práctico se aplica simétricamente.

**Hallazgo menor R1-1.** La media y desviación estándar de la tabla central no
codifican el estatus inferencial de cada dataset. Remedio mínimo: incorporar el
número y tipo de evaluaciones en el encabezado o en una columna de evidencia y
marcar Outex como un único split.

**Hallazgo menor R1-2.** El control top-$k$ hereda el valor de $k$ de GFS. Esta
limitación está correctamente declarada y no exige una nueva ejecución para
sostener las conclusiones actuales; la tabla debe llamarlo explícitamente
“control de composición”.

**Recomendación:** Minor Revision.

### R2 — dominio y antecedentes

**Fortalezas.** Related Work está orientado a la necesidad de combinar
representaciones; RGB Pixel N-grams funciona como antecedente directo y no como
decoración bibliográfica. La comparación oficial de Outex conserva imágenes,
split, parametrización y clasificador. La auditoría bibliográfica verificó las
30 referencias y corrigió los metadatos problemáticos.

**Hallazgo menor R2-1.** La tabla de “contexto publicado” coloca en un mismo
cuerpo una comparación directamente reproducible y tres comparaciones de
contexto. Aunque el texto lo explica, el diseño visual puede sugerir un
leaderboard. Remedio mínimo: separar “comparación directa” de “contexto no
homólogo” y sustituir prosa larga por una categoría de comparabilidad con una
nota precisa.

**Recomendación:** Minor Revision.

### R3 — reproducibilidad y lectura externa

**Fortalezas.** Los extractores, dimensiones, datasets, clasificadores y reglas
de GFS están descritos; los manifiestos, hashes y conteos permiten auditar la
procedencia. La Figura 1 y el protocolo anidado permiten entender el flujo sin
conocer previamente la implementación.

**Hallazgo menor R3-1.** La tabla de 20 extractores depende de una reducción
global de escala, lo cual disminuye la legibilidad y oculta la agrupación por
familia. Remedio mínimo: usar grupos visuales, abreviar la salida común y mover
los identificadores largos de checkpoint a una nota o apéndice de
reproducibilidad.

**Hallazgo menor R3-2.** La tabla de frecuencias presenta frases completas en una
sola celda y no permite comparar verticalmente los tres rangos. Remedio mínimo:
una columna por rango y porcentajes alineados.

**Recomendación:** Minor Revision.

### DA — abogado del diablo

**Contraargumento más fuerte.** Ningún descriptor clásico aparece entre los tres
bloques más recurrentes. Por ello, los resultados no demuestran que mezclar
familias clásicas y profundas sea el mecanismo de mejora; podrían demostrar
principalmente diversidad entre preentrenamientos profundos fuertes.

**Adjudicación DA-1: resuelto, no crítico.** El manuscrito lo reconoce de forma
explícita en resultados, discusión y limitaciones. El título afirma que la
biblioteca evaluada es heterogénea y que se seleccionan/concatenan sus bloques;
no afirma que la mezcla clásico--profunda sea universalmente superior. Debe
conservarse este encuadre y evitar que una tabla o leyenda vuelva a insinuar una
causalidad por familia.

**Contraargumento secundario.** Cuatro aciertos adicionales en Outex pueden ser
azar de muestreo.

**Adjudicación DA-2: resuelto, no crítico.** El manuscrito informa el IC95 % que
incluye cero, McNemar $p=0{,}585$ y limita la afirmación a una mejora puntual.

**Recomendación:** Minor Revision; cero problemas CRITICAL validados o no
resueltos.

## Síntesis editorial

### Consenso 5/5

1. El núcleo de la tesis es válido y coherente: concatenación y selección se
   evalúan como decisiones de bloques bajo separación interna/externa.
2. La evidencia respalda una conclusión condicional: concatenar puede elevar el
   máximo; seleccionar comprime; GFS no domina universalmente a completa ni a
   top-$k$.
3. Outex constituye la comparación publicada más fuerte por identidad de
   protocolo, pero la ventaja de 0,0059 es puntual y estadísticamente incierta.
4. La próxima revisión debe mejorar tablas y jerarquía visual, no fabricar una
   afirmación de estado del arte ni volver a ejecutar experimentos sin una nueva
   pregunta.

### Estado de las objeciones del dictamen de 2026-08-07

| Bloque anterior | Estado actual | Evidencia |
|---|---|---|
| Sobreafirmación del resumen/conclusión | Cerrado | Resumen y conclusión distinguen mejora puntual, incertidumbre y dependencia del dataset. |
| Estadística incompleta | Cerrado | Dispersión, deltas, margen práctico, bootstrap, Holm y límites por dataset están en el cuerpo. |
| Comparación con publicaciones | Cerrado metodológicamente; mejorar presentación | Outex es directa; DTD/FMD/CUReT se declaran contexto parcial. |
| Literatura y reproducibilidad de extractores | Cerrado | Related Work ampliado y Tabla de extractores parametrizada. |
| Asimetría gris/RGB y contaminación | Cerrado como limitación | Ambas amenazas están declaradas sin inferencias causales. |
| Costo de extracción no medido | Cerrado como alcance | Se afirma ahorro dimensional/de ajuste, no latencia extremo a extremo. |
| URL pública del código | Pendiente para envío | La sección de disponibilidad todavía contiene un compromiso futuro. |

## Hoja de ruta autorizable

Prioridad 1: rediseñar las tablas principal, de contexto publicado, de
extractores y de frecuencia, conservando exactamente los valores trazados.  
Prioridad 2: recompilar y revisar visualmente todas las páginas con tablas;
eliminar cajas desbordadas, texto microscópico y advertencias tipográficas.  
Prioridad 3: antes de envío externo, fijar revista objetivo y archivar una
versión pública del código para ejecutar una revisión final con criterios
vinculantes.

