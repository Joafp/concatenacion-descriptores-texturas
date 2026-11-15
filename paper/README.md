# Tesis: Top-k directo y activación por margen

Actualizada el 15-11-2026: **90 páginas**, E1/E2 completo en **27/27 condiciones y seis datasets**, accuracy principal. Macro-F1, precisión macro y recall macro complementan el reporte; la selección histórica por macro-F1 permanece explícita.

- [PDF vigente](tesis.pdf) y [fuente](tesis.tex).
- [Cierre experimental y reservas](../docs/fsc_tex/CIERRE_FIDELIDAD_KTH_E1_E2_2026-11-15.md).
- [Entrega e integración](../docs/fsc_tex/INTEGRACION_TESIS_SEIS_DATASETS_2026-11-15.md).
- [Plan vigente](../docs/fsc_tex/PLAN_TOPK_MARGEN_2026-11-13.md).
- [Auditoría de seis datasets](../results/analysis/top4_fixed_kth_completion_audit_20261115_v1/summary.json).
- [Tablas nuevas y hashes](../results/analysis/thesis_six_dataset_integration_20261115_v1/tables_receipt.json).
- [Protocolo de latencia pendiente](../docs/fsc_tex/PROTOCOLO_LATENCIA_TOP4_DIRECTO_MARGEN_2026-11-15.md).

Accuracy media E1: 0,944449 directa y 0,944581 por margen; p exacto=0,5625, sin superioridad significativa ni equivalencia demostrada. La reducción de adquisición del 75,00 % es proyectada, no latencia física.

Pasaron **102 pruebas**. Se revisaron visualmente las 90 páginas y las tablas E1/E2 en detalle; cero referencias indefinidas, desbordes y caracteres de reemplazo. La versión anterior de 87 páginas y sus recibos conservan su alcance histórico. No hubo ajustes o llamadas neuronales nuevas al integrar el texto.

El título y el recorrido Top-k directo → optimización por margen se conservan. Continúan las reservas de procedencia, representaciones online y DeepLumina; el cierre KTH no las elimina. Los artículos y presentaciones anteriores mantienen su propia versión.

Compilación desde paper:

    ../.tools/tectonic-0.16.9/tectonic --keep-logs --keep-intermediates tesis.tex
