# Pendientes para Joaquín: paper Top-k directo vs activación por margen

Fecha: 2026-11-18 · De: Carlos · Para: Joaquín

Joaco, junté acá todo lo que queda pendiente del paper (`carlos/main.tex`) y
que necesita tu máquina, tus datos o tu decisión. Yo no corro experimentos;
cuando algo esté, avisame qué carpeta queda como canónica y actualizo el paper.

Además del profesor, un revisor pidió tomar como referencia el esquema de
HyTexNet (KBS 2026). La comparación está en
[revision_paper/ESQUEMA_HYTEXNET.md](revision_paper/ESQUEMA_HYTEXNET.md). Lo que
se podía sacar de las predicciones guardadas ya lo integré el 18-11:
- McNemar por condición;
- kappa de Cohen;
- media ± DE entre particiones;
- calidad de la compuerta;
- matrices de confusión.

Lo que sigue es lo que no puedo hacer yo.

## Resumen

| # | Qué | Tipo | Prioridad |
|---|---|---|---|
| 1 | Latencia online de E1: Top-4 directo frente a la cascada por margen con Top-4 | Experimento | **Alta** |
| 2 | DeepLumina: completar DTD `f3` y corregir la convergencia | Experimento | **Alta** |
| 3 | E4 (cascada con ResMLP): la diapositiva 15 muestra resultados que no están en el repo | Subir resultados o correr | **Alta** |
| 4 | Reservas de KTH (evaluación estática) y Outex (DeiT-S) | Verificación | **Alta** |
| 5 | Parámetros y GFLOPs de cada red | Cálculo sin entrenar | Media |
| 6 | Figura con ejemplos mal clasificados (algodón → lino en KTH) | Cálculo sin entrenar | Media |
| 7 | t-SNE de los embeddings de Top-4 | Cálculo sin entrenar | Media |
| 8 | Curvas de entrenamiento de ResMLP, si se guardaron | Consulta | Media |
| 9 | E6: diagnóstico de ViT-B/16 online frente a guardado (Soil y CUReT) | Diagnóstico | Media |
| 10 | E5: Top-4 más el bloque de color | Experimento | Baja |
| 11 | E1 con otras semillas | Experimento | Baja |
| 12 | Robustez a ruido y brillo, y evaluación cruzada entre datasets | Experimento | Opcional |
| 13 | E7 (memoria de GPU) y E8 (variación entre equipos con ResMLP) | Experimento | Opcional |
| 14 | Decisiones y declaraciones de los autores | Decisión | **Alta** |

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
limitaciones.

## 2. DeepLumina (alta)

Está detallado en [PEDIDO_DEEPLUMINA_JOAQUIN.md](PEDIDO_DEEPLUMINA_JOAQUIN.md):
- **A:** completar DTD `s42_f3` sin el límite de 1 h.
- **B:** escalar los rasgos y subir `max_iter` en las 47 condiciones.
- **C (opcional):** un SVM más parecido al de MATLAB.

## 3. E4: cascada con ResMLP (alta)

