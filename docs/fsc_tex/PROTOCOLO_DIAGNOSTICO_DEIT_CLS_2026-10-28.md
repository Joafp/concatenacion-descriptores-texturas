# Diagnóstico autorizado de DeiT-small

## Material Passport

- Fecha: 28-10-2026; ARS, ejecución inline.
- Autorización: diagnosticar CLS, corregir solo si coincide y repetir preflight
  en carpeta nueva, sin modificar embeddings o resultados de calidad.
- Estado al guardar: previo a esta ejecución diagnóstica.

Usar las mismas dos filas y hashes del preflight fallido FMD/42/0, sin
selección nueva de imágenes. Mismo procesador de imágenes y checkpoint local
facebook/deit-small-patch16-224; desactivar la creación de pooling y tomar
last_hidden_state[:,0,:]. Exigir que no falten pesos del backbone ni existan
dimensiones de pesos incompatibles. El descarte de la cabeza clasificadora
del checkpoint es explícito; no se entrena ninguna capa.

Normalización L2 idéntica y tolerancia original: dimensión igual, valores finitos
y error absoluto máximo <= 1e-4 por vector. Guardar vectores, errores, loading
info, hashes y versiones. Usar GPU compartida solo para comprobar números,
con al menos 1 GiB libre; no publicar tiempos. Tiempo límite: cinco minutos.

Solo si ambas filas pasan, implementar un adaptador local explícito CLS sin
pooler, sin modificar el extractor que produjo los embeddings ni el adaptador
histórico usado en otros experimentos. Repetir el preflight de los 22 bloques
en un directorio nuevo, manteniendo sus filas y tolerancia originales. No
extrapolar dos imágenes a todos los datasets. Si aparece otro fallo, conservarlo
y no cambiar taps, checkpoints o tolerancias automáticamente.
