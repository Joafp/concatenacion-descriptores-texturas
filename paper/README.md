# Manuscrito de tesis — corte del 26-10-2026

**Estado: revisión de trabajo; cierre experimental pendiente.** La tesis estudia selección de bloques, ensambles y adquisición condicional para clasificación de texturas.

**Actualización de réplica, 26-10:** PDF de 67 páginas. Se incorporaron cinco condiciones nuevas auditadas: FMD semillas 42/123/2026 y Outex 123/2026, conservando separado el piloto Outex/42. Se añadieron diseño, medias por dataset, barrido de tres reglas y cuatro presupuestos, referencias por semilla y ablación del mismo rescate permanente/condicional. La réplica registra tanto ventajas medias como pérdidas por semilla; no es evaluación del híbrido en los seis datasets ni medición física nueva. Véase el [registro de incorporación](../docs/fsc_tex/INCORPORACION_REPLICA_TESIS_2026-10-26.md).

**Actualización de mesa R2:** PDF de 63 páginas con P0, control estático seleccionado bajo los mismos presupuestos y sensibilidad del benchmark sin KTH. Se añade identificación verificable de SoilOriginal y reconstrucción mínima de tablas. Véanse el [registro de correcciones](../docs/fsc_tex/MESA_EVALUADORA_GRADO_R2_2026-10-25.md) y la [receta de reproducción](../docs/fsc_tex/REPRODUCCION_MINIMA_MESA_2026-10-25.md). Los informes anteriores conservan su fecha y alcance histórico; no prueban que esta versión esté aprobada.

## Fuentes vigentes

- Documento principal: [tesis.tex](tesis.tex).
- Capítulos activos: siete capítulos y anexos en [chapters](chapters/), incluidos explícitamente desde tesis.tex.
- PDF recompilado: [tesis.pdf](tesis.pdf).
- Bibliografía activa: [references.bib](articulo/borrador_profesor/references.bib).
- [Auditoría del corte](../docs/fsc_tex/AUDITORIA_TESIS_Y_CIERRE_2026-10-25.md).
- [Plan de cierre vigente](../docs/fsc_tex/PLAN_CIERRE_VIGENTE_2026-10-25.md).
- [Registro de la revisión editorial aplicada](../docs/fsc_tex/REVISION_EDITORIAL_APLICADA_2026-10-25.md).
- [Mejora integral posterior del manuscrito](../docs/fsc_tex/MEJORA_INTEGRAL_TESIS_2026-10-25.md).

## Alcance que no debe mezclarse

1. Biblioteca de 22 bloques y 20.652 dimensiones nominales.
2. Seis datasets principales: DTD, FMD, CUReT, Outex13Official1360, SoilOriginal y KTH-TIPS-2b. VisTex no está incorporado.
3. Benchmark estático: 47 condiciones por clasificador, SVM y ResMLP.
4. Cascada histórica: 27 condiciones; KTH archivado mantiene reservas de procedencia.
5. Nuevo híbrido de diversidad: piloto Outex/42 y cinco condiciones adicionales de desarrollo OOF en dos datasets. FMD tiene 800 imágenes de desarrollo por semilla; Outex, 680. No se evalúan los tests externos ni se atribuyen seis datasets independientes al híbrido.
6. Los pilotos físicos anteriores no validan el híbrido nuevo; CUReT y Soil mantienen discrepancias de representación.

## Revisión del manuscrito

El título vigente es «Fusión costo-consciente de descriptores de textura mediante ensambles y adquisición condicional». Se separaron método y diseño experimental, se organizaron los resultados por preguntas y se trasladaron especificaciones, procedencia, análisis adicionales y reproducibilidad a anexos. El PDF vigente tiene 67 páginas. El método incorpora ecuaciones, dos pseudocódigos y un diagrama; la curva calidad–costo se genera desde resultados guardados.

