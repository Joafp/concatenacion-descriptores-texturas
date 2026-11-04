# Revisión editorial aplicada — 25-10-2026

## Alcance y autorización

Se aplicó la reorganización propuesta en la auditoría editorial, autorizada por el autor con «dale hace todo eso ahora». Se siguieron las orientaciones de ARS para estructura, argumentación, revisión y delimitación de afirmaciones, y la revisión visual de PDF. Este es un registro local de revisión estructural de LaTeX: **no es una certificación formal completa de ARS, una revisión por pares independiente ni una declaración de manuscrito listo para envío**. No se produjo la cadena formal de autorizaciones y testigos de parches de ese flujo. Tampoco se verificó semánticamente toda la bibliografía previa.

El respaldo previo a esta reestructuración, incluido el PDF anterior, está en [revision_editorial_20261025_before.tar.gz](../../paper/revision_editorial_20261025_before.tar.gz). Se conservaron los cambios preexistentes del repositorio. No se realizaron nuevos entrenamientos, mediciones GPU, commit, push ni ZIP de Overleaf.

## Organización aplicada

| Capítulo actual | Función |
| --- | --- |
| 1. Introducción | Problema, objetivo, tres preguntas, alcance y contribución candidata |
| 2. Antecedentes | Fusión, selección, ensambles y adquisición con presupuesto; comparación conceptual sin declarar prioridad universal |
| 3. Método | Bloques, CKA, sorteo, agregación, base, compuerta, costo compartido y poda; dos pseudocódigos y un diagrama |
| 4. Diseño experimental | Datos, protocolos, clasificadores, controles, agregaciones, medición y contrastes |
| 5. Resultados | Preguntas P1/P2/P3; benchmark, cascada histórica y piloto híbrido separados |
| 6. Discusión | Interpretación, mecanismos alternativos y amenazas a la validez |
| 7. Conclusiones | Respuestas limitadas por la evidencia y comprobaciones aún necesarias |

Los antiguos capítulos 4/5/6 se trasladaron a 5/6/7; no se mantienen versiones paralelas activas. Los anexos reúnen especificaciones de extracción y GFS, perfil de costos, procedencia, resultados adicionales, dispersión y reproducibilidad. Las declaraciones se presentan aparte. Se eliminó la portada duplicada y se añadieron notación e índices de figuras/tablas.

Título vigente: **Fusión costo-consciente de descriptores de textura mediante ensambles y adquisición condicional**. La escritura deja de ser una cronología del proyecto, sin ocultar las reservas metodológicas.

## Evidencia conservada y figuras nuevas

- Se mantienen 22 bloques, 20.652 dimensiones y los seis datasets principales. VisTex no se incorporó.
- Las 470 filas estáticas, las 27 predicciones históricas y los trece resultados del barrido híbrido no se sustituyen por estimaciones nuevas.
- El híbrido continúa siendo desarrollo OOF sobre las 680 imágenes del entrenamiento oficial de Outex, semilla 42; no se le atribuyen los seis datasets ni el test oficial.
- Se conservaron resultados desfavorables, la excedencia de presupuesto y las diferencias entre selección por relevancia y marginal.
- La curva calidad–costo, seis controles, perfil de costos y tabla separada de desviaciones se construyeron desde archivos existentes con [el generador](../../scripts/build_editorial_thesis_artifacts.py). [Su procedencia](../../paper/generated_editorial/provenance.json) registra hashes de once entradas y cuatro salidas. No ejecuta modelos.
- Las tablas principales siguen mostrando medias sin formato mixto de ±. La dispersión se informa separadamente en un anexo y no como intervalo de confianza.
- Las cifras físicas históricas no se usan para afirmar que el híbrido ahorra 85,40 % de latencia real. Esa cifra corresponde exclusivamente al modelo de costos del piloto.
- No se reutilizan los p-valores del benchmark como evidencia del híbrido ni se interpreta no significancia como equivalencia.

## Referencias primarias añadidas o corregidas

| Referencia | Verificación y uso limitado |
| --- | --- |
| Kornblith et al., 2019 | [PMLR](https://proceedings.mlr.press/v97/kornblith19a.html): metadatos y fundamento de CKA; no prueba de complementariedad de errores |
| Caruana et al., 2004 | [Artículo de los autores](https://www.cs.cornell.edu/~alexn/papers/shotgun.icml04.revised.rev2.pdf), secciones 1 y 2.1: selección de ensambles y selección con reemplazo; no prioridad de nuestra combinación |
| Xu et al., 2012 | [ICML](https://icml.cc/2012/papers/592.pdf), resumen e introducción: aprendizaje con costo de extracción, no el mismo algoritmo implementado |
| Nan y Saligrama, 2017 | [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2017/hash/d9ff90f4000eacd3a6c9cb27f78994cf-Abstract.html): clasificador adaptativo bajo presupuesto, antecedente de compuerta/predictor |
| Ma et al., 2019, EDDI | Se corrigió el enlace a [ma19c](https://proceedings.mlr.press/v97/ma19c.html), pues ma19a correspondía a otro artículo. Se corrigió también la última autora a Cheng Zhang |

Son comprobaciones puntuales, no una revisión sistemática exhaustiva ni certificación de novedad frente a toda la literatura.

## Declaraciones

El autor confirmó ausencia de financiación externa y de conflictos de interés. Se incorporaron esas declaraciones. La distribución individual de contribuciones entre Carlos y Joaquín no fue proporcionada: no se inventó una asignación CRediT. Se informa la asistencia de IA utilizada en esta revisión, sin presentarla como fuente científica.

## Verificación de esta entrega

- PDF: 54 páginas; compilación con BibTeX y pasadas sucesivas de pdfLaTeX, sin citas/referencias indefinidas, advertencias ni cajas desbordadas o subllenas en el log final.
- Pruebas: 80 aprobadas en 34,85 s, ejecutadas con PYTHONPATH=.:src y la virtualenv confirmatory. No son una reproducción independiente de entrenamiento.
- Revisión visual de portada, diagrama, comparación de antecedentes, cobertura experimental, curva y barrido completo, y tablas del anexo de variabilidad. No equivale a certificación de cada afirmación científica.
- El [verificador](../../scripts/check_thesis_revision.py) recorre dependencias activas, verifica 120 celdas principales frente al resumen estático recalculado, hashes del material generado y preservación de entradas archivadas. Su salida nueva se conserva en [el manifiesto editorial](../../results/analysis/editorial_revision_20261025/manifest.json); no reemplaza el manifiesto de la revisión anterior.

## Pendientes que esta revisión no resuelve

La prioridad científica sigue siendo comparar el mismo rescate podado siempre activo frente a la versión con compuerta. Después corresponden controles GFS/Top-k comparables, réplicas, reconciliación KTH y fidelidad CUReT/Soil, y medición física del híbrido. Véase [el plan vigente](PLAN_CIERRE_VIGENTE_2026-10-25.md). Mejorar la escritura no convierte estas tareas en resultados alcanzados.
