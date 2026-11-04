# Enmienda autorizada: desbloqueo del panel local

## Material Passport

- Fecha: 01-11-2026. Ejecución técnica ARS; no revisión independiente.
- Autoridad: respuesta explícita del usuario a ambas preguntas: «Sí, autorizo
  esa enmienda versionada» y «Sí, repetir el split completo con observabilidad».
- Alcance: nuevos archivos únicamente; originales y fallos se conservan.
- No modifica manuscrito ni protocolo nocturno original. No commits/push.

## Outex y Soil: versión nueva de DeiT

La representación archivada no coincide con el pooler recuperado: errores
máximos 0,18–0,21 frente a tolerancia 1e-4. Tampoco coincide con ninguna otra
fila de sus archivos; un reordenamiento simple no explica los dos vectores
diagnosticados. Esto no identifica la causa ni recupera el estado perdido.
Outex no registra semilla/estado del pooler; Soil carece de metadata DeiT.

Se autoriza regenerar únicamente deit_s de Outex13Official1360 y SoilOriginal
mediante reextract_confirmatory_embeddings.py, seed42, batch16, checkpoint y
procesador locales originales. Se conserva el pooler fijo recuperado seed42,
no se lo llama preentrenado. No buscar semillas ni ajustar tolerancias.
Cada dataset se guarda en una raíz nueva; los otros bloques se vinculan a
archivos originales con hashes y no se regeneran. Etiquetas y filas deben
coincidir con manifiestos originales. No descargar modelos ni datos.

Comprobar una vez primera/última fila, tolerancia1e-4, contra la representación
NUEVA. No es repetición del diagnóstico sobre el archivo fallido ni lo valida.
Un nuevo fallo científico exige revisión, sin retry automático.

Para las 32 condiciones se recalculan OOF adaptativo y heads usando solo train,
con el ejecutor de calidad existente, y se auditan antes de medir. Se conservan
las recetas archivadas de los controles (Top-4, 15 miembros diversidad/tómbola),
el procedimiento de selección adaptativa y candidatos, biblioteca22, presupuesto60,
cuantiles, máximo3miembros, CPU2hilos, semillas42/123/2026, splits, agrupamientos
y transformaciones train-only. No se reranquean controles por resultados de test.
Las nuevas selecciones adaptativas se congelan antes de evaluar test; no se
copian las decisiones/heads de la representación anterior. Esta es una enmienda
de representación, no una reproducción bitwise del archivo histórico.

Cada celda F1/ms procede de las mismas llamadas batch1 online nuevas; los F1
previos se conservan como históricos y no rellenan columnas nuevas.

## KTH: habilitación acotada

La reconciliación local verificó 4752 imágenes y hashes, roles de los cuatro
splits invertidos (3564train/1188test), agrupación interna por muestra física,
21 bloques finitos con etiquetas alineadas y cache N-grams raíz configurado.
La discrepancia histórica de otro cache no pertenece al configurado.
Evidencia: results/analysis/blocker_resolution_20261101/kth_reconciliation.json.

Se habilita nueva calidad de ocho condiciones con configs originales, no
equivalencia con cascada histórica (distinta semilla interna/escala/selección).
Online depende del diagnóstico KTH nuevo y probado: alias KTH-TIPS2-b,
primera/última fila0/4751, pooler recuperado, tolerancia1e-4. Si falla, retener
online y conservar calidad; no regenerar KTH por la autorización Outex/Soil.

## DTD/SVM: segunda medición completa, no sustitución silenciosa

Repetir solo seed42 fold6/official7, cinco métodos, 1880 imágenes, repeat1,
misma calidad/heads/selección y receta física. Directorio nuevo. Conservar
original completo y sus extremos; reportar ambas versiones y su procedencia.
No elegir la versión por menor latencia, no fusionar llamadas ni borrar outliers.
La repetición autorizada es evidencia adicional de sensibilidad; no elimina
por sí sola la reserva física del original ni certifica hardware aislado.

Observador separado cada30s, UTC/monotónico/boottime, PID+startticks, CPU/RSS;
sin GPU polling adicional por defecto y sin modificar cronómetro/ruta. El
observador tiene overhead no nulo y no identifica eventos dentro de una llamada.
No se recuperaron eventos Windows útiles en la consulta local del intervalo;
su ausencia no prueba que no hubiera suspensión o contención.

## Ejecución y cierre

Una cola GPU serial para extracción/diagnóstico/benchmark; un worker CPU de
dos hilos para calidad/replay. Cada dependencia debe completar y validar su
estado/hash. Outputs nuevos, fuentes/configs hasheadas, locks, timeout propio,
sin retries automáticos. Un plazo de despacho no mata el trabajo activo.
La repetición DTD no aumenta cobertura: quedan94condiciones únicas previstas.
Solo contar nuevas celdas tras cobertura y auditoría completas. Papers después
de cerrar/adjudicar el panel local; no inventar permisos nuevos de réplica.