El rescate nuevo utiliza el ensamble de diversidad completo o reducido. Se conservan sus trece resultados y la excedencia de validación; no se declara superioridad universal, equivalencia o ahorro físico del 85,40 %. La financiación externa y los conflictos de interés se declaran inexistentes, según confirmación del autor. No se inventó una distribución individual de contribuciones.

La mejora integral anterior a P0 formalizó la selección restringida bajo presupuesto y su condición algebraica de ahorro de adquisición; aclaró las dos agregaciones de F1, los niveles OOF y el traslado del umbral al modelo reajustado. Añadió interpretación del perfil de costos y multiplicidades verificadas por pliegue. Ese corte tenía 54 páginas. El respaldo inmediatamente anterior a esa mejora es [revision_mejora_integral_20261025_before.tar.gz](revision_mejora_integral_20261025_before.tar.gz).

P0 separa poda y activación en el archivo de desarrollo: relevancia/B60 reduce 69,76 % por poda y otro 51,72 % respecto del mismo rescate podado permanente, con pérdidas de F1 observadas. Marginal/B60 conserva las 680 predicciones con 43,09 % menos adquisición proyectada, pero más llamadas. No se afirma ahorro físico ni superioridad frente a selección estática optimizada bajo el mismo presupuesto. Las tablas nuevas se reconstruyen mediante `OPENBLAS_NUM_THREADS=2 .venv-confirmatory/bin/python scripts/build_p0_thesis_tables.py` desde la raíz del repositorio. El generador verifica 156 campos numéricos y conserva hashes en `paper/generated_p0/provenance.json`. Respaldo previo: [revision_p0_20261025_before.tar.gz](revision_p0_20261025_before.tar.gz).

R2 incorpora un rival estático dentro del pool de 22 individuales y miembros de diversidad, enumerado hasta tres modelos. Relevancia/B60 alcanza 0,910742 frente a 0,892923 con costos proyectados de 53,316 y 44,831 ms; ambos cumplen B60 en la media reunida. En B15/B120 el estático obtiene mayor F1 con mayor costo. Se mantienen las cuatro comparaciones y no se afirma optimalidad global. La sensibilidad SCI2S sin KTH conserva GFS–Individual significativo con ResMLP (Holm 0,0270), no con SVM; Friedman alineado no rechaza. Las nuevas tablas están en `generated_mesa_r2` con procedencia separada. La suite registra 83 pruebas aprobadas. Respaldo previo a R2: [revision_mesa_r2_20261025_before.tar.gz](revision_mesa_r2_20261025_before.tar.gz).

El respaldo anterior a esta reestructuración, incluido el PDF previo, está en [revision_editorial_20261025_before.tar.gz](revision_editorial_20261025_before.tar.gz). Se conserva también el [respaldo de la revisión numérica anterior](revision_20261025_before.tar.gz). No se modificaron resultados experimentales para reescribir el manuscrito. La compilación correcta no certifica cierre científico ni una revisión formal completa de ARS.

La réplica se reconstruye con `OPENBLAS_NUM_THREADS=2 PYTHONPATH=.:src .venv-confirmatory/bin/python scripts/build_replication_thesis_tables.py` desde la raíz. Las cuatro tablas y sus hashes están en `generated_replication`; las fuentes auditadas, en `results/analysis/mesa_replication_20261026`. La suite final registra 97 pruebas aprobadas, incluida reconstrucción byte-idéntica de tablas. Los estáticos FMD recuperados conservan las decisiones originales; no se repitieron las otras etapas. Respaldo anterior a esta incorporación: [revision_replica_20261026_before.tar.gz](revision_replica_20261026_before.tar.gz). No se generó un ZIP Overleaf nuevo ni se sincronizó el repositorio remoto en este corte.

## Compilación local

Ejecutar pdflatex, bibtex y dos pasadas de pdflatex desde este directorio sobre tesis.tex. La plantilla y los paquetes existentes se conservan. Los paquetes Overleaf y presentaciones anteriores no se consideran actualizados por recompilar este PDF; verificar su fecha antes de compartirlos.
