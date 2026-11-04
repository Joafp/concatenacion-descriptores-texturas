# Preflight de extracción online del panel local

## Material Passport

- Fecha: 28-10-2026. Tipo: protocolo numérico, ARS inline.
- Alcance autorizado: preparar la comparación local de F1 y tiempos reales.
- Estado al guardar: antes de la ejecución de esta comprobación nueva.

Tomar dos filas fijas: primera y última de la prueba externa del piloto FMD/42/0
completado. No seleccionar por clase, acierto, score o compuerta. Comprobar
hashes de las imágenes antes de extraer. Cargar un solo extractor profundo
simultáneamente y liberarlo entre bloques; no interrumpir otros procesos.
Si CUDA tiene menos de 2 GiB libres, registrar el bloqueo y no cargar el modelo.

Reutilizar los adaptadores de extracción originales. Clásicos en CPU; modelos
profundos en CUDA; N-grams mediante conteo original y SVD ajustada únicamente
con el entrenamiento externo, misma configuración que la evaluación de calidad.
Exigir dimensión idéntica, valores finitos y error absoluto máximo <= 1e-4
por vector normalizado. No ajustar la tolerancia al observar resultados.

Ante discrepancia, conservar archivo y detener este preflight, sin reintento
automático ni sustitución por otro extractor. Si todos pasan, verificar además
clase y compuerta de los cinco métodos sobre las dos imágenes contra las
cabezas guardadas y embeddings. No se reajustan cabezas ni seleccionan políticas.

Este proceso usa GPU compartida solo para verificar números, no para publicar
latencia o ahorro. Un éxito en dos imágenes es un preflight limitado: todavía
hace falta paridad y cronometraje sobre las imágenes de la medición emparejada.
