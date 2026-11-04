# Mejora integral del manuscrito — 25 de octubre de 2026

## Alcance

Se atendió la autorización «bueno ahora mejora toda la tesis como vos digas que hace falta». Se conserva el enfoque, los tres interrogantes, la biblioteca, el panel y los resultados. La mejora actúa sobre argumentación, especificación matemática, correspondencia con el código, interpretación y presentación. No se ejecutan entrenamientos ni benchmarks nuevos ni se modifican predicciones experimentales.

Se utilizaron las orientaciones de ARS para revisión y escritura académica y la inspección visual de PDF. Se mantuvo el flujo local de revisión LaTeX con respaldo y parches acotados; no se fabricaron un pasaporte, una adjudicación exacta del autor, anclas formales o testigos de autorización del contrato ARS #670. **Este registro no certifica el flujo formal completo de ARS ni novedad, adecuación a una revista o cierre científico.** La revisión de los resúmenes existentes en español e inglés se hizo como edición local, no como ejecución del generador bilingüe formal de ARS.

Dos comprobaciones acotadas de subagentes, sin escritura, examinaron claridad del manuscrito y correspondencia de método con implementación. Comparten el contexto de este trabajo y no constituyen un panel independiente de pares ni verificación entre familias de modelos. La síntesis y los cambios fueron revisados por el agente principal.

Respaldo previo: [fuentes y PDF anteriores](../../paper/revision_mejora_integral_20261025_before.tar.gz). Se preservaron los cambios locales preexistentes. No se hizo commit, push ni paquete Overleaf.

## Cambios aplicados

| Superficie | Mejora |
| --- | --- |
| Resúmenes y palabras clave | Explican las dos decisiones de fusión, el costo compartido y el compromiso observado; mantienen el carácter de desarrollo y los pendientes |
| Introducción | Conecta selección de bloques, reducción de miembros y activación por imagen; formula el aporte de modo concreto sin afirmar prioridad universal |
| Antecedentes | Describe con precisión agregación multicapa frente a adquisición condicional y conecta las líneas futuras de los dos artículos de textura con la pregunta del estudio |
| Método | Explicita el objetivo restringido a políticas visitadas bajo presupuesto y deriva la condición algebraica de ahorro de adquisición frente a la misma unión permanente |
| Especificación contra código | Corrige cuatro ambigüedades: media de F1 por pliegue frente a F1 OOF reunido; umbral numérico conservado tras reajuste; prioridad de costo cero exclusiva del mérito marginal; votos repetidos frente a modelos únicos |
| Diseño | Define entrenamiento y validación productores y los pliegues internos; distingue las 680 predicciones de desarrollo de las puntuaciones que seleccionan la política |
| Resultados | Sustituye una lista parcial de ganadores por patrones contrastantes; distingue saldo de aciertos de macro-F1 y conserva los trece puntos y la excedencia |
| Discusión | Explica la dependencia del perfil de costos, el peso de Gabor en Completa y la dominancia descriptiva de B60 sobre B120 por relevancia; conserva las reservas causales y de generalización |
| Conclusiones | Resume lo aprendido sobre representación y adquisición, con límites explícitos, en lugar de presentar únicamente una lista de correcciones pendientes |
| Anexos y declaraciones | Añade tamaños de pliegue y multiplicidades; separa disponibilidad, verificación y consideraciones éticas; elimina comentarios propios de la conversación |
| Presentación | Ajusta ubicación de pseudocódigos y tabla de configuración, elimina remanentes de pocas líneas en páginas aisladas y añade metadatos al PDF |

No se cambia la denominación archivada de la política «relevancia»: se aclara que, en la poda, significa ganancia de F1 de la ruta y no la relevancia individual normalizada usada para sortear bloques. La condición algebraica de ahorro corresponde al modelo de adquisición, excluye latencia de clasificadores y no constituye una nueva medición física.

## Fuentes y comprobaciones

- Neshov et al., sección 5 de [Electronics 14, 4779](https://doi.org/10.3390/electronics14234779): agregación multicapa, limitaciones de cómputo y propuestas de compresión/fusión. Se distingue compuerta de fusión de compuerta de adquisición.
- Scabini et al., sección 6 de [Journal of Imaging 11, 304](https://doi.org/10.3390/jimaging11090304): 25 modelos, ocho tareas y direcciones sobre agregación y eficiencia. No se trasladan sus puntuaciones como controles propios.
- Se leyeron esas secciones en los PDF locales proporcionados; las páginas editoriales devolvieron HTTP 429. El preflight estructural opcional quedó UNAVAILABLE por ausencia de pypdf en la virtualenv, no PASS. Se usaron localizadores de sección visibles, no anclas de página no verificadas. No se hizo una nueva revisión sistemática de toda la bibliografía.
- La comparación de método se basó en los seis archivos de implementación ligados por hashes al metadata del híbrido, incluyendo selección y puntuaciones, y en sus tres registros de pliegue. Se corrigió el texto, no el algoritmo.
- El perfil asigna a Gabor 1.029,21 de 1.706,42 ms de Completa (60,3 %). Es una descomposición de constantes guardadas, no una medición nueva.

El [manifiesto de esta mejora](../../results/analysis/thesis_integral_20261025/manifest.json) registra hashes y comprobaciones. El [verificador complementario](../../scripts/check_thesis_integral_revision.py) comprueba las trece filas del híbrido, los tamaños y modelos únicos de tres pliegues, las diferencias de calidad/costo comunicadas y 60 casos algebraicos de la condición de ahorro. El [verificador estructural](../../scripts/check_thesis_revision.py) comprueba las 120 celdas principales, las dependencias, la compilación y la preservación de 59 entradas archivadas, además de once entradas y cuatro salidas de presentación.

El PDF final tiene 54 páginas. La compilación final no presenta errores, advertencias de referencias ni cajas overfull/underfull. Se inspecciona la distribución global de páginas y se revisan en detalle fórmulas, procedimiento OOF, pseudocódigos, diagrama, curvas y tablas afectadas. La verificación de software se registra aparte de cualquier afirmación sobre generalización predictiva.

## Estado científico que permanece abierto

El paso decisivo sigue siendo comparar exactamente el mismo rescate podado permanente y condicional. Después corresponden réplicas, Top-k/GFS comparables, reconciliación KTH, diagnóstico de fidelidad CUReT/Soil y medición física del híbrido. La formulación más precisa y la mejora de escritura no sustituyen esas comprobaciones. No se inventó la distribución individual de contribuciones, todavía no informada por los autores.
