# Estado de la tesis y resultados para exponer — 23 de octubre de 2026

> Corte histórico. La [reauditoría del 25-10](AUDITORIA_TESIS_Y_CIERRE_2026-10-25.md) y el [plan v11](PLAN_CIERRE_VIGENTE_2026-10-25.md) actualizan el estado: manuscrito reescrito, 80 tests aprobados y cierre experimental pendiente. Las cifras experimentales siguientes no cambiaron; no hubo nuevos entrenamientos en esa revisión.

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: validate; síntesis documental de resultados existentes.
- Origin Date: 2026-10-23.
- Verification Status: ANALYZED.
- Version Label: reunion_resultados_v1; plan documental integración v10.
- Alcance: comprobación de archivos, replay de selección y métricas; sin nuevos entrenamientos hoy ni reproducción independiente de los ajustes.

## 1. Qué estamos investigando ahora

La investigación pasó de comparar concatenaciones estáticas a estudiar **qué bloques adquirir, qué modelos combinar y cuándo activar una segunda etapa**, buscando un compromiso explícito entre calidad predictiva y costo. La concatenación completa se conserva como referencia, no como única contribución de la tesis.

La variante más reciente combina un descriptor base seleccionado dentro del entrenamiento con un rescate obtenido del ensamble de diversidad. La base acepta las muestras con margen suficiente; las inciertas se derivan. El rescate puede conservar los 15 votos originales o reducirse a unos pocos modelos únicos. Los descriptores compartidos y el bloque de la base no se cobran otra vez.

Es una contribución candidata implementada y ensayada: todavía no se ha demostrado su originalidad frente al estado del arte ni su superioridad general. Los resultados actuales tampoco prueban que la regla ganancia/costo marginal sea mejor que seleccionar por ganancia bajo el mismo presupuesto.

## 2. Biblioteca y cobertura

La biblioteca principal sigue teniendo **22 descriptores y 20.652 dimensiones nominales**: 16 extractores aprendidos, cinco descriptores clásicos (DRLBP, Gabor, GLCM, HOG y LBP) y RGB N-grams+SVD. Los 21 bloques estáticos suman 20.396 dimensiones; N-grams aporta hasta 256 componentes aprendidas en cada fit. No se usa una SVD global aprendida con imágenes de evaluación.

| Dataset principal | Imágenes en registro | Clases | Condiciones del panel |
|---|---:|---:|---:|
| DTD | 5.640 | 47 | 10 |
| FMD | 1.000 | 10 | 5 |
| CUReT | 5.612 | 61 | 2 |
| Outex13Official1360 | 1.360 | 68 | 1 |
| SoilOriginal | 1.140 | 7 | 5 |
| KTH-TIPS-2b | 4.752 | 11 | 4 |
| Total de condiciones | — | — | 27 |

Fuente: `results/analysis/integration_v3/canonical_registry_20261021/canonical_conditions.csv`. Son 27 condiciones, no 27 datasets. VisTex no se incorporó. La existencia del panel no significa que el nuevo híbrido se haya ejecutado en esas 27 condiciones.

## 3. Qué trabajo se completó

1. **Base histórica:** comparación de concatenación, selección de bloques y cascada anterior sobre el panel de seis datasets. Los clasificadores estáticos incluyen SVM y ResMLP; los pilotos nuevos aquí descritos usan SVM. No mezclar sus contrastes.
2. **Reauditoría de desarrollo:** se recalcularon 147 métricas históricas y se detectaron límites de comparabilidad, incluyendo el protocolo de desarrollo DTD distinto del oficial, ponderación de costos y trazabilidad histórica parcial. Se conserva el informe, sin reinterpretarlo como reentrenamiento.
3. **Selector bajo presupuesto:** selección interna de base, rescates y compuerta, comparando ganancia/costo marginal con ganancia sola. Pilotos de FMD y Outex; resultados mixtos, sin ganador universal.
4. **Controles de diversidad y tómbola:** se ejecutaron las recetas de Carlos en las mismas particiones de esos pilotos, conservando parámetros y funciones fuente y declarando las adaptaciones.
5. **Ablación de color:** se probó quitar N-grams de una ruta fija y después se corrigió el generador de candidatos para ofrecer cada rescate estático con y sin color. El pool antiguo no incluía Top-2 solo y alteraba los sorteos al añadir color; su mejor cifra no sustituye al piloto corregido.
6. **Híbrido nuevo:** se implementó el ensamble como rescate completo y como rescate reducido. La evaluación nueva terminó en Outex; no hay todavía un barrido del híbrido en los seis datasets.

