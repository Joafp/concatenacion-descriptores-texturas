# Salidas LaTeX SCI2S organizadas

Esta carpeta contiene copias navegables de las salidas generadas por Java.
Los archivos originales permanecen en `results/confirmatory/nonparametric/` y
las copias anteriores en `latex_sci2s/`.

## Cómo encontrar cada salida

La estructura es:

```text
latex_sci2s_organizado/
├── ControlTest/
│   └── <métrica>/
│       ├── primary.tex
│       └── sensitivity.tex
└── MultipleTest/
    └── <métrica>/
        ├── primary.tex
        └── sensitivity.tex
```

Métricas disponibles:

- `accuracy`
- `balanced_accuracy`
- `precision_macro`
- `recall_macro`
- `macro_f1`
- `auc_roc_ovr_macro`

## Significado de las carpetas

- **ControlTest:** el programa elige una estrategia de control y la compara
  contra las restantes.
- **MultipleTest:** el programa compara todos los pares de estrategias.
- **primary:** cuatro bloques independientes, DTD, FMD, CUReT y Outex.
- **sensitivity:** ocho bloques dataset-clasificador, separando SVM y ResMLP.

## Ejemplos

- `ControlTest/macro_f1/sensitivity.tex`: ControlTest para macro-F1 en la
  sensibilidad.
- `MultipleTest/macro_f1/sensitivity.tex`: todas las comparaciones de
  macro-F1 en la sensibilidad.
- `MultipleTest/auc_roc_ovr_macro/primary.tex`: todas las comparaciones de AUC
  en el análisis primario.

También se conservaron copias históricas y las ejecuciones focalizadas de GFS
vs. Individual en la raíz de cada módulo.
