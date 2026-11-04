# Enmienda operativa: reintento autorizado de Outex

## Material Passport

- Origin Skill: ARS experiment-agent, ejecución local guiada
- Origin Mode: run
- Origin Date: 2026-10-26
- Verification Status: PENDING — ejecución y auditoría nuevas pendientes
- Version Label: outex_timeout_retry_120min_v1

## Autorización y alcance

El autor respondió: «Sí, repetir solo Outex con ese límite», a la consulta sobre repetir únicamente las tres condiciones Outex en directorios nuevos, sin cambiar el método, con hasta 120 minutos por condición y sin repetir FMD. Este registro documenta esa autorización; no es una preinscripción científica ni una nueva elección de método.

La cola original `results/exploratory/integration_v12/matched_concat_20261026` se conserva íntegra. Sus tres condiciones Outex (semillas 42, 123 y 2026) terminaron por límite de 1.800 segundos, código −15, durante selección interna. No guardaron decisiones ni predicciones finales. No se interpreta el timeout como una derrota predictiva ni se recuperan scores parciales como resultados terminados.

## Únicos cambios operativos

- Límite por condición: de 1.800 a 7.200 segundos (120 minutos).
- Cola nueva limitada a Outex/42, Outex/123 y Outex/2026, en ese orden.
- Salidas nuevas: `results/exploratory/integration_v13/matched_concat_outex_retry_20261026`.
- Configuración nueva: `configs/fsc_tex/matched_concat_outex_retry_20261026.json`.

Se conservan dos condiciones simultáneas y dos hilos BLAS por condición. Los 120 minutos son un techo por condición, no una estimación de duración ni una garantía de finalización; la tercera condición espera un lugar en la cola. Se autoriza un reintento por condición, no una cadena automática de reintentos. El ejecutor conserva su vigilancia de proceso y límite temporal con terminación al alcanzarlo.

## Método preservado

El documento científico pasado al ejecutor sigue siendo `PROTOCOLO_GFS_TOPK_EMPAREJADO_2026-10-26.md`, SHA-256 `50a9b49f519b8d8e5ecde9f6b026ddea0660b33bc0bf5bb07343f0c6301c8814`. El congelamiento original tiene SHA-256 `cdbd4e566ec28d0481aa0459fae5f4882e295796b22c8a581587ed1b4855cc75`.

Antes del lanzamiento se comprobaron los 48 archivos enlazados por ese congelamiento, incluidos ejecutor, selectores, dependencias y referencias. No se modifican las fuentes científicas. Cada condición conserva semilla, referencia, 680 imágenes de desarrollo, índices productores e internos, 22 bloques, SVM, transformaciones de N-gramas y perfil de costos. No se usa el test externo. No se extraen imágenes ni se entrenan extractores GPU.

Se mantienen GFS libre hasta ocho bloques, parada tras dos mejoras inferiores a 0,001, devolución del mejor paso y desempate original; Top-k hereda k del GFS libre. GFS presupuestado y prefijo factible se seleccionan por separado para B15/B30/B60/B120. Se conservan las diez políticas, tres pliegues productores y tres internos, incluidas las políticas inviables. No se cambian las reglas para acelerar la selección ni se seleccionan semillas por desempeño.

## Trazabilidad y siguiente puerta

El recibo `results/analysis/matched_concat_outex_retry_20261026/authorization.json` guarda hashes, comparación de configuraciones, autorización y estados previos. La nueva cola guarda su propio `frozen_protocol.json`, logs y estados. FMD no se repite y sus resultados siguen procediendo de la cola original.

Al completar una condición, auditar por separado:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONPATH=.:src \
  .venv-confirmatory/bin/python scripts/audit_matched_concat_controls.py \
  --suite results/exploratory/integration_v13/matched_concat_outex_retry_20261026 \
  --output results/analysis/matched_concat_outex_retry_20261026/audit
```

Solo después de esa auditoría se integrarán las condiciones recuperadas con FMD, manteniendo visibles los intentos originales y su procedencia. Hasta entonces el panel científico sigue incompleto. Los costos de adquisición siguen siendo proyecciones del perfil fijo, no cronometrajes de inferencia. Este reintento no modifica el PDF ni añade inferencia estadística.
