# Plan de integración: selección de subconjuntos y adquisición condicional

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: análisis de resultados archivados y propuesta de experimentos.
- Origin Date: 2026-10-19.
- Verification Status: ANALYZED. Corte 25-10: 147 métricas históricas recalculadas, 470 filas estáticas verificadas, 27 archivos de predicciones canónicas auditados, 36 decisiones/13 resultados del híbrido reproducidos y pool emparejado comprobado. Suite completa: 80 aprobadas. Sin reproducción independiente de ajustes ni medición física del híbrido.
- Version Label: integración_v11 (25-10-2026). Pool emparejado e híbrido implementados; manuscrito actualizado. Falta aislar poda/compuerta y replicar/medir el método nuevo. Rige el [plan de cierre vigente](PLAN_CIERRE_VIGENTE_2026-10-25.md).
- Referencia histórica del repositorio: `bf5e7f9970b1e4eac7aa4e3f8d70a296c95f38bc`; los pilotos nuevos incluyen cambios locales y registran sus hashes de fuente y entorno en cada `metadata.json`.
- Alcance: seis datasets principales; VisTex sigue excluido por decisión del autor. Las afirmaciones comparativas con artículos externos del informe de Carlos no fueron verificadas en esta revisión.

## 1. Dictamen y dirección recomendada

**Prioridad vigente:** comparar exactamente el mismo rescate podado siempre activo frente a su versión condicional. El pool emparejado ya está corregido y el ensamble de Carlos ya está integrado como rescate; siguen las reservas sobre robustez, controles GFS/bases y costo físico. La [reauditoría del 25-10](AUDITORIA_TESIS_Y_CIERRE_2026-10-25.md) y el [plan v11](PLAN_CIERRE_VIGENTE_2026-10-25.md) sustituyen las prioridades anteriores. Las secciones previas a 12 y los cortes 12.1–12.7 conservan la evolución histórica, no una lista literal de faltantes actuales.

El trabajo incorporado de Carlos aporta evidencia útil sobre selección estática y ensambles de subconjuntos. La cascada aporta adquisición condicional y mediciones físicas piloto. Los resultados actuales no permiten declarar que uno sustituya al otro: difieren las semillas, las bibliotecas disponibles, la procedencia KTH y las condiciones de medición.

Recomiendo conservar como pregunta central **cómo adquirir y combinar descriptores de forma condicional para mejorar el compromiso entre macro-F1 y latencia**, y probar una integración acotada: una etapa económica seleccionada en entrenamiento y una etapa de rescate que combina pocos subconjuntos de Carlos. El rescate reutiliza los embeddings ya extraídos y calcula cada bloque adicional una sola vez por imagen.

La contribución candidata será la selección conjunta de ruta económica, subconjuntos de rescate y umbral de escalado bajo costo de la unión de bloques. Combinar una cascada con un ensamble no basta para acreditar originalidad: su valor debe demostrarse frente a las dos piezas por separado y a controles con igual presupuesto. La novedad bibliográfica queda pendiente de una búsqueda específica si esta integración funciona.

## 2. Evidencia observada y límites

Medias de macro-F1 recalculadas de `results/analysis/selection_stats/{svm,resmlp}_metodos.csv`: primero una media por dataset y luego igual peso entre los seis.

| Método | SVM | ResMLP |
|---|---:|---:|
| Completa-22 | 0,939137 | 0,928786 |
| Ensamble diversidad | 0,938261 | 0,939425 |
| Ensamble tómbola | 0,936930 | 0,939357 |
| Top-4 | 0,936554 | 0,933077 |
| Top-k histórico | 0,935182 | 0,933755 |
| GFS histórico | 0,929483 | 0,933569 |

Interpretación:

- Diversidad mejora a Completa en ResMLP en **0,010639 de macro-F1 (1,064 puntos porcentuales)**; con SVM queda **0,000876 por debajo**. No mezclar ambos clasificadores para obtener un único ganador.
- En SVM Top-4 pierde 0,036772 en Outex frente a Completa. La media global no justifica un k universal ni una garantía por dataset.
- Las tablas archivadas dan Wilcoxon bilateral p=0,0625 para los ensambles ResMLP frente a Completa. En los 28 pares corregidos por Holm, los pares significativos son los ensambles frente a Individual con ResMLP; no prueban superioridad frente a Completa, Top-k, GFS o nuestra cascada.
- La no inferioridad archivada con margen 0,01 da p(t)=0,0104 para Top-4 ResMLP y p=0,1850 para SVM. Es un análisis exploratorio con seis medias y margen cuya justificación prospectiva no está acreditada aquí. No usar el «margen mínimo» calculado después de ver los datos como margen predefinido.
- Carlos evalúa 47 condiciones por clasificador: DTD 10, CUReT 2, Outex 1, KTH 4, FMD 15 y Soil 15. Nuestra cascada archivada usa 27 condiciones, con una semilla en FMD/Soil. Sus medias históricas 0,9345/0,9341/0,9409 (cascada/Top-k/Completa) no se pueden restar directamente de las medias de Carlos para adjudicar una mejora.
- Las búsquedas nuevas usan 21 bloques **sin RGB N-grams+SVD**. Estos 21 no son la biblioteca histórica de 21 que incluía n-gramas y todavía no incluía BEiT-v2. Completa-22 sí usa n-gramas.
- Los ensambles de 15 sorteos usan en promedio una unión de 8,9 bloques (tómbola) o aproximadamente 9,9 (diversidad), según los JSON de tablas. Cuatro bloques por miembro no equivalen a cuatro extractores en total.
- El costo de Carlos se mide sobre embeddings: por ejemplo, SVM diversidad suma 1,07 s de predicción sobre seis condiciones frente a 0,54 s de 21 bloques. No incluye extracción de imágenes ni acredita ahorro físico. Nuestra evidencia física también es piloto: 204 imágenes, con alertas de fidelidad en CUReT/Soil.

Fuentes: `carlos/REPORTE_SELECCION_DESCRIPTORES.tex`, `results/analysis/selection_tables/{svm,resmlp}.json`, tablas `tabla_metodos.tex`, `tabla_no_inferioridad.tex`, `tabla_costo.tex`, `tabla_tamano.tex`, y `docs/fsc_tex/REPORTE_CASCADA_ADAPTATIVA_CANONICA_27.md`.

## 3. Hallazgos de código que condicionan la integración

### 3.1 Normalización dependiente del lote de test — prioridad P0

`decision_scores()` en `src/run_weighted_lottery_selection.py` calcula `scores.std()` sobre todas las puntuaciones recibidas. `external()` le pasa `x[test]`. La misma lógica aparece en diversidad y control, y `run_ensemble_size.py` importa esa función.

La escala de cada miembro depende así de la composición del lote externo. No utiliza etiquetas externas; es una dependencia transductiva de las covariables, incompatible con asumir sin comprobación una predicción online independiente por imagen. No implica que todas las etiquetas predichas cambien, pero sí exige corregir y medir el efecto.

Trabajo: ajustar escalas o calibradores únicamente con entrenamiento/OOF y persistirlos; aplicarlos congelados a cada imagen. Verificar invariancia al particionar, permutar o añadir otras imágenes al lote. Guardar la variante histórica y la nueva, con sus diferencias. Incluir voto duro como control para aislar el efecto del escalado.

