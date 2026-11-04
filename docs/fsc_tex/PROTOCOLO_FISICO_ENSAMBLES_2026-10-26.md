# Piloto físico de rutas de ensamble congeladas

## Material Passport

- Origin Skill: ARS experiment-agent, ejecución local guiada.
- Origin Mode: run.
- Origin Date: 2026-10-26.
- Verification Status: PENDING; este protocolo no acredita una medición terminada.
- Version Label: frozen_ensemble_physical_cpu_pilot_v1.

## Alcance autorizado

El autor solicitó ejecutar los pasos acordados y preparar la presentación. Se implementa un piloto de fidelidad e inferencia física sin cambiar la selección archivada. No es una nueva búsqueda de políticas, no se añaden extractores y no se evalúa el test externo. Los resultados previos no se sobrescriben.

Cuatro rutas: ensamble de diversidad de Carlos permanente, ensamble estático B60, cascada de relevancia/B60 del pool anterior e híbrido relevancia/B60 con miembros de Carlos. Se conservan miembros, multiplicidades, escalas de scores, base y umbral por pliegue. N-grams ocupa al final la misma posición que en `block_matrices` y ajusta SVD solo sobre las filas del fit productor. El margen activa rescate estrictamente cuando es menor que el umbral.

Condiciones fijadas para el piloto: FMD/42 y Outex/123, primer pliegue productor, seis filas uniformemente espaciadas en el orden de validación, tres repeticiones pareadas. El orden de las cuatro políticas se permuta con semilla 20261026. Estas filas no se eligen por calidad ni por favorecer el enrutamiento. No se estima F1 general a partir de seis imágenes ni se cuentan repeticiones como imágenes independientes.

## Dispositivo y restricciones

El corte de recursos muestra la RTX 4060 de 8 GB con aproximadamente 6,5 GB ocupados por actividad ajena. No se interrumpe esa actividad ni se confunde su contención con un benchmark GPU limpio. El piloto inicial usa **CPU**, con dos hilos BLAS y checkpoints locales en modo offline. Sus tiempos, si pasan los controles, serán específicos de esa configuración CPU y no se presentarán como aceleración GPU ni como validación del perfil proyectado en RTX.

El ejecutor mantiene los extractores cargados en memoria CPU, excluyendo carga de checkpoints y ajuste de SVM. Cada tiempo incluye decodificación por extractor adquirido, preprocesamiento, forward, conversión a vector, clasificación y decisión de ruta. Cada bloque se extrae como máximo una vez por imagen y política; cada modelo único se evalúa una vez, conservando multiplicidades en el voto. No comparte características entre políticas competidoras. Se excluyen dos filas de calentamiento por política. La memoria residente y la disponibilidad de checkpoints son límites de ejecución, no resultados predictivos.

## Puertas de fidelidad

1. Comprobar hashes de los artefactos auditados, particiones y fuentes de imágenes.
2. Reajustar SVM con el mismo fit productor y escala calculada solo con entrenamiento.
3. Reproducir exactamente las clases y compuertas archivadas usando características en caché.
4. Antes de cronometrar, comparar características extraídas de las primeras dos filas: misma forma y error absoluto máximo ≤ 1e-4 sobre vectores normalizados.
5. Durante todas las mediciones, exigir igualdad de clase y activación respecto de la ruta archivada. Si falla, no publicar tiempos como válidos ni cambiar umbrales/checkpoints para hacerlos pasar.

El margen de paridad es un control de fidelidad numérica del piloto, no una prueba estadística de equivalencia. Las verificaciones no garantizan que la reconstrucción sea posible: algunos checkpoints/preprocesamientos históricos pueden faltar o diferir, particularmente componentes con poolers inicializados aleatoriamente.

## Salidas y límite

`scripts/benchmark_frozen_ensemble_routes.py` exige una carpeta de salida nueva. Guarda rutas y filas antes de extracción y mantiene `status.json`; si completa, añade `paired_timings.csv` con observaciones pareadas y resúmenes de media/mediana/p95. Un fallo conserva el diagnóstico y `physical_timing_validated=false`. No hay reintento científico automático.

El piloto se ejecuta con un techo operativo de 45 minutos por condición. Un límite alcanzado conserva el estado como inconcluso, no como ahorro ni derrota. Cualquier comparación física posterior en GPU requiere una sesión sin contención, las mismas puertas de fidelidad y un registro nuevo.
