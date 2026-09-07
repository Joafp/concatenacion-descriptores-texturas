# Auditoría bibliográfica

Fecha de cierre: 2026-08-04  
Alcance: 30 referencias citadas en el manuscrito, 22 registros con DOI y
9 registros con URL (un registro puede contener ambos identificadores).

## Resultado

- Las 30 claves del archivo bibliográfico aparecen en el manuscrito.
- No existen claves citadas sin entrada bibliográfica ni entradas sin citar.
- Los 22 DOI fueron contrastados con Crossref o con la página del editor.
- Las afirmaciones bibliográficas de mayor impacto se contrastaron con fuentes
  primarias, no solamente con metadatos de buscadores.
- Estado final: **PASS AFTER CORRECTION**.

## Correcciones materiales

| Registro | Problema detectado | Corrección aplicada |
|---|---|---|
| Ojala et al., LBP | DOI asociado a otro artículo | DOI corregido a `10.1109/TPAMI.2002.1017623` |
| Haralick, análisis de textura | Últimos dígitos incorrectos en el DOI | DOI corregido a `10.1109/TSMC.1979.4310073` |
| DRLBP | Año, sede y DOI no correspondían al trabajo citado | Sustituido por Mehta y Egiazarian, *Pattern Recognition Letters* (2016), DOI `10.1016/j.patrec.2015.11.019` |
| FMD | La entrada previa no identificaba el artículo fuente del dataset | Sustituida por Sharan et al., *International Journal of Computer Vision* (2013), DOI `10.1007/s11263-013-0609-0` |
| Fisher Vector | DOI incorrecto | DOI corregido a `10.1007/s11263-013-0636-x` |
| Revisión de clasificación de texturas | Título y autores no correspondían al DOI consignado | Sustituida por Liu et al., *From BoW to CNN* (2019), DOI `10.1007/s11263-018-1125-z` |

También se corrigió el nombre de Sammy Mohamed en la referencia de DTD y se
eliminaron ocho entradas que no eran citadas por el manuscrito. La depuración
no modifica resultados experimentales.

## Afirmaciones bibliográficas auditadas

| ID | Afirmación resumida | Fuente primaria consultada | Estado |
|---|---|---|---|
| C-041 | Aplicaciones y alcance de la clasificación de texturas | [Liu et al., IJCV](https://link.springer.com/article/10.1007/s11263-018-1125-z) | SUPPORTED |
| C-042 | Dependencia del dominio y de variaciones intraclase | [Cimpoi et al., DTD](https://openaccess.thecvf.com/content_cvpr_2014/html/Cimpoi_Describing_Textures_in_2014_CVPR_paper.html); [Liu et al., IJCV](https://link.springer.com/article/10.1007/s11263-018-1125-z) | SUPPORTED |
| C-043 | Mecanismos de LBP, GLCM y HOG | Artículos originales identificados por DOI en `references.bib` | SUPPORTED |
| C-044 | Sesgos y objetivos de arquitecturas profundas | Artículos originales de ResNet, EfficientNet, ViT, Swin, DINO y DINOv2 | SUPPORTED |
| C-045 | Agregación y codificación de características profundas | [FV-CNN](https://link.springer.com/article/10.1007/s11263-015-0872-3); [DeepTEN](https://openaccess.thecvf.com/content_cvpr_2017/html/Zhang_Deep_TEN_Texture_CVPR_2017_paper.html) | SUPPORTED |
| C-046 | Propiedades y riesgos de métodos wrapper | [Kohavi y John](https://www.sciencedirect.com/science/article/pii/S000437029700043X); [Guyon y Elisseeff](https://www.jmlr.org/papers/v3/guyon03a.html) | SUPPORTED |
| C-047 | Selección automatizada por grupos en AutoGFS | [Fan et al., SIAM](https://epubs.siam.org/doi/10.1137/1.9781611976700.39) | SUPPORTED |
| C-048 | Subconjuntos aceptables e inestabilidad por sobrebúsqueda | [Ruggieri et al., JMLR](https://jmlr.org/papers/v20/18-035.html) | SUPPORTED |
| C-049 | Distinción entre colección Outex y suites de evaluación | [Artículo original de Outex](https://citeseerx.ist.psu.edu/document?doi=4bf0ca857419da52bc82bcd6197675c42ed7a638&repid=rep1&type=pdf) | SUPPORTED |
| C-050 | Configuración publicada de CUReT | [Oxford VGG](https://www.robots.ox.ac.uk/~vgg/research/texclass/setup.html) | SUPPORTED |

## Límites de esta auditoría

La coincidencia bibliográfica y el soporte textual no demuestran por sí solos
que una afirmación generalice a todos los dominios. La auditoría confirma que
las fuentes existen, que sus metadatos son coherentes y que sostienen el alcance
con el que se las cita en esta versión del manuscrito.
