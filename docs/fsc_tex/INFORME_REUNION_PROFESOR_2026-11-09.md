# Informe de avance de tesis para reunión con el profesor

**Reunión prevista:** 9 de noviembre de 2026.  
**Preparado con evidencia disponible al:** 8 de noviembre de 2026.  
**Estado:** documento de trabajo para discusión, no versión final del manuscrito.

## 1. Resumen para comenzar la reunión

El trabajo compara estrategias de combinación de descriptores de textura en
calidad predictiva y costo de inferencia. El panel local está completo: **94/94
condiciones**, en seis datasets. Para las comparaciones con la literatura se
implementaron adaptaciones de Neshov, HyTexNet, 6LBP+dCellNN y DeepLumina.
Además, Carlos aportó un estudio complementario de Scabini y de costos de
extracción y entrenamiento.

**Resultado central:** existe un compromiso entre calidad y tiempo. Por
ejemplo, en FMD la política adaptativa con SVM obtuvo macro-F1 **0,97760** y
38,63 ms medios por llamada, frente a **0,94213** y 16,89 ms de la adaptación
Neshov. La diferencia observada es +0,03547 de F1 y +21,74 ms. Los tiempos
provienen de mediciones en momentos distintos, por lo que son descriptivos.

**No sostenemos superioridad universal:** en Soil, Top-4/SVM obtuvo F1 0,85940
frente a 0,86310 de Neshov y fue más lento en las mediciones disponibles.
Además, las adaptaciones no equivalen automáticamente al código original ni
demuestran que se reprodujeron exactamente los porcentajes publicados.

## 2. Qué se completó

| Bloque | Estado | Observación |
|---|---|---|
| Panel de cinco estrategias propias | 94/94 condiciones | Cinco estrategias con SVM y ResMLP; seis datasets. No repetir el panel cerrado. |
| Comparaciones por llamada | 1.780 por condición y 230 por dataset | IDs, etiquetas, hashes de imágenes y registros de predicciones y tiempos contrastados. |
| Neshov, HyTexNet y 6LBP+dCellNN | 47/47 condiciones por adaptación | Son evaluaciones en el panel común, no afirmaciones de réplica fiel del paper. |
| DeepLumina | 46/47 condiciones terminadas | Todas las terminadas registran avisos de no convergencia; DTD queda 9/10 y requiere revisión. |
| Neshov FMD aproximado al paper | 100/100 condiciones, 10.000 llamadas | Accuracy 94,22 % frente a 96,7 % publicado; particiones y entorno son aproximados. |
| Aporte de Carlos | Cuatro datasets para Scabini y métodos propios; Neshov en tres y HyTexNet en dos | Tiempos por imagen derivados de lotes de 32 en otra GPU; no son equivalentes a latencia individual batch=1. |

## 3. Tablero principal: seis datasets

Cada celda es **macro-F1 medio por condición / tiempo medio en ms por llamada**.
La columna propia muestra únicamente la **política adaptativa con SVM**. Los
competidores son adaptaciones locales; para cada comparación se verificaron
las mismas imágenes de prueba por ID, etiqueta y hash. En cada método, F1 y
tiempo proceden de las mismas llamadas registradas. Los tiempos de métodos
distintos se midieron en fechas distintas y con hardware compartido: diferencias
pequeñas no prueban ventaja temporal. No se mezclan aquí las mediciones de Carlos.

