# Revisión ARS aplicada: Top-k y activación por margen

Fecha: 13-11-2026, America/Asuncion. Estado: ocho cambios aprobados y aplicados;
PDF compilado de 82 páginas; revisión editorial local completada.

## Decisión y alcance

El autor aprobó explícitamente «Aplicar los ocho cambios» de la propuesta
REV-01 a REV-08. Se conserva el título:

**Concatenación Top-k de descriptores para clasificar texturas: comparación del uso directo y la activación por margen**

La estructura mantiene construcción y comparación de Top-k, justificación
experimental de Top-4, N-gramas y comparadores de literatura, y después
optimización de la ejecución por margen. Los resultados y las reservas
experimentales se conservan.

## Cambios efectivamente aplicados

| ID | Mejora |
|---|---|
| REV-01 | Separación entre fracción activada OOF y externa, costo proyectado de selección y costo proyectado reportado en evaluación. La notación y el texto de resultados identifican las dos magnitudes. |
| REV-02 | Criterio de base/umbral explicado como macro-F1 OOF reunido; diferencia respecto al ranking por media de pliegues; tolerancia de 0,005 expresada como 0,5 puntos porcentuales. |
| REV-03 | Ejemplo real FMD/SVM, semilla 42 y pliegue 0: umbral 0,962190 redondeado, activación en 59/200 imágenes y distinción entre 25 % OOF y 29,5 % externo. |
| REV-04 | Parámetros reproducibles de LinearSVC y ResMLP, incluidos optimizador, lotes, épocas, paciencia y criterio de parada presentes en el código. |
| REV-05 | Identificación de la política con base seleccionada en el caption del piloto físico. Las seis cifras y sus reservas permanecen iguales. |
| REV-06 | Condición algebraica de ahorro de adquisición y tratamiento de los casos de base demasiado costosa o costo incremental nulo. |
| REV-07 | Contribución formulada mediante las dos decisiones del sistema: qué representación adquirir y para qué imágenes ejecutarla. |
| REV-08 | Conclusión de P2 conectada con mejoras, pérdidas, identidad del rescate y cobertura limitada del caso Top-4 fijo. |

En el ejemplo FMD, 133,966 ms corresponde al costo proyectado durante
selección, 153,384 ms a evaluación y 457,598 ms al uso directo de esa
condición. Son registros existentes del perfil por componentes; no se
generaron nuevas latencias ni se combinaron con otro F1.

## Procedimiento y comprobaciones

Se empleó `academic-research-suite` en modo de revisión, con una revisión de
método/código de alcance acotado y una comprobación posterior de los cambios.
Se conservaron `criteria_binding_unavailable` y `NOT_CALIBRATED`: este trabajo
no se presenta como revisión ciega, evaluación institucional ni certificación
de un pipeline académico completo.

La base de trabajo se ancló mediante la herramienta ARS. La aprobación del
autor quedó registrada y el constructor nativo validó la adjudicación. El
aplicador nativo ejecutó **12 operaciones**: **300 de 311 bloques originales
se conservaron byte a byte**. La inserción añade un bloque y los reemplazos
se limitan a los objetivos aprobados. Se exportaron siete fuentes LaTeX,
conservando sus finales de línea y los bytes ajenos a cada reemplazo.

La revisión posterior reconstruyó en memoria esos siete archivos desde la
base y las operaciones aprobadas: todos coincidieron con las fuentes
actuales. Confirmó las tasas OOF/externa, el ejemplo, los parámetros y la
desigualdad de ahorro, sin detectar cambios fuera de la propuesta.

Se verificaron **124 fuentes experimentales sin cambios**. Los gráficos y
tablas numéricas existentes permanecen intactos. Las **26 pruebas de
auditoría y controles relacionados pasaron en 14,10 s**. La compilación
Tectonic finalizó sin referencias indefinidas, etiquetas duplicadas,
caracteres ausentes ni desbordes horizontales registrados. Se revisaron
visualmente las 82 páginas renderizadas y, en mayor tamaño, la notación,
las fórmulas, el ejemplo del umbral, los parámetros y las conclusiones.

No se ejecutaron nuevos fits, extracciones, predicciones o benchmarks. No se
repitieron paneles cerrados, no se alteraron fuentes selladas, ni se realizaron
commits o push. Las reservas KTH, CUReT/Soil, diferencias histórico/online y
DeepLumina/DTD permanecen. No se inventaron contribuciones individuales CRediT
ni aprobación académica.

## Entrega y trazabilidad

- [PDF de esta revisión](../../output/pdf/tesis_topk_margen_ARS_2026-11-13.pdf).
- [Fuente principal vigente](../../paper/tesis.tex).
- [Propuesta exacta aprobada](../../results/analysis/ars_topk_revision_20261113_v1/PROPUESTA_ARS.md).
- [Adjudicación validada](../../results/analysis/ars_topk_revision_20261113_v1/author_adjudication.json).
- [Informe nativo de aplicación](../../results/analysis/ars_topk_revision_20261113_v1/working_ars_rev1.md.apply-report.json).
- [Informe de exportación](../../results/analysis/ars_topk_revision_20261113_v1/finalizer_report.json).
- [Versión final y hashes](../../results/analysis/ars_topk_revision_20261113_v1/manuscript_release_ars.json).

El respaldo anterior está en
`archive/local/tesis_before_ars_revision_20261113_v1.tar.gz`; su hash y los
de las fuentes previas se conservan en `review_receipt.json`. Es un respaldo
local, no una promesa de disponibilidad en GitHub. La versión de 81 páginas y
su manifiesto anterior constituyen el corte previo a esta ronda.

Para compilar de nuevo desde `paper`:

```sh
../.tools/tectonic-0.16.9/tectonic --keep-logs --keep-intermediates tesis.tex
```

La compilación y los controles de integridad respaldan esta revisión de
texto. La valoración final de la tesis corresponde a sus autores y al tutor.
