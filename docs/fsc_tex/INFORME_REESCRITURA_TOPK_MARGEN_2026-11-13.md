# Reescritura de tesis: Top-k directo y optimización por margen

Fecha: 13-11-2026, America/Asuncion. Estado: borrador completo compilado,
evidencia reconstruida y reservas científicas abiertas.

## Título y argumento principal

**Concatenación Top-k de descriptores para clasificar texturas: comparación del uso directo y la activación por margen**

Se reescribieron los siete capítulos, la portada y los resúmenes español e
inglés. El PDF vigente tiene 81 páginas. El recorrido del argumento tiene dos
partes: construir y comparar Top-k; después optimizar cuándo ejecutarlo con
la activación por margen. La versión optimizada se conserva en el cuerpo
principal con selección interna, ecuaciones, diagrama y resultados.

El rescate de ensamble y la poda desarrollados anteriormente se preservan en
un anexo complementario. No se utilizan sus ahorros para atribuir resultados
al rescate Top-k. La versión anterior, incluido el PDF, se respaldó localmente
en `archive/local/tesis_before_topk_rewrite_20261113.tar.gz` y un manifiesto
SHA-256. Este respaldo local no se garantiza en el repositorio remoto.

## Pasos que ahora explica la tesis

1. **Descriptores individuales:** representar la misma imagen mediante
   bloques y puntuarlos por validación interna del entrenamiento.
2. **Concatenación completa:** unir todos los bloques de una biblioteca y
   entrenar un clasificador para comprobar qué aporta utilizar toda esa
   información y cuánto aumenta la representación.
3. **Selección de bloques:** comparar GFS, Homogénea y Top-k de tamaño
   emparejado. Ordenar por rendimiento individual es una regla distinta de
   valorar las adiciones a una combinación.
4. **Barrido del tamaño:** pasar de un tamaño heredado a evaluar todos los
   prefijos de uno a 21 bloques; distinguir el registro inicial de 27
   condiciones del archivo ampliado de 47 por tamaño y clasificador.
5. **Aporte marginal y Top-4:** mostrar cuánto mejora o empeora cada bloque
   adicional y qué dimensión se necesita; conservar todos los tamaños.
6. **Ampliaciones y alternativas:** identificar bibliotecas con/sin N-gramas,
   transformaciones aprendidas y el alcance de otras búsquedas exploratorias.
7. **Comparadores de literatura:** presentar recetas adaptadas y resultados
   online con F1 y tiempo de las mismas llamadas, separados del F1 histórico.
8. **Optimización por margen:** comparar el mismo Top-k siempre ejecutado
   con una base que lo activa cuando su margen es menor o igual al umbral
   aprendido en entrenamiento; contabilizar base y adquisición incremental.

La metodología incluye un ejemplo real: FMD/SVM, semilla 42, pliegue 0,
concatena SigLIP-base (768), DINOv2-large (1.024), EVA02-base (768) y
DINOv2-base (768). Tras normalizar cada bloque, un solo SVM recibe 3.328
coordenadas. Las cuatro identidades corresponden a esa condición, no a una
selección universal.

## Qué sostiene la elección de cuatro

El barrido ampliado contiene 987 filas SVM y 987 ResMLP, con 47 condiciones
para cada tamaño. Se promedia primero dentro de cada dataset y luego se
equiponderan los seis datasets.

| Resultado SVM | Valor |
|---|---:|
| Macro-F1 medio con un bloque | 0,917448 |
| Macro-F1 medio con cuatro | 0,936554 |
| Máximo descriptivo, diez bloques | 0,936764 |
| Ganancia de uno a cuatro | 1,910633 puntos porcentuales |
| Ganancia de cuatro al máximo en diez | 0,020992 puntos porcentuales |
| Dimensión media relativa con cuatro | 15,42 % |
| Dimensión media relativa con diez | 45,17 % |

Top-4 concentra 98,91 % de la mejora observada entre uno y el máximo SVM.
Esta proporción no es accuracy ni una prueba de equivalencia. Después de
cuatro hay ocho pasos negativos y nueve positivos: la curva no disminuye de
forma monótona. Su eje es número de descriptores, no imágenes de entrenamiento
ni épocas.

En FMD, cuatro alcanza el mayor F1 medio del barrido con ambos clasificadores;
en Soil también con SVM. Con ResMLP, el máximo global aparece en cinco.
Outex se beneficia de representaciones mayores. El resultado sustenta una
opción compacta con buena calidad; no superioridad universal, selección ciega
de k ni ahorro físico proporcional al tamaño del vector.

