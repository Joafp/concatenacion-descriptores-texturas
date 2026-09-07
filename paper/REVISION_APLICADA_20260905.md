# Cambios aplicados al paper y la tesis

Se aplicó la retroalimentación del usuario y el plan `PLAN_REVISION_ARS_2026-09-04.md`. Esta es una revisión editorial y de coherencia basada en evidencia local, no una certificación ARS de envío ni una auditoría integral de todas las referencias. El autor pidió expresamente modificar el manuscrito; se aplicaron parches LaTeX y se preservó una copia previa, sin crear el paquete formal de autorización y evaluación de la suite.

## Archivos actuales y respaldo

- Paper: `paper/articulo/borrador_profesor/main.tex` y `main.pdf`.
- Tesis: `paper/tesis.tex`, `paper/tesis.pdf` y los seis capítulos de `paper/chapters/`.
- Respaldo previo: `paper/revision_20260905_antes/` contiene el main.tex/PDF previo, la raíz de tesis y sus capítulos originales. Los experimentos históricos y sus resultados permanecen disponibles.

La tesis se armonizó con el estudio anidado actual. Los capítulos anteriores describían otro alcance (17 descriptores base, seis datasets, cuatro clasificadores y contrastes sobre folds) y afirmaban conclusiones que no se podían transferir al análisis actual. Sus versiones originales están preservadas en el respaldo; la versión compilada utiliza la evidencia vigente del paper.

## Respuesta a los cambios solicitados

| Comentario | Implementación |
|---|---|
| Figura de concatenación | Nueva figura con imagen DTD, cinco ramas, transformaciones esquemáticas, bloques normalizados y rutas individual/concatenada. Fuente y PNG/PDF: `figures/concatenacion_v02.*`. |
| Citas con números | Natbib numérico y bibliografía unsrtnat en ambos documentos; recompilación con BibTeX. |
| Mejor descriptor en tabla principal | Panel B de la tabla de macro-F1 con identidad y frecuencia de selección interna. |
| Estadística como RGB Pixel N-grams | Rankings Friedman/Quade, contraste global y matriz triangular con diez valores p ajustados mediante Holm. |
| N-gramas general | Método multibase con hashing y SVD; tabla completa de ResMLP en DTD, FMD, CUReT y Outex. |
| Tabla de p-value | Matriz Holm procedente de los LaTeX Java originales, con valores mayores que 1 acotados para presentación. |
| Gráfico de folds | Retirado; protocolo explicado en texto. |
| Métodos uniformes | Individual, Completa, Top-k, GFS y Homogénea en método, resultados y estadística. Se explicita el presupuesto heredado de Top-k. |
| Tabla de datasets | Retirada; datasets y particiones descritos en párrafos con sus referencias. |
| Antigua tabla 7, Outex específico | Retirada del cuerpo, sustituida por comparación de la extensión en cuatro datasets. Resultados de reproducción conservados como respaldo. |
| Antigua tabla 8, publicaciones | Retirada: protocolos distintos no sustentan un ranking común. Antecedentes conservados en la revisión de literatura. |
| Nombres de pruebas | Friedman, Quade y Holm identifican el análisis; Java se menciona como implementación. |
| Cambio de conclusión con N-gramas | Mejora descriptiva importante de GFS en Outex con ResMLP, sin mejora uniforme ni conclusión conjunta prematura. |
| Antiguas tablas 9/10 | Retiradas las tablas de margen práctico y Jaccard. Sus datos no se eliminaron. |
| Figura 4 | Retirado el boxplot de subconjuntos aleatorios. |
| Conclusión | Reescrita: objetivo, evidencia, límites estadísticos y extensión de N-gramas. Se eliminaron afirmaciones de dominancia general y equivalencia no demostrada. |
| Métricas adicionales | Tabla de exactitud para las mismas cinco estrategias y condiciones. Las métricas antiguas de otra reevaluación no se atribuyen al protocolo actual. |

Los números de tablas cambian después de estas eliminaciones: la antigua tabla principal 6 es ahora la tabla 4; la tabla 6 actual presenta N-gramas. La matriz Holm es la tabla 9 actual y no es la tabla de margen práctico retirada.

## Evidencia y cierre pendiente

`scripts/build_paper_revision_tables.py` genera las tablas desde CSV, comprueba ausencia de duplicados, cobertura por dataset/método y valores finitos, y verifica que las medias mostradas coincidan con la matriz entregada al Java. Los hashes de las fuentes se conservan en `paper/articulo/borrador_profesor/generated/provenance.json`.

Se validaron 56 condiciones de referencia con cinco estrategias (280 evaluaciones) y las 28 condiciones completas de ResMLP con N-gramas (140 evaluaciones). La prueba principal sigue correspondiendo a 20 descriptores. No se presenta la extensión conjunta como finalizada: falta cerrar SVM, incluidos sus controles Top-k, y regenerar después los contrastes para 21 candidatos. La adaptación utilizada se identifica explícitamente como RGB Pixel N-grams + SVD.

La revisión no modificó el clasificador de los experimentos activos, sus checkpoints ni las salidas Java originales. No se reanudó ni sustituyó SVM por cuML en esta tarea.

## Verificación final

Ambos documentos se compilaron con pdfLaTeX y BibTeX, con pasadas adicionales para resolver citas y referencias. Se corrigió la colocación de tablas y figuras usando la sintaxis de la clase CAS en el artículo, y una envoltura compatible con report en la tesis. Se inspeccionaron visualmente la figura, la tabla principal con el panel de descriptores, la extensión multibase y las tres tablas estadísticas. La revisión dejó el paper en 15 páginas físicas y la tesis en 29, incluidas sus páginas iniciales. No quedaron citas o referencias sin resolver ni desbordamientos de cajas en las compilaciones revisadas.

La figura tiene comprobación estática correcta y revisión visual manual; sus avisos automáticos sobre encabezados y matrices están documentados en `figures/concatenacion_v02_qa.md`.
