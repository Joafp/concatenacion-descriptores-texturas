# Plan vigente: Top-k directo y optimización por margen

Fecha: 13-11-2026, America/Asuncion.

## Título y recorrido confirmado

**Concatenación Top-k de descriptores para clasificar texturas: comparación del uso directo y la activación por margen**

El autor confirmó que la historia debe mostrar primero cómo se construyó
Top-k, por qué se estudia Top-4 y cómo se compara con otras concatenaciones,
N-gramas y métodos de literatura; después, cómo se optimiza su ejecución
activándolo por margen. **La versión optimizada es la segunda parte central
de la tesis**, desarrollada en método, diseño, resultados y conclusiones.

El estudio busca identificar las ventajas de Top-k y los beneficios de su
optimización sin presuponer que ganan todas las condiciones. Una afirmación
de superioridad debe especificar métrica, rival, dataset y protocolo. No se
eligen tamaños, semillas o tolerancias para forzar una conclusión.

## Estado aplicado en esta versión

- **Hecho:** respaldo de la versión anterior, incluidos fuente y PDF, en
  `archive/local/tesis_before_topk_rewrite_20261113.tar.gz` y manifiesto SHA-256.
- **Hecho:** reescritura completa de siete capítulos, portada, resúmenes y
  anexos afectados; PDF vigente de 82 páginas, ampliado con el recorrido de las pruebas.
- **Hecho:** reconstrucción del barrido ampliado y tablas por dataset, con
  bibliotecas diferenciadas; incorporación de N-gramas y comparadores externos.
- **Hecho:** auditoría de 27 condiciones directo/margen y cinco condiciones
  cuyo rescate coincide con el Top-4 del barrido.
- **Hecho:** ecuaciones y diagramas de entrenamiento y clasificación,
  resultados de calidad, activación, adquisición y pilotos físicos.
- **Hecho:** 26 pruebas aprobadas; compilación sin referencias indefinidas ni
  desbordes horizontales; revisión visual del PDF.
- **Conservado:** rescate de ensamble y poda en un anexo complementario.
- **Sin nuevas corridas:** cero fits, extracciones, predicciones o tiempos
  experimentales para esta reescritura. No se repitieron paneles cerrados.
- **Pendiente:** revisión de los autores y el tutor y cierre de las reservas
  científicas identificadas abajo. Esta versión no equivale a aprobación.

Detalle: [informe del corte](INFORME_REESCRITURA_TOPK_MARGEN_2026-11-13.md).

## Preguntas y comparaciones centrales

**P1. Construcción y comparación.** Estudiar el ranking individual interno,
la normalización por bloque y la concatenación de los primeros k. Comparar
el mejor individual seleccionado internamente, Top-k, Top-4, GFS,
Homogénea y Completa, identificando biblioteca y clasificador. Explicar las
ampliaciones y la aportación de N-gramas sin confundir relevancia individual
y complementariedad.

**P2. Optimización de ejecución.** Mantener fijo el rescate Top-k y comparar
ejecutarlo siempre con activarlo mediante el margen de una primera etapa.
Contabilizar base, compuerta, extracción incremental y clasificación cuando
corresponda. Informar pérdidas de calidad junto con ahorro o sobrecosto.
El margen SVM no es una probabilidad calibrada.

## Evidencia auditada

| Bloque | Cobertura e interpretación |
|---|---|
| Barrido de tamaños | 21 tamaños × 47 condiciones por clasificador; 987 filas SVM y 987 ResMLP, seis datasets; 42 puntos medios reconstruidos. |
| Top-4/SVM | Macro-F1 medio por dataset 0,936554, frente a máximo descriptivo 0,936764 en k=10; 15,42 % de dimensiones medias respecto de 21 bloques. |
| Top-4/ResMLP | Macro-F1 0,933077; máximo descriptivo en k=5, 0,935195. |
| Pasos y ganancias marginales | Ocho pasos experimentales, ejemplo real de concatenación y 252 puntos dataset/clasificador/tamaño. SVM gana 1,911 puntos de F1 de uno a cuatro y solo 0,021 más hasta el máximo en diez; hay aumentos y pérdidas después de cuatro. |
| Cascada histórica | 27 condiciones SVM, 31.984 observaciones de prueba con imágenes reutilizadas; rescates de uno a ocho bloques. Se verificó la identidad de predicción del mismo rescate en todos los casos derivados. |
| Rescate con los bloques del Top-4 del barrido | Cinco condiciones: DTD 8/10, FMD folds 2/3, CUReT A→B. La identidad de bloques no acredita identidad de todos los ajustes entre archivos. Hay ganancias, pérdidas y empates. |
| Comparadores externos | Top-4/SVM y adaptaciones externas, F1 y tiempos de las mismas llamadas online; cobertura incompleta no produce medias de dataset completas. |
| Trazabilidad nueva | 124 fuentes experimentales SHA-256; salidas, scripts y versión del manuscrito con hashes. |

