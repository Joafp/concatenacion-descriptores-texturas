# Cierre de fidelidad KTH y E1/E2 en seis datasets

Fecha: 15 de noviembre de 2026, America/Asuncion.

## Resultado

**E1/E2 tiene 27/27 condiciones completas en seis datasets.** Se conservaron
las 25 condiciones terminadas y se ajustaron únicamente los dos casos KTH
que se habían detenido antes de entrenar. Los 27 Top-4 directos reproducen
exactamente la accuracy y el macro-F1 de sus filas archivadas.

La accuracy media equiponderada por dataset es **94,4449 % con Top-4 directo
y 94,4581 % por margen**: diferencia de +0,0132 puntos porcentuales. El
contraste bilateral pareado exacto sobre seis datasets da **p=0,5625**.
Esto no acredita superioridad estadística ni equivalencia.

La adquisición por componentes proyectada pasa de 468,31 a 117,07 ms,
reducción del **75,00 %** sobre el cociente de esas dos medias de seis
datasets. **No es latencia online medida de las políticas completas.**
El corte previo de cinco datasets se conserva y no se compara su media con
la nueva como si fueran exactamente las mismas condiciones.

## E1: ganancias y pérdidas por dataset

| Dataset | Condiciones | Directo, accuracy % | Margen, accuracy % | Diferencia, pp | Directo, ms proyectados | Margen, ms proyectados |
|---|---:|---:|---:|---:|---:|---:|
| CUReT | 2/2 | 99,8574 | 99,7862 | −0,0713 | 625,58 | 148,20 |
| DTD | 10/10 | 87,0266 | 87,1117 | +0,0851 | 586,94 | 154,85 |
| FMD | 5/5 | 98,2000 | 98,3000 | +0,1000 | 586,94 | 142,19 |
| KTH-TIPS2-b | 4/4 | 95,7492 | 95,8333 | +0,0842 | 271,68 | 64,53 |
| Outex | 1/1 | 92,9412 | 92,6471 | −0,2941 | 608,67 | 141,92 |
| Soil | 5/5 | 92,8947 | 93,0702 | +0,1754 | 130,03 | 50,75 |
| Media de datasets | 27/27 | **94,4449** | **94,4581** | **+0,0132** | **468,31** | **117,07** |

Las métricas complementarias —precisión macro, recall macro y macro-F1—
salen de las mismas predicciones y están en los CSV. El ranking, la elección
de la base y el cuantil mantienen el criterio realmente ejecutado: macro-F1
OOF y tolerancia 0,005. Accuracy sigue siendo la métrica principal de reporte.
Son comparaciones exploratorias con tests ya observados.

## Cómo se resolvió el bloqueo de fidelidad

El autor autorizó explícitamente la propuesta congelada y su continuación
condicional con «SI». Antes de medir se comprobó la liberación de Deadlock,
se verificaron pesos e imágenes y se tomó el lock global. Batch1, semilla 42,
CPU dos hilos, un modelo residente y sin fits/extracciones concurrentes.

Se conservaron las mismas 33 imágenes de entrenamiento —tres por cada una
de once clases—, los checkpoints locales y el mínimo 0,999 por imagen.
No hubo búsqueda de otras semillas, recortes o tolerancias.

| Bloque | Cambio de entrada conforme a la fuente histórica | Imágenes aceptadas | Coseno mínimo | Media por componente, ms |
|---|---|---:|---:|---:|
| EVA-02 | Resize bicúbico del lado corto a 248 y recorte central 224; salida del modelo de referencia. | 33/33 | 0,9999999999986 | 25,6715 |
| SigLIP | Resize bilineal 224×224 explícito; normalización 0,5; `pooler_output` del modelo de visión. | 33/33 | 0,9999999999975 | 14,3652 |

Se verificó la huella de cada tensor de entrada antes de su forward. Se
guardaron los vectores, cosenos y tiempos de esas mismas llamadas, con
hashes. Los vectores NPY quedan locales bajo la regla global de Git; las
llamadas, sus hashes y los registros sí forman parte del repositorio.
La carga de pesos, el cálculo del coseno y la verificación SHA de entrada
quedan excluidos del tiempo de adquisición, con su alcance registrado.

