# Preparación de la reunión del lunes 30-11

Fecha: 2026-11-27. Uso de Carlos, para la reunión con el profesor y Joaquín.

Este documento compara la versión de Joaquín (commit `cb8a2d2`, del 26-11)
con la que integramos el 23-11 (`7ec6334`). La versión nueva compila sin
errores ni referencias rotas: 19 páginas en pdfLaTeX local. Verifiqué contra
las tablas las cifras principales: medias, Wilcoxon, intervalos, no
inferioridad y totales de la tabla de cambios de acierto. Todas coinciden.

---

## 1. Qué cambió

- **Revista objetivo: Pattern Recognition.** Joaquín armó dos versiones:
  - `main_en.tex`: formato de envío, en inglés, a doble espacio. Tiene 32
    páginas; la revista pide entre 20 y 35.
  - `main.tex`: borrador en español para el tutor.
- **Estructura nueva.** El paper tiene siete secciones y siete apéndices:
  - Secciones: Introducción, Trabajos relacionados, Método, Protocolo,
    Resultados, Discusión y limitaciones, y Conclusión.
  - Apéndices: biblioteca y color (E5), métricas macro, ResMLP (E4),
    compuertas (E2), sensibilidad de las rutas, ensambles de control y
    trazabilidad.
- **Figuras nuevas (las que mejoró Joaquín):**
  - Fig. 1: cómo se extraen y concatenan los bloques.
  - Fig. 2: la cascada, hecha en TikZ.
  - Fig. 3: curva de k, con la accuracy en test y el macro-F1 interno. El
    máximo interno está en k = 6.
  - Fig. 4: E1 por dataset, con el cambio de accuracy y el costo proyectado.
  - Fig. del apéndice: curvas por dataset respecto de Top-4.
- **Tabla nueva clave: «Cambios de acierto».** Para cada imagen escalada
  muestra si la cascada corrige un error o pierde un acierto. Es nuestro
  análisis por imagen en versión resumida.
- **Declaraciones.** Sin financiamiento y sin conflictos de intereses. Están
  la contribución de cada autor (CRediT) y la disponibilidad de datos, con un
  commit archivado.
- **Verificación.** `scripts/verify_topk_paper_evidence.py` recalcula las
  cifras de E1 y del panel online a partir de los archivos guardados.
- **Material editorial.** Está en `revision_paper/`: highlights, borrador de
  carta y una guía de datos.

## 2. Qué salió del paper (el profesor puede preguntar)

| Estaba el 23-11 | Ahora | Por qué importa |
|---|---|---|
| Matriz de confusión de E1 (Fig. 4) | **Salió** | El revisor pidió matrices de confusión explícitamente. |
| Ejemplos mal clasificados de KTH, algodón y lino (Fig. 5) | **Salió** | Era lo del esquema de HyTexNet. |
| McNemar por condición y kappa | Queda una frase, sin tabla ni kappa | — |
| Media ± DE entre particiones | **Salió** | HyTexNet informa ± DE. |
| Tabla de ablación | Salió; sus partes están repartidas (Top-4 frente a Completa-22, E4, E5) | — |
| Tabla con nuestras corridas de HyTexNet y DeepLumina (A y B) | Se reemplazó por «Resultados publicados»: solo las cifras de cada artículo, con su protocolo | **Ya no decimos que les ganamos.** DeepLumina B no aparece. |
| Tabla del piloto físico | Una frase en la Discusión | — |

El material quitado sigue en el repo. Si se decide volver a ponerlo, son unos
minutos:
- `analisis_paper/e1_confusion.csv` y `e1_por_clase.csv`;
- `figures/kth_errores/`;
- las auditorías de DeepLumina B.

## 3. Preguntas probables y qué responder

**1. «¿Por qué DeepLumina no convergía en DTD?»**
No era solo DTD: pasaba en los seis datasets. La causa eran los rasgos sin
escalar. Joaquín corrió la variante B (rasgos estandarizados y hasta 100.000
iteraciones): convergió en las 47 condiciones, sin ningún clasificador en el
tope. La accuracy cambió como mucho ±0,3 puntos (DTD 70,55 %), así que la
falta de convergencia no explicaba la distancia a Top-4. Si pregunta por qué
no está en el paper: el paper ahora usa solo cifras publicadas, porque
nuestras adaptaciones no son réplicas fieles. B quedó documentada en el repo.
*Decidir con él si quiere una frase sobre B.*

