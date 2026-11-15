# Preparación de E1 y E2

Se verificaron 27 condiciones de seis datasets, cuatro bloques por condición, etiquetas, formas NPY, particiones externas/internas y costos disponibles. KTH agrupa por muestra física. Entradas identificadas con SHA-256.

**Perfil de costos incompleto en 4 condiciones.** Los bloques faltantes figuran en `summary.json`; no se sustituyeron con otro dataset.

**No se ejecutó E1 ni E2.** Falta implementar y probar el ejecutor Top-4 fijo; el script histórico usa la selección de tamaño variable y no guarda todos los scores. Esta carpeta contiene una receta candidata e inputs preparados, no resultados nuevos ni un worker listo para lanzar. Los costos siguen siendo proyecciones históricas.

- `conditions.json`: bloques e índices de cada condición.
- `recipe.json`: controles y salidas requeridas.
- `provenance.json`: hashes y versiones del entorno.
- `summary.json`: cobertura de esta preparación.