### 3.2 Selección y procedencia

El informe declara k=4 elegido a partir de la curva externa SVM y beta/lambda elegidos con SVM antes de transferirlos a ResMLP. La selección interna de bloques no borra esa exposición externa de hiperparámetros. Comparar también una regla fijada en entrenamiento; las nuevas evaluaciones sobre estos benchmarks seguirán siendo exploratorias.

`singleton_ranking.py` validaba su caché por nombres de bloques y hash de índices train. La implementación de integración ahora crea un caché separado bajo `results/exploratory/integration_v1/ranking_cache/` y firma índices, valores de embeddings de entrenamiento, etiquetas, grupos y nombres/formas/tipos de bloques. No se alteran los cachés archivados. La firma aún no incorpora un hash explícito del archivo de manifiesto o del código; los splits internos permanecen determinados por el protocolo fijo del ejecutor y deben registrarse en el manifiesto de la corrida.

La selección de subconjuntos, ruta económica y calibración deben rehacerse dentro de cada fold productor OOF. No construir una predicción supuestamente OOF con un subconjunto seleccionado usando las etiquetas de su fold de validación.

## 4. Protocolo común antes de elegir ganador — P0

Entradas: manifiestos, embeddings, filas fuente del manuscrito, resultados de Carlos y JSON/predicciones de cascada.

1. Crear un registro por `(dataset, semilla, partición, clasificador, variante)` con hashes de train/test, etiquetas, muestras físicas, biblioteca, dimensiones, normalización, selección y entorno.
2. No emparejar solo por semilla y número de fold: comprobar índices o identificadores concretos y etiquetas. Los scripts de tablas actuales hacen `reindex` por dataset/seed/fold; eso no verifica identidad de protocolo. Detectar duplicados conflictivos antes de cualquier `drop_duplicates`.
3. Resolver KTH comparando la agrupación por muestra física de las búsquedas nuevas, controles corregidos y cascada histórica. Si cambia el subconjunto caro, reajustar también la cascada y su compuerta.
4. Resolver las discrepancias de representación CUReT/Soil antes de presentar tiempos como validación fiel del modelo cacheado. Mantener el diagnóstico del plan del 18-10.
5. Definir dos comparaciones: 21 bloques sin color para aislar el método y 22 con color para comparar con la tesis. Si se habilita color en selección, ajustar SVD dentro de cada entrenamiento interno; nunca reutilizar un SVD ajustado con validación/test.
6. Corregir la escala de ensambles y la identidad del caché antes de lanzar una grilla nueva.

Salida propuesta: `docs/fsc_tex/AUDITORIA_COMPARABILIDAD_CARLOS_CASCADA.md` y `results/analysis/integration_v1/condition_registry.csv`.

Cierre P0: cada celda aceptada tiene procedencia comprobada; variantes incompatibles quedan identificadas y no se mezclan. Las rutas propuestas no son artefactos existentes.

## 5. Experimento prioritario — cascada con rescate por subconjuntos

Pregunta: ¿un rescate de pocos miembros mejora la calidad de la cascada a un costo físico competitivo, y la adquisición condicional ahorra frente al mismo ensamble estático?

### Diseño

- Clasificador primario de integración: **SVM**, para aislar el cambio frente a la cascada actual. **ResMLP** queda como candidato estático competitivo y extensión condicionada al piloto; no afirmar que un ensamble ResMLP gana a una cascada SVM por arquitectura de adquisición.
- Etapa económica: escoger entre candidatos cuyo costo esté medido y cuya extracción sea reproducible. Selección OOF; ResNet no es obligatorio y el mejor F1 individual tampoco implica mejor calidad–costo.
- Rescate: comparar Top-k actual, Top-4 y ensamble pequeño. Piloto de ensambles con 3 y 5 miembros; 15 sirve como referencia de Carlos. No elegir tamaño usando el F1 externo.
- Relevancia: ranking interno. Diversidad: comparar lambda=0 con lambda=0,25, con beta=8 como configuraciones exploratorias heredadas; no abrir una búsqueda extensa sobre test.
- Evaluar costo de **la unión de extractores nuevos**, no suma ingenua por miembro: `U = unión(S_j)`, descontando los bloques ya computados por la etapa económica. Reutilizar también las salidas compartidas cuando la implementación permita verificar equivalencia.
- Seleccionar umbral, miembros y ruta con objetivos OOF y costo perfilado en entrenamiento. El ahorro esperado incluye ruta económica, compuerta, probabilidad de escalado, unión adicional y predicción del rescate.
- Comparar puntos a igual presupuesto y curvas calidad–latencia; no seleccionar después el único punto externo favorable.

La propuesta va más allá de insertar un ensamble: elegir subconjuntos con una penalización por el costo marginal de su unión permite evitar que miembros individualmente pequeños activen casi toda la biblioteca. Su utilidad sigue siendo una hipótesis; no prometer superioridad ni garantía de F1.

### Controles mínimos

| Control | Qué permite atribuir |
|---|---|
| Mejor individual | Ganancia frente a una sola representación |
| Completa-21 sin color y Completa-22 | Efecto de biblioteca y referencia principal |
| Top-k y GFS reconciliados | Comparación con selección estática existente |
| Top-4 estático | Valor de una ruta simple de tamaño pequeño |
| Ensamble estático idéntico al rescate | Ahorro atribuible a adquisición condicional |
| Cascada actual reconciliada | Ganancia atribuible al nuevo rescate |
| Cascada con Top-4 de rescate | Separar efecto de ensamble y tamaño del rescate |
| Ensamble de mismo subconjunto / voto duro | Diversidad entre subconjuntos y escala de puntuaciones |

No es obligatorio entrenar todos los controles en cada piloto, pero sí los comparadores primarios antes de concluir superioridad. Reutilizar resultados solo cuando pasen el registro P0.

## 6. Orden de corridas y reglas de decisión — P1 a P3

**P1, diagnóstico barato:** completar P0, regenerar métricas desde predicciones disponibles y diseñar la comparación por condiciones coincidentes. Sin elegir arquitectura por una media no emparejada.

**P2, piloto de factibilidad:** DTD official1, FMD fold0 semilla42 y Outex official1, fijados por cobertura y contraste de comportamientos. Outex es obligatorio porque penaliza Top-4. El piloto informa decisiones de desarrollo, no produce confirmación independiente. Medir 3/5 miembros, unión de bloques, escalados y latencia. Persistir fracasos.

**Regla propuesta de avance:** continuar con la integración si el registro es válido, la predicción es invariante al lote y al menos un punto aporta una mejora práctica en la frontera calidad–costo frente a cascada y ensamble estático. Definir antes del piloto la tolerancia de pérdida aceptable y el presupuesto de latencia según el objetivo de tesis; no fijar ahora un margen retrospectivo para asegurar éxito.

**P3, evaluación consolidada:** congelar la variante elegida y correr los seis datasets. Primera comparación emparejada de 27 condiciones con semilla42; ampliar cascada y comparadores a las 47 condiciones de Carlos para estudiar robustez a semillas, sin tratar esas 47 como datasets independientes. Resolver KTH antes de incluirlo en inferencia conjunta; si sigue incompatible, publicar panel reconciliado de cinco datasets y KTH descriptivo.