**2. «¿Cómo se comparan con el estado del arte?»**
La tabla de resultados publicados muestra cada cifra con el protocolo de su
artículo. La comparación directa no es válida si cambian las particiones. Por
ejemplo, HyTexNet obtiene 99,79 % en KTH entrenando con un tercio elegido por
pose, iluminación y escala. Nosotros dejamos afuera una muestra física entera
y obtenemos 95,75 %.

Los protocolos más parecidos son los de Neshov (BEiTv2):
- **DTD**, con las diez particiones oficiales: 82,0 ± 0,9 frente a nuestro
  Top-4 con SVM de 87,03.
- **KTH**, con cuatro particiones: 96,8 ± 2,5 frente a 95,75.

El paper no los presenta como comparación directa, porque no verificamos que
la receta sea la misma.

**3. «¿Por qué solo accuracy?»**
Accuracy es la métrica principal. Además se informan:
- precisión, recall y F1 macro (apéndice de métricas macro; E4 también
  macro-F1);
- Wilcoxon exacto, Friedman, Holm, no inferioridad y McNemar por condición;
- la tabla de cambios de acierto por imagen.

Las matrices de confusión salieron (ver sección 2). Si las pide, se reponen.

**4. «¿El ahorro del 75 % es real?»**
Es una **proyección** con tiempos por bloque: 468,3 → 117,1 ms. No medimos en
línea la cascada exacta: quedó como trabajo futuro, porque tres condiciones
con ViT-B/16 en CUReT y Soil están en revisión de fidelidad. El panel online
mide otra política por margen, que rescata con un ensamble: 245 → 40 ms con
SVM y 233 → 36 ms con ResMLP, en las mismas llamadas.
*No llamarla «Top-4 con margen».*

**5. «¿La cascada es mejor que Top-4?»**
No: es **igual de buena y más barata**.
- SVM: +0,01 pp (IC 95 %: −0,17 a +0,19). Wilcoxon p = 0,5625. La cota de no
  inferioridad, −0,13 pp, queda lejos del umbral de −1 pp.
- ResMLP: −0,03 pp, con cota de −0,21 pp.
- McNemar no da diferencia significativa en ninguna condición.

**6. «¿El margen elige bien o es suerte?»**
Elige bien. Con la misma cantidad de imágenes escaladas, elegirlas al azar da
92,80 % y elegirlas por margen da 94,46 %. Gana en las 27 condiciones.
Wilcoxon da p = 0,0312, el mínimo posible con seis datasets. El margen manda a
Top-4 1.176 de los 1.327 errores que Top-4 podía corregir (88,6 %).

**7. «¿Por qué k = 4?»**
Fue una elección exploratoria, hecha después de ver las curvas, y el paper lo
dice. Con SVM, la ganancia de 1 a 4 bloques es de 1,70 pp; después la curva
se aplana. Las reglas automáticas proponen otros tamaños; por ejemplo, el
máximo interno da k ≈ 6,3 y 94,14 %.

**8. «¿Qué pasa en KTH con el panel?»**
La política con ensamble pierde 1,60 pp con SVM y 1,51 con ResMLP. En Soil
baja la latencia media, pero sube el percentil 95. Ambas cosas están en el
resumen y en la discusión como límites.

## 4. Números para tener a mano

| Qué | Valor |
|---|---|
| Biblioteca | 22 bloques: 6 clásicos y 16 redes congeladas; 20.652 dimensiones |
| Top-4 | ≈ 3.150 dimensiones (≈ 15 %); SVM 94,42 % frente a Completa-22 94,73 % (−0,31 pp) |
| E1 (SVM, 27 condiciones) | Directo 94,44 % y cascada 94,46 %; escala el 21,1 % |
| Costo proyectado | 468,3 → 117,1 ms (−75 %) |
| Control aleatorio | 92,80 % frente a 94,46 %; gana en 27 de 27 |
| E4 (ResMLP) | 94,28 % frente a 94,24 %; escala el 22,5 % |
| E5 (+ N-gramas) | 94,42 → 94,89 %; Outex +3,24 pp |
| Panel online (SVM) | Top-4 245 ms y 94,23 %; margen con ensamble 40 ms y 93,96 %; Completa-22 1.648 ms |

