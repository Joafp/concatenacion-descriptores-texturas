# Diagnóstico DenseNet: lote y precisión numérica

## Material Passport

- Fecha: 28-10-2026; ejecución numérica ARS inline.
- Autoridad: continuar el trabajo tras identificar la discrepancia DenseNet.
- Estado: protocolo guardado antes de ejecutar.

Conservar filas FMD 3 y 996, manifiesto original, checkpoint, semilla 42,
preprocesamiento y tolerancia 1e-4. Verificar hashes de manifiesto y embedding
contra metadata original y hashes de imágenes contra el preflight previo.

Comparar exactamente cuatro configuraciones predefinidas: precisión predeterminada
con batch1; predeterminada con los lotes originales de hasta 16 imágenes;
TF32 deshabilitado con batch1; TF32 deshabilitado con los lotes originales.
No entrenar, cambiar features, buscar hiperparámetros o publicar tiempos.
Estas pruebas diagnostican diferencias de extracción, no optimizan el F1.

Guardar todos los vectores y resultados, no solo el mejor. Un modo batch16 que
pase no demuestra paridad de inferencia individual. Un modo batch1 que pase
en dos filas es solo candidato a una comprobación más amplia, no validación
general de la biblioteca. No relajar tolerancia. Un fallo de ejecución se
conserva sin reintento automático. GPU compartida solo numérica, >=2 GiB libres,
tiempo máximo cinco minutos. El proceso no modifica flags de otros procesos.