Los informes detallados siguen enlazados al final. El nuevo control de diversidad usa k=4, 15 votos, beta=8 y lambda=0,25; modelos repetidos preservan el peso del voto, pero se ejecutan una sola vez. La poda selecciona modelos únicos con pesos uniformes, no optimiza los pesos originales de los 15 votos.

## 4. Resultado principal para mostrar hoy

**Protocolo:** Outex official1, seed42. Las 680 imágenes de entrenamiento se recorren mediante tres folds productores y tres folds internos. La base, el rescate y el umbral se seleccionan dentro del fit productor; su validación se reserva para medir la ruta. Esta tabla informa macro-F1 OOF de desarrollo, no F1 del test oficial. No es comparable directamente con la tabla histórica de test del manuscrito.

| Método / variante | Macro-F1 | Costo medio proyectado (ms) |
|---|---:|---:|
| Individual por ranking interno | 0,871642 | 177,300 |
| Top-3 | 0,882967 | 236,862 |
| Top-4 | 0,884244 | 256,272 |
| Top-5 | 0,900824 | 288,435 |
| Concatenación completa de 22 | 0,913957 | 1.706,420 |
| Diversidad de 15 votos siempre activa | 0,914389 | 365,196 |
| Rescate anterior, marginal / B120 | 0,906690 | 83,772 |
| Rescate anterior, relevancia / B120 | 0,907233 | 89,325 |
| Nuevo rescate completo / B120 | 0,908603 | 104,660 |
| Nuevo rescate podado marginal / B60 | 0,905140 | 55,365 |
| Nuevo rescate podado relevancia / B60 | 0,910742 | 53,316 |

B60/B120 son presupuestos medios de selección, no tiempos medidos ni límites por imagen. La tabla selecciona comparadores ilustrativos y no oculta el barrido: las 13 políticas del híbrido, incluidas B15/B30 y las dos variantes podadas B120, se conservan en el CSV fuente y en el [informe completo](CARLOS_RESCATE_HIBRIDO_OUTEX_2026-10-21.md). El punto relevancia/B60 es favorable entre los observados; no constituye una configuración de despliegue elegida con validación externa.

### Lectura numérica del punto podado relevancia/B60

- Frente al ensamble permanente: −0,003646 de F1, aproximadamente **−0,365 puntos porcentuales** en su escala porcentual, y **85,40 % menos costo proyectado**.
- Frente a Completa-22: −0,003214 de F1. No se afirma que la supere ni que sean equivalentes.
- Frente a Top-5: +0,009919 de F1, aproximadamente **+0,992 puntos porcentuales**, con menor costo proyectado. Esto no demuestra superar toda estrategia Top-k o GFS.
- Frente a las dos rutas anteriores B120: más F1 y menor costo proyectado en este piloto. Frente a los puntos anteriores B60 mejora F1, pero cuesta más.
- Selección por relevancia supera a la marginal en F1 y costo en los puntos nuevos B60 y B120. La razón ganancia/costo no está demostrada como origen de la mejora.

## 5. Qué aporta efectivamente la segunda etapa

El punto relevancia/B60 deriva **278/680 imágenes (40,88 %)**. En ese grupo corrige 52 errores de la base e introduce 5 errores donde la base acertaba: saldo de 47 aciertos. Esto compara la ruta con sus propias bases por fold; no es una diferencia de macro-F1 ni una comparación con el Individual de la tabla.

Las bases elegidas fueron DINOv2-small, BEiT-v2-final y VGG16; los rescates contienen 2, 2 y 1 modelos únicos. Por tanto, no estamos imponiendo ResNet ni ejecutando los 15 modelos en todas las imágenes. Las llamadas medias pasan de 10,665 en diversidad permanente a 1,654 en esta ruta, sin que ese conteo sustituya el cronometraje real.

