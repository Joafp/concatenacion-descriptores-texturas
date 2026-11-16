# Revisión simulada, ronda 1 — `carlos/main.tex`

Fecha: 2026-11-15. Versión revisada: la de accuracy con E1/E2 (22 páginas). Skill: `academic-paper-reviewer`, modo `full`. Los cinco revisores se ejecutaron en una sola sesión, sin subagentes. Todos comparten el mismo modelo, así que sus errores pueden estar correlacionados. Esta revisión no modifica el manuscrito; las correcciones se aplican después, en la ronda de revisión del texto.

## Fase 0 — Configuración del panel

- **Campo:** visión por computadora, clasificación de texturas. Campo secundario: inferencia condicional y costo de cómputo.
- **Tipo de trabajo:** empírico y comparativo, con protocolo anidado y pruebas no paramétricas entre datasets.
- **Revista de referencia:** *Pattern Recognition Letters* o *Expert Systems with Applications* (Elsevier CAS).
- **Madurez:** borrador avanzado, para presentar al tutor.

| Asiento | Identidad | Foco |
|---|---|---|
| EIC | Editor de una revista de reconocimiento de patrones | Encaje, aporte y legibilidad |
| R1, metodología | Especialista en comparación estadística de clasificadores (Demšar, García) | Diseño, pruebas, potencia y fugas |
| R2, dominio | Investigador en descriptores de textura y modelos fundacionales | Literatura, protocolos de datasets y terminología |
| R3, perspectiva | Ingeniero de sistemas de inferencia eficiente | Despliegue, costo real y utilidad práctica |
| DA | Abogado del diablo | Argumento central y posibles sesgos |

## Informes

### EIC

**Fortalezas:**
- E1 responde directamente al título: misma Top-4, mismas 27 condiciones y seis datasets.
- Protocolo anidado cuidadoso, pruebas exactas y trazabilidad excepcional.
- Las reservas están declaradas.

**Debilidades:**
- **E-1 (mayor):** el resumen tiene 285 palabras; Elsevier suele pedir como máximo 250. Además acumula demasiadas cifras para un primer contacto.
- **E-2 (mayor):** la conclusión central de E1 se formula solo como «no se detectan diferencias», pero los datos permiten una afirmación más fuerte y honesta. El paper ya define un margen de no inferioridad (0,01). Si se aplica a E1, la cota inferior de la diferencia es −0,0013. Hoy esa evidencia no aparece.
- **E-3 (menor):** la portada mezcla rótulos en inglés de la plantilla («ARTICLE INFO», «Keywords», «Abstract», «Page x of y», «Preprint submitted to Elsevier») con un texto en español.
- **E-4 (menor):** faltan las declaraciones que pide Elsevier: conflicto de intereses, financiamiento y uso de IA generativa en la redacción. La ética está como «pendiente».

**Recomendación:** revisión menor.

### R1 — Metodología

- **M-1 (mayor, igual a E-2):** falta un análisis de no inferioridad o de intervalo para la diferencia entre la cascada y Top-4 directo.
  - Por dataset, las diferencias son −0,0007, +0,0009, +0,0010, +0,0008, −0,0029 y +0,0018. La media es +0,0001 y la cota unilateral al 95 % es −0,0013.
  - Con δ = 0,01: p(t) < 0,0001; Wilcoxon exacto unilateral p = 0,0156.
  - **Propuesta:** informarlo con el mismo δ que se usa para Top-4 frente a Completa-22, declarado como análisis exploratorio posterior a observar E1.
- **M-2 (menor):** en E1 se informan medias, pero no la dispersión.
  - **Propuesta:** dar en el texto el IC 95 % de la diferencia media cascada − directo, que es [−0,0017; 0,0019].
- **M-3 (menor):** el cambio de métrica fue post hoc y está declarado, pero no se dice hacia dónde mueve los resultados. En la evaluación estática el cambio no favorece a Top-4: en macro-F1 era primera en el ranking y en accuracy queda segunda. En E1, macro-F1 da la misma conclusión (0,9368 frente a 0,9367).
  - **Propuesta:** decirlo explícitamente. Desactiva la sospecha de que se eligió la métrica por conveniencia.
- **M-4 (menor):** la entropía del softmax depende de la escala de las puntuaciones de la SVM, que no están calibradas. Ya figura en las limitaciones, pero en la Sección 3 conviene aclarar que se aplica sobre las puntuaciones crudas, sin temperatura.
- **M-5 (observación):** la unidad de análisis (medias por dataset) es correcta y está bien justificada. La pérdida de potencia está declarada.

### R2 — Dominio

- **D-1 (mayor):** la Sección 4.1 dice «protocolo de cuatro particiones usado por RADAM» sin citar RADAM. Debe citarse (Scabini et al., 2023, *Pattern Recognition*) o reformularse.
- **D-2 (menor):** «Outex» designa una familia de suites. Los datos (68 clases, 1.360 imágenes de 128×128, partición 680/680) corresponden a Outex_TC_00013, y conviene nombrar la suite.
- **D-3 (menor):** las compuertas de E2 tienen antecedentes directos que no se citan:
  - el puntaje máximo del softmax como detector de errores (Hendrycks y Gimpel, 2017);
  - la clasificación selectiva (Geifman y El-Yaniv, 2017);
  - las cascadas que delegan en un modelo mayor cuando el menor duda (Wang et al., 2018, *IDK cascades*; Park et al., 2015, *big/little*).
