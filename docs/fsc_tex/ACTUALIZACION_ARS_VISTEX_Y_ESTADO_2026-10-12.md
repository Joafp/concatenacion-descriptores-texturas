# Actualización ARS: VisTex y estado de la tesis

Fecha: 12 de octubre de 2026. Revisión documental local, no revisión independiente ni certificación de originalidad. ARS 3.22.0, ruta academic-paper/revision. No se ejecutaron nuevos experimentos ni pruebas estadísticas.

## Qué es la tesis ahora

La tesis estudia cómo combinar representaciones visuales para clasificar texturas y reducir el costo de extraerlas. La concatenación estática proporciona los controles; la contribución experimental candidata es una cascada costo-consciente de dos etapas: primero un descriptor económico seleccionado en entrenamiento; cuando el margen del clasificador no permite una salida temprana, se adquiere el conjunto Top-k costoso. Es una evaluación de adquisición condicional y del compromiso calidad–latencia, no una demostración de superioridad universal ni una certificación de novedad.

El estudio principal conserva 22 descriptores, 20.652 dimensiones y seis datasets: DTD, FMD, CUReT, Outex-TC-00013, SoilOriginal y KTH-TIPS-2b. La evaluación estática compara Individual, Completa, Top-k, GFS y Homogénea con SVM y ResMLP. La cascada usa SVM y 27 condiciones; las 31.984 observaciones de prueba acumuladas no son necesariamente imágenes únicas.

Los resultados ya documentados son: macro-F1 descriptivo medio por dataset de 0,9345 para cascada, 0,9341 para Top-k de origen y 0,9409 para Completa-22. En los cinco datasets reconciliados, las diferencias son −0,0004 y −0,0046, respectivamente. Los contrastes no prueban equivalencia ni no inferioridad. KTH queda fuera de esa inferencia conjunta hasta completar la referencia homogénea.

La evidencia física disponible es un piloto DTD de 47 imágenes en RTX 4060: 88,75 frente a 283,33 ms para cascada y Top-k, reducción observada de 68,7% y razón agregada 3,19×. No equivale a una reducción medida sobre los seis datasets. El 75,5% corresponde a una proyección de costo.

## Verificación actual de VisTex

Fuentes locales inspeccionadas:

- `data/VisTex.tar.gz`: SHA-256 `6340ab536dfddd6d0e55012a0b6fa1dd9b3d933da5d1547349b7415a5d180772`.
- `data/confirmatory_sources/VisTex/extracted/VisionTexture/VisTex/Images/Reference`: 167 imágenes, 19 categorías.
- `results/extensions/vistex_reference12/sample_manifests/VisTexReference12.csv`: 140 filas; ninguna ruta histórica existe actualmente, pero 140/140 hashes coinciden con las fuentes del directorio anterior al resolver categoría y nombre.
- `results/extensions/vistex_reference12/data_audit.json`: 20 extractores, suma de dimensiones 19.628.
- `results/extensions/vistex_reference12/nested_summary.csv`: resultados históricos siguientes.

| Clasificador | Individual | Completa-20 | GFS |
|---|---:|---:|---:|
| SVM | 0,9678 | 0,9816 | 0,9640 |
| ResMLP | 0,9630 | 0,9771 | 0,9659 |

Macro-F1 medio de 15 particiones por clasificador; presentación descriptiva de resultados archivados, no una nueva ejecución. No se recalcularon aquí las métricas desde predicciones. No comparar estas filas como si utilizaran la biblioteca principal de 22 descriptores. No se dispone en ese resumen de Top-k ni cascada. Las filas de Homogénea están separadas por familia seleccionada y no deben promediarse sin ponderar sus respectivos conteos.

VisTexReference12 retiene las categorías con al menos siete ejemplos. El original Reference contiene categorías con apenas dos; un protocolo nuevo debe atender esa restricción. La ausencia de un split oficial no impide realizar investigación válida: exige declarar la partición, fijarla antes del análisis y evitar contaminación entre derivados de una misma imagen. Los tamaños alternativos y recortes no constituyen automáticamente observaciones independientes.

