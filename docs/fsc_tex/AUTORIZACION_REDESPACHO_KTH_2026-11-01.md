# Redespacho KTH con alias de ruta corregido

## Material Passport

- Autoridad: usuario respondió «Sí, despachar las ocho mediciones con la ruta corregida».
- Fecha:01-11-2026. Alcance: ocho condiciones online KTH, no nuevos ajustes.
- Estado: autorización posterior al fallo de ruta, no permiso de retries futuros.

Conservar todos los estados/logs de las ocho condiciones originales que fallaron
antes de extraer/medir imágenes. Usar nuevos directorios, mismos fitted_heads,
predicciones de calidad, frozen_decisions, índices externos, recetas, semillas,
presupuesto, normalización y batch1/repeat1. No recalcular selección ni entrenar.

Nuevo ejecutor benchmark_local_single_image_alias_v1.py: copia del original con
único cambio de resolución del archivo DeiT: KTHTIPS2b→KTH-TIPS2-b. Test AST
comprueba igualdad de todo cálculo/cronómetro salvo helper y expresión de ruta.
No editar benchmark original ni scripts activos. Conservar hashes de ambos.
Reusar binding KTH aprobado, tolerancia1e-4, estado de pooler hashverificado.

Cola nueva de ocho condiciones, benchmark y auditoría por condición. Mismo lock
GPU global de Soil: solo una tarea GPU a la vez. Observador externo cada30s,
sin polling GPU adicional, overhead declarado y sin alterar ruta medida.
El worker puede esperar sin competir con el benchmark activo. Ventana10h para
despachar; no matar al expirar ventana una tarea iniciada dentro de su timeout.
Reanudar solo tareas jamás despachadas; un nuevo fallo requiere revisión, no retry.

F1 y tiempos siempre de las mismas llamadas online. Las medias KTH solo se
calculan al completar cuatro splits por clasificador. Esta corrección no elimina
reservas sobre equivalencia de la cascada histórica ni certifica hardware aislado.
No manuscrito, commits/push, VisTex ni papers antes de cerrar el panel local.
