# Outex: trazabilidad de embeddings y entrenamiento — 9 de noviembre

Revisión de solo lectura de los recibos de entrenamiento, decisiones y matrices.
No se reentrenó, extrajo, infirió ni alteró ningún resultado observado.

## Hallazgo: el panel usa una enmienda en DeiT-S

Los dos recibos `quality/status.json` incluyen 1034 y 1302 en
`training_indices`. Sus configuraciones señalan `representation_amendment`:
se regeneró exclusivamente `deit_s` y se reajustaron las cabezas y los OOF
solo con entrenamiento. La ruta del panel es `results/analysis/`
`blocker_resolution_20261101/queue_v1/embeddings/Outex13Official1360`.
El script de diagnóstico de Carlos lee los archivos históricos de
`embeddings_extensions/Outex13Official1360`.

El verificador [audit_outex_embedding_identity_20261109.py](../../scripts/audit_outex_embedding_identity_20261109.py)
reproduce el hash del recibo: array float32 normalizado L2 por fila, con dtype
y forma en el resumen. No compara el SHA-256 del archivo `.npy` con el de un
array, porque son objetos diferentes. Resultado para ambos recibos SVM y ResMLP:

| Bloque | Histórico de Carlos coincide con recibo | Enmendado de panel coincide con recibo |
|---|---|---|
| ViT-B/16 | Sí: `80da278c...1a68663` | Sí: `80da278c...1a68663` |
| DeiT-S | No: histórico `a55a3b03...1f23634` | Sí: `b1f82403...f0d5ef` |

Los hashes completos están en la salida del script y en los recibos. La
coincidencia se refiere al array normalizado registrado, no demuestra identidad
de los archivos originales byte por byte ni verifica la hipótesis de Carlos.
La alerta del DeiT histórico **no se puede trasladar automáticamente** al
DeiT enmendado del panel; sí hay correspondencia del ViT normalizado con el
recibo, pero falta verificar independientemente las filas y su origen.

## Dependencia en modelos congelados

Las recetas congeladas indican que `Completa-22` incluye ambos bloques en SVM
y ResMLP; `Ens-diversidad` SVM incluye ViT en 1 de 15 miembros y no incluye
DeiT. En ResMLP ese ensamble no incluye ninguno. Top-4, tómbola y los miembros
finales de la política adaptativa no los incluyen. La biblioteca de búsqueda
adaptativa sí lista ambos bloques; por lo tanto, excluirlos de la receta final
no prueba que no influyeran en la selección. La sola pertenencia a train y a
una receta identifica exposición potencial, no cuantifica efecto causal.

La revisión previa de 30 llamadas de tres filas test acertadas se mantiene,
pero no permite inferir que la totalidad del panel sea inmune a las dos filas
train ni que la alerta inicial esté confirmada.

## Fuentes

- Configuración SVM: `results/analysis/blocker_resolution_20261101/queue_v1/configs/Outex13Official1360_svm_s42_f0.json`.
- Recibo SVM: `.../jobs/Outex13Official1360_svm_s42_f0/quality/status.json`, SHA-256 `0f958e12211d6390e945f3741404aa2cc8add097179c5f3d688db5e2460fed67`.
- Recibo ResMLP: `.../jobs/Outex13Official1360_resmlp_s42_f0/quality/status.json`, SHA-256 `d8d2069ea5074de0dbcdb79735df2057cf73fb693a52f8fe5d5f995215174cc3`.
- Decisiones SVM SHA-256 `963552537a99e4b4140b872dfab84e7e9aff4ccc3636acd4ee4a84ea2570a682`; ResMLP `4f803c3812c0a9483b05bd31fac714f993bea7de7597e6e73d182f60359709be`.
- `src/run_confirmatory_nested.py` SHA-256 `8cf4778e873c7ae5a8a9e8c05e87fed55c2db2a3789624eab83504399e4f36c3`, coincide con el recibo.

## Próximo paso

Verificar independientemente las cinco filas de ViT y los detalles de la
regeneración DeiT mediante evidencia existente. Si se necesita una evaluación
contrafactual, diseñar y congelar previamente un protocolo y salidas nuevas;
no sustituir el panel ni repetir fallos científicos automáticamente.
