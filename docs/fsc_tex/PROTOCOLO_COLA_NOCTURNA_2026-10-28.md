# Cola nocturna autorizada: panel local de calidad y latencia

## Material Passport

- Fecha: 28-10-2026. Ejecución ARS inline, con seguimiento automático del chat.
- Autoridad: el usuario pidió dejar programadas todas las tareas y corridas
  pendientes mientras descansa. No autoriza inventar protocolos o resultados.
- Estado: previo a lanzar los workers nuevos.

## Alcance científico fijo

94 condiciones del archivo auditado: DTD 10, FMD 15, CUReT 2, Outex 1,
SoilOriginal 15 y KTH-TIPS2-b 4, por separado en SVM y ResMLP. Cinco métodos
por condición: Completa-22, diversidad, tómbola, Top-4 y selección adaptativa
con margen. VisTex no se incorpora. Las recetas archivadas de ensambles
conservan 21 candidatos; el modelo completo y las bases adaptativas incluyen
el bloque N-grams. No reinterpretar esto como igualdad de pools.

La receta de calidad reproduce el piloto del 28-10 en cada entrenamiento
externo: tres pliegues OOF, presupuesto de diseño 60 ms, cuantiles 0,1/0,25/0,5,
máximo tres miembros, criterio de relevancia, scores propios del clasificador,
escala fijada con entrenamiento y SVD N-grams ajustada por pliegue. Congelar
decisiones antes del test, no optimizar observando el test. Preservar la
adaptación CPU de ResMLP como versión nueva, distinta de cifras GPU históricas.

La fase física aplica el protocolo batch1 ya aprobado: `PROTOCOLO_BATCH1_F1_MS_2026-10-28.md`.
F1 y latencia deben derivarse de las mismas llamadas desde imágenes. Pesos
residentes, un solo proceso de medición GPU, sin reutilizar features entre
políticas/imágenes. Una repetición inicial por imagen, estadísticas descriptivas
y contexto compartido explícito; no inferir equivalencia ni hardware aislado.
No presentar el F1 del archivo batch16 como el F1 online ni sumar componentes
de extracción para fingir una medición end-to-end.

## Cobertura y puertas pendientes

El manifiesto registra todas las condiciones, incluidas las ya terminadas y las
gestionadas por colas previas. No se duplican. Las salidas nuevas tienen
directorios exclusivos y estados por tarea; el manifiesto científico queda
separado de los estados de ejecución.

KTH requiere auditoría/reconciliación de protocolo y fuente de datos antes de
activar sus condiciones nuevas. Su retención no es fallo de proceso ni una
exclusión silenciosa de la tabla. Debe conservarse la reserva metodológica al
interpretar inferencias conjuntas.

El ejecutor físico actual y su evidencia DeiT están vinculados al embedding
FMD. Para otros datasets registrar la tarea de adaptar/verificar ese vínculo
y la receta de extracción original antes de ejecutar. No saltar el hash
existente ni suponer fidelidad por haber validado FMD. El seguimiento puede
implementar diagnósticos acotados y adaptar orquestación dentro del diseño
aprobado, con pruebas y salidas nuevas; cambios científicos requieren consulta.

## Recursos y fallos

Primero respetar las colas ya activas. El worker CPU espera su cierre y el del
piloto físico inicial para no agregar competencia durante ese piloto. Después:
un worker de calidad de dos hilos y un worker físico de GPU, con dependencias
de heads y auditoría. Locks por worker impiden duplicados.

Ventana inicial de despacho: diez horas por worker. No matar una corrida al
cerrarse esa ventana; el timeout propio de la condición sigue aplicando.
Límites nuevos antes de primera ejecución: calidad SVM dos horas, ResMLP tres,
replay treinta minutos y físico cuatro horas, audit físico cinco minutos.
Los pilotos anteriores conservan sus límites anteriores. Estos límites no
autorizan repetir una condición fallida con mayor plazo automáticamente.

Un fallo/timeout se conserva, se marca requiere revisión y no se reintenta.
Se puede avanzar en otras condiciones independientes. Directorios preexistentes
no gestionados/terminados se marcan para revisión, no se sobrescriben. Ante
deriva de scripts/configuración, detener el worker; corregir y versionar una
cola nueva si corresponde, no modificar retroactivamente el protocolo.

## Auditoría, reporte y cierre

Para calidad, replay de cada cabeza sobre cada imagen; para física, reagregación
de cobertura, F1 y tiempos desde las mismas filas de llamadas. No tratar
repeticiones/pliegues como datasets. Medias por dataset solo cuando tengan
todas sus condiciones previstas; medias globales con igual peso por dataset.
Mantener visibles pérdidas de calidad y fallos.

Actualizar cobertura e informe nocturno con fuentes. No editar el manuscrito,
crear commits o hacer push durante las corridas. Papers de referencia después
de cerrar/auditar el panel local; su reproducción requiere código, datos y un
protocolo concreto, no basta con estar anotada como tarea.

No prometer cierre de todas las condiciones durante esta noche. Para ejecutar
trabajo local el equipo, WSL y la aplicación deben permanecer disponibles.