- **D-4 (menor):** «accuracy» es un anglicismo; en español técnico se usa «exactitud». Como la tesis usa «accuracy», se acepta, pero conviene definirlo una vez como «accuracy (exactitud)» y mantenerlo. Hoy ya es así.

### R3 — Perspectiva

- **P-1 (mayor):** no se explica qué es, en la práctica, la etapa barata. En 26 de las 27 condiciones es uno de los propios bloques de Top-4 (casi siempre SigLIP-B), así que la cascada equivale a «calcular un bloque de Top-4 y completar los otros tres solo si duda».
  - Esto vuelve el resultado más fácil de entender y de usar, y explica por qué el costo baja tanto: el bloque barato no se desperdicia.
  - **Propuesta:** decirlo en la Sección 4.7 y en la discusión.
- **P-2 (menor):** el ahorro se analiza imagen por imagen. Con inferencia por lotes, las imágenes escaladas forman lotes más chicos e irregulares, y el ahorro en *throughput* puede ser distinto.
  - **Propuesta:** agregar una frase en la discusión o en las limitaciones.
- **P-3 (menor):** «con una accuracy media similar» en el panel online oculta que con SVM la política por margen pierde 0,0027 en promedio y 0,016 en KTH-TIPS2-b.
  - **Propuesta:** dar las diferencias en el resumen o matizar «similar».

### DA — Abogado del diablo

**Argumento contrario más fuerte.** La activación por margen «conserva» la accuracy de Top-4 porque escala el 21 % de las imágenes con menor margen, y la etapa barata casi siempre es SigLIP-B, el mejor bloque individual y miembro de Top-4. El resultado podría leerse como «SigLIP-B ya resuelve casi todo y Top-4 corrige pocos casos». Visto así, el aporte sería la observación de que un solo modelo fundacional basta para la mayoría de las imágenes, y no la cascada. Además, las particiones de test se inspeccionaron antes de E1, la métrica se cambió después de ver los resultados y la tolerancia de 0,005 es post hoc.

**Adjudicación de ese argumento:** queda parcialmente refutado por los propios datos.
- La etapa barata sola obtiene 0,9234, 0,0210 por debajo de Top-4. No resuelve casi todo.
- Escalar al azar la misma cantidad de imágenes apenas sube a 0,9280. La ganancia viene de *qué* imágenes se escalan.
- La regla congelada eligió q = 0,25 en las 27 condiciones, sin señales de ajuste al test.
- El cambio de métrica no favoreció a Top-4 en la evaluación estática y no cambia la conclusión de E1.

Lo que sí es válido: el paper debe decir explícitamente que la etapa barata pertenece a Top-4 (P-1) y que el cambio de métrica no mueve las conclusiones (M-3).

**Problemas:**
- **DA-1 (mayor, igual a P-1 y M-3):** falta dar los dos datos que neutralizan la lectura escéptica.
- **DA-2 (menor):** el aspecto destacado «conserva su accuracy» solo queda respaldado si se agrega la no inferioridad (M-1). Con ella, la afirmación es defendible.
- **DA-3 (menor):** «en el panel… con una accuracy media similar» repite el problema de P-3.

No hay problemas CRÍTICOS.

## Fase 2 — Decisión editorial

**Decisión:** revisión menor. No hay problemas críticos.

Puntos de consenso:
- La conclusión central necesita la no inferioridad (E-2, M-1, DA-2).
- Falta explicar la etapa barata (P-1, DA-1).
- Falta la cita de RADAM (D-1).

## Hoja de ruta de la revisión

| ID | Prioridad | Cambio | Origen |
|---|---|---|---|
| R1 | Alta | Agregar la no inferioridad de la cascada frente a Top-4 directo (δ = 0,01) y el IC 95 % en la Sección 4.4 (método), en la 4.7, en la discusión y en la conclusión | E-2, M-1, M-2, DA-2 |
| R2 | Alta | Explicar que en 26/27 condiciones la etapa barata es un bloque de Top-4 | P-1, DA-1 |
| R3 | Alta | Citar RADAM o reformular | D-1 |
| R4 | Alta | Reducir el resumen a ≤ 250 palabras | E-1 |
| R5 | Media | Decir que el cambio de métrica no favorece a Top-4 ni cambia E1 | M-3, DA-1 |
| R6 | Media | Precisar «similar» en el panel con las diferencias | P-3, DA-3 |
| R7 | Media | Citar antecedentes de las compuertas (verificar las referencias antes de agregarlas) | D-3 |
| R8 | Media | Rótulos de la plantilla en español | E-3 |
| R9 | Media | Sección de declaraciones con lo que falta, marcado como pendiente de los autores | E-4 |
| R10 | Baja | Nombrar Outex_TC_00013 | D-2 |
| R11 | Baja | Aclarar que la entropía usa puntuaciones crudas | M-4 |
| R12 | Baja | Frase sobre inferencia por lotes | P-2 |
