# Avance semanal de tesis — reunión del 2 de noviembre de 2026

## Apertura de 30 segundos

“Esta semana cerramos la medición de nuestras cinco estrategias en seis datasets, con SVM y ResMLP: 94 de 94 condiciones auditadas. Ahora medimos macro-F1 y latencia individual con las mismas llamadas reales. El adaptativo tiene menor tiempo medio que la concatenación completa en los doce pares dataset–clasificador, pero no gana F1 en todos. También evaluamos dos sistemas externos adaptados; cada uno tiene cinco datasets completos y una condición pendiente. Todavía no afirmamos superar los porcentajes originales de los papers.”

## Guion de 9–10 minutos

1. **Estado general — 45 s.** Mostrar el cierre 94/94. Separar “panel propio terminado” de “comparación externa todavía en ampliación”. No decir que la tesis o todas las réplicas están terminadas.
2. **Pregunta y propuesta — 1 min.** Seleccionar representaciones en entrenamiento y adquirir otras solo cuando el margen de la primera decisión lo justifica. La base no es una red universal fijada a mano. Se distingue selección de representaciones de rescate condicional. El presupuesto B60 pertenece al modelo de selección, no asegura 60 ms por imagen.
3. **Trabajo de la semana — 1 min.** Se pasó de costos proyectados a inferencia física individual archivo→clase; se completó la cobertura, se conservaron errores y se auditaron predicciones, tiempos y procedencia. Las 47 particiones y dos cabezas producen 94 condiciones; las cinco estrategias producen 470 filas condición×método. Hay 362.640 llamadas primarias y 9.400 observaciones DTD adicionales separadas, no nuevas condiciones.
4. **Resultados SVM — 1 min.** FMD: adaptativo 0,9776 y 38,63 ms frente a completa 0,9651 y 1.759,50 ms. Contraejemplo: KTH 0,9390 frente a 0,9599. No esconder la pérdida de calidad. No presentar una media conjunta de datasets.
5. **Resultados ResMLP — 1 min.** FMD: 0,9760 / 36,35 ms frente a 0,9577 / 1.759,70 ms. Outex: 0,9609 / 21,65 ms frente a 0,9477 / 1.563,18 ms. En Soil y KTH el F1 adaptativo es menor que el completo. Son resultados descriptivos.
6. **Comparación externa — 1,5 min.** HyTexNet y LBP+dCellNN son adaptaciones de sistemas completos con recetas explícitas, no componentes aislados ni reproducciones fieles de porcentajes publicados. Cada uno lleva 46/47 condiciones, pero no los mismos datasets completos: falta HyTexNet/Outex y falta una condición CellNN/FMD. Mostrar “sin media completa” donde corresponde. Cada sistema conserva su propio clasificador; no confundirlos con las dos cabezas locales.
7. **Interpretación — 1 min.** La eficiencia observada es el resultado más consistente frente a Completa-22, con calidad dependiente del dataset. No equivale a dominar las otras cuatro estrategias. Una media baja oculta colas: FMD/SVM adaptativo tiene p95 aproximado de 270,77 ms, aunque su media es 38,63 ms.
8. **Bloqueos y límites — 1 min.** HyTexNet/Outex se detuvo en preflight por hash faltante. CellNN/FMD 42/f0 falló serializando después del ajuste; no tiene llamadas online. Neshov falló una comprobación científica de paridad batch 1/8. Se preservaron las evidencias; no se relajaron tolerancias ni se reintentaron. El hardware es compartido y no hay inferencia estadística global.
9. **Cierre — 45 s.** Lo defendible hoy es el panel propio completo y trazable y una comparación externa honestamente delimitada. Sigue resolver revisiones bajo las reglas existentes, cerrar recetas verificables de otros sistemas y definir contraste confirmatorio. La integración al manuscrito sigue pendiente.

## Preguntas previsibles

**¿Ya terminamos nuestras mediciones?** Sí: 94/94 condiciones locales, con reservas documentadas. No deben repetirse por preparar esta exposición.

**¿Ya replicamos los papers?** Hay dos sistemas completos adaptados con cinco datasets completos cada uno. No hay reproducción fiel cerrada de los porcentajes originales. Neshov está en revisión y otros papers necesitan recetas o dependencias verificables.

**¿El nuestro es mejor?** Frente a Completa-22 tiene menor latencia media en los doce pares, con ganancias y pérdidas de macro-F1. Los comparadores externos adaptados tienen menor F1 en las comparaciones disponibles, pero tiempos del mismo orden y a veces menores. Eso no prueba superioridad frente a los métodos originales de la literatura.

**¿Por qué no usar solo el promedio?** F1 se promedia por partición; el tiempo se agrega por llamada y también se conservan mediana/p95. Son unidades de agregación diferentes. Un panel incompleto no tiene media completa.

**¿B60 significa que ninguna imagen supera 60 ms?** No. Es el presupuesto interno del modelo de selección. La medición individual muestra una cola de latencias mayor.

**¿Hay significancia estadística?** No se efectuó inferencia global. Los folds y semillas no deben tratarse como datasets independientes. Antes de afirmaciones inferenciales hace falta un protocolo confirmatorio adecuado.

**¿Se cambió el método para que funcionara?** No se autorizaron cambios para superar los fallos científicos. Las correcciones de infraestructura se probaron y solo se despacharon tareas no ejecutadas o recuperaciones expresamente autorizadas, conservando intentos anteriores.

**¿Qué reservas debemos mencionar?** KTH usa muestras físicas 3 train / 1 test; no se afirma equivalencia con la cascada histórica. DTD conserva la medición física anómala original y observaciones adicionales separadas. Outex/Soil incorporan la representación DeiT fija mediante una enmienda documentada. No hay aislamiento físico del hardware ni prueba de garantía de despliegue.

## Fuentes y respaldo

Rutas relativas a `/home/joaquin/tesis_claude`:

- `results/analysis/blocker_resolution_20261101/full_panel_online_v1/coverage.json`: cierre 94/94 y recuento de llamadas.
- `results/analysis/blocker_resolution_20261101/full_panel_online_v1/dataset_summary.csv`: las 60 filas dataset×cabeza×estrategia, con macro-F1, media, mediana y p95.
- `results/analysis/blocker_resolution_20261101/full_panel_online_v1/condition_summary.csv`: detalle de las 470 filas condición×método.
- `results/analysis/external_adaptation_coverage_20261102_v1/coverage.csv`: cobertura y medias externas solo donde el dataset está completo.
- `results/analysis/external_adaptation_coverage_20261102_v1/provenance.json`: fuentes selladas de los agregados externos.
- `.build/sources.json`, en el directorio padre de este guion: hashes de los insumos de la presentación.

El PowerPoint contiene tablas editables y notas por diapositiva. Esta preparación no lanzó benchmarks, repitió condiciones, modificó el manuscrito ni hizo commits.