Si el piloto no aporta frontera útil, cerrar la integración y conservar los resultados negativos. Comparar entonces las opciones verificadas: cascada para latencia; ensamble ResMLP para calidad; Top-4 para simplicidad. Un único «mejor método» requiere declarar el objetivo y el presupuesto.

## 7. Medición, análisis e integridad — P4

- Métricas: macro-F1 primaria, accuracy secundaria; diferencias por dataset y distribución de fallos. Identificar clases y ponderación.
- Tiempo: imagen RGB decodificada→predicción, con sincronización GPU, warmup, orden pareado y modelos bajo el mismo régimen de residencia. Separar entrenamiento, ranking/CKA, extracción, compuerta, clasificadores, memoria y carga de modelos.
- Repeticiones: agrupar por imagen; no multiplicar el tamaño muestral por repeticiones de hardware. Registrar media, mediana y cola de latencia, junto a la probabilidad de escalado y bloque unión realmente ejecutado.
- Estadística entre datasets: agregar primero condiciones y semillas dentro de cada dataset; contrastes por clasificador y familia de hipótesis fijada antes del barrido. Informar efectos y p ajustados; no elegir entre Friedman, alineado y Quade por cuál rechaza.
- No inferioridad: solo si existe margen de relevancia práctica justificado antes de la nueva corrida. En datasets ya expuestos, mantener carácter exploratorio y declarar las limitaciones de N=6. Un p no significativo de superioridad no acredita no inferioridad.
- Nuevos datos de confirmación: evaluar viabilidad al final; no incorporar VisTex ni otro dataset sin nueva decisión del autor. Congelar ahora el método mejora trazabilidad, pero no vuelve vírgenes los benchmarks reutilizados.
- Preservar predicciones por imagen, puntuaciones, escalas, rutas, selección OOF, hashes, versiones y comandos efectivos. Configurar logs, PID y timeout tras un smoke run medido; no inventar duración o CLI en este plan.

## 8. Escaneo ARS de interpretación: 11/11 revisados

| Riesgo | Estado en esta revisión |
|---|---|
| Simpson | No demostrado; diferencias entre SVM/ResMLP y ponderaciones exigen paneles separados |
| Falacia ecológica | No extrapolar una media de datasets a garantía por imagen/dataset |
| Berkson | No establecido; documentar elegibilidad de condiciones y bibliotecas |
| Collider | No establecido; revisar si se filtran condiciones por resultado o factibilidad |
| Tasas base | No es cribado clínico; reportar macro-F1, clases y accuracy para revelar desbalance |
| Regresión a la media | No demostrada; evitar seleccionar el mejor piloto externo y atribuir estabilidad |
| Supervivencia | Registrar condiciones fallidas, ausentes y costos no disponibles |
| Comparaciones múltiples | Holm existe para 28 pares; contrastes suplementarios requieren familia explícita |
| Caminos analíticos | Exposición externa de k/beta/lambda declarada; resultados exploratorios |
| Correlación/causalidad | Controles insuficientes para afirmar que PCA descarta toda explicación por capacidad |
| Causalidad inversa | No aplica directamente al benchmark; no atribuir mecanismos a correlaciones CKA/F1 |

La inspección identifica límites y prioridades; no es una certificación independiente ni una auditoría exhaustiva de todas las predicciones.

## 9. Entregables y actualización de tesis — P5

1. Registro de comparabilidad y resolución de P0.
2. Reporte piloto, con decisión avanzar/cerrar y costos de unión.
3. Evaluación consolidada de la variante congelada, predicciones y tablas por condición/dataset.
4. Frente de Pareto medido para los comparadores implementados; diferenciar proyecciones de mediciones.
5. Decisión documentada del método principal según evidencia, alcance y objetivo, seguida de actualización coordinada de tesis, presentación y ZIP.

La tesis puede adoptar como hilo conductor **composición y adquisición condicional de descriptores bajo presupuesto**. Los resultados estáticos explican el problema; la integración solo pasa a ser aporte central si mejora el compromiso evaluado. Si no, la cascada verificada sigue como aporte aplicado, con el ensamble como alternativa de calidad y sus límites explícitos.

## 10. Avance aplicado — 19 de octubre de 2026

Se implementó en `src/ensemble_scoring.py` una normalización global por miembro ajustada sobre sus filas de entrenamiento. Tómbola, diversidad, control de ensamble y curva por tamaño aplican esa escala congelada a inferencia. El resultado de tómbola registra por miembro la escala y la diferencia máxima entre puntuar cinco ejemplos dentro del lote y puntuar cada ejemplo por separado. Los resultados antiguos quedan en sus rutas; la integración escribe en una carpeta nueva.

Piloto pareado del escalado: FMD, SVM, semilla 42, fold 0, `k=4`, `beta=8`, tres sorteos; Outex13 official1, `k=4`, `beta=8`, 15 sorteos. En ambos la variante histórica, que escala con el lote de test, y la variante que fija escala en entrenamiento produjeron las mismas etiquetas, macro-F1 y accuracy en ese piloto. Diferencia numérica máxima al puntuar cinco casos del lote por separado: FMD `2,78e-15`; Outex `9,77e-15`. Esto valida la invariancia de la implementación y muestra que corregir la dependencia no cambia siempre las decisiones. Registros pareados en `results/exploratory/integration_v1/score_scale_paired_pilot/`.

Piloto de cascada con rescate por ensamble: SVM, `k=4`, 15 sorteos, `beta=8`, umbral `q=0,25` fijado con márgenes OOF normalizados del entrenamiento. La biblioteca disponible es específica por dataset: 21 bloques en FMD, Outex y Soil; 22 en KTH, donde hay BEiT-v2 multilayer en vez del bloque RGB N-grams+SVD. Ninguno de estos cuatro pilotos usa RGB N-grams+SVD, y los conjuntos de bloques no se deben tratar como idénticos. Selección y threshold son internos; benchmarks ya observados hacen que siga siendo exploratorio.

| Dataset/condición | Bloques disponibles | Macro-F1 base | Top-4 estático | Ensamble estático | Completa disponible | Cascada-rescate | Escaladas | Unión | Llamadas SVM/im. | Extracción proyectada cascada / Top-4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FMD, seed42 fold0, base SigLIP | 21 | 0,9449 | 0,9596 | 0,9546 | 0,9346 | 0,9546 | 64/200 (32,0%) | 9 bloques | 4,52 | 125,74 / 265,95 ms |
| Outex13 official1, base BEiT-v2 | 21 | 0,8903 | 0,9288 | 0,9399 | 0,9618 | 0,9384 | 148/680 (21,8%) | 9 bloques | 3,39 | 90,40 / 271,77 ms |
| SoilOriginal, seed42 fold0, base SigLIP | 21 | 0,8883 | 0,8972 | 0,9064 | 0,8701 | 0,9064 | 47/228 (20,6%) | 9 bloques | 3,27 | 42,75 / 64,64 ms |
| KTHTIPS2b, seed42 official1 invertido, base BEiT-v2 | 22 | 0,9670 | 0,9916 | 0,9822 | 0,9745 | 0,9822 | 172/1188 (14,5%) | 10 bloques | 2,88 | No estimable |

