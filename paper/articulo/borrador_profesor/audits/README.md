# Auditoría académica del borrador

Esta carpeta contiene los artefactos de integridad que vinculan el manuscrito
con sus fuentes bibliográficas y experimentales. No forma parte del texto que
se compila para el artículo.

## Artefactos

- `claim_registry.csv`: registro de afirmaciones cuantitativas, factuales y
  metodológicas. Distingue evidencia bibliográfica de evidencia producida por
  los experimentos del proyecto.
- `material_passport.yaml`: procedencia de los experimentos y archivos que
  respaldan las afirmaciones del manuscrito.
- `result_traceability.md`: correspondencia legible entre los principales
  resultados del artículo y sus archivos fuente.
- `bibliography_audit.md`: verificación de identidad y adecuación de las
  referencias que sostienen las afirmaciones bibliográficas del manuscrito.
- `integrity_report_stage2_5.md`: informe de la verificación previa a la
  revisión metodológica.

## Regla de interpretación

La existencia de un archivo o de una referencia no demuestra por sí sola que
una afirmación sea correcta. Una afirmación experimental se considera alineada
solo cuando su valor puede reconstruirse desde el resultado señalado. Una
afirmación bibliográfica requiere además localizar en la fuente primaria el
pasaje que sostiene la redacción utilizada.

## Alcance

Estos documentos verifican divulgación y fidelidad entre afirmaciones y
procedencia. No sustituyen una evaluación humana del diseño científico, ni
garantizan que los resultados sean generalizables a otros datasets.
