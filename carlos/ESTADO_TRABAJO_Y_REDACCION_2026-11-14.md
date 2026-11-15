# Qué escribimos y en qué estamos trabajando

**Actualizado:** 15 de noviembre de 2026, America/Asuncion.

**Cierre posterior vigente:** E1/E2 completo en 27/27 condiciones y seis
datasets, con 98 pruebas aprobadas. Se conservaron 25 casos y se completaron
solo dos KTH tras validar EVA-02/SigLIP con el umbral original. El PDF de 87
páginas todavía refleja el corte anterior; falta integrar el cierre nuevo.
[Informe y tabla de seis datasets](../docs/fsc_tex/CIERRE_FIDELIDAD_KTH_E1_E2_2026-11-15.md).

El trabajo está organizado alrededor del título acordado:

> Concatenación Top-k de descriptores para clasificar texturas: comparación del uso directo y la activación por margen

El recorrido es primero explicar cómo construimos y comparamos Top-k, con
atención a Top-4, y después estudiar cómo optimizamos su ejecución mediante
la activación por margen. Ambas partes siguen en el cuerpo principal.

## 1. Qué escribimos

Reescribimos el borrador de tesis, su portada, los resúmenes en español e
inglés y los siete capítulos. La versión compilada vigente tiene **87 páginas**,
con accuracy como métrica principal y la ampliación E1/E2 del 15-11.

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
Después de esa entrega, el commit `484572a` incorporó las respuestas al paper
breve y actualizó su PDF. El commit `bb0ef4e` añadió los cálculos propios del
paper y la lista de experimentos pendientes. Ambos ya se integraron a esta copia.

## 4. Qué estamos haciendo ahora

El trabajo vigente es **integrar el cierre experimental completo en el texto
y preparar el protocolo de latencia online**. Accuracy media: 94,4449 %
directa y 94,4581 % por margen; p exacto=0,5625 y adquisición proyectada
75,00 % menor. Las cifras anteriores de cinco datasets se conservan abajo
como recorrido del mismo día, no como cobertura vigente.

Se completó una revisión CPU de las entradas EVA-02/SigLIP de KTH. En las
33 imágenes congeladas de cada red se demostraron diferencias entre el
preprocesamiento histórico reconstruido y el online que falló. Hay adaptadores
candidatos y una propuesta de validación preparada, sin inferencia neuronal
nueva; no equivale a fidelidad recuperada. E1/E2 conservan 25/27 condiciones.
El [informe](../docs/fsc_tex/REVISION_FIDELIDAD_KTH_2026-11-15.md) precisa
hallazgos y reservas, y la [propuesta](../docs/fsc_tex/PROTOCOLO_VALIDACION_KTH_CORREGIDA_2026-11-15.md)
define el siguiente paso pendiente de decisión sobre los fallos científicos.

La etapa actual es **revisar la tesis actualizada y los resultados E1/E2 con
los autores y tutor**. Las respuestas técnicas ya están incorporadas al paper
breve; se mantiene la distinción entre Top-4 fijo y Top-k de tamaño heredado.
La tesis principal ahora usa accuracy; los borradores de artículos conservan
su versión hasta que el equipo incorpore este cambio.

El paper separa las métricas históricas, los costos proyectados y las
latencias físicas; conserva las pérdidas y señala reservas. Ya están
disponibles en [analisis_paper](analisis_paper/README.md) los cálculos de la
familia estadística de tres métodos, el F1 **OOF del entrenamiento** de la
etapa barata elegida (27 condiciones) y el p95 de las llamadas reunidas
(36 grupos). El F1 de la etapa barata sola **en test** sigue pendiente;
no se reemplaza con el valor OOF en el archivo histórico. La ampliación E1
sí guarda y reporta las predicciones de todas sus bases solas en test.

## 5. Qué falta como experimento específico

