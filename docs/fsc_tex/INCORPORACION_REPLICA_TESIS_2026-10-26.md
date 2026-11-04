# Incorporación de la réplica al manuscrito — 26-10-2026

## Alcance y autoridad

Se continuó el plan vigente, a pedido del autor, después de recuperar y auditar las cinco condiciones nuevas. Se utilizó ARS como guía local de escritura y comprobación de afirmaciones, junto con la skill PDF para compilación y revisión visual. No es una ejecución formal de la cadena de revisión/autorización de ARS, una revisión institucional ni una certificación de cierre científico. No se reinterpretó «continua» como autorización para nuevos experimentos, push o publicación.

Se preservó el estado anterior en `paper/revision_replica_20261026_before.tar.gz`. No se modificaron resultados científicos, predicciones ni decisiones para incorporar la evidencia.

## Cambios del documento

- Resumen, abstract e introducción: cobertura explícita del híbrido en dos datasets, separada del benchmark de seis, con las pérdidas y la ausencia de medición física.
- Diseño: cinco condiciones nuevas, 800 imágenes de desarrollo FMD y 680 Outex por condición; tres pliegues productores y tres internos; semillas y efecto sobre particiones, sorteos y transformaciones; tests externos excluidos.
- Resultados: nueva sección de réplica, medias por dataset y cuatro presupuestos, sin mezclar Outex/42 en las medias nuevas. Se conserva el contraejemplo FMD/42/B60 y la falta de orden uniforme entre reglas.
- Anexo C: barrido completo de tres reglas y estático en las cinco condiciones; referencias del mismo protocolo; vista del mismo rescate permanente/condicional con todos los presupuestos. Los resultados por imagen permanecen en sus archivos originales.
- Discusión y conclusión: se restringieron al piloto las afirmaciones que no se sostienen de manera uniforme en la réplica.
- Reproducibilidad: registro de la recuperación de tamaño, decisiones byte-idénticas, fuentes y reconstrucción de tablas. README y plan sincronizados con el corte nuevo.

## Hallazgo que modifica la interpretación

No debe generalizarse «la compuerta no mejora F1» fuera del piloto Outex/42. En relevancia/B60, la media FMD del mismo rescate permanente es 0,974596 frente a 0,977489 condicional; la media de las nuevas semillas Outex es 0,912135 frente a 0,905991. Las dos vistas conservan los miembros fijados, no son dos rescates reoptimizados. La mejora media FMD tampoco establece un efecto uniforme por semilla ni una confirmación poblacional.

Frente al estático optimizado bajo presupuesto, las medias relevancia/B60 son favorables al híbrido en ambos datasets, pero FMD/42 favorece al estático tanto en F1 como en costo. Los presupuestos no garantizan igual adquisición realizada. No se reutilizaron los valores p del benchmark estático para la propuesta nueva ni se añadieron tests tratando semillas como datasets.

## Generación y verificación

`scripts/build_replication_thesis_tables.py` verifica los hashes de las cinco auditorías y genera cuatro tablas desde 170 resultados de políticas y 60 vistas P0: ocho filas de medias, veinte de barrido, treinta referencias y veinticuatro medias P0. El detalle de entradas y salidas está en `paper/generated_replication/provenance.json`. La prueba de reconstrucción obtiene tablas byte-idénticas en una carpeta temporal.

- Suite completa: **97 aprobadas en 105,02 s**.
- Documento compilado: **67 páginas**, siete capítulos y anexos.
- Verificador estructural: 120 celdas estáticas comprobadas; 40 claves citadas, todas resueltas; 35 dependencias activas; 59 entradas archivadas preservadas; cero desbordes, advertencias de referencias indefinidas o cajas insuficientes en el log final.
- Revisión visual: vista de conjunto de las 67 páginas y revisión ampliada de la tabla principal de réplica y las tres tablas nuevas del anexo; sin recortes o superposiciones observados. La comprobación estructural no sustituye esta inspección.
- El primer intento de preflight en WSL declaró `UNAVAILABLE` por ausencia de pypdf. La ejecución posterior con el Python incluido en el runtime devolvió `PASS`, 67 páginas declaradas/enumeradas/leídas y ninguna advertencia. Ese resultado acredita estructura del PDF, no exactitud científica.

PDF: `paper/tesis.pdf`. SHA-256: `56f96e70a32ece1defe5c97429dc1fc92160ae91fb7d2f8d128f70f7fb7652f5`.

## Pendiente real

Controles GFS/Top-k concatenados reajustados bajo el protocolo del híbrido; medición física de esa ruta; extensión a otros dominios; fidelidad CUReT/Soil y reconciliación KTH; portabilidad y entrega pública. No se preparó un ZIP Overleaf nuevo ni se hizo commit/push en este corte. La tesis está actualizada con esta réplica, pero esas objeciones no se consideran cerradas.