| Dataset | Adaptativa SVM | Neshov + MLP | HyTexNet | 6LBP+dCellNN | DeepLumina † |
|---|---:|---:|---:|---:|---:|
| DTD | 0,86686 / 54,35 | 0,80203 / 16,79 | 0,62415 / 33,51 | 0,21618 / 31,52 | 9/10; sin media completa |
| FMD | 0,97760 / 38,63 | 0,94213 / 16,89 | 0,74142 / 31,18 | 0,24765 / 29,66 | 0,85591 / 53,33 † |
| CUReT | 0,99840 / 36,83 | 0,99396 / 14,27 | 0,98307 / 32,41 | 0,69337 / 31,02 | 0,98806 / 53,00 † |
| Outex-13 | 0,92758 / 40,33 | 0,91930 / 14,61 | 0,89275 / 29,04 | 0,63557 / 29,91 | 0,90727 / 53,54 † |
| SoilOriginal | 0,87254 / 38,48 | 0,86310 / 19,17 | 0,78796 / 33,11 | 0,35497 / 32,98 | 0,80501 / 57,80 † |
| KTH-TIPS2b | 0,93900 / 30,95 | 0,92448 / 16,48 | 0,82586 / 30,98 | 0,57503 / 31,94 | 0,87437 / 51,57 † |

† **DeepLumina está bajo revisión científica:** hubo advertencias de no
convergencia en las 46 condiciones terminadas; 1.653 de 2.441 clasificadores
binarios inspeccionados alcanzaron el límite de iteraciones. No se conoce cuánto
afecta eso al F1. DTD no tiene cobertura completa y no se presenta una media de
dataset. DTD conserva una reserva física de la medición local `official7`; KTH
conserva una reserva de reconciliación con el protocolo histórico de cascada.

**Cómo leerlo:** el tablero no demuestra significación estadística ni que una
sola estrategia sea mejor en toda situación. El detalle incluye las otras cuatro
estrategias y ambos clasificadores; por ejemplo, la pérdida de Top-4/SVM frente
a Neshov en Soil aparece allí. Fuente: [tablero y reservas](PROPUESTA_GUION_Y_TABLERO_VERIFICADO_2026-11-04.md)
y [comparaciones completas](../../results/analysis/reconciliation_full_panel_20261104_v1/comparison_by_dataset.csv).

## 4. ¿Qué tan cerca estamos de los papers?

| Trabajo | Estado y evidencia | Límite de interpretación |
|---|---|---|
| Neshov | En FMD 10×10, accuracy 94,22 %; publicación 96,7 %: −2,48 puntos porcentuales. | Aproximación paper-like; semillas, particiones, versiones y hardware no son idénticos. Accuracy no es macro-F1. |
| HyTexNet | Carlos informa 98,7 % de accuracy en una aproximación al protocolo de KTH y 85,0 % con muestra física separada. | La cercanía numérica no prueba identidad del código ni del reparto. En nuestra adaptación DenseNet se congeló; Carlos ajustó el último bloque. |
| Scabini | Carlos informa valores de exactitud cercanos a los publicados en cuatro datasets. | Resultado exploratorio con su receta; cercanía no confirma por sí sola código, pesos y particiones originales. |
| 6LBP+dCellNN | Adaptación evaluada en los seis datasets del panel común. | El examen previo detectó discrepancias entre el protocolo de un script y el descrito en el paper para OTC12; no declarar reproducción completa sin resolverlas. |
| DeepLumina | FMD: 85,53 % de accuracy media en 15 condiciones; un fold alcanzó 90,00 %. | El paper informa 90,15 % ± 1,2; un mejor fold no es la media ni demuestra réplica. Hay no convergencia. |

En la aproximación local del reparto de un tercio en KTH hay **44 muestras
físicas compartidas** entre ajuste y prueba; ese resultado no debe promediarse
con el panel separado por muestra física ni interpretarse como el mismo
protocolo. Fuentes: [conciliación Carlos](CONCILIACION_CARLOS_SOTA_TIMING_2026-11-08.md),
[auditoría Neshov](../../results/analysis/neshov_paperlike_fmd_10x10_consolidated_20261103_v1/INFORME.md)
y [disponibilidad de código](../../results/analysis/paper_code_availability_20261103_v1/INFORME.md).

## 5. Aporte reciente de Carlos y alerta de Outex

Carlos incorporó scripts y resultados para comparar tiempos de extracción,
entrenamiento e inferencia. Sus mediciones son complementarias: se hicieron en
una RTX 5060 Ti, con extracción en lotes de 32 y componentes temporizados por
separado; el panel online auditado usa llamadas individuales en otra GPU. No
deben integrarse como si fueran una medición idéntica.

