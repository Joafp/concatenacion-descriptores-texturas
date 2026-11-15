# Cierre E1/E2: 27 condiciones y seis datasets

[Informe legible y límites](../../../docs/fsc_tex/CIERRE_FIDELIDAD_KTH_E1_E2_2026-11-15.md) ·
[Resumen numérico](summary.json) · [Verificación](verification.json).

Se auditan 25 condiciones conservadas y dos KTH nuevas. Los 27 resultados
directos reproducen exactamente accuracy y macro-F1 guardados. Se recalculan
métricas desde predicciones, compuertas desde scores y costos desde constantes;
no hay ajustes o forwards en esta auditoría. Hay 486 filas E2.

- [Tabla de los seis datasets](e1_complete_dataset_means.csv).
- [Resultados y carpeta fuente de cada condición](e1_conditions.csv).
- [Accuracy, precisión/recall macro y macro-F1 de las bases solas](e1_cheap_candidate_test_metrics.csv).
- [Coincidencia con Top-4 archivado](direct_reference_comparison.csv).
- [Compuertas](e2_conditions.csv), [medias](e2_complete_dataset_means.csv) y [contrastes](e2_statistics.csv).
- [Fuentes y salidas con SHA-256](provenance.json).

Accuracy media: 0,944448526 directa y 0,944580737 por margen; p exacto=0,5625.
Adquisición proyectada 468,31→117,07 ms, reducción 75,00 %. No es una nueva
latencia online de las políticas completas. Los tiempos de componentes de
KTH proceden de sesiones explícitamente distintas.

Los clasificadores joblib, embeddings y vectores NPY permanecen locales con
hashes bajo las reglas globales de Git. Las predicciones y scores de los dos
casos nuevos se guardan comprimidos en la carpeta de continuación, y los de
las otras 25 condiciones conservan sus carpetas originales.

El PDF mantiene la edición previa de 87 páginas; este cierre experimental
todavía requiere integración editorial y nueva compilación.
