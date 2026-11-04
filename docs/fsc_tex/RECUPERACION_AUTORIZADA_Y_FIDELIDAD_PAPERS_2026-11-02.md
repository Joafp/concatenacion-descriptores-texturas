# Recuperación autorizada y fidelidad a los papers

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: corrección de infraestructura y revisión de reproducibilidad.
- Origin Date: 2026-11-02, America/Asuncion.
- Verification Status: autorización nueva registrada; resultados pendientes.

## Autoridad y criterio de cierre

Solicitud nueva del autor: «fixeemos todo y demos por cerrado una vez que
tengamos los mismos numeros que los papers». Autoriza corregir y volver a
ejecutar los casos afectados, preservando intentos anteriores. No autoriza
seleccionar semillas, omitir imágenes ni ajustar parámetros contra el resultado
publicado. No garantiza que los números coincidan. Se separan dos objetivos:

1. Cerrar el panel común ADAPTADO mediante recuperaciones de infraestructura.
2. Reconstruir una receta fiel por paper, con métrica, dataset, partición,
   entrenamiento y pesos verificables, antes de reclamar reproducción.

Un panel adaptado completo no satisface por sí solo el segundo objetivo.
Resultados discrepantes siguen visibles y requieren explicación, no maquillaje.
No se utiliza como tolerancia científica el valor genérico del skill.

## Dos recuperaciones delimitadas

- HyTexNet/Outex: nuevo preflight añade `checkpoint_sha256` faltante, igual al
  hash ya verificado y sellado del checkpoint local DenseNet. Mismos índices,
  fuentes, método, biblioteca y presupuesto. Nuevo directorio, cuatro etapas.
- CellNN/FMD seed42/fold0: nueva extracción y nuevo fit, sin reutilizar el head
  parcial. Runner v2 ya existente convierte escalares NumPy a escalares Python
  sin modificar su valor. Misma receta, tolerancias y cronómetro. Cuatro etapas.

Una sola ejecución nueva autorizada por caso. Fallo nuevo requiere revisión,
sin autoretry. Los otros 14 casos CellNN no se repiten. El panel local 94/94
permanece intacto. CPU dos hilos y lock GPU global durante todas las etapas.
No descargas, manuscrito, commits ni contactos a autores.

## Neshov y fidelidad original

No reanudar su cola fallida. Diagnosticar la diferencia batch1/batch8 antes de
aprobar una nueva corrida. No cambiar kernels, precisión, capas, normalización
o tolerancias solamente para forzar el gate. Un diagnóstico numérico separado
no constituye un resultado F1/latencia ni una reproducción aceptada.

HyTexNet conserva decisiones locales de entrenamiento y un backbone congelado
ante ambigüedad de la fuente. CellNN usa fuente/pesos de autores pero evaluación
común y parámetros locales explícitos. Mantener ambos nombres como adaptados
hasta contrastar cada diferencia contra las fuentes primarias.
