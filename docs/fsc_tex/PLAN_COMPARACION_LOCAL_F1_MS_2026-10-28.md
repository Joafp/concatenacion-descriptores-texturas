# Comparación prioritaria: calidad y latencia de los métodos locales

## Material Passport

- Tipo: protocolo operativo y auditoría de procedencia, guiados por ARS.
- Fecha: 28-10-2026.
- Autoridad: solicitud de comparar primero los métodos locales, en seis datasets y dos clasificadores; después los papers.
- Estado: métricas archivadas reagregadas; evaluación externa nueva y cronometraje pendientes.
- Integridad: resultados históricos preservados; ninguna latencia imputada y ningún cambio al manuscrito.

## 1. Alcance y orden de trabajo

**Decisión vigente de medición:** el usuario eligió latencia individual y F1
verificado en esa ejecución. Rige
`PROTOCOLO_BATCH1_F1_MS_2026-10-28.md`: extraer desde imágenes en batch1,
usar cabezas/selección congeladas y calcular calidad con las mismas llamadas
cronometradas. El archivo batch16 se conserva como referencia, sin declarar
paridad de sus vectores ni asociar directamente su F1 a estos tiempos.
El requisito histórico de pasar 1e-4 no se relaja ni se marca satisfecho:
se distingue explícitamente una evaluación nueva del despliegue batch1.
La primera ejecución FMD/42/0 SVM se inició en una carpeta nueva.

Ejecución física en curso: 200 imágenes por cinco métodos, una observación
por llamada, sin características compartidas entre políticas. Se preparó
una secuencia que espera el cierre y liberación de GPU de SVM, audita sus
registros y solo después inicia ResMLP/42/0 con el mismo protocolo batch1.
Si falla una etapa, detiene la secuencia sin reintento. Los registros de
calidad y tiempo se reagregan desde las mismas filas; cinco pruebas cubren
duplicados, cobertura, estabilidad y tiempos no finitos, y tres cubren la
secuencia de ejecución. 44 pruebas focalizadas pasaron, no la suite completa.

Rutas del piloto físico: `results/exploratory/local_batch1_20261028/FMD_s42_f0_svm/`
y `results/exploratory/local_batch1_followup_20261028/FMD_s42_f0/`. No publicar
medias definitivas por dataset a partir de esta única partición. El entorno
GPU es compartido y las cifras futuras deben etiquetarse como piloto observado.

**Avance de ejecución:** primer piloto externo FMD/42/0 completado en SVM y
ResMLP; cinco métodos sobre las mismas 200 imágenes. Se reprodujeron 2.000
clases/compuertas desde cabezas guardadas. ResMLP usó selección propia. Esto aún no
completa ninguna media por dataset ni los tiempos físicos. La ruta adaptativa
supera Top-4 y ambos ensambles en esta partición SVM, pero pierde frente a
Top-4/tómbola con ResMLP. Véase
[resultado parcial](RESULTADO_PANEL_EXTERNO_LOCAL_2026-10-28.md).

El preflight físico se detuvo en DeiT-small: el cargador inicializa pesos de
pooling ausentes y los vectores no pasan la tolerancia original. No reintentar
el benchmark ni publicar latencias hasta reconciliar el tap del extractor;
el usuario autorizó diagnosticar CLS. Ese diagnóstico no pasó en la primera
imagen y además falló su registrador (corregido y testeado, sin repetir la
extracción). No se cambió el adaptador. Véase el
[registro y la pista de semilla original](RESULTADO_DIAGNOSTICO_DEIT_CLS_2026-10-28.md).
Se consultó por comprobar ese estado original en un diagnóstico separado.
Las corridas de calidad sobre embeddings continúan como tarea independiente.

**Actualización posterior autorizada:** reconstruir el estado original con
semilla 42 pasó en ambas imágenes (error máximo 3,05e-7). Se integró un
adaptador local que restaura exclusivamente el pooler validado y se inició
preflight completo en carpeta nueva. Esto reproduce el pooling histórico,
que no debe describirse como preentrenado. Véase
[diagnóstico y límites](RESULTADO_DIAGNOSTICO_DEIT_SEED42_2026-10-28.md).

**Estado físico vigente:** DeiT corregido pasó el preflight repetido. El nuevo
bloqueo está en DenseNet121 (error máximo 0,000112459 > 0,0001). No se cambió
la tolerancia ni se repitió automáticamente. Aún no pasan los 22 bloques ni
las rutas completas y no hay latencias publicadas para este panel.