La proyección suma cada extractor una vez, agrega una compuerta de `0,45 ms` y omite tiempo de clasificación; es una estimación, no medición física. Frente a Top-4 estático, F1 cambia `−0,0050`, `+0,0096`, `+0,0092` y `−0,0093` en FMD, Outex, Soil y KTH. En los primeros tres, la extracción proyectada de la cascada-rescate cae `52,7%`, `66,7%` y `33,9%`; el costo KTH no es estimable porque la unión incluye `beitv2_base_multilayer`, no presente en el perfil de hardware. La cascada Top-4 conserva la F1 estática en FMD, pierde `0,0015` en Outex y gana `0,0034` en Soil; en KTH coincide con Top-4 estático. La Completa disponible de 21 bloques sigue siendo mejor en Outex (`0,9618`). Frente al ensamble estático la cascada-rescate empata en FMD, Soil y KTH, y pierde `0,0014` en Outex. El control KTH usa el protocolo oficial invertido (tres muestras para entrenamiento y una para prueba) y agrupación interna por `sample`, consistente con la prueba de regresión del repositorio. Los 15 sorteos generaron 11 rutas únicas en FMD, Outex y Soil, y 13 en KTH. No hay inferencia con estos pilotos ni evidencia de no inferioridad. La escala corregida y la histórica dieron las mismas predicciones en los pilotos pareados de FMD y Outex. Archivos por muestra, subconjuntos y escalas: `results/exploratory/integration_v1/cascade_rescue_pilot/{FMD,Outex13Official1360,SoilOriginal,KTHTIPS2b}/`.

El control Top-4 bajo la misma compuerta separa el efecto de la política adaptativa del efecto del ensamble de rescate:

| Dataset/condición | Macro-F1 cascada con rescate Top-4 | Top-4 estático | SVM/im. (cascada Top-4) | Extracción proyectada cascada Top-4 / Top-4 estático |
|---|---:|---:|---:|---:|
| FMD, seed42 fold0 | 0,9596 | 0,9596 | 1,32 | 93,50 / 265,95 ms |
| Outex13 official1 | 0,9273 | 0,9288 | 1,22 | 69,16 / 271,77 ms |
| SoilOriginal, seed42 fold0 | 0,9006 | 0,8972 | 1,21 | 23,05 / 64,64 ms |
| KTHTIPS2b, official1 invertido | 0,9916 | 0,9916 | 1,14 | No estimable |

Estos valores son pilotos con un único split exterior cada uno; las estimaciones ignoran costo del clasificador y solo son válidas para el perfil de extracción existente. En FMD, Outex y Soil, la compuerta Top-4 reduce la extracción proyectada frente a Top-4 estático y conserva una F1 próxima. En KTH coincide en F1 con Top-4 estático, pero falta perfil de costo. Esto motiva completar controles, pero no prueba no inferioridad ni una mejora generalizable.

Archivos por muestra: `results/exploratory/integration_v1/cascade_rescue_pilot/{FMD,Outex13Official1360,SoilOriginal,KTHTIPS2b}/`. Próximo paso: revisar tamaños de ensamble 3/5 y diversidad, medir físicamente la variante congelada y completar CUReT/DTD; luego construir curvas de calidad–costo sobre condiciones coincidentes. Los cuatro pilotos no justifican todavía reemplazar el método de tesis ni actualizar sus resultados principales.

## 11. Registro del desarrollo exploratorio con 21 bloques — integración v2

La sección 12 actualiza prioridades y alcance tras revisar el código y recalcular los artefactos. En particular, la contabilidad de costos de esta sección no acredita selección por costo, y los tests no usados por esta ejecución ya estuvieron expuestos en la historia del proyecto.

### 11.1 Pregunta y decisión de desarrollo

**Pregunta:** ¿seleccionar en entrenamiento el conjunto de descriptores de rescate, su composición y el umbral de adquisición permite mejorar la frontera macro-F1–latencia frente a selección estática, la cascada existente y el ensamble estático de Carlos?

**Hipótesis de trabajo:** un rescate pequeño con selección que penalice el costo marginal de la unión de extractores puede retener ganancias de combinación sin activar indiscriminadamente toda la biblioteca. El rescate Top-4 sirve como referencia de complejidad; los ensambles de 3/5 miembros son candidatos. Los 15 sorteos quedan como referencia experimental. Esta hipótesis todavía no está validada y la originalidad bibliográfica sigue pendiente.

La comparación relevante es entre rescates bajo la misma compuerta, no solamente contra Top-4 estático:

| Piloto | Δ macro-F1: cascada ensamble − cascada Top-4 | Extracción proyectada: ensamble / Top-4 | Implicación de desarrollo |
|---|---:|---:|---|
| FMD fold0 | −0,00505 | 125,74 / 93,50 ms | Top-4 es mejor en ambas magnitudes observadas |
| Outex official1 | +0,01115 | 90,40 / 69,16 ms | Existe un intercambio calidad–costo que merece evaluación |
| Soil fold0 | +0,00581 | 42,75 / 23,05 ms | Hay ganancia de F1 con costo adicional relevante |
| KTH official1 invertido | −0,00934 | Perfil incompleto | Top-4 gana en F1; eficiencia relativa aún desconocida |

No adoptar una regla manual «ensamble para Outex/Soil, Top-4 para FMD/KTH»: esa decisión usaría los resultados externos. La regla evaluada debe elegir dentro del entrenamiento de cada condición. La observación FMD de mejor calidad y menor extracción proyectada no constituye dominancia física demostrada, porque falta latencia de clasificación y medición real.

### 11.2 Auditoría inicial de comparabilidad y biblioteca común

**Estado: inventario estático completado; integración del bloque dinámico de N-grams pendiente.** DTD, FMD, CUReT, Outex y Soil comparten 21 bloques estáticos y 20.396 dimensiones. KTH añade `beitv2_base_multilayer` (3.072 dimensiones), excluido del panel común. El proyecto sí tiene `RGBNgramSVDBlock` y caches de conteos en los seis datasets; el nuevo evaluador no los conecta todavía. Por eso los pilotos nuevos usan 21 bloques. No buscar un embedding SVD global ni regenerar todos los conteos por esa ausencia.

1. Fijar una lista explícita de bloques y persistirla junto con dimensiones y hashes de embeddings, manifiestos, índices train/test y grupos internos. Añadir el hash/versión del código al registro. Verificar que el caché del ranking también cambia al modificar protocolo interno o hiperparámetros.
2. Ejecutar el panel de desarrollo con la misma biblioteca de 21 bloques sin n-gramas en los seis datasets, excluyendo la variante multilayer de KTH para este panel. Conservar su resultado actual como variante exploratoria separada.
3. Integrar el `RGBNgramSVDBlock` existente: reutilizar conteos con manifiesto coincidente, conservar hashing fijo y ajustar SVD dentro de cada fold productor. Usar la misma biblioteca de 22 para Individual, Completa, Top-k, GFS y cascadas.
4. Mantener KTH con tres muestras de entrenamiento y una de prueba por clase; registrar explícitamente la inversión del manifiesto y el agrupamiento interno por `sample`. Mantener CUReT en sus dos direcciones y Outex en su split auditado de 1360 imágenes.

**Salidas iniciales generadas:** `results/analysis/integration_v2/six_dataset_library_inventory.csv`, `condition_registry.csv`, `pilot_comparability_summary.csv`, `audit_summary.json` y `docs/fsc_tex/AUDITORIA_COMPARABILIDAD_CARLOS_CASCADA.md`. El registro contiene hashes de embeddings, etiquetas, manifiestos, índices train/test, caché de ranking, configuración y ejecutor. Para los seis datasets solo se inventarió una partición representativa; expandirlo a todas las condiciones canónicas sigue siendo requisito antes del barrido. Ningún emparejamiento aceptado dependerá solo del nombre del dataset, seed o fold.

