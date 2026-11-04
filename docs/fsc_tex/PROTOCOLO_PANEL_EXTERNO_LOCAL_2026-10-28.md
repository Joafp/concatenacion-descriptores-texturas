# Piloto externo local: recetas archivadas y selección adaptativa

## Material Passport

- Fecha: 28-10-2026. Tipo: protocolo de ejecución, ARS inline.
- Autoridad: continuar la comparación local F1/ms solicitada por el usuario.
- Estado al congelar: antes de ejecutar el nuevo piloto externo.
- Primer objetivo: FMD, semilla 42, partición externa 0, SVM; el ejecutor admite
  ResMLP como clasificador distinto, con sus propios scores de entrenamiento.
- Salidas nuevas; ningún resultado, proyección o manuscrito anterior se sobrescribe.

## Contrato previo

Se usa el manifiesto y la partición externa del piloto FMD/42 existente:
800 imágenes para entrenamiento y 200 externas. Se comprobará ausencia de
grupos compartidos; se conservarán índices y hashes de manifiestos/embeddings.
Las recetas históricas de diversidad (lambda=0,25, beta=8, 15 miembros de cuatro)
y tómbola (beta=8, mismo tamaño) se recuperan de sus JSON, sin redibujarlas.
Se preserva el orden de bloques y la multiplicidad de votos. Top-4 se recupera
del barrido archivado para la misma condición.

Estas familias tienen 21 candidatos sin N-grams. Completa-22 incorpora
RGB N-grams+SVD; cada proyección SVD se ajusta solamente en las filas de
entrenamiento correspondientes. No se presume igualdad de bibliotecas.

La ruta adaptativa conserva el criterio de relevancia del piloto previo:
base entre los 22 individuales, rescate de hasta tres miembros únicos del
ensamble de diversidad archivado, presupuesto analítico de diseño fijo 60 ms,
cuantiles 0,1/0,25/0,5, costos y overhead del perfil existente. No es una
selección del presupuesto usando el test. Los scores para elegir base,
miembros y umbral se obtienen mediante tres pliegues estratificados agrupados
del entrenamiento externo. El pool archivado se había construido con ese
entrenamiento: sus scores OOF no son una estimación anidada imparcial del
proceso completo de generación del pool; la evaluación externa es la medida
de calidad para este piloto.

La decisión completa se escribe y hashea antes de ajustar/puntuar en prueba.
El rescate reemplaza la predicción base solo si margen < umbral; sin rescate
factible la política puede degenerar en base sola. No se ocultan estos casos.

Las cabezas se reajustan sobre las 800 filas, con el clasificador real indicado.
SVM conserva los parámetros existentes. ResMLP mantiene arquitectura y receta
del constructor, con dispositivo CPU explícito y dos hilos para esta
reconstrucción. No se asegura reproducción bit a bit de cabezas GPU históricas.

## Normalización y reconciliación histórica

Para la comparación nueva se usa por miembro la desviación global de scores
ajustada sobre entrenamiento y congelada. Esto permite inferencia individual.
Se recalcula el F1 de todos los controles bajo esa implementación.
Por separado se calcula el diagnóstico de normalización dependiente del lote
externo para contrastar la hipótesis sobre las cifras archivadas. Este
diagnóstico no es el predictor destinado al cronometraje ni valida por sí solo
la identidad de las predicciones históricas, que no están archivadas en esas
recetas. Una coincidencia de F1 no demuestra identidad muestra por muestra.

## Archivos y límites

Guardar: scores OOF, particiones internas, decisiones congeladas, modelos y
escalas, predicciones externas por método, F1/exactitud, diagnóstico histórico,
auditoría de ajustes N-grams, hashes de entradas y salidas, versiones y fallos.
Tiempo límite del primer piloto: 30 minutos. No reintentar automáticamente
fallos científicos ni alterar tolerancias, recetas o selección con los resultados.

Esta ejecución **no mide latencia desde imágenes**. La columna ms queda vacía
hasta comprobar paridad online de todos los extractores y la ruta, y medir en
el régimen emparejado del plan local. No usar el tiempo transcurrido de esta
ejecución ni el presupuesto de diseño como ms/imagen.

El test histórico ya fue observado en el proyecto. Esta ampliación es una
evaluación exploratoria trazable, no confirmación ciega o prerregistrada.
Una partición FMD tampoco completa sus tres semillas/cinco pliegues ni los
otros cinco datasets. No se realizan nuevas pruebas de significancia aquí.
