# Continuación autorizada: solo KTH 1 y 3

Esta carpeta ajusta únicamente `KTHTIPS2b_svm_s42_f0` y `KTHTIPS2b_svm_s42_f2`,
que no habían entrenado por costos ausentes. El [protocolo](protocol_frozen.json)
indexa además los otros 25 casos por sus carpetas originales; no los copia ni
repite. [Estado global de 27/27](status.json).

Se conservan los bloques, semillas, particiones, agrupación física y criterio
de selección OOF del E1 anterior. Solo se completan los costos faltantes con
componentes que superaron la validación autorizada. Los costos aceptados
anteriores permanecen exactamente iguales.

[Auditoría de seis datasets](../../../analysis/top4_fixed_kth_completion_audit_20261115_v1/README.md)
y [reporte](../../../../docs/fsc_tex/CIERRE_FIDELIDAD_KTH_E1_E2_2026-11-15.md).
Los modelos joblib quedan locales con hashes; predicciones y scores OOF/test
completos están en `conditions/*/scores_predictions.json.gz`.