Las figuras presentan los 42 puntos medios, 40 ganancias marginales y 252
puntos dataset/clasificador/tamaño, sin omitir valores posteriores a cuatro.

## Auditoría del uso directo y optimizado

Se reconstruyeron 27 condiciones SVM y 31.984 observaciones de prueba desde
predicciones guardadas. Las imágenes se reutilizan entre particiones y no
se consideran observaciones independientes. En cada imagen derivada, la
predicción condicional coincide con la del mismo rescate directo. Los tamaños
son de uno a ocho, no siempre cuatro.

Cinco condiciones tienen cuatro bloques y coinciden con el Top-4 del barrido:
dos DTD, dos FMD y una CUReT. La coincidencia de bloques no acredita identidad
de todos los ajustes entre archivos. Se conservan mejoras, pérdidas y empates.
No se atribuye cobertura Top-4 fijo por margen en los seis datasets.

La calidad, fracción activada, adquisición proyectada y pilotos físicos se
presentan por separado. Por ejemplo, la cascada mejora FMD en promedio y
empeora Outex. Un ahorro de adquisición por componentes no se etiqueta como
una nueva medición de latencia.

## Validaciones y procedencia

- **26 pruebas aprobadas en 15,63 s**: integridad, cobertura, reconstrucción de
  métricas, identidad del rescate, ganancias y controles relacionados. No se
  sumaron tests históricos para formar este conteo.
- Compilación Tectonic satisfactoria, sin referencias indefinidas, etiquetas
  duplicadas, caracteres ausentes ni desbordes horizontales registrados.
- PDF renderizado y revisado visualmente, incluidos diagramas, las curvas
  nuevas y las tablas de resultados.
- 124 fuentes experimentales vinculadas por SHA-256 en la auditoría principal;
  hashes adicionales de fuentes y salidas en el análisis de ganancias.
- Metadatos de DeepLumina, HyTexNet y LBP+dCellNN corregidos contra los DOI
  consultados y conservados en `reference_metadata.json`.
- Cero fits, extracciones, nuevas predicciones o tiempos experimentales para
  esta reescritura. Se utilizaron resultados existentes; no se repitieron
  paneles cerrados, no se alteraron fuentes experimentales selladas y no se
  ejecutaron nuevos benchmarks GPU.
- Sin commits ni push. Esta entrega es local y requiere revisión de autores
  y tutor antes de considerarse aprobada.

Comando de pruebas desde la raíz:

```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 MPLBACKEND=Agg \
.venv-confirmatory/bin/python -m pytest -q \
  tests/test_topk_margin_thesis_evidence.py \
  tests/test_cheap_stage_selected_report.py \
  tests/test_cascade_multidataset_benchmark.py \
  tests/test_audit_outex_crosscalls_20261104.py \
  tests/test_deeplumina_stationarity_20261104.py
```

## Reservas y trabajo pendiente

Permanecen las discrepancias entre Top-4 histórico y online, especialmente
Soil; las variantes y reservas de procedencia KTH; las diferencias de
representación de los pilotos CUReT/Soil; DeepLumina bajo revisión por no
convergencia y cobertura DTD incompleta; y controles específicos faltantes
de complementariedad con N-gramas. No se inventaron causas ni se eligió la
cifra más favorable entre archivos.

Una campaña física íntegra del mismo Top-k directo/margen exige conciliar
las representaciones y congelar receta, semillas, particiones y presupuesto.
Los datos ya observados conservan su carácter exploratorio. No se requieren
porcentajes idénticos a los papers para describir honestamente la evidencia.

## Entrega y reconstrucción

- [PDF vigente](../../paper/tesis.pdf) y [fuente principal](../../paper/tesis.tex).
- [Plan actualizado](PLAN_TOPK_MARGEN_2026-11-13.md).
- [Auditoría principal](../../results/analysis/topk_margin_rewrite_20261113_v1/summary.json).
- [Ganancias y curvas por dataset](../../results/analysis/topk_marginal_gains_20261113_v1/summary.json).
- [Manifiesto de versión y hashes](../../results/analysis/topk_margin_rewrite_20261113_v1/manuscript_release.json).

Los generadores `scripts/build_topk_margin_thesis_20261113.py` y
`scripts/build_topk_progression_20261113.py` rechazan directorios existentes;
usar rutas nuevas para reconstruir sin alterar esta entrega. La identificación
de los cinco casos se verifica con `scripts/audit_top4_margin_subset_20261113.py`.
La compilación desde `paper` utiliza
`../.tools/tectonic-0.16.9/tectonic --keep-logs --keep-intermediates tesis.tex`.
Las presentaciones y paquetes Overleaf anteriores conservan su propia fecha.