La diapositiva 15 de `Defensa_texturas_diagramas_v2.pdf` («Resultados E4: la
comparación con ResMLP») muestra resultados, pero no encuentro su fuente en el
repo. Hoy toda la comparación pareada del paper es con SVM.
- **Si lo corriste:** subí la carpeta y decime cuál es la canónica.
- **Si no:** el protocolo está en
  [EXPERIMENTOS_PENDIENTES.md](EXPERIMENTOS_PENDIENTES.md#e4-cascada-con-resmlp).
  Es el mismo de E1, con el margen tomado de los logits de ResMLP. Hasta que
  esté, conviene sacar esa diapositiva de la presentación.

## 4. Reservas de KTH y Outex (alta)

Hoy el paper las declara como reservas, no como errores. Si se pueden cerrar,
salen de las limitaciones:
- **KTH-TIPS2-b, evaluación estática:** ¿los controles archivados de 22
  bloques corresponden a la variante con agrupación interna por muestra física?
- **Outex:** el arreglo histórico de DeiT-S, que entra en Completa-22 pero no
  en Top-4, no coincide con el del panel. ¿Cuál es el correcto? Esta reserva
  pesa porque la ventaja de Completa-22 sobre Top-4 sale sobre todo de Outex.

## 5 a 8. Cálculos sin entrenar (media)

En esta compu no hay Python. Lo que sigue lo pidió el esquema de HyTexNet.

5. **Parámetros (M) y GFLOPs** de las 16 redes, con la resolución de entrada que
   usamos (`fvcore`, `thop` o el contador de `timm`). Con eso armo una tabla como
   las Tablas 4 y 8 de HyTexNet. Los ms por bloque ya están en
   `component_costs_ms`; esa columna la agrego yo.
6. **Ejemplos mal clasificados.** Una figura con 4 a 6 imágenes de algodón que
   Top-4 y la cascada predicen como lino. Los índices de test y las
   predicciones están en `carlos/analisis_paper/e1_por_imagen.csv` (KTH, clase
   real 4, predicha 7); falta mapearlos a los archivos con el manifiesto de KTH.
7. **t-SNE** de los embeddings concatenados de Top-4 en KTH-TIPS2-b, coloreado
   por clase. Debería verse el solapamiento algodón–lino. Los embeddings están
   en `embeddings*/`, fuera de git.
8. **Curvas de ResMLP.** ¿Guardaste las de pérdida y accuracy por época? Si
   están, decime dónde. Las de SVM no aplican, porque no entrena por épocas.

## 9 a 13. Diagnóstico y experimentos de menor prioridad

Los protocolos de 9, 10 y 13 están en
[EXPERIMENTOS_PENDIENTES.md](EXPERIMENTOS_PENDIENTES.md).

9. **E6.** Encontrar por qué ViT-B/16 extraído en línea no coincide con el
   guardado en Soil y CUReT. Explicaría la diferencia de Soil entre el panel y
   la evaluación estática.
10. **E5.** Top-4 más `rgb_ngram_svd` en las 47 condiciones. El ranking nunca
    pudo elegir el bloque de color.
11. **E1 con otras semillas** (por ejemplo 123 y 2026, en FMD y Soil, que ya
    las tienen en la evaluación estática). Hoy la comparación pareada usa una
    sola semilla.
12. **Experimentos al estilo HyTexNet**, solo si el revisor insiste:
    - robustez de Top-4 y de la cascada con ruido gaussiano y +20 % de brillo
      en las imágenes de test;
    - evaluación cruzada entre datasets.
13. **E7 y E8.**
    - E7: memoria de GPU por política.
    - E8: la misma condición de Top-4 con ResMLP corrida en GPU y en CPU.

E3 ya no hace falta: E1 cubrió los seis datasets.

## 14. Decisiones y declaraciones (alta)

- **No inferioridad.** El paper afirma que la cascada es no inferior a Top-4
  directo (δ = 0,01, definida después de ver los resultados); la tesis evita
  esa afirmación. Hay que alinear ambos textos. ¿La mantenemos con la reserva
  o la sacamos?
- **Declaraciones**, de todos los autores y el tutor: ética, conflicto de
  intereses, financiamiento, uso de IA y contribuciones (CRediT). Hoy figuran
  como «Pendiente de confirmación por los autores».
- **Versión archivada.** El repo es tuyo (`Joafp`). Para la disponibilidad de
  datos y código conviene una versión con DOI, por ejemplo un release en
  Zenodo.

## Reglas para cualquier corrida

- Toda selección (bloques, umbral, ruta, compuerta) se hace solo con el
  entrenamiento externo, y el test se consulta una vez.
- Mismas particiones, semillas y perfiles de costo que la evaluación que se
  reemplaza; si algo cambia, se documenta.
- Las corridas originales quedan intactas, y se informan las versiones vieja y
  nueva lado a lado, salga como salga.
- Registrá hashes de entradas y salidas, como en
  `results/analysis/consultas_joaquin_20261114_v1/`.
