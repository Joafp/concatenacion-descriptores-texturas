# Continuación del panel FMD: semilla 42, pliegues 1–4

## Material Passport

- Fecha: 28-10-2026. Ejecución ARS inline.
- Autoridad: continuar la comparación de F1/ms en todos los datasets y ambos
  clasificadores; esta cola constituye una parte explícita de esa cobertura.
- Estado: previo al inicio de la cola nueva.

Reutilizar sin cambios de método la receta del piloto externo FMD/42/0,
documentada en `PROTOCOLO_PANEL_EXTERNO_LOCAL_2026-10-28.md`, sobre los pliegues
externos 1, 2, 3 y 4. El único cambio de la configuración fuente es el pliegue.
Cada pliegue recupera sus propias recetas archivadas, selecciona base/rescate/
umbral solo con su entrenamiento y evalúa sus propias 200 imágenes externas.
No elegir configuraciones por el test. Mantener presupuesto de diseño 60 ms,
cuantiles 0,1/0,25/0,5, máximo tres miembros, tres pliegues internos y escalas
de entrenamiento. SVM y ResMLP son colas separadas con scores propios.

Crear directorios nuevos y registrar configuraciones, hashes, logs y estado.
Por condición: máximo 30 minutos para calidad y cinco para repetición desde
cabezas. Ante cualquier error o timeout detener la cola, conservar lo obtenido
y no reintentar ni omitir esa condición silenciosamente. Dos hilos CPU.

La cola inicial ejecuta SVM; ResMLP requiere su ejecución separada, no se
considera completado por compartir el script. Estos cuatro pliegues, junto
con el piloto, completan una semilla FMD, no sus tres semillas ni los seis
datasets. No se publican latencias desde embeddings; el problema de paridad
online se investiga por separado.
