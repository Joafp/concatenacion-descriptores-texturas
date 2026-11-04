# Ejecución individual: F1 y latencia de las mismas llamadas

## Material Passport

- Fecha: 28-10-2026. ARS, ejecución inline.
- Autoridad: el usuario eligió «Latencia individual y F1 verificado en esa ejecución».
- Estado: protocolo previo al primer piloto físico nuevo.
- Primer piloto: FMD/42/0, SVM, cinco métodos, 200 imágenes externas.

## Cambio de pregunta de medición

Se evalúa la ejecución real batch1 de las cabezas y selecciones congeladas.
No se exige ni se declara que esos vectores reproduzcan los del archivo
batch16 dentro de 1e-4: el diagnóstico DenseNet demostró que no es así en las
filas comprobadas. La tolerancia histórica no se relaja ni se declara pasada.
Se conservan diferencias de vectores y clases como diagnósticos, pero F1 se
calcula con las predicciones de las propias llamadas cronometradas.

No reentrenar cabezas ni reoptimizar base/rescate/umbral usando el test. La
tabla nueva es una evaluación de despliegue de esos modelos congelados; no
debe confundirse con reentrenamiento de toda la selección en features batch1.
Si su calidad cambia, reportarlo en lugar de copiar la calidad histórica.

## Implementación congelada

- Misma RTX 4060 para las cinco rutas, deep extractors residentes en GPU;
  clásicos y cabezas en CPU. La carga de todos los pesos precede la medición.
  Si no caben, detener y conservar el fallo: no cambiar silenciosamente a
  intercambio de modelos o carga desde disco dentro de una ruta.
- Se requieren >=5 GiB libres al inicio. Registrar ocupación y utilización
  antes, durante y después. GPU compartida: resultados exploratorios del
  entorno observado, no benchmark aislado definitivo.
- Reutilizar transformaciones/checkpoints originales. Construir cada modelo
  con semilla 42. Para DeiT usar el estado de pooling reconstruido y validado.
  No presentar los poolers inicializados en la receta histórica como entrenados.
- Los extractores potencialmente estocásticos, incluido el enmascaramiento de
  MAE, conservan su configuración. Fijar antes del forward una semilla por
  imagen y bloque: `(20261028 + row_id * 1009 + posición_bloque) mod 2^31`.
  La posición se define por el orden alfabético de los 22 bloques. No depende
  de clase, acierto, clasificador o política. Guardar/restaurar RNG; su costo
  forma parte de la llamada. Esta realización estocástica puede diferir de
  los lotes históricos y es otra razón para volver a calcular F1.
- Proyección N-grams+SVD ajustada solo con el entrenamiento externo original,
  misma configuración y semilla. Conteo desde la imagen en cada llamada.
- Cada método abre/decodifica su imagen y adquiere sus propios features. No
  comparte vectores entre métodos o imágenes; dentro de una ruta cada bloque
  se calcula una sola vez, compartido por sus miembros si corresponde.
- Batch1 sin relleno con otras imágenes. Concatenación, normalización,
  transferencias, clasificación CPU, RNG y compuerta/votación dentro del reloj.
  Sin acceso a embeddings archivados para construir la predicción cronometrada.

## Diseño y salidas

Primero cargar todos los modelos. Calentar con las primeras dos imágenes
externas, sin filtrar por etiquetas/score; registrar diferencias frente al
archivo, sin elegir parámetros con ellas. Después procesar las 200 imágenes
externas, una por una, con orden de métodos aleatorizado de semilla 20261028.
Sincronizar CUDA antes y después de cada llamada. Primera ejecución: una
observación por imagen/método, 1.000 llamadas. Es un piloto físico de una
partición, no una estimación de variabilidad entre repeticiones o datasets.

Guardar cada llamada, predicción, etiqueta, activación, bloques, llamadas a
cabezas y ms. Calcular F1 y exactitud sobre imágenes únicas, media/mediana/p95
de ms, y acuerdo de clases con el archivo (solo diagnóstico). Si se usan
repeticiones futuras, no tratarlas como imágenes independientes y comprobar
que clases/compuertas sean estables. Interrumpir ante dimensiones incorrectas,
NaN, error de runtime o inestabilidad de predicciones repetidas. Nunca ocultar
un fallo o repetirlo automáticamente cambiando el diseño.

Límite del primer piloto: 30 minutos. Directorio nuevo, sin modificar el
archivo o manuscrito. Los otros pliegues, ResMLP y demás datasets requieren
ejecuciones propias. Los valores de F1/ms de este piloto no rellenan las
medias completas de las tres semillas FMD.
