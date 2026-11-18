# Pendientes para Joaquín: paper Top-k directo vs activación por margen

Fecha: 2026-11-18 (actualizado a la noche) · De: Carlos · Para: Joaquín

Joaco, junté acá todo lo que queda pendiente del paper (`carlos/main.tex`) y
que necesita tu máquina, tus datos o tu decisión. Yo no corro experimentos;
cuando algo esté, avisame qué carpeta queda como canónica y actualizo el paper.

## Actualización 18-11 (noche): lo que integré de tu paquete

Gracias por `results/metricas_compartidas_20261118_v1/` (commit `f635a5b`).
Con eso ya entraron al paper:

- **E4, cascada con ResMLP (27/27).** Está en §4.7, la discusión, la
  conclusión y la tabla de ablación (Tabla 14).
  - Top-4 directo 0,9428 frente a 0,9424 por margen; diferencia media −0,0003.
  - Cota inferior de no inferioridad: −0,0021.
  - Escala el 22,5 % de las imágenes.
  - Saqué de las limitaciones «la comparación usa solo SVM». La diapositiva 15
    ya tiene fuente.
- **E5, Top-4 + N-gramas (47/47).** Está en §4.6, la discusión, la conclusión
  y la Tabla 14.
  - La media pasa de 0,9442 a 0,9489, por encima de Completa-22 (0,9473).
  - Tres datasets suben y tres bajan; Wilcoxon exacto bilateral da *p* = 1,0.
- **Cálculos.** Las medias por dataset y la no inferioridad de E4 las calculé
  con `carlos/analisis_paper/e4_e5_resumen.ps1`, a partir de tus auditorías.

Antes de esto, ese mismo día, ya había agregado:
- **Al paper**, como pidió el revisor con el esquema de HyTexNet:
  - McNemar por condición y kappa;
  - media ± DE entre particiones;
  - calidad de la compuerta;
  - matrices de confusión;
  - ejemplos mal clasificados de KTH;
  - la tabla de ablación.
- **Un informe de revisión de consistencia:**
  [revision_paper/RONDA5_CONSISTENCIA.md](revision_paper/RONDA5_CONSISTENCIA.md).
- **La comparación con HyTexNet:**
  [revision_paper/ESQUEMA_HYTEXNET.md](revision_paper/ESQUEMA_HYTEXNET.md).

## Resumen

| # | Qué | Tipo | Prioridad | Estado |
|---|---|---|---|---|
| 1 | Latencia online de E1: Top-4 directo frente a la cascada por margen con Top-4 | Experimento | **Alta** | Pendiente |
| 2 | DeepLumina: completar DTD `f3` y corregir la convergencia | Experimento | **Alta** | Pendiente |
| 3 | E4: cascada con ResMLP | Experimento | — | **Integrado el 18-11** |
| 4 | Reservas de KTH (evaluación estática) y Outex (DeiT-S) | Verificación | **Alta** | Pendiente |
| 5 | Parámetros y GFLOPs de nuestras 16 redes | Cálculo sin entrenar | Media | Pendiente (el de HyTex ya está) |
| 6 | Figura con ejemplos mal clasificados | — | — | **Hecho por Carlos** (Figura 5) |
| 7 | t-SNE de los embeddings de Top-4 | Cálculo sin entrenar | Media | Pendiente |
| 8 | Curvas de entrenamiento de ResMLP, si se guardaron | Consulta | Media | Pendiente |
| 9 | E6: diagnóstico de ViT-B/16 online frente a guardado (Soil y CUReT) | Diagnóstico | Media | Pendiente |
| 10 | E5: Top-4 más el bloque de color | Experimento | — | **Integrado el 18-11** |
| 11 | E1 con otras semillas | Experimento | Baja | Pendiente |
| 12 | Robustez de Top-4 a ruido y brillo, y evaluación cruzada entre datasets | Experimento | Opcional | Pendiente (la de HyTex en FMD ya está) |
| 13 | E7 (memoria de GPU) y E8 (variación entre equipos con ResMLP) | Experimento | Opcional | Pendiente |
| 14 | Decisiones y declaraciones de los autores | Decisión | **Alta** | Pendiente |
| 15 | E4: etapa barata, costo proyectado y predicciones por imagen | Datos que faltan | Media | **Nuevo** |
| 16 | ¿Qué receta de HyTexNet va en la tabla de métodos recientes? | Decisión | Media | **Nuevo** |

