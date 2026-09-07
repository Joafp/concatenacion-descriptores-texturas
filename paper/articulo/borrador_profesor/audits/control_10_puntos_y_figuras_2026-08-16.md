# Control de los diez puntos del profesor y auditoría de figuras

Fecha: 16 de agosto de 2026  
Manuscrito evaluado: `main.tex` / `main.pdf`

## Verificación de la retrospectiva

| N.º | Requisito del profesor | Estado | Evidencia en el manuscrito |
|---:|---|---|---|
| 1 | Reservar la Sección 3 para el método de concatenación y selección | Cumplido | La Sección 3 contiene representación conjunta, espacio de descriptores, GFS, comparadores y el experimento metodológico de continuidad. No contiene datasets, clasificadores ni resultados. |
| 2 | Trasladar datasets, clasificadores, protocolo y métricas a “Resultados experimentales” | Cumplido | Todos aparecen como subsecciones de la Sección 4. |
| 3 | Incorporar una Figura 1 con el pipeline completo | Cumplido | La Figura 1 recorre imagen, extractores congelados, normalización, tres políticas representacionales, clasificador y evaluación externa. |
| 4 | Mostrar claramente el protocolo anidado | Cumplido | La subsección 4.3 y la Figura 3 separan validación interna, ajuste final y test externo reservado. |
| 5 | Incorporar comparación con métodos publicados | Cumplido | Las subsecciones de comparación distinguen el caso directamente reproducido de Outex del contexto no homólogo en DTD, FMD y CUReT. |
| 6 | Reunir los análisis estadísticos bajo “Statistical analysis” | Cumplido tras corrección | Métodos, supuestos, bootstrap, Wilcoxon, McNemar, margen práctico y resultados de los contrastes quedaron reunidos bajo una única subsección. |
| 7 | Reducir Related Work y orientarlo a representaciones heterogéneas | Cumplido | La sección se limita a complementariedad, el antecedente directo RGB Pixel N-grams y selección de bloques. |
| 8 | Reducir las contribuciones a tres puntos | Cumplido | La introducción presenta exactamente tres contribuciones concretas. |
| 9 | Interpretar inmediatamente cada tabla principal | Cumplido | Las tablas principales van seguidas por una lectura de su resultado y sus límites de comparabilidad. |
| 10 | Simplificar la conclusión | Cumplido | La conclusión sigue propuesta, evaluación, hallazgos y crecimiento futuro del método, sin subtítulos artificiales dentro del texto. |

## Auditoría narrativa de figuras

| Figura | Trabajo narrativo | Relación con las demás | Decisión |
|---:|---|---|---|
| 1 | Presenta la pregunta visual central: individual frente a completa frente a seleccionada, desde la imagen hasta la evaluación. | Es el mapa general; no explica los pasos internos de GFS ni los folds. | **Conservar.** |
| 2 | Explica cómo GFS prueba candidatos, valida y añade el mejor bloque de forma iterativa. | Amplía únicamente la rama “seleccionada” de la Figura 1. | **Conservar.** |
| 3 | Explica la separación entre selección interna y evaluación externa. | Complementa la Figura 1 desde la perspectiva de control de fuga, no desde la representación. | **Conservar, corregida.** Se añadió un nodo explícito de evaluación externa para evitar que el test pareciera entrar al ajuste final. |
| 4 | Representaba reducción dimensional frente a diferencia de macro-F1. | Repetía el panel B de la tabla principal y la subsección de dimensionalidad. | **Eliminar.** La información permanece en tabla y texto, donde es más precisa. |

## Veredicto

Los diez requisitos están cubiertos. Las tres figuras restantes forman una secuencia no redundante: **qué se compara** (Figura 1), **cómo se selecciona** (Figura 2) y **cómo se evita consultar el test durante la selección** (Figura 3). La antigua Figura 4 no añadía una función narrativa independiente y fue retirada.
