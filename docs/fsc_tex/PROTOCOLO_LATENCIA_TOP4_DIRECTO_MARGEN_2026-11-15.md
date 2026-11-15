# Preparación: latencia online del mismo Top-4 directo y por margen

Fecha: 15-11-2026, America/Asuncion. **Protocolo preparado; no ejecutado.**
La preparación no autoriza una corrida ni repite fallos científicos.

## Pregunta y población fijada

Medir la calidad y el tiempo de cada llamada RGB de las dos políticas E1
ya ajustadas, sin cambiar bloques, cabezas, base, umbral, semilla ni particiones.
Son 27 condiciones SVM/42 de seis datasets y 31.984 observaciones de test,
con imágenes reutilizadas entre particiones; no son imágenes independientes.
Se utilizarán todos sus índices, en el orden congelado, sin elegir un
subconjunto por su resultado o tiempo. Los tests ya observados son exploratorios.

Se conserva el criterio de selección histórico por macro-F1 OOF y tolerancia
0,005. Accuracy será la métrica principal; precisión macro, recall macro y
macro-F1 se calcularán con las mismas predicciones que los tiempos nuevos.
No se combinará calidad histórica con tiempos nuevos.

## Insumos y bloqueo previo

El manifiesto de preparación liga los 27 modelos joblib, la selección
pretest, los scores/predicciones de referencia, los manifiestos de imágenes,
las particiones, las versiones y los checkpoints locales por SHA-256. No
ajusta modelos ni carga redes. El congelado de implementación ejecutable,+hardware y driver deberá completarse antes de la primera llamada.

La implementación online todavía debe integrar los adaptadores EVA-02/SigLIP
validados y acreditar las rutas restantes. La concordancia KTH en 33 imágenes
por red no demuestra fidelidad en todos los datasets. El ejecutor genérico
actual no es, por sí solo, una implementación validada de este protocolo.

**Bloqueo científico conocido:** CUReT fold 0 y Soil folds 1 y 4 requieren
`vit_b16`, con discrepancia de representación pendiente. No se ejecutarán
esos casos para repetir automáticamente el fallo ni se omitirán para declarar
un panel de seis datasets completo. Su revisión debe preceder a cualquier
nueva autorización de validación. Swin y los demás bloques conservan también
su comprobación de representación por condición antes del benchmark.

## Dos brazos y residencia

- **Directo:** extraer exactamente los cuatro bloques E1, normalizarlos por
  bloque, concatenar en su orden y predecir con la cabeza Top-4 guardada.
  No añadir un clasificador base por fuera de esos cuatro bloques.
- **Por margen:** ejecutar la base guardada, calcular la diferencia de sus
  dos mayores scores y aplicar el umbral numérico guardado. Si se activa el
  rescate, adquirir solo los bloques Top-4 restantes y usar la misma cabeza.
  Reutilizar una base compartida solo dentro de esa llamada y con representación
  idéntica. Si E1 eligió uso directo, respetar esa ruta, sin inventar una cascada.

Una condición por vez; el conjunto de modelos necesario para ambos brazos
reside en GPU y las cabezas en CPU durante sus llamadas. Carga de pesos y
calentamiento quedan fuera de latencia. No se permite sustituir un modelo
por otro, cambiar precisión, descargar pesos o mover silenciosamente un bloque
a CPU por falta de memoria. Una falta de recursos detiene la preparación.

## Presupuesto y orden pareado

Una llamada por brazo y observación: **63.968 llamadas evaluadas**, como
máximo, más **270 calentamientos** (cinco imágenes de entrenamiento por
brazo y condición). No hay repeticiones adaptativas, búsqueda de cuantiles
ni entrenamiento durante el cronometraje.

En cada imagen se ejecutan los dos brazos por separado. Su orden se sortea
con semilla determinista derivada de 42 y el ID de condición; el manifiesto
fija los bits de orden. No se comparten vectores, resultados ni decisiones
entre brazos o imágenes. La caché del sistema operativo puede afectar la
segunda lectura; el orden aleatorizado se informa, sin llamarlo control
perfecto de toda interferencia temporal.

Batch1, dos hilos CPU, una GPU y lock global existente. No deben coexistir
otros fits, extracciones o benchmarks ni un juego usando la GPU. Registrar
procesos, carga, temperatura, memoria y driver al inicio y al final, con el
estado del entorno de escritorio. Una captura de memoria del conjunto
residente no sustituye el experimento E7 de memoria aislada por política.

## Cronometraje, fidelidad y fallos

El tiempo por llamada incluye lectura/decodificación, preprocesamiento,
transferencias, extracción, normalización/concatenación, compuerta y cabeza
CPU que correspondan. Sincronizar GPU antes de iniciar y al terminar. Las
comprobaciones instrumentales de SHA y coseno se contabilizan por separado;
no se presentan como parte de la inferencia de la aplicación.

Guardar la predicción recién obtenida y su tiempo en el mismo registro.
Contrastar las representaciones con el NPY de esa imagen: forma, finitud y
coseno mínimo 0,999. Comprobar la cabeza, scores, ruta y clase contra E1;
una divergencia se registra para revisión, sin forzar la predicción guardada
como si fuera una predicción online. No se aceptará como panel comparable
una condición con esa divergencia sin revisar.

Un fallo científico detiene el caso en `requires_review`, conserva la imagen
y la evidencia y no permite retry automático, otra tolerancia u omisión.
Las correcciones de infraestructura se prueban antes y no autorizan repetir
una llamada científica fallida. Los archivos E1 y perfiles originales quedan
intactos; todas las salidas físicas usan una carpeta nueva.

## Agregación y entrega

Por llamada: ID/índice, SHA de imagen, orden de brazo, clase real y predicha,
scores, margen, umbral, ruta, bloques ejecutados/reutilizados, tiempo y error.
Registrar hashes de protocolo, código, pesos, cabezas y salidas.

Reportar accuracy y métricas macro, media/mediana/p95 y diferencias pareadas
por condición, después por dataset. La media principal equipondera solo
datasets de cobertura completa, identificando sus nombres. No usar 31.984
observaciones dependientes como tamaño muestral de dominios independientes.
Los contrastes entre políticas usarán las seis medias de dataset solo si
los seis cierran. Informar ganancias, pérdidas y sobrecostos.

Este protocolo no convierte el ahorro proyectado 75,00 % de E1 en un ahorro
físico esperado ni garantiza su reproducción. El resultado online será el
observado en sus propias llamadas y hardware, cuando se pueda ejecutar.
