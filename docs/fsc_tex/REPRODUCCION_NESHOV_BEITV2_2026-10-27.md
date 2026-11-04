# Inicio de reproducción: agregación BEiTv2 + MLP de Neshov et al.

## Material Passport

- Origin Skill: ARS experiment-agent, implementación inicial guiada por la petición del autor.
- Origin Mode: plan / comprobación funcional, no evaluación de calidad.
- Origin Date: 2026-10-27.
- Verification Status: ANALYZED para lectura de receta; reproducción empírica pendiente.
- Version Label: neshov_beit_reference_prototype_v1.

## Elección y alcance

El primer candidato implementable es *Improving Texture Recognition via Multi-Layer Feature Aggregation from Pre-Trained Vision Architectures*, Electronics 14 (2025), 4779, DOI <https://doi.org/10.3390/electronics14234779>. Se usa su rama BEiTv2 porque el paper especifica un checkpoint que ya está en caché. Esto es una reimplementación basada en la descripción, **no código oficial ni reproducción de sus porcentajes**.

La revisión estructural previa del PDF local pasó para sus 26 páginas, SHA256 `e9d5eb4c004e6ae17e615a0043dfdee4ef76122931848d28fd7ea49992fbec67`. Se inspeccionaron el texto de método/entrenamiento y la Figura 1 renderizada. No se afirma haber leído el artículo de manera humana por el usuario.

## Receta identificada en la fuente

| Elemento | Fuente y elección |
| --- | --- |
| Backbone | Sección 4.2: `beitv2_base_patch16_224.in1k_ft_in22k_in1k` de timm. |
| Puntos de extracción | Secciones 4.2/4.5 y Tabla 2: conjunto Shifted `[2, 5, 8, 11]`. |
| Agregación | GAP de tokens de cada representación y concatenación. 4 × 768 = 3.072 dimensiones (Sección 3.8). |
| Cabeza | Figura 1 y Sección 4.4: FC(64), BatchNorm, ReLU, Dropout(0,2), FC(K), softmax. La implementación devuelve logits al entrenar con CrossEntropyLoss. |
| Entrada | Sección 4.2: resize 224 × 224, media ImageNet `(0.485, 0.456, 0.406)` y desviación `(0.229, 0.224, 0.225)`. No reutilizar silenciosamente el transform del checkpoint si difiere. |
| Entrenamiento descrito | 100 épocas, batch 32, Adam, lr 1e-3, weight decay 1e-4, semilla 42. La mención de momentum 0,9 se interpreta como beta1=0,9 si se implementa; beta2 no está detallada. No se ha ejecutado este entrenamiento aquí. |
| Software de la fuente | timm 1.0.15, PyTorch 2.5.1. El entorno local utiliza versiones posteriores, por lo que se declara la diferencia. |

## Decisiones de implementación que no deben ocultarse

1. La Tabla 2 incluye capas de 1 a 12. Se interpreta Shifted como numeración **desde 1**, equivalente a índices Python `[1, 4, 7, 10]`. No se escoge entre indexaciones según el resultado de FMD. El código del autor podría resolver esta interpretación.
2. Se excluye el token CLS al promediar, siguiendo la descripción de DeiT3 y la referencia «as with DeiT3» en BEiTv2. No se aplica otra LayerNorm ni L2 por capa que el texto no especifique. El vector de 3.072 dimensiones no sustituye nuestro bloque final de 768.
3. El paper no indica interpolación para el resize. Se fija bilineal como decisión explícita, no como detalle supuestamente confirmado.
4. Se ejecuta `forward_features` completo del backbone, capturando los cuatro puntos mediante hooks. No se atribuye una optimización de parada temprana al paper; truncar tras la última capa seleccionada sería una variante separada.
5. El backbone permanece congelado y en evaluación, incluyendo cuando se entrene la cabeza. Esta es la interpretación de la descripción de extracción sin fine-tuning. Sus estrategias preliminares de selección de Swin no se mezclan con esta rama BEiTv2.
6. La fuente no entrega aquí salidas numéricas o una implementación oficial con las que exigir paridad. Cargar los pesos de manera estricta y verificar dimensiones solo acredita funcionamiento, no coincidencia empírica con el paper.

## Código y comprobación inicial

- `src/neshov_beit_reference.py`: extracción de cuatro capas, carga offline estricta y arquitectura MLP. Solo se descarta explícitamente la cabeza de clasificación del preentrenamiento.
- `tests/test_neshov_beit_reference.py`: prueba de indexación, exclusión de CLS, concatenación, limpieza de hooks, backbone congelado y estructura de cabeza.
- `scripts/smoke_neshov_beit_reference.py`: dos imágenes del **fit de desarrollo** FMD/42, no del test externo, en CPU con dos hilos. Exige directorio nuevo y checkpoints locales; no descarga, entrena, mide calidad ni publica tiempos. La cabeza está sin entrenar y sus scores no tienen interpretación predictiva.

Comando de comprobación funcional, con techo operativo de 180 segundos:

```bash
timeout 180s .venv-confirmatory/bin/python scripts/smoke_neshov_beit_reference.py \
  --output results/analysis/neshov_beit_functional_smoke_20261027
```

Si falla, se conserva `status.json`; no se reintenta automáticamente ni se sustituye el checkpoint para obtener un pase.

### Primer intento y compatibilidad pendiente de integrar

Los siete tests iniciales pasaron. La comprobación con imágenes se detuvo durante la carga estricta del checkpoint: doce claves `relative_position_index` no figuran como estado persistente del BEiT de la versión local de timm. No llegó a extraer las cuatro capas ni a producir F1 o tiempos. El fallo se conserva en `results/analysis/neshov_beit_functional_smoke_20261027/status.json`.

Se añadió un puente de compatibilidad que acepta retirar esos índices **solo si coinciden exactamente** con los buffers regenerados por el modelo. No cambia pesos aprendidos ni usa `strict=False`: siguen fallando parámetros ausentes, desconocidos, formas incorrectas o índices diferentes. Se añadió un test específico. Ese cambio de implementación no convierte retrospectivamente el primer intento en un pase ni acredita una reproducción; no se repitió automáticamente la comprobación completa con imágenes.

## Para pasar a una reproducción evaluada

Extraer las representaciones del fit y validación del protocolo acordado, entrenar la MLP con una receta fijada y medir F1/accuracy propios. Usar nuestros pliegues implica una **adaptación al benchmark común**. Reproducir sus protocolos originales (por ejemplo, 10 repeticiones de 10-fold en FMD) es otra tarea, no se cumple ejecutando un fold local. Conservar cabeza entrenada, logits por imagen, índices, pesos y transformaciones; después cronometrar esa ruta completa sin GPU ocupada.

No usar el porcentaje publicado ni la tabla nueva del ensamble de referencia como si fueran métricas de este prototipo.
