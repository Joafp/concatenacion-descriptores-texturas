# P2: pool emparejado de rescates en Outex

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: validate
- Origin Date: 2026-10-21
- Verification Status: ANALYZED
- Version Label: paired_pool_v1
- Alcance: desarrollo OOF dentro del entrenamiento oficial; no evaluación externa ni reproducción independiente de ajustes.

## Cambio implementado

El evaluador anterior permanece intacto. `src/run_budgeted_rescue_paired.py` usa un núcleo de 21 bloques estáticos, ordenados por su F1 interno. Incluye Top-2/3/4/5, cinco sorteos ponderados de cuatro bloques (beta=8) y los tres estáticos más baratos. Se eliminan duplicados. Cada candidato tiene dos versiones en la biblioteca de 22: sin color y con RGB N-grams+SVD. La posición de N-grams no altera los sorteos estáticos.

Se conservan las funciones de ranking/muestreo utilizadas por Carlos y la selección greedy bajo presupuesto. Esto no es una nueva demostración de superioridad frente a sus ensambles de 15 miembros. La comparación con ellos sigue siendo calidad frente a costo, no un ganador único.

La frontera de bases admite todos los bloques disponibles: N-grams puede ser base en 22. Por tanto, esta comparación estudia disponibilidad de color bajo un pool emparejado, no mantiene fija la ruta; la ablación anterior de ruta fija responde otra pregunta.

## Protocolo y trazabilidad

- Outex13Official1360, official1, seed42; 680 imágenes del entrenamiento oficial, tres folds productores y tres internos.
- Dos bibliotecas: 21 estáticos y 22 incluyendo N-grams con SVD ajustada por fit.
- Presupuestos 15/30/60/120 ms; cuantiles 0,1/0,25/0,5; máximo tres miembros.
- Presupuesto medio proyectado en selección, no límite garantizado fuera de muestra ni medición física. No incluye tiempo del clasificador.
- Resultados nuevos: `results/exploratory/integration_v7/outex_paired21_20261021` y `outex_paired22_20261021`.
- Auditor de decisiones: `src/audit_budgeted_rescue.py`, separado por corrida.
- Auditor de emparejamiento: `src/audit_paired_rescue_pool.py`.
- Pruebas específicas: 18 aprobadas. No se ejecutó la suite completa.

## Ejecución y auditoría completadas

Ambas corridas finalizaron con código 0 y cobertura de 680 imágenes por política. Se reprodujeron 48 selecciones y 26 resultados desde scores guardados; se auditaron las 12 proyecciones SVD de la corrida con color. Esto no constituye reproducción independiente del entrenamiento.

El auditor emparejado verificó en los tres folds: índices productores e internos idénticos, ranking estático idéntico, scores individuales y de rescates comunes iguales con tolerancia absoluta 1e-12, reconstrucción determinista del pool y cierre exacto con/sin color. Tamaños: 8/16, 9/18 y 9/18 candidatos para 21/22 bloques.

Auditorías: `results/analysis/integration_v7/paired21_replay`, `paired22_replay` y `paired_pool`. Los hashes de fuentes coincidieron en los dos replays. `paired_pool/comparison.csv` contiene las 26 filas, incluidos los controles.

### Resultados de desarrollo OOF

| Regla / presupuesto | F1 sin color | ms sin color | F1 con color | ms con color |
|---|---:|---:|---:|---:|
| Marginal / 15 | 0,858056 | 12,220 | 0,858056 | 12,220 |
| Relevancia / 15 | 0,858056 | 12,220 | 0,858056 | 12,220 |
| Marginal / 30 | 0,857483 | 19,969 | 0,882821 | 25,271 |
| Relevancia / 30 | 0,857483 | 19,969 | 0,884590 | 25,271 |
| Marginal / 60 | 0,885153 | 53,533 | 0,889123 | 30,725 |
| Relevancia / 60 | 0,886089 | 49,894 | 0,889838 | 42,577 |
| Marginal / 120 | 0,900563 | 97,245 | 0,906690 | 83,772 |
| Relevancia / 120 | 0,896500 | 93,726 | 0,907233 | 89,325 |

Los ms son costos medios proyectados, no latencias físicas. Con color, los controles son Individual 0,871642/177,300 ms; Top-3 0,882967/236,862; Top-4 0,884244/256,272; Top-5 0,900824/288,435; Completa-22 0,913957/1706,420. Completa-21 obtiene 0,902203/1687,920.

La regla marginal/120 con color supera numéricamente Top-5 en este piloto, pero queda debajo de Completa-22 y de diversidad soft de Carlos (0,914389/365,196 ms en la corrida emparejada anterior). No hay dominancia de calidad frente a esos dos controles. La regla marginal tampoco domina relevancia: a 120 tiene menor costo y algo menos F1; a 30 ambas tienen igual costo y relevancia mayor F1.

Al permitir color y reseleccionar, marginal/120 cambia 0,900563→0,906690 y 97,245→83,772 ms. No es simplemente cobrar menos por añadir un descriptor: se eligieron rutas diferentes. Las tres rutas marginal/120 usan N-grams en algún rescate, pero ninguna como base. La versión corregida con color obtiene menos F1 que el antiguo piloto de pool desigual (0,909417); conservar y reportar ambos, sin seleccionar retrospectivamente el mayor como evidencia final.

### Excedencias y límites

Los 48 presupuestos internos se cumplen. En validación hay dos excedencias, ambas relevancia/60/fold1: 61,689648 ms sin color y 60,617841 con color. Ninguna de las 24 selecciones marginales excedió en estos artefactos; no implica garantía futura. Las medias globales ocultan esas excedencias por fold.

No se calcularon contrastes inferenciales del piloto. No se afirma equivalencia con Completa, novedad demostrada, generalización a otros datasets ni ahorro físico.

## Control de interpretaciones — 11/11 patrones revisados

1. Simpson: reportar presupuestos separados; un promedio no establece una ventaja universal.
2. Falacia ecológica: Outex no representa los seis datasets.
3. Berkson: selección de un dataset de desarrollo limita generalización.
4. Colisionador: las rutas se seleccionan internamente; no filtrar por aciertos externos.
5. Tasas base: macro-F1 multiclase; no interpretar como valor predictivo de cribado.
6. Regresión a la media: el mejor punto interno necesita evaluación externa.
7. Supervivencia: conservar todos los presupuestos, inviabilidad y fallos.
8. Búsqueda múltiple: no calcular p-valores sobre el punto más favorable del piloto.
9. Caminos de decisión: modificación informada por desarrollo; no es confirmación ciega.
10. Causalidad: disponibilidad de color con reselección no aísla una ruta fija.
11. Causalidad inversa: no aplica como inferencia temporal; no atribuir el desempeño a una explicación no ensayada.

## Siguiente criterio de avance

Emparejamiento de scores, particiones y candidatos cerrado; decisiones reproducidas y excedencias registradas. Faltan estabilidad por semilla, sensibilidad de base y controles GFS/cascada reconciliados. Solo entonces congelar la configuración antes del panel de 27 condiciones. No modificar aún las cifras de la tesis.
