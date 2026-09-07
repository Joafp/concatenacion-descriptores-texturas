# Benchmark narrativo de diez papers de clasificación de texturas

Fecha: 2026-08-15  
Objeto evaluado: *Selección y concatenación de descriptores heterogéneos para
la clasificación de texturas*.  
Método: ARS `deep-research`, comparación WHY--HOW--WHAT y lectura estructural
de introducción, organización, figuras/tablas, discusión y conclusión. No se
utilizó una lista de títulos como sustituto de lectura: se descargaron y
extrajeron los diez textos completos.

## Pregunta de la revisión

¿El manuscrito cuenta una historia científica con la concentración, progresión
y jerarquía visual de trabajos profesionales del área, o se limita a documentar
correctamente una colección de experimentos?

## Corpus

| # | Trabajo | Tipo de historia dominante | Recurso narrativo principal |
|---:|---|---|---|
| 1 | Paiva Pavón et al. (2023), *RGB Pixel N-grams* | Un descriptor nuevo extiende Pixel N-grams de gris a color | El método se convierte en una secuencia operativa; resultados y pruebas estadísticas sostienen competitividad |
| 2 | Cimpoi et al. (2014), *Describing Textures in the Wild* | Falta lenguaje semántico y datos realistas para describir texturas | Ejemplos visuales abren el paper; dataset, representación y transferencia forman una sola historia |
| 3 | Cimpoi et al. (2015), *Deep Filter Banks* | Las texturas reales aparecen en regiones y desorden; las capas FC no son la representación adecuada | Figura inicial de reconocimiento en clutter; una tabla central compara variantes y dominios |
| 4 | Lin et al. (2015), *Bilinear CNN Models* | Las interacciones locales de dos extractores pueden modelarse con una arquitectura simple | Figura 1 define toda la arquitectura; experimentos y visualizaciones explican por qué funciona |
| 5 | Gao et al. (2016), *Compact Bilinear Pooling* | Bilinear pooling funciona, pero su dimensión impide usarlo ampliamente | La tensión dimensión--desempeño aparece en la primera página y gobierna teoría, tablas y conclusión |
| 6 | Zhang et al. (2017), *Deep TEN* | Los pipelines de textura están fragmentados; deben aprenderse de extremo a extremo | Figura 1 contrapone BoW, FV-CNN y Deep-TEN antes de entrar en ecuaciones |
| 7 | Song et al. (2015), *Fusing Subcategory Probabilities* | Variación intraclase y similitud interclase limitan el clasificador plano | Figura 1 presenta entrenamiento y prueba; ablaciones, confusiones y casos corregidos validan el mecanismo |
| 8 | Liu et al. (2019), *From BoW to CNN* | El campo necesita una taxonomía que explique dos décadas de representación | Taxonomía histórica, tablas de benchmarks y discusión de problemas abiertos |
| 9 | Varma y Zisserman (2005), *A Statistical Approach to Texture Classification* | La clasificación debe resistir cambios de vista e iluminación desde una sola imagen | Tres diagramas consecutivos separan aprendizaje del diccionario, modelo y clasificación |
| 10 | Bell et al. (2015), *Material Recognition in the Wild / MINC* | Los datasets pequeños y fuera de contexto limitan el reconocimiento de materiales reales | Figura 1 resume construcción y uso; curvas de escala, ejemplos y transferencia justifican el dataset |

## Cómo cuentan la historia los trabajos más eficaces

### 1. Comienzan con una tensión, no con una cronología

Los artículos más claros tardan poco en establecer una oposición concreta:
representaciones potentes pero demasiado grandes; componentes aislados frente a
aprendizaje conjunto; clasificación plana frente a variación intraclase; datos
controlados frente a materiales reales. La literatura aparece para construir esa
tensión, no para enumerar generaciones de métodos.

RGB Pixel N-grams es menos concentrado que los papers de CVPR/ICCV: dedica más
espacio a definiciones generales y familias de descriptores. Aun así, conserva
una transición inequívoca: Pixel N-grams solo trabaja en gris, el color contiene
información útil y el paper propone dos variantes RGB.

### 2. La Figura 1 funciona como una promesa verificable

En Deep-TEN, Compact Bilinear, Bilinear CNN, Fusing Subcategory Probabilities y
MINC, la primera figura no intenta documentar cada detalle. Expone la diferencia
que el lector debe recordar: pipeline fragmentado frente a integrado,
representación completa frente a compacta, o flujo de datos de entrenamiento y
prueba. Las figuras posteriores explican el mecanismo, las ablaciones o los
errores.

### 3. Los experimentos siguen preguntas, no inventarios

Los mejores artículos organizan los resultados como una secuencia de pruebas:

1. ¿funciona el método completo?;
2. ¿qué componente produce la mejora?;
3. ¿qué costo o limitación introduce?;
4. ¿se mantiene en otro dataset, régimen o tarea?;
5. ¿qué errores corrige y cuáles conserva?

Song et al. es particularmente claro: presenta el resultado global, analiza
componentes, compara formas de generar subcategorías y muestra ejemplos que el
nuevo modelo corrige. Gao et al. hace que dimensión, memoria y desempeño vuelvan
en varias tablas hasta sostener la conclusión de compresión. Bell et al. conecta
tamaño del dataset, escala del parche, transferencia y segmentación.

### 4. Las conclusiones recuperan una sola frase central

Las conclusiones profesionales suelen ser breves. Repiten el problema y la
solución en lenguaje directo, seleccionan uno o dos resultados memorables y
derivan trabajo futuro de una limitación observada. No reproducen toda la tabla
de resultados. El artículo de RGB Pixel N-grams es más extenso y enfático; los
papers de conferencia más concentrados cierran en uno o dos párrafos.

## Comparación con nuestro manuscrito

### Lo que ya está al nivel profesional

1. **La pregunta experimental es real.** El paper no concatena bloques y luego
   busca una explicación retrospectiva: separa individual, completa, GFS,
   familia homogénea, top-$k$ y subconjuntos aleatorios.
2. **El protocolo sostiene la historia.** La separación entre selección interna
   y test externo es más explícita que en varios trabajos del corpus.
3. **Los resultados negativos se conservan.** Outex favorece la concatenación
   completa; top-$k$ empata globalmente a GFS; los clásicos no aparecen entre los
   bloques más recurrentes. Esto da credibilidad y evita una narrativa
   promocional.
4. **La evidencia visual cumple funciones distintas.** La figura del pipeline
   explica el sistema, la de GFS la búsqueda, la del protocolo la independencia
   del test y la de Pareto el compromiso dimensión--desempeño.
5. **Las tablas centrales ya tienen jerarquía.** Desempeño, efecto/presupuesto y
   comparación publicada están separados. La comparación directa de Outex ya no
   se confunde con el contexto no homólogo.
6. **La conclusión actual es profesional.** Después de eliminar las etiquetas
   visibles de plantilla, progresa naturalmente de problema a evidencia y a
   trabajo futuro.

### Lo que todavía impide que la historia sea sobresaliente

#### A. Compiten dos centros narrativos

La primera historia pregunta cuándo seleccionar o concatenar 20 descriptores. La
segunda continúa RGB Pixel N-grams sobre Outex. Ambas son válidas, pero el
resumen y la introducción conceden suficiente espacio a cada una como para que
el lector dude cuál es la contribución principal.

El orden lógico más fuerte es:

> **Historia principal:** una biblioteca amplia no garantiza que concatenar todo
> sea mejor; se necesita decidir qué bloques conservar sin consultar el test.
> **Caso de continuidad:** Outex + RGB Pixel N-grams proporciona una comparación
> directa y reproducible que prueba esa decisión sobre el antecedente local.

La continuación de n-gramas debe funcionar como la evidencia externa más fuerte,
no como un segundo método coprotagonista.

#### B. La introducción revela demasiados resultados antes de cerrar el vacío

La introducción actual es rigurosa, pero incluye diseño, resultados por patrón,
Outex y una interpretación casi completa. En los mejores trabajos, la
introducción formula la tensión, explica por qué los comparadores existentes no
la resuelven y entrega una vista compacta de método/contribuciones. Los matices
de top-$k$, selección completa y significación de Outex se desarrollan después.

#### C. La primera figura documenta más de lo que argumenta

La Figura 1 actual es técnicamente clara, pero su mensaje principal es “así
circulan los datos”. Deep-TEN y Compact Bilinear usan la primera figura para
mostrar “qué cambia respecto de lo anterior”. Para elevar la historia, la figura
principal debería hacer visible el contraste que gobierna el paper:

`un descriptor` vs. `todos los bloques` vs. `subconjunto seleccionado`, con el
test aislado y el resultado/costo de cada ruta. El detalle de extracción puede
permanecer en una segunda figura.

#### D. El paper es más exhaustivo que selectivo

La exhaustividad es apropiada para una tesis y para revisión con el profesor,
pero un artículo competitivo necesita distinguir con mayor dureza entre
evidencia principal y evidencia de auditoría. Conteos de ejecuciones, hashes,
determinismo, tiempos y reglas específicas son valiosos; no todos necesitan el
mismo peso narrativo en el cuerpo. Parte de esa información puede migrar a un
apéndice de reproducibilidad sin desaparecer.

#### E. Falta una frase de resultado que el lector pueda repetir

El manuscrito posee un hallazgo memorable, pero todavía lo expresa en varias
frases. La síntesis empírica que mejor sobrevive al corpus es:

