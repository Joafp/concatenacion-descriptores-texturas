# Capítulo 6 — Conclusión

## 6.1. Conclusión principal

La presente tesis evaluó sistemáticamente si la **concatenación de múltiples descriptores visuales** mejora la clasificación de texturas más allá del mejor descriptor individual, y bajo qué condiciones. El diseño experimental comprende **6 datasets, 17 extractores base —ampliados a 20 en el estudio SOTA—, 4 clasificadores y aproximadamente 1200 corridas controladas**. Los resultados permiten las siguientes conclusiones:

1. **La concatenación aporta valor cuando se controla qué representaciones se combinan.** GFS mejora o iguala al mejor descriptor individual en 5/6 datasets y evita la redundancia introducida por la concatenación completa.

2. **La complementariedad es específica del problema.** Los subconjuntos óptimos cambian entre datasets y clasificadores y combinan representaciones de distintas familias. La selección conjunta de DINOv2-base y DINOv2-large en 9/24 casos constituye una evidencia particular, no una regla universal.

3. **La estrategia de selección es determinante:**
   - GFS gana en 5/6 datasets, con k=2-5 extractores (84% reducción en dim vs prefix)
   - GFS es **significativamente** superior al mejor individual en 6/24 casos (DTD svm/resmlp, CUReT svm/knn, VisTex svm) con Holm-Bonferroni
   - GFS elimina el "concat hurts" del prefix concat en VisTex knn (+0.100 F1, p<0.005)

4. **ResMLP es competitivo con SVM lineal** (promedio 0.902 vs 0.863). ResMLP sobresale en datasets pequeños (VisTex); SVM en datasets grandes y discriminantes (DTD, FMD).

5. **La diversidad entre familias importa más que la acumulación de modelos.** El primer descriptor profundo causa el mayor salto (+0.41 a +0.51 F1), mientras que los componentes posteriores producen mejoras incrementales y dependientes del dataset.

## 6.2. Contribuciones originales de esta tesis

1. **Benchmark sistemático de estrategias de combinación**: 17 extractores base, ampliados a 20 en el estudio SOTA, evaluados sobre 6 datasets y 4 clasificadores mediante un protocolo común.

2. **GFS como metodología reproducible de selección**: identifica subconjuntos compactos de 2-5 extractores que superan al prefix concat con orden canónico. La reducción de 84% en la cantidad de componentes mejora el balance entre desempeño y costo.

3. **Demostración de que la concatenación indiscriminada no es óptima**: los resultados separan claramente el efecto de agregar representaciones del efecto de seleccionar representaciones complementarias.

4. **Caracterización empírica de la complementariedad**: se identifica qué familias y descriptores se combinan bajo distintos datasets y clasificadores, incluyendo casos de complementariedad entre modelos arquitectónicamente próximos.

5. **Documentación rigurosa de "fracasos" informativos**:
   - Prefix concat sub-óptimo en VisTex knn (FIX con GFS)
   - LoRA sub-óptimo en VisTex (V1)
   - GFS con screening 1-fold da resultados casi idénticos al exhaustivo (acelera 2.5×)
   - ResMLP supera a SVM en data-scarce, no en data-rich

6. **Validación estadística rigurosa**: paired t-test + Holm-Bonferroni en 6,936 comparaciones de Exp 3a y 48 comparaciones de GFS vs Prefix/individual.

## 6.3. Respondiendo las hipótesis originales

**H1 (DTD): "La concatenación de clásicos + deep mejora F1 en ≥2 puntos sobre el mejor individual."**
✅ **Confirmada con GFS.** GFS subset (k=4, 3858d) alcanza F1=0.868 vs best individual 0.842 (Δ=+0.026, significativo Holm p=0.0006).

**H2 (FMD): "El primer deep causa el mayor salto, deep adicionales aportan mejoras marginales."**
✅ **Confirmada con prefix concat.** Salto de +0.51 al primer deep, luego <+0.05 por deep adicional. Con GFS, el subset óptimo es aún más compacto (k=2-3).

