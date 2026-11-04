# Medición de controles y métodos completos de los papers

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: plan.
- Origin Date: 2026-10-27 (America/Asuncion).
- Verification Status: UNVERIFIED para latencia; inspección de recetas y fuentes realizada.
- Version Label: physical_comparators_plan_v1.

## Alcance acordado

El autor eligió **ambos**: controles del proyecto y métodos completos de los papers de referencia. Este documento prepara esa comparación, no anuncia tiempos medidos ni autoriza mensajes a autores. No se modifica la selección archivada ni se sobrescriben protocolos, predicciones, fallos o resultados previos. Los nuevos resultados de preparación quedan aparte.

Pregunta: ¿qué compromiso calidad–latencia presenta la ruta con selección y margen frente a controles estáticos y métodos publicados ejecutados localmente bajo un régimen comparable? No se presupone que la propuesta gane. La calidad debe corresponder al mismo método cronometrado.

## Panel local preparado

Recetas por condición y pliegue: Individual, Completa-22, Top-k con tamaño GFS, GFS libre, ensamble permanente, ensamble estático seleccionado, ruta adaptativa del pool previo y ruta adaptativa del pool con diversidad. Los cuatro últimos conservan el punto de presupuesto interno de 60 ms conocido en desarrollo, registrado como parámetro y no como nombre comercial del método. No se lo presenta como presupuesto óptimo ni límite físico por imagen.

Preparación inicial: FMD/42 y Outex/123, tres pliegues productores por condición. Eso produce 48 recetas (8 × 3 × 2), **no 48 mediciones ni 48 datasets**. El cronometraje piloto previo estaba delimitado al primer pliegue, seis filas deterministas y tres repeticiones. Preparar los otros pliegues no implica que ya se hayan ejecutado ni que ese piloto baste para publicar distribuciones de latencia.

`scripts/prepare_physical_comparison_panel.py` comprueba que las fuentes concatenadas y de ensamble remiten al mismo fit y validación productores. Verifica los archivos portadores de recetas contra sus auditorías, y esas auditorías contra el panel conjunto previo. Conserva orden de características y multiplicidad de votos. Genera un manifiesto nuevo con huellas, sin GPU, entrenamiento, selección por resultados externos ni cronometraje. No vuelve a auditar el corpus completo de embeddings. El ejecutor físico anterior solo admite cuatro rutas; el manifiesto extendido todavía necesita conectarse a un ejecutor que valide todos los comparadores.

## Métodos de referencia y barreras de reproducción

| Trabajo | Unidad que realmente hay que cronometrar | Estado de preparación |
| --- | --- | --- |
| Scabini et al., J. Imaging 11, 304 | Backbone y checkpoint exactos, preprocesamiento, representación y clasificador. Separar extracción de predicción completa. | La biblioteca permite iniciar la auditoría de backbones. Coincidir en nombre de arquitectura no basta: faltan cerrar equivalencias de checkpoint, entrada, pooling y clasificador. Su media publicada de tres clasificadores no es nuestro SVM solo. |
| Neshov et al., Electronics 14, 4779 | Agregación de cuatro capas, GAP, concatenación y MLP entrenada. | Nuestro BEiT-v2 final de 768 dimensiones **no** reproduce esta agregación de 3.072 dimensiones. Requiere adaptador de capas y cabeza MLP/entrenamiento documentados. La declaración de disponibilidad remite a consultas al autor; no se ha localizado aquí una implementación oficial completa. |
| RGB Pixel N-grams | Codificación y clasificación de la receta original completa. | El bloque `rgb_ngram_svd` de la tesis no se etiqueta automáticamente como el método completo del paper. Auditar receta original antes de cronometrar. |
| AsTexNet | Representación híbrida de escalas, rama profunda, compresión y clasificación de su receta completa. | El PDF declara detalles de implementación disponibles por solicitud al autor. Su tabla de tiempos no equivale a una medición local comparable. Código/checkpoint completos no verificados aquí. |
| HyTexNet | Codificación local guiada por percentiles, DenseNet-121, fusión y clasificación. | El PDF declara código/datos procesados disponibles por solicitud razonable. No basta con cronometrar DenseNet-121 solo. Código/checkpoint completos no verificados aquí. |
| Compact color–texture (2015), selección independiente de aplicación (2010), integración de ventanas (2007), DeepLumina (2022), multiescala (2023), LBP + CellNNs (2024) | Receta completa de cada trabajo, no solo el componente disponible más parecido. | Inventariados desde `docs/referencias/README.md`. Verificación de implementación, granularidad de tarea, particiones y costo pendiente. El trabajo por píxel no debe mezclarse sin adaptación declarada con clasificación por imagen. |

Los dos primeros trabajos corresponden a los dos papers principales usados originalmente para la comparación. Los otros quedan en el inventario, sin afirmar disponibilidad, reproducción o cobertura experimental. Una búsqueda de código sin hallazgo no demuestra que el código no exista. No se enviaron correos ni solicitudes a autores.

Fuentes primarias: <https://www.mdpi.com/2313-433X/11/9/304>, <https://www.mdpi.com/2079-9292/14/23/4779>, y los PDF locales de AsTexNet/HyTexNet. El acceso directo a MDPI devolvió 429; se usaron el contenido indexado y las copias aportadas, sin insistir para eludir el límite. La versión arXiv del survey no se sustituye silenciosamente por su versión de revista.