### 11.3 Diagnóstico de dónde ayuda el rescate

**Estado: completado para los cuatro pilotos disponibles.** Se generaron transiciones por imagen y por clase para cascada con ensamble y con Top-4. En Outex ambos dejan sin escalar dos errores que sus respectivos rescates estáticos corregirían; en los otros tres pilotos la cifra es cero. En KTH Top-4 corrige 31 errores e introduce dos, frente a 23 corregidos y cinco introducidos por el ensamble. En Outex el ensamble corrige 36 e introduce cuatro, frente a 29 y cinco con Top-4. Son conteos descriptivos de un solo split y no comparaciones inferenciales.

Este diagnóstico describe mecanismos plausibles; no seleccionar umbrales o bloques con las etiquetas externas. Una compuerta oráculo basada en test puede mostrarse exclusivamente como cota diagnóstica explícita, nunca como método desplegable ni evidencia de selección prospectiva. Igual macro-F1 tampoco implica igualdad de todas las predicciones: comprobarla por imagen.

**Salidas generadas:** `results/analysis/integration_v2/rescue_error_transitions.csv`, `rescue_error_transitions_by_class.csv` y el informe `docs/fsc_tex/AUDITORIA_COMPARABILIDAD_CARLOS_CASCADA.md`. El diagnóstico sugiere que la compuerta deja pocos errores estáticamente corregibles sin escalar; el mayor margen inmediato está en seleccionar un rescate de mejor calidad/costo, especialmente para KTH.

### 11.4 Tercer paso: selección interna del rescate y su costo marginal

**Estado: comparación interna de controles completada; selector por costo aún pendiente.** El ejecutor compara Top-3/4/5, ensambles de 3/5 subconjuntos de tamaño cuatro y cuantiles 0,10/0,25/0,50. La base maximiza macro-F1 individual interno y los subconjuntos se sortean por ranking; el costo se calcula después. Las siete condiciones son DTD-SGKF fold0 (distinto del oficial), FMD fold0, CUReT a→b y b→a, Outex split1, Soil fold0 y KTH split1 invertido. Esta ejecución no calcula métricas en su test externo, aunque los datasets y tests ya se observaron previamente. Se conservaron las fronteras OOF completas.

Para añadir un subconjunto candidato `S` a una unión ya seleccionada `U`, calcular su costo incremental como `ΔC(S|U) = suma de costos de b en S que no están en U ni en la etapa base`. Seleccionar mediante la frontera de calidad OOF y costo de la unión; contrastar contra selección por relevancia sola. No sumar el costo de un extractor repetido entre miembros. Deduplicar subconjuntos idénticos conservando su peso de voto y contar las llamadas de modelos únicos.

La variante candidata debe elegir **tipo/tamaño de rescate, etapa base y umbral** usando solamente entrenamiento. El criterio operativo será minimizar costo estimado sujeto a una tolerancia de pérdida OOF frente al control estático; la tolerancia debe justificarse y congelarse antes del próximo barrido. Esa tolerancia operativa no equivale automáticamente a un margen estadístico de no inferioridad. Si todavía no hay una tolerancia defendible, devolver la frontera de Pareto completa y postergar la elección de un único punto.

**Validación interna requerida:** en cada fold de evaluación de una política, repetir ranking, selección de subconjuntos y cualquier SVD usando exclusivamente la porción de entrenamiento de ese fold. Producir sus predicciones en la validación retenida y evaluar la compuerta sobre ellas. Seleccionar un subconjunto con todo el outer-train y luego llamarlo OOF al evaluarlo dentro de ese mismo outer-train daría una estimación optimista. Registrar esta diferencia respecto al piloto actual, cuyo ranking se calculó una vez en outer-train y cuyo umbral base sí usa márgenes OOF.

**Ablaciones:** compuerta fija con rescates distintos; rescate fijo con umbrales distintos; selección por relevancia frente a selección que considera costo de unión; modelo estático idéntico frente a adquisición condicional. Controlar la biblioteca y el clasificador SVM en todas estas comparaciones. La extensión ResMLP se mantiene separada y depende de evidencia suficiente en SVM.

**Lectura preliminar:** las fronteras OOF contienen puntos adaptativos de menor costo proyectado que sus controles estáticos en varios datasets, y en CUReT b→a aparece un ensamble-3 entre los puntos no dominados. La ganancia, base elegida y frecuencia de escalado varían por condición; el costo excluye clasificación y no es físico. Esto justifica continuar la validación, pero no seleccionar una variante final ni actualizar resultados de tesis.

**Salidas:** `results/exploratory/integration_v2/nested_frontier21/` guarda CSV de frontera, predicciones OOF y configuración por condición; `results/analysis/integration_v2/nested_selection_registry.csv` verifica siete particiones y cobertura exacta del outer-train; `nested_frontier_summary.csv` reúne las 147 políticas. El código de experimento es `src/run_rescue_nested_selection.py`; el registro se crea con `src/register_nested_frontiers.py`. No se capturó el hash exacto del código al inicio de estas corridas, así que el registro declara esa limitación explícitamente.

**Cierre pendiente:** predefinir el criterio operativo o mantener la frontera completa, incorporar N-grams con ajuste dentro de cada fold productor y evaluar la política congelada una sola vez en el test externo.

### 11.5 Cuarto paso: completar cobertura y medir costo físico

**Estado: controles internos completados en una partición de desarrollo por dataset y dos direcciones CUReT; evaluación canónica y medición física pendientes.** Hay OOF para DTD-SGKF y ambas direcciones CUReT, además de las otras cuatro condiciones de 11.4. DTD debe alinearse con sus diez splits oficiales. Resolver primero la contabilidad, el selector de costo y N-grams; luego evaluar la regla congelada sobre condiciones canónicas emparejadas. La ampliación de 27 a 47 queda para robustez a semillas. Los benchmarks ya observados siguen siendo exploratorios.

Comparadores obligatorios: Individual seleccionado internamente, Completa de la biblioteca correspondiente, Top-k y GFS reconciliados, Top-4 estático, cascada existente, cascada Top-4, cascada con rescate seleccionado y ensamble estático idéntico. Reutilizar artefactos solo cuando el registro confirme igualdad de splits y representación.

Medir imagen RGB decodificada→predicción incluyendo extracción realmente ejecutada, compuerta y clasificadores. Controlar warmup, sincronización, orden pareado, tamaño de lote, residencia/carga de modelos y memoria. Medir `beitv2_base_multilayer` solo si la variante adicional continúa en el panel correspondiente. Resolver primero la fidelidad físico–caché en CUReT/Soil. Los actuales 23–126 ms del rescate son proyecciones parciales, no tiempos físicos del sistema.

**Monitoreo de futuras corridas:** persistir configuración, comando efectivo, seed, hashes, entorno, estado, timestamps y artefactos por condición. Comprobar proceso vivo y progreso en sus logs. Determinar timeout después del smoke run medido; registrar fallos y cualquier cambio antes de reintentar. No hay nuevas corridas lanzadas por esta actualización documental.

