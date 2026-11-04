# Panel local FMD/SVM: cinco pliegues, semilla 42

## Material Passport

- Fecha: 28-10-2026. Resultado de ejecución ARS inline.
- Estado: cinco pliegues externos completos y reproducidos desde cabezas;
  agregación validada por claves, hashes y cobertura. Latencia pendiente.
- Alcance: solo SVM, una semilla de las tres previstas para FMD.
- Protocolos: piloto externo local y continuación FMD del 28-10.

## Media por pliegue frente a F1 agrupado

| Método | Media macro-F1, cinco pliegues | Macro-F1 agrupado, 1.000 imágenes |
| --- | ---: | ---: |
| Completa-22 | 0,965099 | 0,965031 |
| Ensamble diversidad | 0,978911 | 0,978972 |
| Ensamble tómbola | 0,978912 | 0,978977 |
| Top-4 | 0,981922 | 0,981983 |
| Selección adaptativa con margen | 0,977976 | 0,977997 |

La tabla principal usa la media de macro-F1 de las condiciones, como el archivo
histórico. El F1 agrupado se conserva como métrica distinta; no intercambiarlo
por esa media. Hay 1.000 imágenes externas únicas por método y 5.000 predicciones
en total, no 5.000 imágenes independientes ni cinco datasets.

## Interpretación acotada

La ruta adaptativa supera numéricamente a Completa-22, pero queda por debajo
de los dos ensambles y Top-4. La ventaja frente a todos ellos en la primera
partición no se mantiene al completar esta semilla. Se activó el rescate en
13,8% de las imágenes externas, media ponderada por imagen.

Las pérdidas no se ocultan ni se afirma equivalencia con el ensamble. Sin
latencia física no se puede concluir que un eventual ahorro compense la
diferencia de F1. No se ajustaron presupuesto, umbral o candidatos con el test,
ni se realizaron contrastes inferenciales nuevos.

## Verificación y artefactos

Cada pliegue contiene su selección OOF previa al test, heads finales, scores,
predicciones, métricas y auditoría por imagen. La agregación exige que cada
fila de FMD aparezca exactamente una vez por método, etiquetas idénticas entre
métodos, cinco pliegues y hashes de auditorías/CSV sin cambios. Rechaza colas
incompletas e imágenes repetidas; se probaron ambos rechazos y el caso completo.

- Piloto: `results/exploratory/local_external_panel_20261028/FMD_s42_f0_svm/`.
- Continuación: `results/exploratory/local_external_followup_20261028/FMD_s42_svm/`.
- Agregación: `results/analysis/local_fmd_seed42_summary_20261028/svm/`.

La cola ResMLP/42 de los otros cuatro pliegues continúa aparte. Las semillas
123 y 2026, los demás datasets y el cronometraje todavía no están completos.
La tabla histórica de FMD promedia tres semillas y no es directamente esta
fila de una sola semilla. Los resultados históricos y el manuscrito permanecen
intactos.
