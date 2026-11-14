# Qué escribimos y en qué estamos trabajando

**Actualizado:** 14 de noviembre de 2026, America/Asuncion.

El trabajo está organizado alrededor del título acordado:

> Concatenación Top-k de descriptores para clasificar texturas: comparación del uso directo y la activación por margen

El recorrido es primero explicar cómo construimos y comparamos Top-k, con
atención a Top-4, y después estudiar cómo optimizamos su ejecución mediante
la activación por margen. Ambas partes siguen en el cuerpo principal.

## 1. Qué escribimos

Reescribimos el borrador de tesis, su portada, los resúmenes en español e
inglés y los siete capítulos. La versión compilada tiene **82 páginas**.

| Parte | Contenido escrito |
|---|---|
| Introducción | Problema, objetivos y dos preguntas: qué concatenar y cuándo ejecutar la concatenación. |
| Antecedentes | Descriptores clásicos y profundos, N-gramas, selección de bloques, métodos de literatura y clasificación por etapas. |
| Método | Ranking mediante validación interna, normalización L2 por bloque, concatenación y entrenamiento de un clasificador; uso directo y activación por margen. |
| Diseño experimental | Datasets, bibliotecas, particiones, SVM/ResMLP, selección interna, métricas y distintos regímenes de medición. |
| Resultados | Barrido de k, Top-4, comparaciones con otras concatenaciones y N-gramas, adaptaciones de papers y comparación directo/margen. |
| Discusión | Interpretación de mejoras y pérdidas, complementariedad, condición de ahorro y límites de la evidencia. |
| Conclusiones | Respuestas a las dos preguntas y trabajo pendiente, con la cobertura real de los experimentos. |

Agregamos el recorrido de las pruebas, un ejemplo real de concatenación y
gráficos de calidad por número de descriptores, ganancia marginal y curvas
por dataset. Los estudios anteriores de ensamble y poda se conservan en un
anexo complementario.

La revisión ARS aprobada incorporó ocho mejoras: distinguir los costos
proyectados de selección y evaluación; precisar el criterio OOF de la
compuerta; explicar un umbral con datos reales; completar parámetros
reproducibles; identificar el piloto físico; y reforzar la condición de
ahorro, la contribución y las conclusiones. Pasaron **26 pruebas de auditoría
y software**. Este es un borrador para revisión de los autores y el tutor.

## 2. Qué evidencia ya está disponible

Los siguientes experimentos y registros existían antes de esta actualización.
Durante la redacción los reconstruimos o auditamos; no los contamos como
corridas nuevas.

| Bloque | Evidencia disponible | Alcance |
|---|---|---|
| Barrido Top-k | k=1 a 21, 47 condiciones por tamaño y clasificador: 987 filas SVM y 987 ResMLP, seis datasets. | Exploratorio; identifica calidad y dimensión al ampliar la representación. |
| Panel local online | 94 condiciones, cinco estrategias y 362.640 llamadas primarias. | F1 y tiempo de las mismas llamadas, con reservas de hardware y representación documentadas. |
| Cascada Top-k por margen | 27 condiciones SVM y 31.984 observaciones de prueba, con imágenes reutilizadas entre particiones. | Mismo rescate directo/condicional; k varía de uno a ocho. |
| Casos con cuatro bloques | Cinco condiciones cuyo rescate coincide en tamaño y bloques con el Top-4 del barrido. | Evidencia parcial de tres datasets; no un panel completo Top-4 fijo por margen. |
| N-gramas y literatura | Ablaciones de biblioteca y comparadores externos con protocolos identificados. | Distinguir adaptación local, aproximación al protocolo y reproducción fiel. DeepLumina conserva revisión pendiente. |
| Piloto físico de la cascada | Una condición por dataset, 204 imágenes y 612 pares temporales. | Modelos residentes; discrepancias de representación CUReT/Soil y reserva histórica KTH. |

Con SVM, Top-4 registra macro-F1 medio por dataset de **0,936554**, frente
al máximo descriptivo de **0,936764 en k=10**, usando aproximadamente
**15,42 % de las dimensiones** de la biblioteca de 21 bloques. La curva
muestra una opción compacta cercana al máximo medio; no demuestra que cuatro
sea óptimo en todos los casos. En FMD, cuatro alcanza el máximo medio con
ambos clasificadores; otros datasets y ResMLP presentan máximos diferentes.