La lista vigente es [EXPERIMENTOS_PENDIENTES.md](EXPERIMENTOS_PENDIENTES.md).
Sus ocho entradas incluyen un caso condicional y dos mediciones opcionales;
no son ocho requisitos igualmente necesarios para terminar el texto.

| Experimento | Estado al corte |
|---|---|
| E1 / B1: Top-4 fijo directo/por margen | Cerrado y auditado: 27/27, seis datasets y KTH 4/4. Los fallos y el corte previo se conservan en sus carpetas. |
| E2 / B2: margen frente a puntuación máxima y entropía | 486 filas auditadas de las 27 condiciones; consolidados y contrastes de seis datasets completos. |
| E3: reconciliar la cascada histórica de KTH | Pendiente solo si se conserva esa comparación como central y no se hace E1. E1 con el protocolo corregido puede cubrir esa necesidad. |
| E4 / B3: misma cascada con ResMLP | Pendiente; la política ResMLP del panel de ensamble es otra comparación. |
| E5 / B4: Top-4 fijo más N-gramas | Pendiente como control específico; las ablaciones existentes no lo sustituyen. |
| E6: diagnóstico de ViT-B/16 | Discrepancia localizada; causa primaria pendiente. Diagnosticarla no valida retrospectivamente las mediciones históricas. |
| E7: memoria máxima de GPU por política | Opcional; no registrada como comparación separada de esas políticas. |
| E8: variación de Top-4/ResMLP entre equipos | Opcional; comparación controlada no medida. |

La decisión inicial era escribir con lo disponible. En las actualizaciones
de redacción y auditoría del 13–14 de noviembre no se hicieron nuevas
corridas. El 15-11 Joaquín autorizó E1/E2 y se ejecutó esa ampliación;
los demás experimentos específicos siguen pendientes.

La preparación del 14-11 identificó entradas y costos faltantes. El 15-11 se
implementó y probó el ejecutor, se midió el perfil KTH y se completaron los
casos viables. EVA-02 y SigLIP fallaron el mínimo de fidelidad congelado y
quedaron en revisión, sin repetición. La media de accuracy de cinco datasets
es 0,941839915 directa y 0,941830218 por margen; el costo por componentes
proyecta 74,87 % de reducción. No se denomina ahorro físico online.

[Informe actualizado del 15-11](../docs/fsc_tex/AVANCE_ACCURACY_E1_E2_2026-11-15.md).
Pasaron 52 pruebas de trazabilidad, métricas y contratos. La revisión visual
cubre las 87 páginas del PDF vigente.

## 6. Dónde seguir

| Material | Archivo |
|---|---|
| Tesis actualizada | [PDF](../paper/tesis.pdf) y [fuente LaTeX](../paper/tesis.tex) |
| Paper breve | [Fuente](main.tex) y [PDF del borrador](main_topk_margen.pdf) |
| Respuestas técnicas y pendientes | [CONSULTAS_JOAQUIN.md](CONSULTAS_JOAQUIN.md) |
| Experimentos por decidir | [EXPERIMENTOS_PENDIENTES.md](EXPERIMENTOS_PENDIENTES.md) |
| Cálculos ya añadidos al paper | [Índice y fuentes](analisis_paper/README.md) |
| Plan vigente | [Plan Top-k y margen](../docs/fsc_tex/PLAN_TOPK_MARGEN_2026-11-13.md) |
| Cambios ARS aplicados | [Informe de revisión](../docs/fsc_tex/REVISION_ARS_TOPK_MARGEN_2026-11-13.md) |
| Evidencia de las respuestas | [Resumen de auditoría](../results/analysis/consultas_joaquin_20261114_v1/summary.json) |
| Las 94 trazas canónicas | [Manifiesto CSV](../results/analysis/consultas_joaquin_20261114_v1/canonical_panel_calls_94.csv) |

El commit `e9f9902` publicó la tesis y las respuestas técnicas. Este documento
añade el panorama de redacción, evidencia disponible y trabajo pendiente.
