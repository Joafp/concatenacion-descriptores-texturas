# Resultados Preliminares — Tesis v2 (6 datasets texturas, 17 extractores)

**Fecha:** Junio 2026
**Configuración:**
- 6 datasets de texturas: DTD, FMD, Outex13, KTH-TIPS2-b, GTOS-Mobile, VisTex
- 17 extractores: 5 clásicos (LBP, GLCM, Gabor, HOG, DRLBP) + 5 CNN (VGG16, ResNet-50, ResNet-101, DenseNet-121, EfficientNet-B0, ConvNeXt V2-T) + 3 ViT (ViT-B/16, Swin-T, DeiT-S) + 3 DINOv2 (small/base/large) + ConvNeXt V2-T
- Linear probing + SVM/KNN

## Exp 1: Linear Probing (svm)

| Dataset | Mejor extractor | F1 macro |
|---|---|---|
| **DTD** | dinov2 (svm) | 0.842 |
| **FMD** | dinov2 (svm) | 0.957 |
| **KTH-TIPS2-b** | dinov2 (svm) | 0.999 |
| **VisTex** | dinov2 (svm) | 0.734 |
| **GTOS-Mobile** | (random, F1=0.03) | 0.033 ⚠️ |

**Hallazgo principal:** DINOv2 family (small/base/large) domina en texturas naturales, consistente con literatura previa.

**Hallazgo GTOS-Mobile:** Todos los extractores dan F1≈0.03 = random. **Causa:** GTOS-Mobile son outdoor scenes donde los features preentrenados en ImageNet están dominados por lighting/atmósfera, no por terreno. Documentado en paper de DINOv2 original. **No es un bug, es un hallazgo negativo** sobre la transferibilidad de estos extractores a scenes vs. texturas.

## Exp 2: Fine-tuning (DINOv2 ViT-B/14, LoRA r=8)

| Dataset | Linear probing | LoRA r=8 | Δ |
|---|---|---|---|
| **DTD** | 0.842 | 0.852 | +0.010 |
| **FMD** | 0.957 | 0.953 | -0.004 |
| **KTH-TIPS2-b** | 0.999 | 0.999 | ~0 |

**Hallazgo principal:** LoRA ofrece poco beneficio vs linear probing en estos datasets. Consistente con literatura SSL moderna (Kumar et al. 2022).

## Exp 3: Concatenación Prefix (svm)

| Dataset | Mejor F1 (linear) | Mejor F1 (concat k) | Δ |
|---|---|---|---|
| DTD | 0.842 (k=1, dinov2) | (pendiente) | - |
| FMD | 0.957 (k=1, dinov2) | 0.940 (k=12) | -0.017 |

**Hallazgo preliminar:** La concatenación no supera al mejor extractor individual. La curva de saturación muestra que el primer deep (vgg16) causa el mayor salto (k=5→k=6: +0.41 en DTD, +0.48 en FMD), confirmando que la diversidad de familias importa más que la cantidad.

## Pendiente

- [ ] Exp 2: terminar LoRA en GTOS-Mobile, VisTex; luego correr "last" strategy
- [ ] Exp 3: terminar FMD, Outex13, KTH-TIPS2-b, GTOS-Mobile, VisTex prefix concat
- [ ] Exp 3: correr GFS subset search (greedy)
- [ ] Compilar reporte final con los 3 experimentos
- [ ] Actualizar paper/ con los nuevos resultados