**H3 (VisTex, data-scarce): "Concatenación clásico+deep competitiva con fine-tuning en datasets pequeños."**
✅ **Confirmada con GFS.** GFS concat (F1=0.902 svm) supera a Last-block fine-tuning (F1=0.811 V1). En ResMLP, GFS=0.924 vs best indiv=0.882.

**H4 (Selección): "GFS supera a prefix concat con orden canónico fijo."**
✅ **Confirmada.** GFS gana en 16/24 casos (67%), con subsets más compactos (k=2-5 vs 17) y F1 igual o mejor. Significativos: 2/24 (DTD knn, VisTex knn).

**H5 (diversidad representacional): "Los subconjuntos seleccionados combinan información complementaria y no solamente los mejores descriptores individuales."**
✅ **Respaldada.** GFS selecciona composiciones diferentes según el dataset y el clasificador; los descriptores auto-supervisados aparecen con frecuencia, pero el beneficio final depende de su interacción con otras representaciones.

**H0 (nula): "La concatenación no aporta mejora significativa sobre el mejor extractor individual."**
❌ **Rechazada.** Mejoras significativas en 6/24 casos (GFS vs best individual con Holm p<0.05), y el delta promedio de +0.026 F1 es consistente con la dirección esperada.

## 6.4. Mensaje final

> La pregunta central de esta tesis —"¿vale la pena combinar múltiples descriptores visuales para clasificar texturas?"— tiene una respuesta positiva, pero condicionada por la estrategia de combinación. La concatenación completa puede añadir redundancia e incluso reducir el desempeño; en cambio, **Greedy Forward Selection identifica subconjuntos compactos de representaciones complementarias que mejoran o igualan al mejor descriptor individual y al prefix concat**. El resultado central no es la superioridad universal de una arquitectura, sino que **la diversidad de representación, la selección del subconjunto y el clasificador deben considerarse conjuntamente**. Esta perspectiva desplaza el problema desde la búsqueda de un descriptor único hacia el diseño de combinaciones eficientes y adaptadas al dominio.

## 6.5. Limitaciones del trabajo

1. **Sesgo optimista en GFS** por falta de nested cross-validation. Esperaríamos un drop de ~1-2% F1 con nested CV. **Parcialmente mitigado** por la comparación con subsets aleatorios (Cap. 5.12.3, GFS > random en 24/24) y la validación held-out (Cap. 5.12.4, F1 held-out ~0.87 similar al training).
2. **Datasets limitados a texturas públicas** — sin validación en texturas industriales, médicas, o naturales no-Web.
3. **Sin validación externa** — todos los resultados son in-distribution.
4. **Hiperparámetros fijos** del clasificador (no grid search exhaustivo).
5. **No probamos CLIP, MAE, EVA-02, SigLIP, BEiT-3** — extensiones naturales para trabajo futuro.
6. **GFS con screening 1-fold** puede perder candidatos en casos raros (validado: diferencia < 0.002 F1).
7. **max_k=8 en GFS** — no exhaustivo pero suficiente en este trabajo.
8. **Outex13 con 68 clases y 20 imgs/clase** es límite para 5-fold CV estable.
9. **"Complementariedad" DINOv2-B + L es contextualmente verdadera** (DTD, FMD) pero no universal (Outex13, CUReT, Soil, VisTex). En datasets saturados o data-scarce, un solo DINOv2-large es suficiente.

## 6.6. Líneas de trabajo futuro (priorizadas)

### 6.6.1. Corto plazo (próximos meses) — **prioridad ALTA**

1. **Nested CV para GFS** (outer 5-fold para evaluar, inner 5-fold para buscar) — resolver el optimism bias definitivamente.
2. **Validación de GFS con screening exhaustivo** (1-fold + verify top-3 vs exhaustive) — confirmar el ahorro de 2.5× sin pérdida.
3. **Comparación con EVA-02, MAE, SigLIP, BEiT-3** — los SOTA 2023-2026 en visión que no se probaron en esta tesis.
4. **Validación en texturas no-Web** (Flickr Material original, ALOT, Brodatz) — verificar generalización a texturas no capturadas en wild.

