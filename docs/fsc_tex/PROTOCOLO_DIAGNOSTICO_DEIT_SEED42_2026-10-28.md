# Reconstrucción autorizada del estado original de DeiT

## Material Passport

- Fecha: 28-10-2026. Tipo: protocolo numérico, ARS inline.
- Autoridad: el usuario aprobó comprobar el estado original con semilla 42;
  integrar únicamente si coincide con el archivo, sin cambiar la representación.
- Estado: previo al diagnóstico.

Usar las mismas dos imágenes del preflight fallido FMD/42/0, con hashes intactos.
Comprobar que la metadata original declara semilla 42 y que su hash de embedding
coincide con el archivo actual. Reutilizar `load_legacy_extractors`, llamar a
`set_seed(42)` antes de `get_extractor("deit_s", device="cuda")`, exactamente
como la reextracción original. No cambiar procesador, tap o checkpoint.

Evaluar de una en una las imágenes y normalizar L2 como en el archivo leído.
Exigir dimensión igual, finitud y error absoluto máximo <= 1e-4 en ambas.
Guardar el estado del pooler reconstruido para que el adaptador posterior no
dependa del orden de carga de otros modelos. Ese pooler no se describirá como
preentrenado: reproduce una inicialización de la receta histórica.

GPU compartida solo para comparación numérica, al menos 1 GiB libre, máximo
cinco minutos. No medir latencias ni regenerar embeddings/cabezas. Si pasa,
usar un adaptador local nuevo que cargue/verifique ese estado recuperado,
preservando el adaptador histórico, y repetir preflight en carpeta nueva.
Si no pasa, no integrar la corrección ni cambiar tolerancias automáticamente.