### 11.6 Quinto paso: decisión científica y actualización del manuscrito

**Estado: posterior a la evaluación emparejada.** Presentar diferencias por dataset y curvas calidad–latencia; agregar primero condiciones/semillas dentro de cada dataset. Fijar la familia de comparaciones antes de recalcular p-valores y mantener SVM/ResMLP separados. Usar Holm donde corresponda. La inferencia conjunta solo puede incluir datasets reconciliados; KTH no entra automáticamente porque este piloto haya terminado.

La decisión del aporte central dependerá de tres posibilidades: selección del rescate con costo de unión que mejora la frontera medida; cascada Top-4 que conserva calidad descriptiva con ahorro físico; o ausencia de mejora suficiente, documentando el alcance y los resultados negativos. No reclamar originalidad por la sola combinación de técnicas: realizar la búsqueda bibliográfica específica cuando exista una definición implementada y resultados estables, antes de presentar la contribución final.

Actualizar metodología, resultados, discusión y conclusión con la variante que pase estos criterios; conservar la conciliación de bibliotecas y los experimentos negativos. El plan mantiene el objetivo de tesis de optimizar adquisición y combinación de descriptores. Los pilotos aún no permiten prometer que el método supere Completa en calidad ni que resulte superior en todos los datasets.

### 11.7 Orden de trabajo y entregables siguientes

| Orden | Trabajo | Producto verificable | Estado |
|---|---|---|---|
| 1 | Auditoría inicial de biblioteca y comparabilidad | Inventario de seis datasets y registro con hashes de cuatro pilotos | Completado; falta alinear DTD y conectar el N-gram existente |
| 2 | Diagnóstico con predicciones existentes | Transiciones por imagen y clase, cobertura y errores no escalados | Completado para los cuatro pilotos disponibles |
| 3 | Controles de ranking y contabilidad de costo | Fronteras en 7 condiciones, 21 políticas por condición | Completado como desarrollo; selector por costo pendiente |
| 4 | DTD/CUReT y variante congelada | DTD-SGKF y ambas direcciones CUReT | Desarrollo parcial; DTD oficial y regla congelada pendientes |
| 5 | 27 condiciones y medición física | Predicciones emparejadas, latencias y frontera | Pendiente; depende de N-grams y regla congelada |
| 6 | Estadística y escritura | Tablas auditadas y manuscrito coherente | Pendiente |

El trabajo vigente se detalla en la sección 12. Las fronteras actuales son controles de desarrollo y no reemplazan las tablas del manuscrito.

## 12. Secuencia y avances — integración v11, 25-10-2026

### 12.1 Evidencia de partida y alcance corregido — corte histórico del 21-10

La reauditoría recalculó 147/147 macro-F1 desde predicciones con error máximo 1,11×10⁻¹⁶. Reconstruyó siete condiciones con cobertura exacta, sin grupos solapados y sin clases ausentes en los fits productores. Esto respalda las cifras descriptivas de los controles; no reproduce sus entrenamientos ni prueba novedad.

Se detectaron cuatro correcciones prioritarias:

- DTD usó SGKF 4.512/1.128, no su split oficial. Su train contiene 1.501 imágenes del test oficial 1. La comparación con resultados oficiales exige otro emparejamiento, sin presentar esos datos como nunca observados.
- El costo por imagen debe ponderar tamaños de folds. Cambian 56/147 costos, hasta 1,300543 ms, sin cambios de Pareto en estos artefactos.
- N-grams ya tiene implementación y 102 caches de conteos; 101 coinciden con manifiestos vigentes, con al menos uno utilizable por dataset. La representación SVD se aprende por fold, no como matriz global.
- El selector por costo marginal no existe todavía: base, Top-k y sorteos dependen de ranking; costos y Pareto se calculan al final. Faltan las ablaciones que demuestren el aporte propuesto.

Evidencia reproducible: [informe completo](REAUDITORIA_INTEGRACION_2026-10-21.md), `src/reaudit_integration_v2.py` y `results/analysis/integration_v2/reaudit_20261021/`. Los tests externos ya expuestos mantienen carácter exploratorio. No se recalculan p-valores a partir de máximos OOF.

### 12.2 Secuencia ejecutable y criterios de cierre

| Orden | Trabajo | Criterio verificable para avanzar |
|---|---|---|
| P0-A | Implementado; smoke técnico completado | El evaluador pondera costos por tamaño de validación y guarda hashes de código, entorno, perfiles, manifiesto y embeddings; índices, clases, selección, modelos únicos, márgenes, umbrales, compuertas y predicciones. El smoke de FMD verificó el esquema. Los resultados anteriores no se sobrescribieron |
| P0-B | Registro canónico generado; reconstrucción histórica parcial | 27 condiciones y 216 filas de referencia creadas con hashes de manifiestos y particiones. Los logs históricos fijan comandos y protocolos, pero no guardaron índices por fila; la identidad exacta histórica queda sin certificar y debe comprobarse con una corrida emparejada nueva |
| P1-A | Implementado; ejercitado en FMD | Conteos coincidentes en lectura; SVD en cada fit de ranking/calibración/productor. Tres corridas técnicas, 15 proyecciones auditadas y control emparejado de 21. Biblioteca de 22/20.652 dimensiones. Cobertura experimental restante pendiente |
| P1-B | Implementado; pilotos FMD/Outex completados | Búsqueda greedy de base, miembros y compuerta con ganancia/costo marginal; ablación de ganancia sola bajo el mismo presupuesto y candidatos; 48 selecciones reproducidas y 26 filas auditadas. Resultados de entrenamiento externo, no evaluación final |
| P2 | En avance; pool requiere corrección | Controles directos tómbola/diversidad de 15 miembros en FMD/Outex, Outex-21 y ruta fija sin color completados; 16 pruebas aprobadas. Corregir pool con/sin color, armonizar CV y completar estabilidad, bases y controles GFS/cascada antes de congelar |
| P3 | Evaluación externa emparejada | Método y controles en las mismas condiciones y biblioteca; curvas completas, fallos e inviabilidad registrados; ampliación a 47 solo después de cerrar el panel canónico |
| P4 | Medición física | RGB→predicción con clasificadores y extractores realmente ejecutados; orden pareado, repeticiones y memoria; resolver fidelidad CUReT/Soil; controles físicos suficientes para las comparaciones declaradas |
| P5 | Estadística y manuscrito | Agregación por dataset; familia de contrastes fijada; SVM/ResMLP separados; KTH según reconciliación; escritura sustentada en resultados externos y físicos |

**Cierre P0 (21-10-2026):** `src/run_rescue_nested_selection.py` ahora usa medias de costo ponderadas por imágenes de validación y captura procedencia al inicio de cada ejecución. Los artefactos incorporan splits productores con índices y hashes, distribución de clases, ranking completo, base, subconjuntos Top-k, todos los miembros sorteados, subconjuntos/modelos únicos, márgenes, umbrales, compuertas y predicciones por imagen. Se protege contra sobrescribir resultados y la caché de ranking ahora vive en `integration_v3`. El registro se genera con `src/build_canonical_condition_registry.py` en `results/analysis/integration_v3/canonical_registry_20261021/`.

