# Tesis: Top-k directo y optimización por margen

**Revisión ARS aplicada, 13-11-2026:** el PDF vigente tiene **82 páginas**. Se aplicaron los ocho cambios aprobados por el autor, con fórmulas de costo más precisas, ejemplo real del umbral, parámetros reproducibles y conclusiones revisadas. Las 26 pruebas pasaron; se conservaron los resultados experimentales. [Informe de la revisión](../docs/fsc_tex/REVISION_ARS_TOPK_MARGEN_2026-11-13.md) y [manifiesto vigente](../results/analysis/ars_topk_revision_20261113_v1/manuscript_release_ars.json).

**Título vigente:** «Concatenación Top-k de descriptores para clasificar texturas: comparación del uso directo y la activación por margen».

Se reescribieron los siete capítulos, la portada y ambos resúmenes el 13-11-2026. La tesis mantiene dos etapas centrales: construir y comparar Top-k, incluido Top-4; después optimizar su ejecución activándolo por margen y compararlo con el mismo Top-k directo. La activación está desarrollada en el cuerpo principal, con ecuaciones, diagrama, selección interna y resultados.

El [PDF vigente](tesis.pdf) es un borrador completo para revisión de los autores y el tutor. La compilación y la auditoría no equivalen a aprobación académica ni cierre de todas las reservas.

## Fuentes y trazabilidad

- [Fuente principal](tesis.tex) y [capítulos y anexos](chapters/).
- [Bibliografía activa](articulo/borrador_profesor/references.bib).
- [Plan vigente](../docs/fsc_tex/PLAN_TOPK_MARGEN_2026-11-13.md).
- [Informe de reescritura](../docs/fsc_tex/INFORME_REESCRITURA_TOPK_MARGEN_2026-11-13.md).
- [Auditoría](../results/analysis/topk_margin_rewrite_20261113_v1/summary.json).
- [Versión compilada y hashes](../results/analysis/topk_margin_rewrite_20261113_v1/manuscript_release.json).

Los estudios de rescate de ensamble y poda se conservan en un anexo complementario. La versión anterior se respaldó en `archive/local/tesis_before_topk_rewrite_20261113.tar.gz`, con manifiesto SHA-256. Ese respaldo es local y no se garantiza su disponibilidad en GitHub.

## Evidencia y límites

1. Barrido de 21 tamaños y 47 condiciones por tamaño y clasificador en seis datasets: 987 filas SVM y 987 ResMLP. Las medias equiponderan datasets.
2. Top-4 frente a concatenaciones completas, selección y N-gramas, identificando las diferentes bibliotecas.
3. Comparadores externos con macro-F1 y milisegundos de las mismas llamadas online, separados del barrido histórico.
4. Auditoría de 27 condiciones SVM y 31.984 observaciones de prueba del mismo Top-k directo/por margen. Se reutilizan imágenes entre particiones; no son observaciones independientes y k no siempre es cuatro.
5. Cinco condiciones cuyo rescate coincide en bloques con el Top-4 del barrido: dos DTD, dos FMD y una CUReT. Se conservan ganancias, pérdidas y empates; no representan Top-4 por margen en los seis datasets.

Top-4/SVM registra macro-F1 medio 0,936554 frente a 0,936764 del máximo descriptivo en k=10, con aproximadamente 15,42 % de las dimensiones de los 21 bloques. Respalda un compromiso compacto, sin demostrar optimalidad universal ni equivalencia estadística. La optimización por margen se evalúa por separado en calidad, activación, adquisición y tiempo físico.

Se mantienen las reservas KTH, DeepLumina/DTD y no convergencia, las diferencias entre Top-4 histórico y online y las discrepancias de representación de pilotos CUReT/Soil. Los costos proyectados se distinguen de tiempos físicos. Esta reescritura no añade fits, predicciones ni cronometrajes, ni repite paneles cerrados.

## Verificación y compilación

Se aprobaron 26 pruebas de trazabilidad, reproducción de métricas y controles relacionados. El generador verifica 124 fuentes por SHA-256 y rechaza reutilizar directorios de auditoría existentes. Las recetas figuran en el anexo de reproducibilidad y el informe.

La versión anterior a la ronda ARS tenía 81 páginas. Incluye los ocho pasos del recorrido experimental y un ejemplo real de concatenación de cuatro bloques en 3.328 coordenadas. Las figuras nuevas muestran todos los tamaños, las ganancias incrementales y las curvas de los seis datasets. Con SVM, de uno a cuatro se ganan 1,911 puntos porcentuales de macro-F1; de cuatro al máximo en diez, 0,021 puntos, con mayor dimensión. Los incrementos posteriores a cuatro conservan ambos signos: la curva no disminuye de forma monótona. Fuentes y resultados del gráfico: [auditoría de ganancias](../results/analysis/topk_marginal_gains_20261113_v1/summary.json).

Desde `paper`, en Ubuntu/WSL:

```sh
../.tools/tectonic-0.16.9/tectonic --keep-logs --keep-intermediates tesis.tex
```

Los paquetes Overleaf y presentaciones anteriores no se actualizan por recompilar este PDF. Los informes históricos conservan su fecha y alcance. Esta revisión no crea commits ni realiza push.