## Etiquetas obligatorias

1. **Reproducción del método publicado**: implementación/capas/checkpoint/cabeza, transformaciones y protocolo identificados. Registrar modificaciones aunque se use código del autor.
2. **Adaptación al benchmark común**: cualquier sustitución de clasificador, partición, dimensión, pesos o preprocesamiento queda declarada. No adjuntar el F1 publicado como si fuera el de la adaptación.
3. **Componente aislado**: tiempo de un extractor; no se presenta como latencia completa de AsTexNet, HyTexNet, agregación multicapa u otro sistema.
4. **Pendiente/no reproducible aún**: se conserva como tal, sin inventar latencia, inferirla desde parámetros/FLOPs ni tomar el tiempo de otra GPU.

## Protocolo de medición propuesto

- Pilotar primero fidelidad de todos los extractores y del clasificador. Para rutas existentes, conservar el criterio ya fijado (error absoluto máximo normalizado ≤ 1e-4, clases y compuertas iguales). Un diagnóstico parcial de DINOv2-small no abre la puerta para todo el sistema. Una reproducción nueva necesita su propia evidencia de fidelidad; no puede exigir concordancia con un archivo que no existe.
- Mantener imágenes/manifiestos y política de muestreo comunes, independientes de errores y márgenes. Separar selección/entrenamiento de inferencia. No repetir la búsqueda para favorecer el tiempo observado.
- Medir regímenes identificados: batch 1 para latencia y, si se añade, throughput por separado. Mantener FP32/precisión de referencia; una variante FP16 requiere otro punto con calidad propia. No sustituir la resolución necesaria de un método sin declararlo.
- Calentamiento fuera del cronómetro, orden intercalado por imagen y método, sincronización CUDA antes y después, repeticiones y unidades registradas. Mantener CPU/hilos documentados. No cronometraje concurrente con entrenamiento ni extracción ajenos.
- Distinguir: (a) imagen ya decodificada a clase, (b) archivo a clase incluyendo lectura/decodificación, (c) arranque frío/carga de modelos. Misma política de decodificación para competidores dentro de cada régimen. El ejecutor antiguo decodifica por extractor; eso necesita decisión explícita antes del benchmark ampliado.
- Registrar extracción real de la unión, normalización/concatenación/transferencia, SVM/MLP, agregación y compuerta. No compartir embeddings ya calculados entre competidores; sí reutilizar bloques dentro de un mismo método.
- Declarar residencia de modelos. Si Completa-22 no cabe en VRAM, marcarlo y ensayar **otro régimen** bajo demanda con la carga incluida. No comparar un método con todo residente y otro con cargas excluidas. Registrar VRAM/RAM pico sin convertirlas en energía consumida.
- Informar media, mediana, p95, distribución pareada por imagen, porcentaje derivado y llamadas reales. Repeticiones no son imágenes adicionales. El tiempo de entrenamiento/selección se reporta aparte; no se usa `time_s` de validación cruzada como inferencia por imagen.
- No inferir significancia o equivalencia desde seis imágenes ni reutilizar p-valores históricos. Antes de una corrida publicable se fija cobertura, repeticiones y contrastes de latencia; la incertidumbre conserva su unidad por imagen/dataset.

## Estado observado y siguiente paso

Consulta de recursos del 27-10: RTX 4060, 8.188 MiB totales, aproximadamente 4.521 MiB ocupados y 55 % de utilización. Es una observación puntual, no prueba de exclusividad ni un tiempo de inferencia. No se interrumpe actividad ajena ni se publica un benchmark bajo esa contención.

El diagnóstico anterior de DINOv2-small pasó cuatro comparaciones GPU; permanecen los fallos CPU y la falta de fidelidad online completa. No se reintentan automáticamente como si estuvieran resueltos.

Secuencia de trabajo: preparar las recetas locales sin cambiar decisiones; resolver paridad y régimen de ejecución; conectar Top-k/GFS/Individual/Completa al ejecutor ampliado; cerrar una receta y cabeza entrenada por método externo; pilotar cada método; congelar la corrida publicable antes de medir. El panel externo no está listo solo por figurar en esta tabla. Los adaptadores faltantes se desarrollan sin modificar el protocolo físico anterior.

## Comando de preparación (sin medición)

```bash
PYTHONPATH=src .venv-confirmatory/bin/python scripts/prepare_physical_comparison_panel.py \
  --protocol docs/fsc_tex/PLAN_MEDICION_COMPARADORES_Y_PAPERS_2026-10-27.md \
  --output results/analysis/physical_comparison_preparation_20261027_v2
```

La salida exige directorio nuevo. Cualquier error de procedencia se conserva como bloqueo de preparación, no como resultado de rendimiento. Este plan y manifiesto no sustituyen la implementación ni la medición de los métodos externos.

La primera preparación `physical_comparison_preparation_20261027` se conserva como registro inicial. La revisión `v2` añade comprobación explícita de los hashes de todos los archivos portadores de recetas contra sus auditorías. Ninguna de las dos contiene latencias medidas.
