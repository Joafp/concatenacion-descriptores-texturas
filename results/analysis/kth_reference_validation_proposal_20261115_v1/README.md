# Propuesta congelada de validación KTH

**Preparada para decisión del autor; no ejecutada.** Cero llamadas neuronales.
No es una cola activa ni un resultado de fidelidad aceptado.

[Protocolo revisable](../../../docs/fsc_tex/PROTOCOLO_VALIDACION_KTH_CORREGIDA_2026-11-15.md) ·
[Diagnóstico previo](../../../docs/fsc_tex/REVISION_FIDELIDAD_KTH_2026-11-15.md) ·
[Manifiesto](proposal.json) · [SHA-256](proposal.sha256).

El manifiesto fija las mismas 33 imágenes y las huellas de sus entradas
candidatas por red, los checkpoints locales, el umbral 0,999, dos modelos,
66 llamadas evaluadas como máximo y diez calentamientos. Conserva los
estados fallidos originales y liga sus archivos por SHA-256.

La continuación propuesta separa dos condiciones KTH que no ajustaron
modelos de las 25 ya completadas. Verifica sus artefactos (incluidos los
clasificadores locales excluidos de Git), la independencia de los dos KTH
completos y las seis constantes de costo aceptadas que deben conservarse.
Solo una validación aceptada permitiría preparar ese cierre, en carpetas
nuevas y con una decisión explícita. No se genera una media KTH parcial.

El preparador no importa torch, no carga redes y no ejecuta experimentos:

```bash
python3 scripts/prepare_kth_reference_validation.py --output <directorio-nuevo>
```

El protocolo y el informe ya están ligados por sus hashes al manifiesto.
Cualquier cambio de receta exige una propuesta nueva; no se reescribe esta.

La verificación ampliada pasó **66 pruebas en 42,56 s**, sin inferencia.
[Registro y hashes](verification.json). El PDF de 87 páginas conserva su
SHA-256 anterior; no se modificó el manuscrito durante esta revisión.
