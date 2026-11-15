# Propuesta: validación de la receta corregida EVA-02/SigLIP en KTH

Fecha: 15-11-2026. **Estado: propuesta preparada, no ejecutada.**

## Pregunta y cambio único de receta

Determinar si el preprocesamiento y la salida del código histórico recuperan
la fidelidad frente a los embeddings KTH guardados. Se abandona la ruta
manual incompatible para estas dos redes; no se cambian checkpoints,
imágenes, etiquetas, capas de referencia ni el mínimo de aceptación para
forzar un resultado. La comparación usa datos ya observados y es exploratoria.

La [revisión](REVISION_FIDELIDAD_KTH_2026-11-15.md) demuestra la diferencia
de entradas; no contiene una validación neuronal de la corrección.

## Entradas y receta que se deben congelar antes de ejecutar

- Las mismas 33 imágenes de entrenamiento del primer perfil KTH: tres por
  cada una de 11 clases, con los mismos índices y SHA-256. No seleccionar
  otro subconjunto tras observar los cosenos.
- Los mismos NPY de referencia y sus hashes, preservando su orden y clases.
- EVA: `eva02_base_patch14_224.mim_in22k`, revisión
  `0ecfe3fab2be96198054b55157bd448097ba1828`; pesos SHA-256
  `a8f6984e7baf3d935b3c0d834e3fe1df5ebfe1d91f2e034041d1e0bf0afbed7b`.
  Transformación de evaluación `timm` con input RGB 224, crop_pct 0,9,
  bicúbico, resize corto 248 y crop central 224; salida `model(batch)`.
- SigLIP: `google/siglip-base-patch16-224`, revisión
  `7fd15f0689c79d79e38b1c2e2e2370a7bf2761ed`; pesos SHA-256
  `2c63cb7d1f2e95ba501893cbb8faeb4ea9a3af295498d35097126228659c2af8`.
  `SiglipVisionModel`, resize bilineal explícito 224×224, ToTensor,
  normalización RGB media/std 0,5 y salida `pooler_output`, conforme al
  código histórico. Cualquier clave de visión no cargada se registra y bloquea
  la validación; no se acepta una capa de visión inicializada aleatoriamente.
- Versiones completas de torch, torchvision, timm, transformers, Pillow y
  numpy, junto con código, configuración, GPU y driver. No descargar pesos.
- Exactamente dos modelos, batch1, semilla 42, CPU dos hilos y lock global.
  Un modelo residente por vez, sin fits ni extracciones concurrentes.

## Presupuesto y aceptación

Cinco calentamientos y 33 llamadas por bloque: como máximo 66 llamadas
evaluadas y diez de calentamiento. No se añade una búsqueda de opciones
de resize, capas, tolerancias ni semillas.

Antes de un forward se comprueba que el tensor de entrada coincida con la
huella de la receta candidata registrada en la auditoría CPU. Después se
comprueban forma, valores finitos y coseno frente al NPY de la misma imagen.

**Aceptación:** cada una de las 33 imágenes de cada bloque debe alcanzar
coseno >=0,999. Un mínimo inferior, una forma incompatible o un valor no
finito deja el bloque en `requires_review` con evidencia y detiene la nueva
validación; no hay retry ni exclusión de imágenes.

Si se registran tiempos de esas mismas llamadas, siguen siendo un perfil de
adquisición por componente con carga de modelos excluida. Solo los costos
de un bloque aceptado pueden utilizarse. No se combinan sus tiempos con F1
histórico para atribuir una latencia online nueva a la política completa.

## Salidas y conservación

Carpeta nueva con protocolo, versiones, hashes de entradas y pesos, coseno,
tiempo y errores por imagen, huellas de las salidas y estado final. Los
perfiles originales fallidos, sus fuentes selladas y el E1/E2 previo no se
reescriben ni se promueven a completos.

## Continuación E1 solo si pasa esta validación

Preparar una carpeta nueva para las particiones KTH 1 y 3 que no llegaron a
ajustar sus clasificadores. Mantener biblioteca, cuatro bloques, semilla,
particiones, agrupación física, criterio OOF y clasificadores del E1 previo.
Reutilizar las 25 condiciones completadas con sus hashes, sin nuevos ajustes.

Si se completa el perfil por componentes, conservar exactamente las seis
constantes ya aceptadas y añadir solo las dos nuevas verificadas. Documentar
que sus mediciones proceden de sesiones distintas; sigue siendo un perfil
analítico, no un cronometraje homogéneo de las políticas. Las dos condiciones
KTH ya completadas no usan los dos bloques modificados ni esas constantes.
Verificar esa independencia antes de reutilizarlas y no reseleccionar sus rutas.

Una futura media KTH completa requiere las cuatro condiciones y su auditoría;
una media de seis datasets requiere cobertura íntegra de todos ellos. La
autorización de esta propuesta y su huella deben registrarse antes de medir.