El smoke final `FMD/seed42/fold0` usó dos folds productores y dos folds de calibración; produjo 21 políticas, 800 predicciones OOF sin faltantes, 2 folds detallados, hashes de los 21 bloques, márgenes y seis columnas de compuerta. Sus archivos están en `results/exploratory/integration_v3/smoke_fmd_20261021_final/`. Es una comprobación técnica de desarrollo, no un resultado comparable con la evaluación canónica. No se reentrenó el barrido histórico ni se alteraron sus artefactos. La compilación sintáctica terminó correctamente; no se ejecutó la suite de pruebas.

El registro cubre DTD oficial 1–10, FMD seed42 folds 0–4, CUReT a→b/b→a, Outex oficial1, Soil seed42 folds 0–4 y KTH oficial1–4 invertido. Hay 216 filas de referencia primary22 (SVM/ResMLP × cuatro métodos por condición). Los hashes actuales de partición se reconstruyen desde manifiestos y el código actual; los logs viejos no guardaron esos índices. Por ello, este registro identifica el panel prospectivo, pero no certifica que cada predicción histórica corresponda fila por fila. La inferencia conjunta de KTH continúa condicionada a su reconciliación.

**Cierre P1-A (21-10-2026):** el evaluador admite `--include-rgb-ngram` y un cache explícito validado contra el manifiesto. Ranking, calibración y modelos productores usan SVD aprendida en el fit correspondiente. Se conserva el modo 21 como ablación. Las pruebas pertinentes terminaron 6/6 aprobadas; tres corridas FMD de 800 filas OOF cada una permitieron auditar 63 resultados y 15 proyecciones SVD. Todas las proyecciones ejecutadas usaron únicamente outer-train, sin solapamiento fit/evaluación y con 256 componentes. Fuente, comandos, firmas y límites están en [INTEGRACION_NGRAM_RESCATE_2026-10-21.md](INTEGRACION_NGRAM_RESCATE_2026-10-21.md).

En este piloto N-grams quedó en posiciones 18/18/17 del ranking y no cambió los Top-3/4/5. La base N-gram impuesta como diagnóstico obtuvo 0,255538, frente a 0,970082 de SigLIP; no se recomienda como base FMD con esta evidencia. No descartar su utilidad marginal en combinaciones únicamente por su rendimiento individual. Los tres folds productores y dos de calibración son una configuración técnica de desarrollo; sus cifras no reemplazan resultados canónicos.

**Cierre P1-B (21-10-2026):** `src/budgeted_rescue.py` selecciona dentro de cada fit productor bases en la frontera individual, miembros de rescate y umbral, con presupuestos de desarrollo 15/30/60/120 ms. El costo de la unión participa en cada paso greedy. La ablación usa el mismo pool, bases, cuantiles y presupuesto, cambiando solo ganancia/costo por ganancia. `src/run_budgeted_rescue.py` rehace selección y ajuste por fold; guarda scores internos, rutas, decisiones y predicciones. El auditor reproduce 48 selecciones y 26 resultados en FMD/Outex; las 21 SVD ejecutadas son internas y de 256 componentes. Detalle: [reporte P1-B](PILOTOS_SELECTOR_PRESUPUESTO_2026-10-21.md).

En Outex/120 ms, costo marginal obtiene 0,909417 frente a 0,900622 de relevancia, con 81,148 frente a 80,263 ms proyectados. Top-5 registra 0,900824/288,435 ms y Completa-22 0,913957/1706,420 ms. En FMD la comparación con relevancia cambia por presupuesto. Hay una excedencia de presupuesto observada en relevancia/Outex/60 ms en un fold; todos los presupuestos internos se cumplen. Estas cifras justifican validación adicional, sin declarar superioridad global ni ahorro físico.

**Avance P2:** se ejecutaron las recetas de Carlos con k=4, beta=8, lambda=0,25 y 15 miembros, usando sus funciones y parámetros archivados, escalas congeladas y la misma biblioteca/particiones del piloto. Diversidad soft obtiene FMD 0,978777/350,660 ms y Outex 0,914389/365,196 ms. Los puntos adaptativos mostrados tienen menos costo y algo menos F1; no se ha demostrado que sustituyan a su método. El ranking/muestreo de Carlos es componente del rescate y sus ensambles son controles competitivos.

Outex B120: 22 bloques registra 0,909417; quitar color de la misma ruta baja a 0,900328; reseleccionar con 21 da 0,895772. La primera comparación conserva base/umbral/gate y respalda aporte de color en esas rutas. La segunda mezcla cambios del descriptor y del generador: el pool tiene Top-2+N-grams pero no Top-2 solo, y el sorteo cambia al ampliar la biblioteca. Detalle y auditoría de 55 filas comparativas: [reporte P2](P2_CARLOS_Y_ABLACION_COLOR_2026-10-21.md).

**Siguiente acción concreta — P2:** (1) pool común estático con sorteos emparejados, incluyendo Top-2, y cada rescate con/sin N-grams; versionar y repetir el piloto; (2) CV interno común donde los grupos lo permitan; (3) bases de frontera frente a base de mayor F1 y controles GFS/cascada reconciliados; (4) estabilidad por semilla y desviación de costo; (5) congelar antes del panel de 27. El presupuesto es una media proyectada de selección y no garantiza cumplimiento fuera de muestra.

### 12.3 Especificación de la contribución candidata

La primera implementación de la contribución candidata construye la ruta bajo un presupuesto medio proyectado de adquisición. Busca mejorar macro-F1 interno mediante greedy de ganancia/costo marginal, considerando la base y la unión de bloques de rescate ponderada por escalado. El agregado de un miembro usa `ΔC(S|U)`, sin cobrar dos veces bloques compartidos. Base, subconjuntos, tamaño y compuerta se reajustan dentro del fit productor. No se garantiza un óptimo global ni un límite de costo fuera de muestra.

La variante implementada compara costo marginal y relevancia bajo presupuesto con el mismo generador y bases en la frontera individual. La regla registra inviabilidad, desempates deterministas y parada sin mejora positiva. El paso pendiente es comprobar si estas restricciones y el generador acotado explican sus resultados mediante ablaciones; una base dominada individualmente podría tener márgenes útiles para el escalado.

Esta formulación permite conservar la curva completa sin forzar una tolerancia de no inferioridad no justificada. No acredita originalidad: se contrastará con adquisición activa de características, cascadas y selección de ensambles bajo presupuesto cuando la implementación concreta y sus ablaciones estén disponibles.

**Controles mínimos:** base seleccionada; Complete-22; Top-k y GFS de protocolo reconciliado; rescates Top-3/4/5; ensambles de Carlos de relevancia y diversidad; cascada previa; misma ruta estática; selector propuesto sin costo marginal y con costo marginal. Comparaciones predictivas a biblioteca idéntica, y comparación de eficiencia a presupuestos comunes. Registrar llamadas de clasificadores y medirlas antes de afirmar ahorro de extremo a extremo.

### 12.4 Criterios de decisión científica

Continuar con el selector por costo solo si aporta puntos útiles frente a controles de igual presupuesto en evaluación externa y luego física. Si la mezcla adaptativa básica explica toda la ventaja, conservar ese resultado y acotar el aporte; no declarar novedoso el mero cálculo de una frontera. Si ninguna variante supera la calidad de Complete-22, evaluar el compromiso de menor costo para una pérdida explícita, sin llamar equivalencia a la ausencia de significancia.

