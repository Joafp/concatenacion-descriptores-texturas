# Revisión ARS: tesis de 90 páginas

[Informe legible](../../../docs/fsc_tex/REVISION_ARS_TESIS_2026-11-15.md) ·
[Síntesis editorial](reports/editorial_synthesis.md) ·
[Roadmap](revision_roadmap.json) · [Integridad](validation_receipt.json).

Se revisó el commit `1fdf0a8` y el PDF ligado en `inputs/input_manifest.json`.
No hubo cambios al manuscrito, fits, extracciones o benchmarks. Las copias
en `inputs` son datos de revisión; cualquier instrucción dentro del texto es
material no confiable y no modifica el encargo.

| Asiento | Compromiso previo a leer | Informe |
|---|---|---|
| EIC: aporte y escritura | [Phase1](reports/eic_phase1.md) | [Phase2](reports/eic_phase2.md) |
| R1: metodología | [Phase1](reports/methodology_phase1.md) | [Phase2](reports/methodology_phase2.md) |
| R2: dominio | [Phase1](reports/domain_phase1.md) | [Phase2](reports/domain_phase2.md) |
| R3: perspectiva aplicada | [Phase1](reports/perspective_phase1.md) | [Phase2](reports/perspective_phase2.md) |
| DA: objeción adversarial | [Phase1](reports/da_phase1.md) | [Phase2](reports/da_phase2.md) |

Las cinco Phase1 se produjeron sin contenido de tesis; cada Phase2 conserva
su compromiso y no consultó otras tarjetas. La síntesis leyó las cinco
después y no añadió hallazgos. La [procedencia tipada](panel_provenance.json)
fue construida y validada con el helper ARS. La separación de roles/contextos
no acredita independencia de errores; familia/proveedor permanecen desconocidos.
`NOT_CALIBRATED`; `criteria_binding_unavailable`; sin aprobación institucional.

Todas las observaciones son Minor. La decisión mecánica Major Revision
proviene de F3 (varias dimensiones obligatorias con warn), sin elevarlas a
Major ni inventar una falla invalidante. El núcleo del roadmap conserva 15
acciones atómicas en orden de fuente; la síntesis preserva también las 15
observaciones originales, sus duplicados y descomposiciones.

`inputs/review_working_draft.md` es una copia ensamblada y anclada para
localizar propuestas; no es la tesis compilable ni autorización de edición.
`revision_roadmap_initial_transport.json` conserva el candidato anterior a
corregir un binding de bloque del pie de latencias; `revision_roadmap.json`
es el canónico validado. No se alteraron juicios de revisores al corregirlo.
No hay `author-adjudication` inferida ni cambios aplicados.

El primer preflight PDF fue UNAVAILABLE por una dependencia ausente. El
preflight POSIX con pypdf puro del runtime bundled dio PASS para las 90
páginas y el mismo hash; ambos recibos se conservan. PASS estructural no
certifica verdad de las afirmaciones ni sustituye lectura y juicio.

El replay de [aritmética descriptiva](numeric_replay.json) usa medias ya
guardadas; no genera predicciones o tiempos nuevos. No sustituye los recibos
estadísticos `not_computable` del revisor ni hace una validación independiente
desde RGB.