Su diagnóstico señaló **cinco filas de embeddings** de ViT-B/16 y DeiT-S en
Outex13 que no encajarían con sus imágenes. El cruce con el manifiesto indica
tres filas de test y dos de train. En el panel online local las cinco políticas
con ambos clasificadores acertaron en las tres imágenes de test: 30/30 llamadas
primarias. **Eso no descarta impacto indirecto** de las filas train ni verifica
independientemente la hipótesis sobre los embeddings.

En las corridas de Carlos, Completa-22 declara ambos bloques; diversidad/SVM
declara ViT-B/16; Top-4 no declara ninguno en la selección final. Los CSV de
Carlos examinados contienen métricas agregadas, no predicciones por imagen;
por sí solos no permiten reconstruir los F1. Fuente: [trazabilidad Outex](TRAZABILIDAD_OUTEX_CARLOS_2026-11-08.md).

## 6. Pendientes y decisiones para conversar

1. **Mensaje central:** ¿priorizar la relación F1–latencia y presentar la
   política adaptativa como una alternativa de compromiso, mostrando también
   los casos donde pierde?
2. **Criterio de comparación:** ¿usar como tablero principal el panel común
   batch=1 y presentar las mediciones batch=32 de Carlos en una sección aparte?
3. **Réplicas:** acordar qué grado de fidelidad exigir y cuáles diferencias
   de código, pesos y particiones deben quedar explícitas por paper.
4. **Outex:** decidir el alcance de una verificación independiente de las
   cinco filas y del efecto potencial en selección y entrenamiento, preservando
   los resultados originales y documentando cualquier nueva corrida.
5. **DeepLumina:** revisar científicamente los avisos de convergencia y el
   caso DTD incompleto antes de decidir si procede un nuevo protocolo. No hay
   reintentos automáticos ni se oculta el fallo previo.
6. **Entrega:** confirmar el título aprobado: el PDF de tesis y el material de
   presentación consultados previamente no coincidían. Decidir qué correcciones
   del guion y las diapositivas adoptar; el manuscrito no se cambió.

## 7. Guion oral breve

> Cerramos el panel de nuestros métodos en seis datasets y reconstruimos las
> comparaciones con las adaptaciones de la literatura a partir de predicciones
> y tiempos registrados. La conclusión no es que ganemos siempre: en FMD la
> política adaptativa mejora el F1 frente a Neshov, pero también tarda más;
> y en Soil Top-4 queda ligeramente por debajo de esa adaptación. La medición
> de tiempos debe leerse con la reserva de que se realizó en fechas distintas.
>
> También evaluamos la cercanía a los papers. En Neshov FMD quedamos en 94,22 %
> de accuracy frente al 96,7 % publicado, bajo una aproximación del protocolo.
> El trabajo de Carlos aporta otro estudio de métodos y costos, pero usa lotes
> de 32 y otra GPU, así que no lo mezclamos con la latencia individual. Quedan
> por revisar la convergencia de DeepLumina y cinco filas de embeddings de
> Outex; queremos acordar qué verificaciones son necesarias para el cierre.

## 8. Documentos de respaldo

- [Plan maestro y estado de las corridas](PLAN_MAESTRO_ACTUALIZADO_2026-11-04.md).
- [Auditoría del panel y ganancias/pérdidas](../../results/analysis/reconciliation_full_panel_20261104_v1/INFORME.md).
- [Diagnóstico DeepLumina](../../results/analysis/deeplumina_stationarity_review_20261104_v1/INFORME.md).
- [Informe original de Carlos](../../results/exploratory/sota_timing/README.md).
- [Comparación de recetas y trazabilidad](CONCILIACION_CARLOS_SOTA_TIMING_2026-11-08.md).

Este informe resume archivos existentes; no ejecutó experimentos, no modificó
el manuscrito y no reemplaza la revisión científica de los casos pendientes.