El [diagnóstico DenseNet](RESULTADO_DIAGNOSTICO_DENSENET_2026-10-28.md) terminó:
reproduce el archivo en los lotes originales, pero batch1 y desactivar TF32
no recuperan la tolerancia. Se consultó por latencia individual con F1
verificado en esa ejecución, o tiempo medio por imagen en lotes explícitos.
No mezclar esos alcances. En paralelo se inició la cola FMD/SVM/42 de los
otros cuatro pliegues, con verificación y detención ante fallos.

También se inició la cola separada ResMLP/42, pliegues 1–4, bajo el mismo
protocolo de continuación y con selección interna propia. Ambas colas siguen
siendo trabajo parcial, no cobertura de tres semillas. El agregador
`scripts/summarize_fmd_local_seed42.py` exige cinco pliegues completos y
reproducidos, sin imágenes de test repetidas, antes de publicar la media de
esa semilla; conserva también el F1 agrupado como métrica distinta.

**SVM/42 cerrado:** cinco pliegues y 1.000 imágenes únicas por método,
agregados tras replay. F1 medio adaptativo 0,977976, Completa 0,965099,
diversidad 0,978911, tómbola 0,978912 y Top-4 0,981922. No se mantiene
la ventaja del primer pliegue contra todos los controles. Véase
[resultado de la semilla](RESULTADO_FMD_SEMILLA42_LOCAL_2026-10-28.md).
ResMLP restante en ejecución; otras semillas/datasets y tiempos pendientes.

**Actualización nocturna:** ResMLP/42 también cerró sus cinco pliegues, replay
y agregación (F1 adaptativo 0,972955 frente a Top-4 0,978017; no hay mejora
uniforme). El piloto físico FMD/42/0 SVM terminó y pasó auditoría de llamadas;
ResMLP físico está en ejecución. Rige ahora el
[plan nocturno y manifiesto de las 94 condiciones](PLAN_NOCTURNO_F1_LATENCIA_2026-10-28.md),
con seguimiento activo cada quince minutos, workers y puertas explícitas.

Esta prioridad sustituye temporalmente la ampliación de las réplicas de papers.
Comparar por separado SVM y ResMLP en DTD, FMD, CUReT, Outex13Official1360,
SoilOriginal y KTH-TIPS2-b. VisTex permanece fuera.

Panel mínimo: Completa-22, ensamble de diversidad, ensamble de tómbola,
Top-4 y selección adaptativa con margen. Top-k de tamaño variable y GFS son
controles adicionales, no sinónimos de Top-4.

Cada fila final debe contener dataset, clasificador, método, macro-F1 externo,
ms/imagen medidos, diferencia de F1 y aceleración respecto del comparador.
No calcular aceleraciones mientras falten tiempos físicos comparables.

## 2. Qué se verificó ahora

El auditor `scripts/audit_local_f1_latency_panel.py` vuelve a calcular las medias
desde las filas fuente, sin eliminar duplicados silenciosamente. Exige claves
dataset/semilla/pliegue únicas e idénticas entre los cuatro controles. Contrasta
las medias con `results/analysis/selection_stats/{svm,resmlp}_metodos.csv`
(tolerancia absoluta 1e-9) y conserva hashes de las fuentes.

Se verificaron 47 condiciones por clasificador: DTD 10, FMD 15 (tres semillas
por cinco pliegues), CUReT 2, Outex 1, Soil 15 (tres por cinco), KTH 4.
En total: 94 filas de condiciones, 48 medias de referencia y 188 recetas de
ensambles (dos familias por condición). La agregación reproduce la tabla
compartida; no constituye reproducción desde imágenes o predicciones.

El registro de cobertura contiene 60 celdas: cinco métodos por seis datasets
por dos clasificadores. Las 60 latencias permanecen vacías. Las 12 medias
externas de la variante adaptativa nueva también permanecen vacías.
Los pilotos de desarrollo SVM en dos datasets no rellenan estas celdas.

### Diferencias de implementación que impiden copiar números sin verificar

1. Las 188 recetas históricas declaran 21 candidatos. Las listas de candidatos
   disponibles de tómbola no contienen RGB N-grams; ninguna unión de miembros
   de ambas familias lo contiene. Completa-22 incluye el bloque adicional.
   Esto se mantiene explícito al reproducir el archivo. Una versión con 22
   candidatos sería una adaptación nueva, con nuevas métricas.
2. Las recetas inspeccionadas no registran normalización de scores ni escalas
   por miembro. El código actual sí congela escalas con entrenamiento. No se
   debe afirmar que ese código reproduce las predicciones archivadas sin
   reconstruirlas. El auditor registra esta información por receta.
3. El ejecutor de rescate previo llama a `make_model("svm", ...)`: cambiar
   la etiqueta de sus resultados a ResMLP no es una evaluación ResMLP.
4. Igualdad de claves no demuestra igualdad de imágenes o protocolos. KTH
   mantiene la reserva de reconciliación ya documentada.

