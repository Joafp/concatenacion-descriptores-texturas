# Piloto: diversidad de Carlos como rescate adaptativo

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: validate
- Origin Date: 2026-10-21
- Verification Status: ANALYZED
- Version Label: carlos_hybrid_v1
- Alcance: desarrollo dentro del entrenamiento oficial de Outex; comparación descriptiva, sin evaluación externa ni medición física.

## Pregunta y variantes

Se prueba si el ensamble de diversidad de Carlos puede funcionar como segunda etapa: una base individual resuelve las imágenes confiables y deriva las inciertas. Se compara el ensamble permanente con la cascada completa y con su reducción bajo presupuesto.

1. **Siempre activo:** mismos 15 miembros y voto soft del control auditado.
2. **Rescate completo:** mismos 15 miembros, conservando repeticiones como ponderación del voto; se eligen base y cuantil de activación internamente. Base sola sigue siendo una opción.
3. **Rescate podado marginal:** hasta tres modelos únicos extraídos de esos miembros, seleccionados por ganancia/costo marginal.
4. **Rescate podado por relevancia:** mismo pool y presupuesto, selección por ganancia sola.

La poda no optimiza los pesos de los 15 votos: cada modelo único seleccionado recibe el mismo peso. Por tanto, no se interpreta como una réplica del ensamble completo con menos tiempo. Es una ablación adicional. Se conserva el rescate de pool emparejado anterior como control de desarrollo.

## Protocolo

Outex13Official1360 official1, seed42, 680 imágenes de entrenamiento, tres folds productores y tres internos. Biblioteca de 22, SVD de N-grams ajustada por fit. Presupuestos 15/30/60/120 ms y cuantiles 0,1/0,25/0,5; bases en frontera calidad/costo individual. Ninguna selección usa las etiquetas de validación productora. El ranking y CKA que generan el ensamble se calculan dentro del fit productor; la poda y compuerta se seleccionan con sus scores internos.

Se reutilizan las predicciones de validación de los miembros ya entrenados en `integration_v6/carlos_outex22_20261021`, con hashes de entradas, fuentes y particiones comprobados. Se ajustan nuevos scores OOF internos para sus miembros faltantes y se ajustan las bases seleccionadas. No se presenta esta reutilización como reentrenamiento independiente del control.

El costo por imagen es `c(base) + overhead + gate × c(unión de rescate menos base)`, o solo `c(base)` cuando no hay rescate. Cada extractor se cobra una vez; modelos repetidos mantienen su voto pero se ejecutan una vez. La latencia del clasificador, carga/residencia y memoria no están incluidas; se registra el número de llamadas. El límite es medio en selección, no una garantía en validación o por imagen.

## Artefactos

- Implementación: `src/carlos_hybrid.py`, `src/run_carlos_hybrid.py`.
- Auditor: `src/audit_carlos_hybrid.py`.
- Pruebas: `tests/test_carlos_hybrid.py`; 21 pruebas específicas totales aprobadas, sin ejecutar la suite completa.
- Corrida: `results/exploratory/integration_v8/carlos_hybrid_outex22_20261021`.
- Referencia de pool anterior: `results/exploratory/integration_v7/outex_paired22_20261021`.

## Resultados completados y auditados

La corrida terminó con código 0. Sus 13 políticas cubren las mismas 680 imágenes. Auditoría en `results/analysis/integration_v8/carlos_hybrid_outex22_20261021`: 36 decisiones reproducidas exactamente desde scores guardados, 13 resultados recalculados, 9 proyecciones SVD internas comprobadas y predicciones del ensamble permanente idénticas al control de Carlos. Se comprobaron hashes de fuentes, entradas y artefactos reutilizados, rutas por imagen, escalas heredadas y costos. El replay no es reproducción independiente de los ajustes.

| Variante | Presupuesto | Macro-F1 | ms proyectados | Llamadas medias |
|---|---:|---:|---:|---:|
| Carlos diversidad siempre activo | — | 0,914389 | 365,196 | 10,665 |
| Rescate completo | 15 | 0,858056 | 12,220 | 1,000 |
| Podado marginal | 15 | 0,858056 | 12,220 | 1,000 |
| Podado relevancia | 15 | 0,858056 | 12,220 | 1,000 |
| Rescate completo | 30 | 0,854129 | 20,485 | 1,000 |
| Podado marginal | 30 | 0,893488 | 25,394 | 1,201 |
| Podado relevancia | 30 | 0,893488 | 25,394 | 1,201 |
| Rescate completo | 60 | 0,891759 | 57,839 | 2,266 |
| Podado marginal | 60 | 0,905140 | 55,365 | 1,672 |
| Podado relevancia | 60 | 0,910742 | 53,316 | 1,654 |
| Rescate completo | 120 | 0,908603 | 104,660 | 3,694 |
| Podado marginal | 120 | 0,908781 | 84,018 | 1,715 |
| Podado relevancia | 120 | 0,909396 | 78,938 | 1,656 |

