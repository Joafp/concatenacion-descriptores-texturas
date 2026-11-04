# Controles concatenados emparejados — protocolo de desarrollo

## Material Passport

- Origin Skill: ARS experiment-agent, guía local de ejecución, no pipeline formal
- Origin Date: 2026-10-26
- Verification Status: UNVERIFIED — protocolo fijado antes de las nuevas selecciones
- Version Label: matched_concat_v1

## Pregunta y cobertura

Continuación de P1 del plan vigente: evaluar GFS y Top-k concatenados sobre los mismos entrenamientos y validaciones productores que el híbrido. No cambiar el híbrido para mejorar su resultado. No se utiliza el benchmark externo como sustituto de este control.

Se incluyen FMD semillas 42, 123 y 2026, Outex semillas 123 y 2026 de la réplica, y Outex/42 del piloto. Son seis condiciones de desarrollo en dos datasets, no seis dominios independientes. FMD tiene 800 filas de desarrollo por condición y Outex, 680. Se reutilizan exactamente los tres pliegues productores y tres internos guardados, los grupos, etiquetas, biblioteca de 22 bloques, ranking y perfil de costos. Las imágenes externas quedan excluidas.

## Controles predefinidos

1. **GFS sin presupuesto:** búsqueda hacia delante hasta ocho bloques; evalúa todas las adiciones posibles en cada paso; elige mayor macro-F1 interno (media de los tres pliegues). Empate: nombre léxico mayor, como el GFS archivado. Para después de dos mejoras consecutivas inferiores a 0,001 y devuelve el mejor paso histórico, no el último. La adaptación necesaria usa tres pliegues guardados en lugar de los cuatro internos predeterminados del benchmark y concatenación en orden canónico, igual que el híbrido. No se modifica el programa histórico.
2. **Top-k con tamaño GFS:** usa el ranking individual guardado y exactamente el tamaño del GFS sin presupuesto. No son Top-3/4/5 ni un tamaño elegido mirando validación productora. Sus empates de ranking siguen el registro del piloto. Se informa su propio F1 interno, sin usarlo para cambiar k.
3. **GFS bajo presupuesto, variante diferenciada:** repite el camino greedy desde cero para cada B=15/30/60/120, descartando adiciones cuya suma de costos exceda B; conserva parada y mejor paso de GFS. No es truncar retrospectivamente el camino libre ni una búsqueda óptima global.
4. **Prefijo bajo presupuesto, variante diferenciada:** entre prefijos del ranking de tamaño 1 a 8 factibles bajo B, selecciona el mayor F1 interno. Desempates por menor costo, tamaño y orden léxico. Su k no procede de GFS y no se lo denomina Top-k histórico. Si ningún prefijo cumple, se registra inviabilidad; no se omiten bloques caros para construir otro ranking ni se usa un modelo fuera del presupuesto.

Estas variantes presupuestadas evitan presentar GFS/Top-k libres como si cumplieran automáticamente los presupuestos del híbrido. Se conservan sus resultados negativos y las políticas inviables. La factibilidad de un control estático es por unión fija de bloques; la del híbrido restringe una media de selección, cuyo valor en validación puede diferir.

## Ajustes, reutilización y registro

Se mantiene SVM C=1, bloques congelados y normalizados por fila, receta del piloto y SVD de N-gramas aprendida únicamente en el entrenamiento pertinente. Se reutilizan las puntuaciones OOF internas archivadas de individuales y candidatos solo con igualdad de índices, fuentes y configuración; las concatenaciones faltantes se ajustan en los tres pliegues internos guardados. El criterio de GFS es la media de F1 por pliegue, igual que su antecedente, no F1 reunido. La selección de políticas se congela para los tres productores antes de ajustar/evaluar sus validaciones. El F1 reportado se calcula reuniendo una predicción productora por imagen y política.

Se guardan: configuración/comandos/hashes antes de ejecutar, todos los candidatos y caminos, scores internos y productores, índices, decisiones congeladas, predicciones, transformaciones N-gramas, costos y estados de cobertura. Los resultados van a un directorio nuevo. No se sobreescriben ni reajustan híbridos, estáticos de ensamble, pilotos o réplicas anteriores.

## Ejecución y auditoría

Dos condiciones simultáneas, dos hilos BLAS por proceso; límite de 30 minutos por condición, con PID, estado y logs. No se reintentan fallos automáticamente. Una ausencia temporal de logs es una advertencia, no una refutación científica. Solo una salida con cobertura completa y auditoría posterior puede incorporarse como resultado terminado.

La auditoría reproduce decisiones desde scores internos, índices/grupos y F1/costos desde predicciones, incluyendo el k heredado, presupuestos y ausencia de test. Comparará después con el híbrido y estático del mismo origen; no escogerá una política por F1 productor. Los dos datasets y semillas dependientes no justifican nuevos p-valores poblacionales ni equivalencia. Los costos son proyecciones del perfil compartido, no latencia física ni tiempo de entrenamiento. El diseño se fija después de observar el híbrido y no se presenta como preinscripción ciega.