Fuentes institucionales identificadas en la investigación precedente: [MIT VisTex](https://vismod.media.mit.edu/vismod/imagery/VisionTexture/vistex.html) y [organización del archivo](https://vismod.media.mit.edu/vismod/imagery/VisionTexture/information.html). Este inventario no establece por sí solo permisos de redistribución.

## Cambios documentales aplicados

1. Plan actualizado a v1.7 con estado real de VisTex y prioridades.
2. Índice `datasets/README.md` actualizado con originales, hash, cobertura y limitaciones.
3. Este registro distingue evidencia actual, resultados previos y trabajo pendiente. Los datos, manifiestos históricos y resultados no fueron alterados.

## Propuesta archivada: no aplicar al manuscrito

**Decisión explícita del autor, 12-10-2026: «No incorporar VisTex todavía».** Los textos siguientes se conservan como propuesta no adoptada, no como trabajo autorizado ni pendiente obligatorio. No se añadieron al manuscrito y no se lanzarán corridas de VisTex por esta actualización.

Texto propuesto para metodología:

> Como extensión histórica se conserva VisTexReference12, un subconjunto de 140 imágenes de las 12 categorías con al menos siete ejemplos de la colección Reference de VisTex, cuyo archivo local contiene 167 imágenes en 19 categorías. Se verificó la correspondencia SHA-256 de las 140 imágenes con las fuentes originales. Esta evaluación utiliza una biblioteca previa de 20 descriptores (19.628 dimensiones), sin BEiT-v2 ni RGB N-grams+SVD, y no forma parte del benchmark principal de seis conjuntos y 22 descriptores.

Texto propuesto para resultados y limitaciones:

> En la extensión histórica VisTexReference12, los macro-F1 medios de Individual, Completa-20 y GFS fueron, respectivamente, 0,9678, 0,9816 y 0,9640 con SVM, y 0,9630, 0,9771 y 0,9659 con ResMLP. Estos resultados resumen 15 particiones repetidas y se presentan únicamente de forma descriptiva; no se incorporan como observaciones independientes a los contrastes del estudio principal. La evaluación con la biblioteca de 22 descriptores, Top-k y la cascada queda pendiente bajo un protocolo común previamente fijado.

ARS exige autoridad explícita sobre los cambios concretos antes de aplicar una revisión del manuscrito (`ars/academic-paper/references/revision_patch_protocol.md`, regla #670). No se inventó una aprobación ni un certificado de aplicación. El PDF y el ZIP existentes permanecen sin cambios en esta actualización; no se afirma una compilación nueva.

## Qué falta cerrar

1. Completar Top-k corregido de KTH en folds 1–3 o mantener su exclusión inferencial claramente justificada.
2. Documentar de forma homogénea procedencia, transformaciones, grupos y selección interna de los resultados principales.
3. Reconciliar la explicación de discrepancias físico/caché con los artefactos que la sustentan antes de presentarla como causa demostrada: el memorando afirma interpolación Bilinear/Bicubic, mientras el plan aún lo registra como pendiente.
4. Revisar expresiones de saturación dimensional y diseño completamente prospectivo que permanecen en conclusiones: los resultados actuales no justifican una ley general de saturación ni borrar la influencia de observaciones externas sobre el diseño.
5. Si se amplía el piloto físico: registrar observaciones por imagen, repetir y alternar/aleatorizar el orden, medir los controles pertinentes y delimitar carga de modelos y decodificación.
6. VisTex queda fuera del manuscrito por decisión del autor. Solo si se retoma en el futuro, fijar protocolo y completar descriptores antes de una comparación común; no es un requisito para cerrar la tesis actual.

La prioridad científica es cerrar trazabilidad y calidad–costo, no aumentar el número de datasets sin comparabilidad. La evaluación documental realizada no sustituye una revisión independiente del código, de todas las referencias o del manuscrito completo.