A 15 todas las variantes eligen base sola. A 30 el rescate completo también elige base sola, aunque cambia la base según el fold; no confundir la etiqueta de política con un escalado efectivamente ejecutado. La calidad de validación no es monótona con el presupuesto.

### Comparación con controles

El rescate previo de pool emparejado marginal/60 obtuvo 0,889123/30,725 ms y relevancia/60 0,889838/42,577 ms. A 120, marginal obtuvo 0,906690/83,772 y relevancia 0,907233/89,325. El nuevo podado por relevancia/60 obtiene más F1 y menor costo proyectado que ambos puntos previos de 120; frente a los puntos de 60 aumenta calidad y también costo. Son comparaciones descriptivas de un piloto y no un contraste inferencial.

Top-5 obtiene 0,900824/288,435 ms; Completa-22 0,913957/1706,420. El podado relevancia/60 supera numéricamente Top-5, pero no a Completa-22 ni al ensamble de Carlos permanente. Respecto de este último, la diferencia de F1 es −0,003646 (−0,3646 puntos porcentuales en la escala porcentual) y el costo proyectado es 85,40 % menor. No equivale a demostrar no inferioridad ni ahorro físico de 85,40 %.

La poda por relevancia supera a la poda marginal en calidad y costo en los puntos de 60 y 120 de este piloto. Por tanto, los resultados no respaldan atribuir la ventaja a la razón ganancia/costo marginal: el pool de diversidad y el enrutamiento selectivo son explicaciones alternativas que deben aislarse mediante ablaciones. El punto relevancia/60 es prometedor descriptivamente, no una configuración elegida para despliegue con evidencia externa.

### Complementariedad y excedencias

Podado relevancia/60 deriva 278/680 imágenes (40,88 %). En ellas corrige 52 errores de la base e introduce 5 errores donde la base acertaba. El saldo de 47 aciertos se refiere a esas bases por fold, no a una ganancia equivalente de macro-F1 ni al descriptor Individual del benchmark. Las bases seleccionadas son DINOv2-small, BEiT-v2-final y VGG16; los rescates tienen 2, 2 y 1 modelos únicos respectivamente.

Los 36 presupuestos medios internos se cumplen. Hay una excedencia de validación: rescate completo/60/fold1 llega a 70,019604 ms, frente a 59,602804 ms internos. Las 24 selecciones podadas no exceden en estos artefactos; esto no garantiza futuros presupuestos. El promedio global del rescate completo/60 (57,838882) oculta dicha excedencia.

### Ejecución reproducible

```bash
PYTHONPATH=.:src OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  .venv-confirmatory/bin/python src/run_carlos_hybrid.py \
  --reference-run results/exploratory/integration_v7/outex_paired22_20261021 \
  --carlos-run results/exploratory/integration_v6/carlos_outex22_20261021 \
  --output results/exploratory/integration_v8/carlos_hybrid_outex22_20261021
```

La salida debe ser nueva/vacía; el comando documenta la corrida realizada, no autoriza sobrescribir sus resultados. El auditor usa `--run` sobre ese directorio y `--output` nuevo.

## Riesgos de interpretación — 11/11 revisados

1. Simpson: conservar todas las variantes y presupuestos, no solo la media o el máximo.
2. Ecológica: no extrapolar Outex a seis datasets ni el costo medio a cada imagen.
3. Berkson: dataset de desarrollo seleccionado; generalización pendiente.
4. Colisionador: el subconjunto incierto es una selección del gate; no comparar su dificultad como si fuera aleatorio.
5. Tasas base: F1 macro no equivale a accuracy ni a valor predictivo diagnóstico.
6. Regresión a la media: el punto más favorable del piloto exige evaluación posterior.
7. Supervivencia: conservar inviabilidad, base sola, excedencias y todos los presupuestos.
8. Búsqueda múltiple: no inferencia sobre un ganador elegido retrospectivamente.
9. Caminos analíticos: hipótesis informada por resultados anteriores; estudio exploratorio.
10. Causalidad: no atribuir ahorro físico al costo analítico ni mejor calidad a un mecanismo no aislado.
11. Causalidad inversa: no aplica temporalmente; no inventar mecanismos causales.

## Criterio de continuación

El piloto aporta puntos útiles del ensamble podado frente al rescate anterior; el ensamble completo como rescate no es la mejor opción observada. Continuar con ambos criterios de poda como ablaciones, sin favorecer retrospectivamente el marginal. Antes del panel de 27: réplica en otro dataset con CV armonizado, estabilidad por semilla, sensibilidad de base, comparación de cada ensamble podado siempre activo frente al mismo ensamble con gate, controles GFS/cascada reconciliados y congelamiento. Esta última ablación distingue ganancia por poda de ganancia por enrutamiento. La novedad no queda demostrada por combinar ensamble y cascada. No cambiar todavía las cifras del manuscrito.