## 3. Qué resolvimos para continuar el paper

Respondimos **A1–A11** de [CONSULTAS_JOAQUIN.md](CONSULTAS_JOAQUIN.md),
anotamos el estado de **B1–B4** y verificamos **D1–D2**, con rutas y cálculos.

- **Soil:** los bloques y F1 con características guardadas coinciden entre
  barrido y panel; la diferencia aparece en la extracción online,
  especialmente en ViT-B/16. La causa primaria sigue sin diagnosticar.
- **Piloto físico:** contamos las imágenes con discrepancias y separamos
  concordancia de predicciones de fidelidad de los vectores.
- **KTH:** distinguimos las correcciones del comparador temporal y de la
  selección interna. La cascada archivada no queda reconciliada por la
  existencia del control corregido.
- **Latencia:** dejamos la lista exacta de las 94 fuentes canónicas y la
  observación adicional excluida, para continuar los cálculos del paper.
- **Estadística:** comprobamos los números consultados y aclaramos que el
  control aleatorio original pertenece al piloto con ResNet-50 fijo.

Estas respuestas se basan en una auditoría de **295 fuentes con hashes**.
El borrador breve `carlos/main.tex`, su PDF y su bibliografía se conservaron
como se recibieron; las respuestas aún deben incorporarse allí por el equipo.

## 4. Qué estamos haciendo ahora

La etapa actual es **consolidar el texto del paper con la evidencia existente**:
incorporar las respuestas, mantener coherencia entre título, métodos, tablas
y conclusiones, y distinguir Top-4 fijo del Top-k de tamaño heredado.

El paper debe separar las métricas históricas, los costos proyectados y las
latencias físicas; conservar las pérdidas y señalar qué resultados tienen
reservas. Los cálculos de la familia estadística de tres métodos, el F1 de
la base sola y el p95 reunido siguen identificados en la sección C de las
consultas para continuar su integración.

## 5. Qué falta como experimento específico

| Consulta | Estado al corte |
|---|---|
| B1: panel completo Top-4 fijo directo/por margen | Pendiente. Los cinco casos coincidentes no cubren las 27 condiciones ni todos los controles pedidos. |
| B2: margen frente a puntuación máxima y entropía | No localizado como comparación pareada y auditada con ese protocolo. |
| B3: misma cascada con ResMLP | Pendiente; la política ResMLP del panel de ensamble es otra comparación. |
| B4: Top-4 fijo más N-gramas | Pendiente como control específico; las ablaciones existentes no lo sustituyen. |

La decisión registrada es continuar escribiendo con lo disponible. Estos
experimentos quedan como pendientes, sujetos a acuerdo del equipo. En las
actualizaciones de redacción y auditoría del 13–14 de noviembre **no se
hicieron nuevos entrenamientos, extracciones, predicciones ni benchmarks**.

## 6. Dónde seguir

| Material | Archivo |
|---|---|
| Tesis actualizada | [PDF](../paper/tesis.pdf) y [fuente LaTeX](../paper/tesis.tex) |
| Paper breve | [Fuente](main.tex) y [PDF del borrador](main_topk_margen.pdf) |
| Respuestas técnicas y pendientes | [CONSULTAS_JOAQUIN.md](CONSULTAS_JOAQUIN.md) |
| Plan vigente | [Plan Top-k y margen](../docs/fsc_tex/PLAN_TOPK_MARGEN_2026-11-13.md) |
| Cambios ARS aplicados | [Informe de revisión](../docs/fsc_tex/REVISION_ARS_TOPK_MARGEN_2026-11-13.md) |
| Evidencia de las respuestas | [Resumen de auditoría](../results/analysis/consultas_joaquin_20261114_v1/summary.json) |
| Las 94 trazas canónicas | [Manifiesto CSV](../results/analysis/consultas_joaquin_20261114_v1/canonical_panel_calls_94.csv) |

El commit `e9f9902` publicó la tesis y las respuestas técnicas. Este documento
añade el panorama de redacción, evidencia disponible y trabajo pendiente.
