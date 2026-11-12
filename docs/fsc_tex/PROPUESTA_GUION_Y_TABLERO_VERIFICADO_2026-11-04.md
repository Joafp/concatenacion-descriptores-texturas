# Propuesta para corregir el tablero y el guion de defensa

Documento de trabajo, 04-11-2026. Propone reemplazos basados en llamadas y
auditorías existentes. **No modifica** `paper/tesis.pdf`,
`paper/presentacion_defensa.tex`, su PDF ni el guion del equipo. Antes de
adoptar los cambios, mantener visibles las reservas indicadas abajo.

## 1. Tablero trazable para la diapositiva 15

Cada celda es **macro-F1 medio por condición / latencia media en ms por
llamada**. La columna propia es `Adaptive-selection-margin` con clasificador
**SVM**: no mezcla SVM y ResMLP. Las cuatro columnas externas son adaptaciones
locales; se compararon las mismas imágenes por ID, etiqueta y hash. Se
registraron predicción y tiempo en la misma llamada de cada método.

| Dataset | Adaptativa SVM | Neshov BEiTv2+MLP | HyTexNet | 6LBP+dCellNN | DeepLumina † |
|---|---:|---:|---:|---:|---:|
| DTD | 0,86686 / 54,35 | 0,80203 / 16,79 | 0,62415 / 33,51 | 0,21618 / 31,52 | **9/10; sin media completa** |
| FMD | 0,97760 / 38,63 | 0,94213 / 16,89 | 0,74142 / 31,18 | 0,24765 / 29,66 | 0,85591 / 53,33 † |
| CUReT | 0,99840 / 36,83 | 0,99396 / 14,27 | 0,98307 / 32,41 | 0,69337 / 31,02 | 0,98806 / 53,00 † |
| Outex-13 | 0,92758 / 40,33 | 0,91930 / 14,61 | 0,89275 / 29,04 | 0,63557 / 29,91 | 0,90727 / 53,54 † |
| SoilOriginal | 0,87254 / 38,48 | 0,86310 / 19,17 | 0,78796 / 33,11 | 0,35497 / 32,98 | 0,80501 / 57,80 † |
| KTH-TIPS2b | 0,93900 / 30,95 | 0,92448 / 16,48 | 0,82586 / 30,98 | 0,57503 / 31,94 | 0,87437 / 51,57 † |

† Las 46 condiciones DeepLumina terminadas tienen avisos de no convergencia.
La inspección de modelos guardados encontró 1.653/2.441 clasificadores binarios
en el límite de iteraciones. Son **resultados observados bajo revisión
científica**, no un cierre validado. En DTD falta `s42_f3` por timeout y no
se informa una media completa. Las latencias son descriptivas: se midieron en
fechas distintas y con hardware compartido; diferencias pequeñas como KTH
30,95 vs. 30,98 ms no justifican afirmar superioridad temporal. En DTD la
medición local SVM conserva además la reserva física de la condición original
`official7`; en KTH se mantiene la reserva de reconciliación con el protocolo
histórico de la cascada.

Fuentes: [conciliación de llamadas](../../results/analysis/reconciliation_full_panel_20261104_v1/INFORME.md),
[230 comparaciones por dataset](../../results/analysis/reconciliation_full_panel_20261104_v1/comparison_by_dataset.csv)
y [diagnóstico de optimización](../../results/analysis/deeplumina_stationarity_review_20261104_v1/INFORME.md).
El CSV incluye todas las cinco estrategias y los dos clasificadores locales,
con deltas positivos y negativos. No se usó la variante Neshov LogReg del
cuadro anterior porque su cadena de evidencia no se identificó en esta revisión.

## 2. Texto oral propuesto para la comparación

> «Para comparar, adaptamos cuatro sistemas de literatura a nuestras mismas
> imágenes de prueba y guardamos la predicción y el tiempo de cada llamada.
> Esta tabla muestra la política adaptativa con SVM; tenemos también las cinco
> políticas y ambos clasificadores en el detalle. En FMD, por ejemplo, nuestra
> política alcanzó F1 0,97760 y la adaptación BEiTv2+MLP de Neshov 0,94213;
> sus latencias medias observadas fueron 38,63 y 16,89 ms, respectivamente.
> Por tanto, la ganancia de calidad en este caso viene con mayor tiempo.
> Las latencias provienen de fechas y condiciones de hardware distintas, así
> que las tratamos como descriptivas. No afirmamos que una política domine en
> calidad y tiempo en todos los casos.»

> «DeepLumina quedó bajo revisión: aunque tenemos resultados de cinco datasets,
> el entrenamiento registró avisos de no convergencia; en DTD falta una
> condición que agotó el tiempo. Por eso mostramos lo observado con esa reserva
> y no declaramos reproducidos los porcentajes del artículo.»

Para mostrar explícitamente una pérdida en el conjunto de estrategias locales:
en Soil, **Top-4/SVM** obtuvo F1 **0,85940** frente a **0,86310** de
Neshov+MLP (Δ local − externo **−0,00370**); sus tiempos medios observados
fueron **70,98 vs. 19,17 ms**. No se trata de una prueba de significación.

## 3. Sustituir afirmaciones de fidelidad

- **DeepLumina/FMD:** el paper informa accuracy 90,15 % ± 1,2; la adaptación
  obtuvo **85,53 % de accuracy media** en 15 condiciones y **90,00 % en un
  fold**. El mejor fold no establece réplica exacta. El código/pesos MATLAB y
  el split exactos no fueron verificados; además hay avisos de convergencia.
- **Neshov:** la aproximación FMD 10×10 auditada obtuvo **94,22 % de accuracy**
  frente a **96,7 % publicado**; es una aproximación con diferencias de split,
  versiones y hardware. No intercambiar accuracy con macro-F1.
- **HyTex y CellNN/KTH:** el reparto local aproximado de un tercio comparte
  **44 muestras físicas** entre ajuste y prueba; es distinto del panel común
  separado por muestra física y no se promedia con él. El subconjunto exacto
  usado por los autores no fue confirmado.
- **CellNN/OTC12:** hay código de autores para componentes y un pipeline,
  pero el script examinado y la partición descrita en el paper difieren. La
  paridad de un componente no prueba identidad del método y protocolo completos.

No atribuir causalmente las cifras publicadas a una supuesta fuga o declarar
«reproducción exacta» sin una demostración completa de código, datos, pesos y
partición. Ver [auditoría de código](../../results/analysis/paper_code_availability_20261103_v1/INFORME.md).

## 4. Pendientes antes de editar o presentar

1. Localizar la evidencia de las cifras distintas del cuadro nuevo, o dejarlas
   fuera como **no verificadas**. La búsqueda realizada y sus límites están en
   [FUENTES_TABLERO.md](../../results/analysis/reconciliation_full_panel_20261104_v1/FUENTES_TABLERO.md).
2. Resolver el estado científico de DeepLumina sin reintentos automáticos ni
   cambiar silenciosamente el presupuesto o el método.
3. Verificar el **título aprobado**: la portada del PDF de tesis y el título de
   la presentación/guion actualmente no coinciden.
4. Si se adopta esta propuesta, editar y recompilar la presentación y el guion
   como una tarea separada; el manuscrito sigue protegido por la instrucción
   previa del proyecto.
