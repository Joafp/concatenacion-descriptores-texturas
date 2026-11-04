# Piloto de desarrollo de Neshov/BEiTv2 en FMD

## Material Passport

- Origin Skill: ARS experiment-agent.
- Origin Mode: run, continuación solicitada por el autor.
- Origin Date: 2026-10-28, America/Asuncion.
- Verification Status: PENDING antes de ejecutar el piloto.
- Version Label: neshov_fmd_matched_development_v1.

## Alcance fijado antes de extraer

Continuación de la reproducción documentada en `REPRODUCCION_NESHOV_BEITV2_2026-10-27.md`. La segunda comprobación funcional, guardada en `results/analysis/neshov_beit_functional_smoke_20261028/status.json`, pasó: checkpoint cargado estrictamente, doce índices posicionales regenerados idénticos y características de forma 2 × 3.072. Su cabeza estaba sin entrenar; no se toman sus scores como calidad.

Se ejecuta ahora una **adaptación al benchmark de desarrollo común**, no una reproducción de los porcentajes del paper ni de su FMD 10 × 10-fold. Dataset FMD; semilla y partición externa heredada 42; tres pliegues productores del archivo `integration_v11/replication_20261026/FMD_s42/paired/fold*.json`. Sus 800 imágenes de desarrollo se validan exactamente una vez cada una. Las 200 imágenes externas quedan fuera de extracción, ajuste y evaluación. No se añaden otros datasets o semillas.

## Modelo y entrenamiento

- Mismo checkpoint BEiTv2 y decisiones de capas/pooling/preprocesamiento del prototipo, registradas el 27-10: capas 2,5,8,11 interpretadas desde 1; GAP sin CLS; 3.072 valores, sin L2 o estandarización adicionales; resize 224 × 224 bilineal y normalización ImageNet. Versiones locales distintas de la fuente, declaradas.
- Backbone congelado y en evaluación. Se pueden cachear características de las 800 imágenes porque el extractor no se ajusta con ninguna de ellas. Cada MLP recibe exclusivamente etiquetas y características del fit de su propio pliegue.
- FC(64), BN, ReLU, Dropout(0,2), FC(10). CrossEntropyLoss con logits. Adam lr 0,001, weight decay 0,0001, betas (0,9; 0,999); beta2 es el valor por defecto no detallado por el artículo.
- Exactamente 100 épocas por cabeza, batch 32, shuffle y semilla 42. Se conserva la cabeza de la **época final**, sin early stopping ni selección del mejor resultado de validación. Sin grid search o ajustes posteriores al F1 observado.
- CPU con dos hilos; extracción por lotes de ocho, independiente del batch de entrenamiento. No se ocupa la GPU compartida. Esto no reproduce el régimen de hardware del paper y no acredita latencia de inferencia.

## Integridad y salidas

Verificar hashes de manifiesto y pliegues contra la auditoría FMD/42; comprobar filas, exclusión de grupos, unión de fit/validación y hashes del desarrollo/test externo. Verificar cada imagen de desarrollo antes de extraer. Guardar receta y hashes de código/protocolo antes de la extracción. No sobrescribir intentos o resultados previos.

Salida nueva: `results/exploratory/reference_papers/neshov_fmd_development_20261028`. Conservar estado, características y orden de filas, hashes de imágenes/checkpoint, tres cabezas, logits por pliegue, historial de pérdida de entrenamiento, métricas y 800 predicciones OOF. Informar macro-F1 agrupado de las 800 imágenes, accuracy y media de F1 por pliegue como cantidades diferentes.

Una comparación posterior con nuestras rutas usará predicciones de **esa misma condición y esas mismas filas**, no las medias de tres semillas ni la tabla externa de seis datasets aportada por el compañero. No se reutilizan p-valores históricos ni se anuncian equivalencia o superioridad estadística a partir de este piloto.

## Ejecución y vigilancia

```bash
timeout 1200s .venv-confirmatory/bin/python scripts/run_neshov_fmd_development.py \
  --protocol docs/fsc_tex/PROTOCOLO_PILOTO_NESHOV_FMD_2026-10-28.md \
  --output results/exploratory/reference_papers/neshov_fmd_development_20261028
```

Techo operativo de 20 minutos para este piloto. Se vigilan el proceso y `status.json`, con progreso de extracción y cambio de pliegue. No hay reintento automático tras fallo o timeout. La falta de un proceso activo no se confunde con terminación correcta: exige estado final y predicciones completas.

Este archivo conserva su estado previo a ejecución. Los resultados se registrarán aparte; no se cambia el protocolo al conocer el desempeño.