La tesis conserva seis datasets y la biblioteca principal de 22. Los experimentos actuales de 21 sirven como desarrollo y ablación; la actualización del manuscrito espera los criterios anteriores.

### 12.5 Corrección emparejada del pool — v8

Se implementó `src/run_budgeted_rescue_paired.py` sin modificar el evaluador histórico. El pool se construye sobre el ranking relativo de los 21 bloques estáticos: Top-2/3/4/5, cinco sorteos de cuatro bloques con beta=8 y los tres bloques estáticos más baratos. La variante de 22 contiene cada candidato estático sin color y su copia con N-grams; el sorteo no depende de la posición del descriptor de color. La frontera de bases sí puede incorporar N-grams en 22: esta flexibilidad se declara y no se confunde con una ablación de ruta fija.

Las 18 pruebas específicas aprobadas cubren cierre con/sin color, determinismo, Top-2 y preservación de sorteos al cambiar la posición de N-grams. Se lanzaron dos pilotos Outex official1, seed42, con 3 folds productores y 3 internos, presupuestos 15/30/60/120 ms y cuantiles 0,1/0,25/0,5. Directorios nuevos: `results/exploratory/integration_v7/outex_paired21_20261021` y `outex_paired22_20261021`. El estado final y las cifras se deben tomar del informe emparejado, no de esta nota de lanzamiento.

**Cierre de este punto:** ambas corridas finalizaron; 48 decisiones y 26 resultados reproducidos, 12 SVD auditadas. El auditor emparejado verificó particiones, ranking estático, scores comunes y cierre del pool en los tres folds (8/16, 9/18 y 9/18 candidatos). Marginal/120 con color obtiene F1 0,906690 y 83,772 ms proyectados frente a 0,900563/97,245 sin color. Sigue debajo de Completa-22 (0,913957) y diversidad soft de Carlos (0,914389). Relevancia/120 obtiene 0,907233/89,325: la regla marginal no domina en calidad y costo. Dos excedencias de validación, ambas relevancia/60/fold1, una por biblioteca. Detalle: [informe emparejado](POOL_EMPAREJADO_OUTEX_2026-10-21.md).

**Próximo trabajo P2:** estabilidad por semilla con CV interno armonizado, sensibilidad a base de mayor F1 frente a frontera de bases y controles GFS/cascada reconciliados bajo el mismo protocolo. No congelar el método ni iniciar las 27 condiciones antes de cerrar esas ablaciones. No se alteran las tablas del manuscrito ni se incorporan nuevos datasets.

### 12.6 Ensamble de Carlos como rescate — v9

Se implementaron y ejecutaron en Outex tres variantes: ensamble diversidad15 completo con gate, poda de hasta tres modelos únicos por ganancia/costo y poda por ganancia sola, además del control siempre activo. Misma biblioteca de 22, particiones productoras e internas del piloto emparejado; nuevos scores OOF internos, reutilización declarada de scores de validación auditados de Carlos. Los 15 votos mantienen sus repeticiones en el rescate completo; la poda usa pesos uniformes sobre modelos únicos.

La auditoría reprodujo 36 selecciones, recalculó 13 resultados y comprobó 9 SVD internas; 21 pruebas específicas aprobadas. Carlos permanente: F1 0,914389/365,196 ms proyectados. Rescate completo/120: 0,908603/104,660. Podado marginal/60: 0,905140/55,365. Podado relevancia/60: 0,910742/53,316. Este último queda debajo de Carlos y Completa-22 en calidad, pero aporta un punto de menor costo proyectado; no demuestra equivalencia o ahorro físico. Hay una excedencia: completo/60/fold1=70,019604 ms. Informe: [rescate híbrido](CARLOS_RESCATE_HIBRIDO_OUTEX_2026-10-21.md).

**Orden siguiente P2:** (1) ablación estática del mismo ensamble podado, para separar poda de gate; (2) réplica en otro dataset con CV armonizado y estabilidad por semilla; (3) sensibilidad de base y controles GFS/cascada reconciliados; (4) congelar el protocolo antes de evaluar las 27 condiciones. La poda por relevancia debe conservarse como control competitivo: superó al marginal en calidad y costo a 60 y 120 en este piloto. No declarar como contribución probada la razón ganancia/costo; investigar la selección conjunta del ensamble y adquisición selectiva de sus bloques.

### 12.7 Corte documental para exposición — v10, 23-10-2026

Se consolidó el [resumen de resultados para exponer](RESUMEN_RESULTADOS_PARA_EXPONER_2026-10-23.md), sin ejecutar nuevos entrenamientos ni cambiar las tablas del manuscrito. Hoy se repitieron 21 pruebas específicas (21 aprobadas en 7,18 s), el replay del híbrido (36 decisiones, 13 resultados, nueve SVD, una excedencia) y la auditoría de emparejamiento de los tres folds con/sin color. Fuentes y archivos de entrada conservan sus hashes. Nuevas salidas: `results/analysis/integration_v8/reunion_20261023_hybrid/` y `results/analysis/integration_v7/reunion_20261023_paired/`.

El resultado a comunicar es un compromiso observado de desarrollo en Outex: podado relevancia/B60 F1 0,910742 y 53,316 ms proyectados, diversidad permanente 0,914389 y 365,196. Diferencia −0,003646 de F1 y reducción de costo estimado 85,40 %. No comunicar equivalencia, superioridad frente a Completa, significancia confirmatoria, ahorro físico o cobertura del híbrido en los seis datasets. Top-5 sí queda numéricamente por debajo de ese punto del híbrido, pero ello no sustituye un control GFS ni toda búsqueda Top-k.

El próximo trabajo sigue siendo la ablación del mismo ensamble podado siempre activo frente a su versión con compuerta. No está completada. Tampoco están completadas las réplicas del híbrido en otros datasets/semillas ni su medición física. Se conservan las reservas KTH y de fidelidad CUReT/Soil. Esta versión actualiza documentación y exposición, no el método ni su evaluación experimental.

### 12.8 Reauditoría y manuscrito actualizado — v11, 25-10-2026

Se repitió la suite completa (80 aprobadas en 32,48 s), el replay del híbrido y del pool emparejado, la revisión del selector bajo presupuesto y el recálculo de las 147 métricas históricas. Una auditoría nueva verificó las 470 filas estáticas, recalculó los contrastes de Friedman/post-hoc con Holm por clasificador y las mediciones físicas archivadas. También se recalcularon los tres métodos en las 27 predicciones canónicas: 81 filas métricas, 31.984 observaciones de test acumuladas.

Se reescribió el manuscrito para incluir el rescate de diversidad, las 13 políticas del piloto, sus límites y los controles pendientes; PDF de 39 páginas. Se conservó respaldo de las fuentes anteriores. No se alteraron los resultados originales, no se reentrenó ni se midió el híbrido en GPU. No se actualizaron ZIP de Overleaf ni el remoto.

**Dictamen:** no está cerrado experimentalmente. El [plan de cierre v11](PLAN_CIERRE_VIGENTE_2026-10-25.md) fija P0 (misma poda siempre activa frente a condicional), P1 (robustez/controles), P2 (congelamiento y panel reconciliado), P3 (fidelidad y física), P4 (estadística acorde al diseño) y P5 (entrega). La [auditoría](AUDITORIA_TESIS_Y_CIERRE_2026-10-25.md) delimita las verificaciones y no constituye certificación independiente de ARS.