El barrido sin N-gramas no es Completa-22. Se distinguen B20, B21 con
N-gramas/sin BEiT, B21 con BEiT/sin N-gramas y B22. Las decisiones surgidas
tras observar tests mantienen carácter exploratorio.

## Definiciones que se conservan

| Variante | Definición |
|---|---|
| Top-4 fijo | k=4; los cuatro descriptores pueden variar por condición y clasificador. |
| Top-k histórico | k heredado del GFS de la condición y composición por ranking individual. |
| Uso directo | Ejecutar el Top-k fijado sin una base adicional innecesaria. |
| Versión optimizada por margen | Ejecutar la base y activar el mismo Top-k si el margen es menor o igual al umbral aprendido; reutilizar solo bloques idénticos. |
| Rescate de ensamble | Otra variante estudiada; no acredita por su nombre identidad con el rescate Top-4. Se conserva como complemento. |

No se sustituyó la optimización por margen por una compuerta nueva pendiente
de desarrollo. La idea de aprender otra compuerta optimizando F1 es trabajo
futuro distinto de la política que ya tiene evidencia.

## Reservas y próximos pasos

| Prioridad | Pendiente concreto | Restricción |
|---|---|---|
| 1 | Revisar redacción y correspondencia de afirmaciones con los autores y tutor. | Borrador completo, no aprobación declarada por el asistente. |
| 2 | Conciliar discrepancias Top-4 histórico/online, especialmente Soil, y variantes KTH. | No escoger la cifra favorable ni inventar una causa. Preservar archivos. |
| 3 | Delimitar comparaciones físicas del mismo Top-k directo/margen y resolver discrepancias de representación CUReT/Soil. | Los costos proyectados no son latencia física; piloto no acredita panel íntegro. |
| 4 | Inventariar controles faltantes de Top-4 más N-gramas y complementariedad. | No atribuir cobertura inexistente ni omitir condiciones. |
| 5 | Mantener DeepLumina en revisión por no convergencia y DTD incompleto. | Sin retry científico automático ni relajación de tolerancias. |
| 6 | Solo después de conciliar y congelar recetas, preparar condiciones nuevas necesarias. | No repetir paneles cerrados ni tareas parciales/requires_review. |

Antes de cualquier benchmark nuevo: revisar procesos, estados, logs y lock;
congelar bibliotecas, pesos, semillas, particiones y presupuesto. F1 y
latencia salen de las mismas llamadas batch1. Un benchmark GPU, CPU dos
hilos y sin fits/extracciones concurrentes al cronometraje. No VisTex,
descargas grandes sin revisar alcance, contacto a autores ni servicios
pagos. Conservar datos ya observados y reservas KTH/DTD.

## Archivos de referencia

- [PDF vigente](../../paper/tesis.pdf), [fuente](../../paper/tesis.tex) e [índice del manuscrito](../../paper/README.md).
- [Auditoría nueva](../../results/analysis/topk_margin_rewrite_20261113_v1/summary.json).
- [Primer inventario de curvas](../../results/analysis/topk_margin_scope_20261113_v1/summary.json).
- [Plan maestro histórico](PLAN_MAESTRO_ACTUALIZADO_2026-11-04.md).
- [Conciliación del panel](../../results/analysis/reconciliation_full_panel_20261104_v1/INFORME.md).
- [Cascada histórica y alcance de costos](../AVANCE_CASCADA_COSTO_CONSCIENTE.md).

No se crearon commits ni se realizó push en esta reescritura.

## Ronda ARS aplicada después de la reescritura

El autor aprobó REV-01 a REV-08. Se aplicaron 12 operaciones en siete fuentes LaTeX mediante el aplicador nativo ARS; 300 de 311 bloques originales permanecieron byte a byte. La revisión posterior confirmó las ocho mejoras, las 26 pruebas pasaron en 14,10 s y el PDF de 82 páginas compiló y fue revisado visualmente. Las tasas interna y externa, los costos proyectados de selección y evaluación, el ejemplo del umbral y los parámetros quedan identificados con precisión. El método optimizado conserva su lugar central y las reservas científicas permanecen abiertas.

[Informe vigente de revisión ARS](REVISION_ARS_TOPK_MARGEN_2026-11-13.md). El corte anterior de 81 páginas y su manifiesto conservan su alcance histórico. No se ejecutaron nuevos experimentos, commits ni push.