## 5. Para corregir antes de enviar (comentarle a Joaquín)

Los puntos 1 a 3 ya los corregí en `main.tex` (español) el 27-11. No toqué
`main_en.tex` ni el PDF de Joaquín.

1. **«Cascada restringida a ResNet-50» (corregido en español).** Entraba en la
   familia de Holm, pero no se definía en ninguna parte. Agregué una frase al
   final del párrafo de las etapas iniciales candidatas, en el Método. En la
   versión anterior daba p = 0,1562 (Holm 0,4688).
   **Falta en inglés.** El problema está en la línea 264 de `main_en.tex`.
   Frase propuesta para el párrafo de la línea 143: *«As an additional
   reference, the cascade restricted to ResNet-50 applies the same selection
   with ResNet-50 as the only initial-stage candidate.»*
2. **«Pliegue» y «fold» (corregido).** «Fuera de pliegue» pasó a «fuera de
   fold (OOF)» en el Método, la Discusión y el apéndice E2.
3. **Sensibilidad que saca un dataset por vez (agregada al español).**
   Traduje al párrafo de limitaciones lo que ya estaba en inglés:
   - −0,019 pp sin Soil y +0,075 sin Outex;
   - DTD por condición entre −0,319 y +0,479;
   - Friedman exacto sin KTH: p = 0,1242 con SVM y 0,5216 con ResMLP. Lo
     recalculé y coincide.
4. **Declaración de uso de IA.** Elsevier la exige al enviar. El registro de
   `REVISION_PARA_REVISTA.md` nombra solo a OpenAI Codex y pide «confirmar si
   hubo herramientas adicionales». **Yo usé Claude (Anthropic)** para el
   análisis por imagen, revisiones de consistencia y redacción. Hay que
   sumarlo a la declaración.
5. **Lo que pidió el revisor.** Faltan la matriz de confusión, los ejemplos
   mal clasificados y la media ± DE. Propuesta: volver a ponerlos como
   apéndice. Lo decidimos con el profesor.

## 6. Estado de los pendientes de Joaquín

| # | Pendiente | Estado con la versión nueva |
|---|---|---|
| 1 | Latencia online de E1 | Declarada como **trabajo futuro**. El paper dice «proyectado». |
| 2 | DeepLumina | Corrida B hecha, pero **fuera del paper**. |
| 4 | Reservas de KTH y Outex | Siguen como limitación. |
| 5, 7, 8 | Parámetros y GFLOPs, t-SNE, curvas de ResMLP | No están. ¿Se descartan? |
| 14 | Declaraciones | Financiamiento y conflictos de intereses, confirmados. Faltan: aprobación del texto final, contribuciones, exclusividad, la declaración de intereses en Word (herramienta de Elsevier) y la de IA (punto 4 de la sección 5). |
| 16 | Receta de HyTexNet | Resuelto: solo se usan cifras publicadas. |
| — | Carta de presentación | Borrador en `revision_paper/COVER_LETTER_DRAFT.md`: revisar y firmar. |

## 7. Agenda sugerida (30–40 min)

1. **Estado y revista** (3 min): Pattern Recognition, versiones en inglés y
   en español.
2. **Resultados** (10 min): Fig. 3 (por qué 4 bloques), Tabla de la cascada
   y Fig. 4 (igual accuracy, 75 % menos de costo proyectado), control
   aleatorio y tabla de cambios de acierto.
3. **Respuesta a lo que pidió** (5 min): DeepLumina B y métricas
   complementarias.
4. **Decisiones** (10 min):
   - ¿Reponemos la matriz de confusión y los ejemplos de KTH?
   - ¿Mencionamos DeepLumina B?
   - ¿Aceptamos la latencia de E1 como trabajo futuro?
   - Declaración de IA.
   - ¿Enviamos ya o esperamos algo?
5. **Próximos pasos y fechas** (5 min).
