# DenseNet121: diferencia por lote de ejecución

## Material Passport

- Fecha: 28-10-2026; diagnóstico numérico ARS inline.
- Protocolo: `PROTOCOLO_DIAGNOSTICO_DENSENET_2026-10-28.md`, previo al cálculo.
- Estado: cuatro configuraciones completadas, ocho comparaciones conservadas.
- Ningún embedding, clasificador o F1 anterior se modificó. Sin tiempos publicados.

## Resultados en las dos filas fijas

| Configuración | Error máximo, fila 3 | Error máximo, fila 996 | Ambas <= 1e-4 |
| --- | ---: | ---: | --- |
| Predeterminada, una imagen | 0,0001124591 | 0,0001412332 | No |
| Predeterminada, lote original | 0 | 0,000000014901 | Sí |
| Sin TF32, una imagen | 0,0001551956 | 0,0002359003 | No |
| Sin TF32, lote original | 0,0001551956 | 0,0002359003 | No |

Las dimensiones coinciden y los vectores son finitos en las ocho comparaciones.
Los lotes originales contienen filas 0–15 y 992–999: el segundo es el último
lote parcial de ocho, no 16 imágenes artificialmente repetidas. Se verificaron
hashes del manifiesto y del embedding contra la metadata original, y de las
imágenes de diagnóstico contra el preflight anterior.

Manteniendo checkpoint, transformaciones y semilla, ejecutar con los lotes
originales reproduce las dos filas archivadas. Batch1 con la configuración
predeterminada no pasa la tolerancia original; deshabilitar TF32 tampoco la
recupera. Esto muestra dependencia numérica del régimen de ejecución. No
localiza por sí solo cada kernel responsable ni prueba todo el conjunto FMD.

## Consecuencia para la tabla

No asociar directamente F1 del archivo batch16 con latencia batch1 como si
ambos se hubieran validado en una única ejecución. Tampoco llamar latencia
individual al tiempo de un lote dividido por el número de imágenes: eso es
tiempo medio por imagen del procesamiento en lote.

Se consultó al usuario por el régimen principal:

- Latencia individual: comprobar F1 usando la ejecución batch1 efectiva,
  conservando la tabla histórica aparte. No equivale a declarar paridad de
  vectores dentro de 1e-4 ni exige sobrescribir embeddings.
- Procesamiento por lotes: validar calidad bajo el mismo régimen y reportar
  throughput/tiempo medio por imagen, con el tamaño de lote explícito.

No se relaja la tolerancia ni se implementa un modo alternativo tras observar
el test. La auditoría de F1 en caché sigue siendo válida en su propio alcance.

## Artefactos y trabajo independiente

`results/analysis/densenet_parity_diagnostic_20261028/` contiene estado completo,
ocho comparaciones y vectores de las cuatro configuraciones. La cola de calidad
FMD/SVM/42, pliegues 1–4, se inició por separado según
`PROTOCOLO_CONTINUACION_FMD_2026-10-28.md`; no produce latencias desde imágenes
ni se considera terminada por haber comenzado.