Hubo **66 llamadas evaluadas y diez calentamientos en total**, sin repetir
EVA ni una llamada científica fallida. Las dos mediciones proceden de
sesiones distintas. Se conservaron exactamente las seis constantes aceptadas
anteriores y se añadieron estas dos. El perfil mixto sustenta proyecciones;
no un cronometraje homogéneo de las políticas completas.

### Correcciones de infraestructura documentadas

Tras aceptar EVA, el primer proceso se detuvo al serializar conjuntos del
informe de carga de transformers a JSON. SigLIP tenía **cero forwards**.
El estado y la evidencia se conservaron. Una corrección probada convierte
esos conjuntos en listas ordenadas y permite ejecutar únicamente el bloque
no ejecutado, sin modificar modelo, pesos, salida ni preprocesamiento.

En la preparación de la continuación también se corrigieron una ruta de
fuente y una comprobación de metadata que el ejecutor E1 no utiliza. Ambos
errores ocurrieron antes de crear la carpeta científica o ajustar modelos;
se añadieron pruebas de resolución de dependencias y cobertura de hashes.
Los arrays y etiquetas efectivamente usados por E1 se contrastaron con las
huellas originales. Ninguna corrección autoriza repetir fallos científicos.

Los dos fallos científicos originales y el corte E1 de 25/27 conservan sus
archivos y estados; no se reescribieron como exitosos. El nuevo perfil y el
cierre tienen directorios independientes. La concordancia en 33 imágenes
por red no recupera la metadata productora original de todos los NPY ni
convierte una adaptación de literatura en reproducción fiel de un paper.

## E2 con seis datasets

Se auditaron las **486 filas E2**: tres cuantiles, tres compuertas y dos
regímenes en las 27 condiciones. No hubo ajustes adicionales para E2.

Con q=0,25 y umbrales OOF, las medias de accuracy son 0,944581 (margen),
0,942485 (máximo) y 0,935649 (entropía softmax). Las fracciones reales de
activación difieren. En el diagnóstico por lote con igual cantidad derivada
son 0,944581, 0,942543 y 0,939839, respectivamente. Este segundo régimen
no es una compuerta individual online.

No hay pares de accuracy significativos tras Holm en las familias de nueve
contrastes por régimen; el menor p ajustado es 0,5625. La selección previa
de la base para margen y los scores sin calibrar limitan la generalización.
No se escogió un cuantil nuevo mirando los tests.

## Estado del manuscrito y próximo trabajo

El PDF conserva sus **87 páginas y su SHA-256 anterior**. Sigue representando
el corte anterior de cinco datasets completos; esta actualización experimental
todavía no se incorporó a su texto ni se recompiló. La siguiente revisión
editorial debe integrar las cifras nuevas y sustituir la reserva de cobertura
KTH por el alcance de la validación realizada, manteniendo las otras reservas.

Después corresponde preparar la latencia online del mismo Top-4 directo y
por margen: requiere su propio protocolo y calidad/tiempos de las mismas
llamadas. E4, E5, E6, E7 y E8 siguen con sus alcances pendientes; este cierre
no los acredita ni repite los paneles históricos.

## Archivos canónicos de este cierre

- [Autorización](../../results/analysis/kth_reference_validation_authorization_20261115_v1/authorization.json).
- [Perfil aceptado y sesiones fuente](../../results/analysis/kth_reference_validated_profile_20261115_v1/status.json).
- [Continuación de dos casos e índice de los 27](../../results/exploratory/topk_cascade/top4_fixed_kth_completion_20261115_v1/protocol_frozen.json).
- [Auditoría y resumen](../../results/analysis/top4_fixed_kth_completion_audit_20261115_v1/summary.json).
- [Calidad y costos por condición](../../results/analysis/top4_fixed_kth_completion_audit_20261115_v1/e1_conditions.csv).
- [Medias de los seis datasets](../../results/analysis/top4_fixed_kth_completion_audit_20261115_v1/e1_complete_dataset_means.csv).
- [Reproducción directa de los 27 casos](../../results/analysis/top4_fixed_kth_completion_audit_20261115_v1/direct_reference_comparison.csv).
- [Contrastes E2](../../results/analysis/top4_fixed_kth_completion_audit_20261115_v1/e2_statistics.csv).