## 1. Latencia online de E1 (alta)

Es lo más importante que falta. El 75 % de ahorro del paper es una
**proyección** a partir de costos por componente. La única medición física es
la de la cascada anterior, con la Top-k archivada. Vos ya lo habías nombrado
como siguiente paso.

- **Qué:** medir en línea Top-4 directo y la cascada por margen con Top-4.
- **Cómo:** el mismo protocolo del panel. RTX 4060, `batch=1`, modelos
  residentes, y la accuracy y la latencia tomadas de las mismas llamadas.
- **Condiciones:** las 27 de E1, o al menos una por dataset, como el piloto.
- **Verificación:** que las rutas y las predicciones coincidan con las de los
  embeddings almacenados, y los cosenos por bloque.
- **Salida:** media, mediana y p95 por política y dataset.

En el paper actualizo la §4.9 (medición física), la discusión y las
limitaciones. La plantilla está lista en
[PLANTILLAS_RESULTADOS_PENDIENTES.md](PLANTILLAS_RESULTADOS_PENDIENTES.md).

## 2. DeepLumina (alta)

Está detallado en [PEDIDO_DEEPLUMINA_JOAQUIN.md](PEDIDO_DEEPLUMINA_JOAQUIN.md):
- **A:** completar DTD `s42_f3` sin el límite de 1 h.
- **B:** escalar los rasgos y subir `max_iter` en las 47 condiciones.
- **C (opcional):** un SVM más parecido al de MATLAB.

## 4. Reservas de KTH y Outex (alta)

Hoy el paper las declara como reservas, no como errores. Si se pueden cerrar,
salen de las limitaciones:
- **KTH-TIPS2-b, evaluación estática:** ¿los controles archivados de 22
  bloques corresponden a la variante con agrupación interna por muestra física?
  Una pista que salió el 18-11:
  - Individual de KTH viene de `results/extensions/kth_tips2b/ngram22_beitv2/`
    y da 0,9415.
  - El primer bloque del ranking de la curva de *k* da 0,9360, igual que
    `inner_group_sample/`.
  - Las dos variantes eligen bloques distintos en cada partición.
  - En los otros cinco datasets, Individual y el primer bloque coinciden
    exactamente.

  Lo explico en la §4.12 del paper.
- **Outex:** el arreglo histórico de DeiT-S, que entra en Completa-22 pero no
  en Top-4, no coincide con el del panel. ¿Cuál es el correcto? Esta reserva
  pesa porque la ventaja de Completa-22 sobre Top-4 sale sobre todo de Outex.
  Ahora pesa también en E5: Top-4 + N-gramas gana +0,0324 en Outex, el mayor
  aumento de los seis datasets.

## 5, 7 y 8. Cálculos sin entrenar (media)

En esta compu no hay Python.

5. **Parámetros (M) y GFLOPs** de nuestras 16 redes, con la resolución de
   entrada que usamos. Vi que ya hiciste el perfil de HyTex
   (`hytex_resource_profile_by_dataset_20261116_v1/`, 0,926 GMAC). Con la
   misma convención para las nuestras armo una tabla como las Tablas 4 y 8 de
   HyTexNet. Los ms por bloque ya están en `component_costs_ms`; esa columna
   la agrego yo.
7. **t-SNE** de los embeddings concatenados de Top-4 en KTH-TIPS2-b, coloreado
   por clase. Debería verse el solapamiento algodón–lino, sobre todo de la
   muestra b. Los embeddings están en `embeddings*/`, fuera de git.
8. **Curvas de ResMLP.** ¿Guardaste las de pérdida y accuracy por época? Si
   están, decime dónde. Las de SVM no aplican, porque no entrena por épocas.

## 9, 11, 12 y 13. Diagnóstico y experimentos de menor prioridad

Los protocolos de 9 y 13 están en
[EXPERIMENTOS_PENDIENTES.md](EXPERIMENTOS_PENDIENTES.md).

9. **E6.** Encontrar por qué ViT-B/16 extraído en línea no coincide con el
   guardado en Soil y CUReT. Explicaría la diferencia de Soil entre el panel y
   la evaluación estática.
