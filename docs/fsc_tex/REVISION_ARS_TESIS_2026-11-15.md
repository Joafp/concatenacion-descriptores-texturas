# Revisión ARS de la tesis: método, evidencia y defensa

Fecha: 15-11-2026, America/Asuncion. Versión revisada: commit `1fdf0a8`, PDF
de 90 páginas, SHA-256 `d420b1d15c1e4e0c5d50c29cbf2224e67a3269fa724cc75c36a39f6415694dbf`.
**Revisión de solo lectura: no se modificaron tesis, resultados ni modelos.**

## Dictamen y significado

La proposición central sobrevive a la revisión: Top-4 es una alternativa
compacta observada y la activación por margen puede cambiar el compromiso
entre calidad y adquisición. El texto no necesita afirmar que cuatro sea
óptimo universal ni que haya una aceleración física del 75 %.

Los cinco informes no identificaron un defecto Critical o Major sustentado.
Conservan **15 observaciones originales, todas Minor**, con coincidencias
que no se cuentan como defectos independientes y algunas propuestas que se
descomponen en acciones distintas. La contribución delimitada recibe pass;
metodología, dominio, coherencia, accesibilidad y escritura reciben warn.

El resultado mecánico del contrato ARS es **Major Revision**: su regla F3
se activa con avisos en al menos dos dimensiones obligatorias. Esto **no
reclasifica los hallazgos Minor como Major**, no implica que se haya probado
un fallo grave ni constituye una decisión del tutor o una universidad.
La revisión no dispone de rúbrica institucional ni criterios confirmados
de revista (`criteria_binding_unavailable`) y permanece `NOT_CALIBRATED`.

## Qué quedó respaldado en la revisión

- El recorrido P1 (qué concatenar) → P2 (cuándo activarlo) responde al título.
- E1 distingue el mismo Top-4 directo de la política por margen y conserva
  el cierre 27/27, las pérdidas y los resultados no significativos.
- El método diferencia concatenación de voto, margen de probabilidad
  calibrada, dimensión de adquisición y proyección de latencia física.
- El cambio a accuracy tras observar resultados está declarado; no se
  reetiqueta como selección por accuracy el ranking histórico por macro-F1.
- Las aproximaciones y adaptaciones de papers se identifican como tales.
  El aporte defendible es empírico y trazable, no prioridad algorítmica mundial.

Estos son juicios de revisión sobre el alcance y la coherencia; no sustituyen
una reproducción independiente desde RGB ni una validación poblacional nueva.

## Correcciones y comprobaciones concretas

| Frente | Hallazgo | Reparación mínima |
|---|---|---|
| Cifra ResMLP | §5.2.1 dice 0,212 puntos de cuatro a cinco; las cifras impresas implican aproximadamente 0,2305 puntos porcentuales de accuracy. EIC, metodología y DA coinciden. | Recalcular con las medias fuente y corregir cifra/unidad; sin entrenamiento. |
| Referencias | §5.3 remite al complemento macro-F1 C.9 cuando explica la tabla principal de accuracy 5.6; el pie de latencias conserva la organización anterior. | Etiquetas, referencias y pies coherentes; compilar y comprobar destinos. |
| Exposición | La secuencia de infraestructura pesa demasiado en resultados E1. | Conservar criterio, corrección y límites en cuerpo; trasladar bitácora al anexo. |
| OOF | Falta destacar en el método central qué ranking/subconjunto se mantiene fijo mientras se producen OOF de los SVM. | Distinguir selección de representación, ajuste de cabezas y selección de ruta; separar el archivo histórico de E1. No atribuirle contaminación externa no probada. |
| Variación de calidad | El promedio y p no significativo no cuantifican por sí solos las pérdidas y variabilidad observadas. | Mostrar diferencias/rangos por condición o sensibilidad con datos guardados, indicando unidad y dependencia. No hacer un bootstrap ingenuo de particiones solapadas. |
| Sensibilidad estática | El análisis secundario sin KTH por macro-F1 no sustituye la sensibilidad de la familia principal de tres estrategias en accuracy. | Recalcular la misma familia sobre cinco medias disponibles, conservando bibliotecas y comparadores. **No se refiere a un E1 incompleto:** E1 sí cerró KTH. |
| Outex | La reserva de correspondencia no delimita suficientemente bloques, archivos y tablas. | Matriz de procedencia y comprobaciones. Solo si se identifica una fila principal afectada, marcarla y mostrar sensibilidad; no presumir desalineación general. |
| Antecedentes | Falta situar antecedentes próximos de selección de métodos de textura y compresión de descriptores combinados. | Incorporar Puig et al. y Khan et al. con diferencias de unidad, protocolo y mecanismo; no ejecutarlos. |
| Comparadores | Las diferencias de receta quedan demasiado fuera del PDF. | Tabla por método con representación/dimensión, pesos/capa, cabeza, reparto y diferencias verificadas/no verificadas; conservar las etiquetas de adaptación. |
| Accesibilidad | SFFS, CNN y MLP necesitan expansión; el coseno necesita una explicación inicial. | Definiciones breves y escala del coseno, identificando vectores de la misma imagen y el alcance muestral del umbral 0,999. |