> La concatenación eleva el rendimiento, pero la mayor parte de la ganancia se
> recupera reuniendo pocos bloques individualmente fuertes; GFS aporta compresión
> y ventajas dependientes del dominio, no dominancia universal.

Esta frase debe gobernar resumen, final de introducción, lectura de la tabla
principal, discusión y conclusión, con la debida cautela estadística.

## Evaluación editorial

| Dimensión | Estado | Juicio |
|---|---|---|
| Problema y relevancia | Profesional | La pregunta es pertinente y está mejor delimitada que una comparación de backbones |
| Rigor experimental | Fuerte | Es el activo principal del paper |
| Originalidad metodológica | Moderada | GFS y concatenación no son nuevos; la novedad reside en el diseño comparativo, escala y control de explicaciones alternativas |
| Narrativa | Buena, no sobresaliente | Dos centros narrativos reducen concentración |
| Figuras | Profesionales | Claras, aunque la Figura 1 podría argumentar mejor la diferencia central |
| Tablas | Profesionales | La jerarquía actual supera la versión previa y evita falsa comparabilidad |
| Discusión | Fuerte | Reconoce top-$k$, asimetría RGB/gris, dependencia del dominio y preentrenamiento |
| Conclusión | Profesional | Natural, prudente y conectada con las limitaciones |
| Preparación para revista | Minor/Major según destino | Científicamente defendible; requiere concentración narrativa y URL archivada, además de adaptación a la revista elegida |

## Veredicto

**No es “un paper más del montón” en rigor experimental, pero todavía puede
parecerlo en posicionamiento.** Su diferencia no es proponer un descriptor o una
arquitectura nueva; es demostrar, con controles que la literatura suele omitir,
qué parte de la mejora de concatenar proviene de selección, dimensionalidad y
fortaleza individual. Esa contribución es menos vistosa que una red nueva, pero
es científicamente valiosa y defendible.

El manuscrito actual se encuentra por encima de un borrador académico promedio:
la evidencia está trazada, las limitaciones son honestas y los comparadores
responden explicaciones alternativas. Para acercarse al nivel narrativo de los
mejores trabajos del corpus debe hacer una última edición de concentración, no
añadir más resultados indiscriminadamente.

## Revisión recomendada, en orden

1. Declarar una sola historia principal y subordinar la continuidad con RGB
   Pixel N-grams como caso directo de validación.
2. Reducir la anticipación de resultados en la introducción y terminarla con una
   frase central estable.
3. Revisar la Figura 1 para que compare las tres decisiones representacionales,
   no solo documente el flujo de una imagen.
4. Trasladar detalles de auditoría secundaria a un apéndice de reproducibilidad,
   manteniendo en el cuerpo las garantías necesarias contra fuga.
5. Conservar el tono prudente de la comparación Outex: mejora puntual, no
   superioridad estadística.
6. Fijar revista objetivo y URL archivada antes de la revisión final de envío.

## Estado de implementación (16 de agosto de 2026)

Se completaron las recomendaciones 1--5 en el manuscrito: el argumento principal quedó centrado en la selección y concatenación de bloques; RGB Pixel N-grams se presenta como validación directa; la introducción fue concentrada; la Figura 1 compara las tres decisiones representacionales; y la trazabilidad detallada se trasladó a un apéndice. La recomendación 6 permanece deliberadamente abierta porque requiere una decisión de los autores antes del envío, no una modificación editorial autónoma.

## Fuentes primarias

- Paiva Pavón et al. (2023), *RGB Pixel N-grams: A texture descriptor*, DOI
  `10.1016/j.image.2023.117028`.
- Cimpoi et al. (2014), *Describing Textures in the Wild*, CVPR Open Access.
- Cimpoi et al. (2015), *Deep Filter Banks for Texture Recognition and
  Segmentation*, CVPR Open Access.
- Lin et al. (2015), *Bilinear CNN Models for Fine-Grained Visual Recognition*,
  ICCV Open Access.
- Gao et al. (2016), *Compact Bilinear Pooling*, CVPR Open Access.
- Zhang et al. (2017), *Deep TEN: Texture Encoding Network*, CVPR Open Access.
- Song et al. (2015), *Fusing Subcategory Probabilities for Texture
  Classification*, CVPR Open Access.
- Liu et al. (2019), *From BoW to CNN: Two Decades of Texture Representation
  for Texture Classification*, DOI `10.1007/s11263-018-1125-z`.
- Varma y Zisserman (2005), *A Statistical Approach to Texture Classification
  from Single Images*, DOI `10.1007/s11263-005-4635-4`.
- Bell et al. (2015), *Material Recognition in the Wild with the Materials in
  Context Database*, CVPR Open Access.