**Pendiente decisivo:** ejecutar siempre exactamente los mismos ensambles podados y compararlos con sus versiones con compuerta. Sin esa ablación no podemos separar cuánto aporta la poda y cuánto la adquisición selectiva.

## 6. Color, pilotos previos y resultados que no se deben mezclar

En el piloto emparejado de Outex, marginal/B120 pasa de 0,900563 y 97,245 ms sin color a 0,906690 y 83,772 ms al permitir N-grams y reseleccionar. Esto conserva candidatos estáticos y sorteos comunes, pero cambia las rutas. No es una ablación de ruta fija. Aquella ablación histórica separada había dado 0,909417→0,900328 al retirar N-grams manteniendo base y compuerta; pertenece al pool antiguo.

En FMD hay controles anteriores comparables dentro de su propio protocolo: diversidad soft 0,978777/350,660 ms, Top-3 0,981270/128,434 y rescate por relevancia/B30 0,978802/17,954. La diferencia de F1 de los dos últimos valores próximos a 0,9788 no respalda superioridad. Ese piloto usa tres folds productores y dos internos, frente a tres internos en Outex, y aún no incorpora el nuevo híbrido. No combinarlo con Outex para producir una media global del híbrido.

## 7. Verificación de hoy y alcance de la evidencia

El 23-10 se repitieron las comprobaciones, sin reentrenar modelos:

- 21/21 pruebas específicas aprobadas en 7,18 s. No se ejecutó la suite completa.
- Híbrido: 36 decisiones reproducidas, 13 resultados recalculados y nueve proyecciones SVD auditadas; el control siempre activo coincide exactamente con las predicciones guardadas de Carlos.
- Pool con/sin color: tres folds emparejados, 26 filas comparativas; particiones, ranking estático y scores de candidatos comunes coinciden. Los pools tienen 8/16, 9/18 y 9/18 candidatos.
- Fuentes e insumos del híbrido conservan sus hashes. Reutilizar scores auditados no es reproducir independientemente el entrenamiento.
- Hay una excedencia de costo en el híbrido completo/B60/fold1: **70,019604 ms** pese a un costo interno de 59,602804. Ninguna de las 24 selecciones podadas excede en estos archivos; no es garantía para otras muestras.

Auditorías nuevas: `results/analysis/integration_v8/reunion_20261023_hybrid/` y `results/analysis/integration_v7/reunion_20261023_paired/`.

Las mediciones físicas archivadas de la cascada anterior no validan el híbrido nuevo. El piloto físico anterior cubrió una condición por dataset, 204 imágenes y 612 parejas; CUReT y Soil mantienen discrepancias entre embeddings extraídos y cacheados. Coincidir en decisiones no prueba identidad de representaciones, y no se atribuye una causa concreta a esas discrepancias sin diagnóstico. Los contrastes históricos tampoco se transfieren al híbrido ni justifican afirmar significancia de este piloto.

## 8. Cómo explicarlo oralmente

La [guía del método, extracción de features, Top-k, GFS, ensamble y cascada](GUIA_METODO_FEATURES_TOPK_ENSAMBLE_CASCADA.md) incluye diagramas, un ejemplo real de ruta y la distinción entre evaluación con caché e inferencia física.

> Partimos de una biblioteca de 22 descriptores sobre seis datasets. El problema es que concatenarlos o ejecutar un ensamble en todas las imágenes obliga a pagar su costo completo incluso en muestras sencillas. Ahora estudiamos una ruta adaptativa: una base seleccionada en entrenamiento atiende primero la imagen y activa un ensamble reducido solamente si hay incertidumbre.
>
> Ya implementamos la integración con el ensamble de diversidad y la probamos en Outex con selección interna anidada. El ensamble permanente obtuvo macro-F1 0,9144 y costo proyectado de 365,20 ms. Una variante reducida y selectiva obtuvo 0,9107 con 53,32 ms: pierde unos 0,365 puntos porcentuales de F1, pero el costo estimado baja 85,4 %. También mejora numéricamente a Top-5 en ese piloto. No supera en calidad al ensamble completo ni a la concatenación completa.
>
> El resultado respalda investigar la selección del ensamble junto con la adquisición selectiva. Todavía debemos separar el aporte de la poda del de la compuerta, repetir en otros datasets y semillas y medir la ruta real. No estamos afirmando equivalencia estadística, superioridad general ni ese ahorro como latencia física ya medida.