La incertidumbre y la sensibilidad de accuracy pueden trabajarse sobre datos
existentes. La sensibilidad Outex es **condicional a lo que demuestre el
rastreo**, no una constatación de datos incorrectos. La revisión no establece
p-valores falsos: los recibos estadísticos acotados no pudieron recomputar
algunos procedimientos exactos y lo declaran, en lugar de sustituirlos por
aproximaciones asintóticas.

## Qué experimentos exige y cuáles no

Los remedios mínimos son escritura, comprobación documental y análisis de
resultados guardados. **Ningún revisor exige nuevos fits o extracciones para
sostener las conclusiones exploratorias actuales.**

Top-4 más N-gramas, ranking plenamente anidado, bases optimizadas para cada
compuerta, evaluación prospectiva o latencia online serían ampliaciones para
preguntas más fuertes. No quedan ejecutados por esta revisión. Medir ahorro
físico seguirá necesitando el protocolo online y resolver sus bloques con
fidelidad pendiente; E5 será necesario si se desea responder específicamente
qué aporta añadir N-gramas al mismo Top-4, no para declarar ya probado ese aporte.

## Objeciones de defensa y alcance de las respuestas

1. **«¿Por qué cuatro si diez o cinco pueden dar más accuracy?»** Cuatro es
   una elección exploratoria compacta cerca del máximo medio; se muestran
   dimensiones, ganancias posteriores y pérdidas. No se afirma óptimo universal.
2. **«¿Demostraron que conservan la calidad?»** La diferencia observada es
   pequeña, con ganancias y pérdidas; p=0,5625 no demuestra equivalencia ni
   no inferioridad. Hay que añadir la información de variación solicitada.
3. **«¿Dónde se midió el ahorro del 75 %?»** Es adquisición proyectada bajo
   perfiles de componentes; no una aceleración online de la política completa.
4. **«¿El margen fue seleccionado sin ver esas imágenes?»** La ruta se elige
   dentro del entrenamiento; debe aclararse que el OOF de cabezas está
   condicionado a un subconjunto archivado y que no valida independientemente
   todo el procedimiento de selección.
5. **«¿Replicaron los papers?»** Hay adaptaciones y aproximaciones con
   reservas; deben resumirse sus recetas en el PDF. Una diferencia de cifras
   no refuta el paper ni acredita una reproducción fiel.

Estas respuestas delimitan lo que ya puede sostenerse; no fingen que las
correcciones o análisis solicitados ya fueron aplicados.

## Evidencia y continuación

- [Síntesis completa y reglas de decisión](../../results/analysis/ars_thesis_review_20261115_v1/reports/editorial_synthesis.md).
- [Informes, compromisos y alcance](../../results/analysis/ars_thesis_review_20261115_v1/README.md).
- [Roadmap fuente-ordenado](../../results/analysis/ars_thesis_review_20261115_v1/revision_roadmap.json).
- [Validación e integridad](../../results/analysis/ars_thesis_review_20261115_v1/validation_receipt.json).

El roadmap conserva fuentes, severidades, costos y criterios de verificación;
no es un ranking ni una selección de trabajo hecha en nombre del autor. Sus
targets corresponden a una **copia de revisión** con bloques, no son permiso
para modificar directamente archivos LaTeX. No se creó una adjudicación de
autor ni se aplicó una revisión. Cualquier corrección posterior deberá
conservar las reservas y quedar ligada a su evidencia.

Los cinco asientos trabajaron en contextos separados sin ver informes de
pares antes de comprometer el propio. Son ejecuciones asistidas por modelos;
no cinco expertos humanos ni evidencia de errores independientes. No hay
identificación suficiente de familias/proveedores para acreditar diversidad,
y el riesgo de errores correlacionados permanece.
