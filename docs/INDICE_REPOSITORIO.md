# Guía para orientarse en el repositorio

Este mapa organiza el acceso sin mover las fuentes ni los resultados: muchas rutas están dentro de manifiestos, scripts, hashes o resultados ya observados. La situación y las cantidades corresponden al corte del **17-11-2026** y deben actualizarse cuando cambien.

## Empezar aquí

| Si necesitás… | Ir a | Alcance |
|---|---|---|
| Leer la versión de revisión de la tesis | [PDF compilado el 17-11](../results/analysis/tesis_revision_20261117_v4/tesis.pdf) | Borrador de revisión; no es aprobación académica. El PDF antiguo `paper/tesis.pdf` no contiene todos los cambios posteriores. |
| Leer el paper actual entregado por el usuario | [Versión actual del 19-11](../carlos/main_actual_2026-11-19.tex) y [nota de procedencia](../carlos/VERSION_ACTUAL_2026-11-19.md) | Fuente recibida sin cambios; dependencias y compilación pendientes de verificar. Distinta de la tesis completa y de `carlos/main.tex` anterior. |
| Editar la tesis | [Fuente principal](../paper/tesis.tex), [capítulos](../paper/chapters/) y [guía de paper](../paper/README.md) | No confundir con borradores históricos bajo `paper/articulo/` o `carlos/`. |
| Saber qué se hizo y qué falta | [Estado de experimentos](fsc_tex/ESTADO_EXPERIMENTOS.md) y [cierre de coordinación](fsc_tex/CIERRE_COORDINACION_TESIS_2026-11-17.md) | Índice curado parcial; verificar siempre las fuentes originales. |
| Consultar cada expediente curado | [Fichas de experimentos](experimentos/fichas_20261118/README.md) | 18 fichas generadas desde el registro; es un corte estático, no el total de corridas. |
| Ver DeepLumina tras el pedido de Carlos | [Resultados auditados del 19-11](fsc_tex/REPORTE_DEEPLUMINA_CARLOS_2026-11-19.md) | Variante escalada B completa; adaptación original A de DTD f3 sigue en revisión. |
| Encontrar datasets, variantes y datos locales | [Catálogo de datasets](datasets/CATALOGO_DATASETS_2026-11-18.md) | Distingue imágenes, archivos, embeddings, marcadores vacíos y reservas; alcance local explícito. |
| Ver datasets usados en cada paper | [Datasets por paper](datasets/DATASETS_POR_PAPER_2026-11-18.md) | Lectura de los 11 PDF locales, con páginas y diferencias frente al material local. |
| Conocer la historia y todas las familias identificadas | [Línea de tiempo](fsc_tex/LINEA_DE_TIEMPO_TESIS_2026-11-17.md) y [catálogo de familias](fsc_tex/CATALOGO_FAMILIAS_EXPERIMENTALES_2026-11-17.md) | Incluyen antecedentes locales y Git; consultar los CSV de evidencia y sus exclusiones. |
| Saber qué se actualizó o eliminó | [Actualización documental y limpieza](fsc_tex/ACTUALIZACION_Y_LIMPIEZA_DOCUMENTAL_2026-11-18.md) | Enumera cambios, única caché retirada y comprobaciones. |
| Buscar un nombre entre carpetas y archivos | [Índice automático](fsc_tex/INDICE_ARTEFACTOS.json) y `python3 scripts/inventario_repositorio.py buscar <términos>` | Catálogo superficial; no valida resultados ni prueba que una ausencia sea nueva. |
| Consultar un protocolo antes de medir | `python3 scripts/tesis_experimentos.py buscar <términos>` y [guía del registro](fsc_tex/GUIA_REGISTRO_EXPERIMENTOS.md) | Identificar condición, versión, semillas, pesos y estado antes de cualquier ejecución. |
| Leer los artículos | [Catálogo por nombre](referencias/por_nombre/README.md) y [análisis de papers](fsc_tex/ANALISIS_PAPERS_Y_PLAN_DE_PRESENTACION_2026-11-17.md) | Los PDF son locales y están excluidos de Git. |
| Revisar figuras y tablas | [Figuras para revisión](../results/analysis/paper_figuras_revision_20261117_v2/README.md), [tabla comparativa](../results/analysis/sota_reporte_20261117_v1/tabla_accuracy.md) | Figuras y tabla descriptivas; conservar las reservas y diferencias de receta. |
| Consultar datos de una revisión | [Informe de coordinación](fsc_tex/CIERRE_COORDINACION_TESIS_2026-11-17.md) | Incluye estado de validación y pendientes. |

