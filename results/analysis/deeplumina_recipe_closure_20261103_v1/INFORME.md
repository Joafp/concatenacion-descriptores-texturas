# Cierre de receta DeepLumina / FMD — avance

Fecha: 2026-11-03. Estado: **preflight de receta concluido; adaptación
especificada, medición no iniciada**.

## Hallazgos accionables

- La fuente primaria describe RGB + luminancia Y de YIQ → ResNet101 preentrenada
  → rasgos `fc1000` concatenados → SVM/ECOC con sparse-random. Reporta para FMD
  accuracy 90,15 % ± 1,2. No proporciona semilla/índices del split ni una
  implementación enlazada que permita atribuirle ese resultado de forma
  independiente. [Artículo (DOI)](https://doi.org/10.1155/2022/9510987).
- Hay datos FMD locales: ZIP original 56 MB, SHA256
  `254475ddb37bf0fe1383ff9ea61eb71042db33af1f9a9aa8747391a72135b8f8`, con
  1000 imágenes y 1000 máscaras; el manifiesto por imagen tiene 1000 filas y
  SHA256 `43f5d02a493763bff351e842d0ec29ac4fdcc9facccfa1364a028ed81d793984`.
- Hay pesos ImageNet ResNet101 timm disponibles offline, revision
  `d90ce63ac1b05b22614f11dcea68fcedfc2c4dee`, SHA256
  `1ba5b660e7c175b3c27c557fc7dc8b2815be830c516815b0155f61b403f27380`. No se
  identificó como el checkpoint exacto del MATLAB usado por los autores.
- El embedding FMD local existente tiene dimensión GAP 2048; no es `fc1000` y
  no incluye la rama de luminancia. Queda excluido para evitar etiquetarlo como
  DeepLumina.
- Se congeló una **adaptación** con 15 condiciones comunes del panel (3 seeds ×
  5 folds; 800/200 por condición), ResNet101 timm `fc` 1000+1000, YIQ-Y explícito,
  y un ECOC sparse-random con solver/hiperparámetros/seed fijados. Receta,
  particiones fuente, versiones y contrato temporal en
  [PROTOCOLO_DEEPLUMINA_ADAPTACION_FMD_2026-11-03.md](../../../docs/fsc_tex/PROTOCOLO_DEEPLUMINA_ADAPTACION_FMD_2026-11-03.md).

## No ejecutado

No se extrajeron nuevos rasgos, no se ajustaron clasificadores y no se midió F1,
accuracy o latencia. No hay benchmark activo al momento de la inspección, pero
la medición sigue bloqueada hasta completar runner, generar y verificar los
índices exactos desde los registros comunes, congelar el manifiesto de corrida
y comprobar recursos/lock en el momento del despacho. No
se repitieron métodos locales ni se tocaron artefactos sellados.

La auditoría de datos de solo lectura sí comprobó 1000 registros/clases,
100 imágenes por cada una de las 10 clases, existencia y SHA256 válido de cada
JPG. También se comprobaron los 15 folds comunes: 200 IDs de prueba únicos por
fold, 20 por clase, sin solapamiento entre los cinco folds de cada semilla, y
cobertura de las 1000 filas por semilla. Los arrays exactos aún deben escribirse
en el manifiesto congelado de la cola nueva antes de medir.

### Preparación de implementación (03-11-2026)

Se añadieron primitives CPU en `src/deeplumina_adaptation.py` para YIQ-Y,
concatenación ordenada de dos vectores `fc1000`, selección reproducible de
ECOC sparse-random y fit/decode hinge explícitos. Las pruebas sintéticas
`tests/test_deeplumina_adaptation.py` pasan **4/4** con el entorno confirmatorio.
Una primera versión de la prueba del empate usó vectores cero pero los
clasificadores conservan intercepto; se corrigió el test usando márgenes cero
inyectados y la suite pasó. Esto solo valida contrato/sintaxis; no constituye
prueba de paridad científica ni habilita por sí sola una corrida. Próximo paso:
runner de extracción estrictamente offline más preflight que materialice IDs y
hashes en un directorio nuevo, verificando antes la compatibilidad del
checkpoint. Seguir sin hacer inferencia/fits hasta que el manifiesto esté
congelado y pase auditoría.

## Criterio de reporte

Los 90,15 % ± 1,2 del paper son **accuracy publicada**, no nuestro macro-F1; la
partición y semilla exactas no constan en la fuente. El resultado futuro se
llamará adaptación y no se describirá como “mismos números” o reproducción fiel
aunque el valor puntual se acerque. La comparación externa/local usará los
mismos row IDs; cada macro-F1 y cada latencia provendrán de las mismas llamadas
de su respectivo método. Latencias de distintas fechas/entornos se mostrarán con
esa reserva, no como comparación temporal controlada.