### 6.6.2. Mediano plazo (próximo año)

5. **GFS con DINOv2 fine-tuned** como extractor base — ¿mejora el subset óptimo?
6. **Validación en texturas industriales** (metalurgia, textiles, maderas) y médicas (histopatología, radiómica).
7. **Probar con más datasets outdoor** (AID, NWPU-RESISC45) para confirmar la hipótesis de domain shift en texturas.
8. **Análisis teórico de la complementariedad** DINOv2-B + L — ¿qué información captura cada uno? (t-SNE, attention maps).

### 6.6.3. Largo plazo (research agenda)

9. **Aprendizaje de la selección de extractores** (learned GFS) en lugar de búsqueda greedy.
10. **Combinación con vision-language models** (CLIP + GPT-4V para texturas con descripción textual).
11. **Extensión a texturas temporales** (videos) — los 17 extractores actuales son para imágenes estáticas.

### 6.6.4. Priorización para publication

- **Items 1-3** son **bloqueantes** para submission a un journal Q1 como *Pattern Recognition* o *Information Fusion*.
- **Items 4-8** son **importantes** pero pueden ir como "future work" si los items 1-3 se completan.
- **Items 9-11** son **largo plazo** y no afectan la decisión de publicación.

### 6.6.1. Corto plazo (próximos meses)

1. **Nested CV para GFS** (outer 5-fold para evaluar, inner 5-fold para buscar) — resolver el optimism bias
2. **CLIP como baseline SSL adicional** (no fue probado en esta tesis)
3. **MAE y EVA-02** como extensiones SSL
4. **Validación en datasets no-Web** (Flickr Material original, ALOT, Brodatz) para verificar generalización

### 6.6.2. Mediano plazo (próximo año)

5. **GFS con DINOv2 fine-tuned** como extractor base — ¿mejora el subset óptimo?
6. **Validación en texturas industriales** (metalurgia, textiles, maderas)
7. **Validación en texturas médicas** (histopatología, radiómica)
8. **Probar con más datasets outdoor** (AID, NWPU-RESISC45) para confirmar la hipótesis de domain shift
9. **GFS con screening más sofisticado** (top-5 verify en lugar de top-3) para reducir el riesgo de perder el mejor candidato

### 6.6.3. Largo plazo (research agenda)

10. **Aprendizaje de la selección de extractores** (learned GFS) en lugar de búsqueda greedy
11. **Combinación con vision-language models** (CLIP + GPT-4V para texturas con descripción textual)
12. **Extensión a texturas temporales** (videos) — los 17 extractores actuales son para imágenes estáticas
13. **Análisis teórico de la complementariedad DINOv2-B + DINOv2-L** — ¿qué información captura cada uno?

## 6.7. Cierre

Esta tesis comenzó con la pregunta de qué descriptor conviene para clasificar texturas y mostró que una formulación más útil es determinar **qué representaciones deben combinarse para una tarea específica**. El benchmark de 17 extractores base, ampliado a 20 en el estudio SOTA, aporta evidencia de que GFS selecciona subconjuntos de 2-5 componentes cuyo desempeño depende del dataset y del clasificador. La contribución final es una metodología empírica para estudiar y aprovechar esa complementariedad.

Confiamos en que los resultados, el código, y los embeddings cacheados permitirán a la comunidad:
- Reproducir todos los experimentos
- Construir sobre estos hallazgos con nuevos extractores
- Aplicar la metodología a otros dominios (médico, industrial, remoto)

La clasificación de texturas, un campo con más de cinco décadas de investigación, sigue evolucionando. Esta tesis contribuye un **mapa actualizado del estado del arte** y una **metodología reproducible** para continuar avanzando.
