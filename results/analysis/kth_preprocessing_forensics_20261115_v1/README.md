# Auditoría de preprocesamiento KTH, sin inferencia

Se demuestra que la receta histórica reconstruida y la ruta online que falló
producen entradas distintas en las mismas 33 imágenes de entrenamiento para
EVA-02 y SigLIP. No se prueba todavía la recuperación de fidelidad neuronal.

- [Informe y límites](../../../docs/fsc_tex/REVISION_FIDELIDAD_KTH_2026-11-15.md).
- [Resumen](summary.json): cero modelos, embeddings, predicciones o cronometrajes nuevos.
- [Píxeles por imagen](pixel_preprocessing_pairs.csv): 66 comparaciones reales y cuatro sintéticas.
- [Configuraciones](pipeline_configuration.json) y [huellas](provenance.json).
- [Propuesta de validación, no ejecutada](../kth_reference_validation_proposal_20261115_v1/README.md).

Reproducir esta auditoría de CPU en una carpeta nueva:

```bash
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
.venv-confirmatory/bin/python scripts/audit_kth_preprocessing_forensics.py --output <directorio-nuevo>
```

El criterio neuronal de coseno 0,999 y los fallos originales se conservan.
Las diferencias de píxeles no son accuracy ni cosenos de embeddings.
