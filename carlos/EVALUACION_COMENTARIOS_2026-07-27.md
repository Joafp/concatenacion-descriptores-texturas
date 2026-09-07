# Evaluación de los cambios propuestos por Carlos

Fecha de revisión: 2026-07-27

## Dictamen

Las correcciones de redacción y de interpretación metodológica son pertinentes,
pero no todos los resultados numéricos descritos en
`CAMBIOS_2026-07-26.md` pueden reproducirse con el contenido actual del
directorio compartido.

## Cambios aceptados

- Evitar una lectura inferencial de pruebas de rangos aplicadas a particiones
  solapadas. Los intervalos pareados se mantienen como resúmenes descriptivos.
- Informar qué extractor resulta ser el mejor descriptor individual, en lugar
  de mostrar únicamente su puntuación.
- Explicitar que `k` y la dimensión de GFS son promedios sobre las particiones
  externas.
- Mantener el foco de la tesis en seleccionar y concatenar bloques de
  descriptores, no en destacar una arquitectura concreta.

## Cambios válidos con cautela

- Las frecuencias de selección pueden servir para describir recurrencia, pero no
  sustituyen el análisis de estabilidad ni demuestran que un descriptor sea
  universalmente necesario.
- Una tabla de antecedentes es útil sólo si cada cifra usa un protocolo y una
  métrica comparables. No corresponde afirmar estado del arte comparando
  exactitud, macro-F1 y particiones diferentes como si fueran equivalentes.

## Cambio aplazado

No se adoptan por ahora las cifras de ocho biparticiones aleatorias de CUReT.
No se encontraron en el proyecto los índices de esas particiones, la opción
`--curet-random-seed`, la constante `CURET_RANDOM_FOLD_OFFSET` ni las filas
correspondientes en el consolidado confirmatorio. Incorporarlas al artículo sin
esos artefactos rompería la trazabilidad experimental.

## Decisión aplicada al artículo

El artículo conserva para CUReT las dos direcciones verificadas del protocolo y
añade Outex_TC_00013 en color mediante los 15 folds estratificados realmente
ejecutados. De esta manera, todas las cifras incorporadas al manuscrito están
respaldadas por archivos presentes en el proyecto.