## Qué contiene cada carpeta principal

| Ruta | Contenido y forma de uso |
|---|---|
| `paper/` | Fuentes de tesis, capítulos, figuras, tablas generadas y borradores anteriores. `paper/presentacion_defensa.tex` está marcada como histórica; su PDF antiguo no es la defensa final. |
| `docs/fsc_tex/` | Planes, protocolos, decisiones, informes, registro e índice. Un documento con fecha antigua puede describir un estado supersedido. |
| `docs/referencias/` | Artículos locales e índices. Las copias en `por_nombre/` identifican los PDF sin alterar sus nombres originales. |
| `src/`, `scripts/`, `tests/` | Implementaciones, ejecutores/auditores y pruebas de software. No todos los scripts son intercambiables ni seguros para correr sin revisar sus entradas. |
| `results/analysis/` | Manifiestos, auditorías, informes, gráficas y algunas colas o resultados; leer `summary.json`, `coverage.json`, `manifest.json` y logs antes de interpretar cada carpeta. |
| `results/exploratory/`, `results/confirmatory/` y demás `results/` | Experimentos y artefactos originales. Los nombres no garantizan que un experimento sea concluyente o que haya finalizado. |
| `data/`, `datasets/`, `embeddings*/` | Datos, características y archivos locales. Son necesarios para distintas rutas y están mayormente excluidos de Git. |
| `presentaciones/` | Distintas versiones para reuniones y defensa; verificar fecha y fuentes antes de reutilizarlas. |
| `carlos/` | Material de colaboración y planes con historia; las notas antiguas no reemplazan auditorías posteriores. |
| `configs/`, `experiments/` | Configuraciones y definiciones de experimentos; comprobar versión y rutas antes de usarlos. |
| `archive/`, `output/`, `tmp/`, `.codex_*` | Material histórico, de salida o temporal. **No se consideran descartables automáticamente**: pueden contener evidencia o archivos no respaldados. |
| `.venv*`, `.tools/` | Entornos y herramientas de esta máquina. Su nombre no asegura que puedan eliminarse; comprobar dependencias antes de cambiar algo. |
| `skills/`, `AGENTS.md` | Procedimiento para agentes y consulta del registro de experimentos. |

## Búsqueda y actualización

En WSL, desde `/home/joaquin/tesis_claude`:

```bash
python3 scripts/tesis_experimentos.py buscar top4 margen
python3 scripts/tesis_experimentos.py verificar
python3 scripts/inventario_repositorio.py buscar e5 audit
python3 scripts/inventario_repositorio.py actualizar --confirmar-reemplazo
```

El último comando regenera **solo el índice automático**. No mueve ni borra resultados. Los estados curados se actualizan manualmente con evidencia en el registro, siguiendo [su guía](fsc_tex/GUIA_REGISTRO_EXPERIMENTOS.md). Los estados de procesos pueden cambiar en cualquier momento.

## Respaldo y limpieza

En el corte se observaron aproximadamente 18 GB en `data/`, 53 GB en `results/` y entornos locales adicionales. Son medidas aproximadas de uso de disco, no un inventario de respaldos. El `.gitignore` excluye datasets, embeddings, pesos y PDF de referencia, entre otros archivos; por tanto, tener el repositorio en GitHub **no demuestra** que todo el material esté respaldado. Revisar qué hay en el respaldo antes de limpiar, migrar o borrar. Los cambios locales y archivos no seguidos por Git también deben preservarse.

## Paper actual para revisión

La versión entregada el 19 de noviembre y su actualización con la variante DeepLumina B están identificadas en [VERSION_ACTUAL_2026-11-19.md](../carlos/VERSION_ACTUAL_2026-11-19.md). La fuente y el PDF de revisión están enlazados allí; se conserva intacta la fuente recibida.