## 3. Ejecución: puertas de aceptación

### P1 — Recuperar las condiciones y reproducir los controles

- Congelar por condición índices y hashes de entrenamiento/prueba, manifiesto,
  clases, versiones de embeddings, receta y configuración del clasificador.
- Verificar la biblioteca y la proyección N-grams entrenada exclusivamente
  sobre entrenamiento; no usar una proyección global para reproducir Completa.
- Reconstruir miembros y multiplicidades originales; comprobar cómo se
  normalizaron sus scores. Si no es posible la reproducción exacta, reportar
  la divergencia y separar archivo histórico de adaptación nueva.
- Para inferencia individual, usar escalas fijas de entrenamiento. Recalcular
  F1 bajo esa misma implementación, sin asociar el F1 antiguo a una latencia
  de otro predictor. No normalizar usando todo el lote de prueba.

### P2 — Selección adaptativa en ambos clasificadores

- Conservar el mecanismo de selección interna OOF de base, rescate y umbral;
  ajustar cada clasificador usando solo entrenamiento externo.
- Obtener scores OOF propios de ResMLP: no reutilizar umbrales o miembros
  elegidos para SVM como si se hubieran seleccionado para ResMLP.
- Congelar antes de abrir la prueba externa: biblioteca, pool de candidatos,
  criterio, presupuesto de diseño, cuantiles y máximo de miembros. Conservar
  todas las configuraciones previstas; no escoger la mejor con el test.
- Separar la comparación de recetas históricas de la comparación controlada
  con biblioteca y escala comunes. Su diferencia no puede atribuirse solo a
  la compuerta si también cambian los candidatos y la normalización.
- La ruta ejecuta base primero. Si margen < umbral, usa el rescate; si no,
  conserva la clase base. No suma un voto base adicional al rescate.
- Guardar por imagen etiqueta, predicción, compuerta, bloques adquiridos,
  scores y configuración. Evaluar las mismas imágenes en todos los métodos.

### P3 — Cronometraje físico emparejado

- Primero validar vectores, clases y compuerta contra la ejecución en caché,
  con tolerancia previamente fijada. El diagnóstico de un único extractor
  no sustituye esta validación completa.
- Misma máquina, precisión, batch=1 y política de residencia por comparación.
  Medir desde imagen hasta clase: lectura/decodificación, preprocesamiento,
  extracción, transferencias, concatenación, clasificador y votación/compuerta.
- Cada método adquiere un bloque una vez por imagen; nunca comparte caché de
  features entre métodos ni imágenes. Puede reutilizarlo entre sus miembros.
- Calentamiento previo y sincronización CUDA antes/después; orden emparejado
  aleatorizado y repeticiones. Guardar observaciones crudas, media, mediana y
  p95. Reportar por separado carga de modelos y entrenamiento/selección.
- Si los 22 extractores no caben residentes, fijar un régimen común que sí
  quepa y contar transferencias en todos. No excluir carga en un método e
  incluirla en otro sin distinguir escenarios.
- Registrar ocupación/competencia de GPU. Una medición con contención se
  etiqueta como tal; no se presenta como benchmark aislado definitivo.
- Los costos del perfil analítico sirven para seleccionar, no para rellenar
  la columna de ms medidos. No trasladar el ahorro de la cascada histórica.

### P4 — Informe y continuación con papers

Agregar primero por condición y después por dataset, conservando las semillas
y particiones previstas. La media global otorga igual peso a cada dataset.
No tratar semillas o pliegues como datasets independientes. Si calidad y
latencia tienen distinta cobertura, publicar ambas coberturas explícitas.

Mostrar pérdidas además de mejoras. No afirmar equivalencia o no inferioridad
por no rechazar una prueba de diferencias. No prometer superar Completa en F1:
el aporte puede ser un compromiso calidad–latencia, si las mediciones lo apoyan.

Solo después de cerrar el panel local, aplicar el mismo contrato a réplicas de
papers. El piloto Neshov existente se conserva como adaptación de desarrollo;
no se incorpora a esta tabla como resultado externo ni como latencia medida.

## 4. Artefactos y criterio de cierre

Auditoría inicial: `results/analysis/local_f1_latency_panel_20261028/`.
La auditoría ampliada registra también la procedencia de escalas en una salida
nueva, sin sobrescribir la inicial. Archivos: `audit.json`,
`reference_conditions.csv`, `coverage.csv`.

Cerrar únicamente cuando existan predicciones externas verificadas y tiempos
físicos emparejados bajo el mismo predictor/protocolo para cada celda publicada.
Una celda pendiente permanece pendiente; no se rellena con otro algoritmo,
otro clasificador, otro dataset o un costo estimado.