11. **E1 con otras semillas** (por ejemplo 123 y 2026, en FMD y Soil, que ya
    las tienen en la evaluación estática). Hoy la comparación pareada usa una
    sola semilla.
12. **Robustez de Top-4, solo si el revisor insiste.** Ya está la robustez de
    HyTex en FMD (brillo ×1,2 y ruido σ = 0,1·255). Para compararla con
    nuestro método hace falta lo mismo para Top-4 directo y la cascada, en las
    mismas 15 condiciones de FMD y con las mismas perturbaciones. La
    evaluación cruzada entre datasets sigue sin hacerse.
13. **E7 y E8.**
    - E7: memoria de GPU por política.
    - E8: la misma condición de Top-4 con ResMLP corrida en GPU y en CPU.

E3 ya no hace falta: E1 cubrió los seis datasets.

## 14. Decisiones y declaraciones (alta)

- **No inferioridad.** El paper afirma que la cascada es no inferior a Top-4
  directo (δ = 0,01, definida después de ver los resultados); la tesis evita
  esa afirmación. Ahora el paper también la calcula para E4 con ResMLP. Hay
  que alinear ambos textos. ¿La mantenemos con la reserva o la sacamos?
- **Declaraciones**, de todos los autores y el tutor: ética, conflicto de
  intereses, financiamiento, uso de IA y contribuciones (CRediT). Hoy figuran
  como «Pendiente de confirmación por los autores».
- **Versión archivada.** El repo es tuyo (`Joafp`). Para la disponibilidad de
  datos y código conviene una versión con DOI, por ejemplo un release en
  Zenodo.

## 15. E4: datos que faltan (nuevo)

La auditoría `e4_resmlp_complete_audit_20261116_v1/summary.json` trae accuracy,
macro-F1 y fracción escalada por condición, pero no:
- la **etapa barata y el cuantil** elegidos en cada condición;
- el **costo proyectado** de cada ruta. Por eso el paper dice que E4 «no
  informa costos proyectados»;
- las **predicciones por imagen**, que harían falta para repetir con ResMLP el
  análisis por imagen de la §4.8 (McNemar y calidad de la compuerta).

Tu informe de cierre cita `results/analysis/e4_resmlp_fixed_20261116_v1/`
(`manifest.json` y `status.json`), pero esa carpeta no está en el repo. Si
podés, subí los JSON de resultados por condición, sin los modelos, o decime
dónde están.

## 16. Qué receta de HyTexNet usamos (nuevo)

En tu paquete hay una receta nueva de HyTex con ajuste fino del último bloque,
33/33 en FMD, CUReT, Soil y Outex (`hytex_paper_metrics_20261116_v3/`). La
tabla de métodos recientes del paper (Tabla 13, §4.11) usa la «HyTex local
adaptation» de `external_paper_metrics_20261116_v2/`.

| Dataset | Tabla 13 (adaptación local) | Receta con ajuste fino |
|---|---:|---:|
| FMD | 0,7417 | 0,7417 |
| CUReT | 0,9831 | 0,9911 |
| Soil | 0,8509 | 0,8675 |
| Outex | 0,8956 | 0,8559 |
| DTD | 0,6260 | — |
| KTH | 0,8392 | — |

FMD coincide exactamente. ¿La fila de FMD de la adaptación local ya es la
receta ajustada? DTD y KTH no se corrieron con la nueva receta. Opciones:
- dejar la adaptación actual en la tabla y mencionar la nueva en el texto;
- reemplazarla en los cuatro datasets, con DTD y KTH vacíos;
- correr DTD y KTH con la receta nueva.

¿Cuál preferís? Yo no mezclaría recetas en una misma fila.

## Reglas para cualquier corrida

- Toda selección (bloques, umbral, ruta, compuerta) se hace solo con el
  entrenamiento externo, y el test se consulta una vez.
- Mismas particiones, semillas y perfiles de costo que la evaluación que se
  reemplaza; si algo cambia, se documenta.
- Las corridas originales quedan intactas, y se informan las versiones vieja y
  nueva lado a lado, salga como salga.
- Registrá hashes de entradas y salidas, como en
  `results/analysis/consultas_joaquin_20261114_v1/`.