## 9. Preguntas previsibles

**¿Usaron el trabajo de Carlos?** Sí: ranking, recetas de muestreo/diversidad y ensamble de 15 votos como control y como fuente de rescates. La nueva investigación es la selección conjunta del rescate y su activación bajo presupuesto, no presentar su ensamble como trabajo ajeno al proyecto.

**¿Ya se terminó la evaluación de la propuesta nueva?** No. Hay un piloto híbrido completo y auditado en Outex; el panel histórico tiene seis datasets, pero el híbrido aún no fue evaluado en todo ese panel.

**¿Ya se ganó en accuracy o F1?** No frente a todo. En este piloto hay mejora numérica respecto de Top-5 y de puntos de la cascada anterior; frente a Completa y diversidad permanente existe una pérdida explícita de F1 a cambio de menor costo proyectado.

**¿El 85,4 % es una aceleración real?** No. Es reducción del costo analítico del perfil empleado. Falta medir extracción, clasificadores y régimen de carga/residencia del nuevo sistema.

**¿La prueba estadística confirma la propuesta?** No se calculó un contraste confirmatorio para este piloto. Los benchmarks ya estuvieron expuestos al desarrollo; tres folds de un dataset no son tres datasets independientes.

**¿Cuál es el aporte defendible hoy?** Una implementación trazable de selección del ensamble y enrutamiento costo-consciente, con un punto de desarrollo prometedor. Su novedad y robustez general siguen pendientes de contraste y evaluación.

## 10. Próximo trabajo en orden

1. Ablación del mismo ensamble reducido siempre activo frente al mismo ensamble con compuerta.
2. Réplica en otro dataset con protocolo interno armonizado; estabilidad por semilla.
3. Sensibilidad de la base y controles GFS/cascada reconciliados, con el mismo protocolo.
4. Congelar método y familia de comparaciones antes del panel de 27; mantener las reservas de procedencia de KTH.
5. Medición física del híbrido; resolver discrepancias históricas CUReT/Soil antes de reutilizar sus conclusiones de fidelidad.
6. Incorporar resultados finales y contrastes pertinentes al manuscrito, sin sustituir tablas históricas por métricas OOF de desarrollo.

## 11. Trazabilidad y revisión ARS

Fuentes principales: [plan vigente](PLAN_INTEGRACION_CARLOS_CASCADA_2026-10-19.md), [piloto híbrido](CARLOS_RESCATE_HIBRIDO_OUTEX_2026-10-21.md), [pool emparejado](POOL_EMPAREJADO_OUTEX_2026-10-21.md), [controles y color](P2_CARLOS_Y_ABLACION_COLOR_2026-10-21.md) y [plan histórico de fidelidad](PLAN_CIERRE_TESIS_2026-10-18.md). Cifras: `results/exploratory/integration_v8/carlos_hybrid_outex22_20261021/results.csv` y `results/exploratory/integration_v7/outex_paired22_20261021/results.csv`.

Se revisaron 11/11 patrones: Simpson (no mezclar presupuestos/datasets); falacia ecológica (medias no son garantías por imagen); Berkson (Outex es desarrollo seleccionado); colisionador (el gate selecciona dificultad); tasas base (macro-F1 no es accuracy); regresión a la media (el mejor piloto no es estabilidad); supervivencia (conservar todos los presupuestos y excedencias); búsqueda múltiple (sin p-valores del máximo); caminos analíticos (diseño informado por desarrollo); causalidad (proyección no es ahorro físico ni mecanismo aislado); causalidad inversa (sin inferencia temporal). La revisión es inline en la misma conversación, no un dictamen independiente.

Esta actualización prepara la exposición de resultados y el plan; no modifica `paper/tesis.tex`, no recompila PDF/ZIP y no declara completadas las tareas pendientes. No se consultó ni sincronizó el remoto en esta revisión local.
