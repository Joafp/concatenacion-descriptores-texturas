# KTH: aproximación separada al reparto de un tercio descrito en los papers

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: aproximación prospectiva a dos evaluaciones publicadas.
- Origin Date: 2026-11-02, America/Asuncion.
- Verification Status: especificación previa; sin mediciones de este protocolo.

CellNN y HyTexNet describen usar 2 poses × 3 iluminaciones × 6 escalas para
fit, equivalente a un tercio de KTH-TIPS2b, pero no identifican inequívocamente
el subconjunto concreto en las fuentes verificadas. La guía oficial KTH mapea
imágenes 1–3 a pose frontal con tres luces, 4–6 a pose derecha con las tres
luces y escalas 2–10 a las distancias. Para una sola aproximación prospectiva,
fijar escalas 2–7 e imágenes 1–6: 1584 fit y 3168 test, una condición por
método. Esta selección específica es **local, no confirmada como la de autores**;
no buscar otras combinaciones después de ver accuracy ni decir réplica exacta.

La separación se hace por imagen, no por objeto físico. Las cuatro muestras
físicas de cada clase aparecen en fit y test, por lo que este protocolo mide
otra situación y puede resultar más fácil que el panel de muestras separadas.
No sustituye las cuatro particiones comunes, no se promedian ambas evaluaciones
y no se presentan como comparación emparejada con nuestros métodos. Registrar
el solapamiento físico de manera explícita en el manifiesto y resultados.

Usar las recetas locales ADAPTADAS y los pesos ya fijados de HyTexNet y
LBP+dCellNN. No se asegura que preprocesamiento, backbone, versión de software,
semilla o entrenamiento coincidan con los autores. Los artículos informan
accuracy 99,79 % y 91,29 %, respectivamente: medir accuracy y macro-F1 desde
las mismas llamadas individuales y reportar resultados, diferencias y límites.
Las cifras publicadas no se mezclan con tiempos físicos propios.

Mismo hash del manifiesto KTH y de cada imagen, 11 clases/44 muestras físicas,
semilla fija 42, salida nueva por sistema, fit solo en los índices indicados,
sin tuning ni seleccionar época por test. Cuatro etapas con auditoría, lock
GPU global, CPU dos hilos, sin benchmarks concurrentes ni autoretry al fallar.
No cambios a código ni archivos sellados de los paneles anteriores.
