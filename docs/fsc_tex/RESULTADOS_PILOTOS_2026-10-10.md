# Resultados auditados de los pilotos P1–P4

**Fecha:** 2026-10-10. **Estado ARS:** ANALYZED. Fuente: JSON P1–P3 y P4 en `results/exploratory/fsc_tex/`; hashes y salvedades en [auditoría vigente](AUDITORIA_P0_P4_CASCADA_2026-10-10.md). No se reentrenó ni midió nuevamente. Las cifras siguientes son agregados guardados, no métricas recalculadas desde predicciones individuales (no persistidas).

## 1. Qué se ejecutó

Piloto P1–P3: DTD oficial1 (3753 filas de entrenamiento) y Soil fold0 (912). Biblioteca de seis: ResNet50, SigLIP, BEiTv2, DINOv2, ConvNeXt-v2-tiny y EVA02-base. P1 evalúa seis individuos y pares/oráculos para tres bases; P2 ejecuta H1/H2 con dos bases y presupuestos35/45/75 ms proyectados. No es una nueva evaluación externa de seis datasets.

En P1 el mejor individual es SigLIP en DTD (F1 0,830789; costo12,13 ms) y EVA en Soil (0,853590;19,77 ms). Los mejores pares desde SigLIP son +DINOv2 en DTD (0,844147;70,23 ms) y +BEiTv2 en Soil (0,873740;24,80 ms). Estos diagnósticos internos no justifican seleccionar por el test la base definitiva.

## 2. P2: macro-F1 y costo proyectado interno

| Dataset | Base | Presupuesto (ms) | H1 F1 | H1 costo | H2 F1 | H2 costo | H2 ≥2 adquisiciones (%) | Cascada F1 | Cascada costo |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DTD | ResNet | 35 | 0,819086 | 26,69 | 0,813133 | 32,16 | 0,00 | 0,806555 | 32,59 |
| DTD | ResNet | 45 | 0,831513 | 40,10 | 0,830839 | 41,47 | 93,31 | 0,820013 | 37,65 |
| DTD | ResNet | 75 | 0,830749 | 40,68 | 0,830839 | 41,48 | 93,34 | 0,820013 | 37,65 |
| DTD | SigLIP | 35 | 0,830789 | 12,18 | 0,831817 | 23,64 | 0,00 | 0,846593 | 26,22 |
| DTD | SigLIP | 45 | 0,831197 | 27,08 | 0,835123 | 31,08 | 12,60 | 0,846593 | 26,22 |
| DTD | SigLIP | 75 | 0,832203 | 27,51 | 0,838181 | 31,77 | 14,31 | 0,846593 | 26,22 |
| Soil | ResNet | 35 | 0,829141 | 27,52 | 0,832023 | 28,56 | 0,00 | 0,836212 | 17,18 |
| Soil | ResNet | 45 | 0,841634 | 33,71 | 0,837136 | 37,16 | 75,11 | 0,836212 | 17,18 |
| Soil | ResNet | 75 | 0,841571 | 34,29 | 0,836786 | 37,50 | 75,66 | 0,836212 | 17,18 |
| Soil | SigLIP | 35 | 0,843747 | 12,22 | 0,849124 | 24,62 | 0,00 | 0,868508 | 13,78 |
| Soil | SigLIP | 45 | 0,841440 | 29,09 | 0,849013 | 32,26 | 38,16 | 0,868508 | 13,78 |
| Soil | SigLIP | 75 | 0,844712 | 30,67 | 0,869940 | 34,23 | 44,41 | 0,868508 | 13,78 |

Las múltiples adquisiciones sí aparecen a 45/75: se resolvió la falta de factibilidad a35 del experimento v2. Su utilidad no es universal. DTD/SigLIP75: H2 pierde 0,008412 frente a la cascada, con mayor costo. Soil/SigLIP75: gana 0,001432, con costo 34,23 frente a 13,78. Se necesita fijar previamente el intercambio calidad–costo; no declarar dominancia de H2 por una mejora mínima de F1.

La cascada de esta tabla es base+un aumentador, no la nueva cascada que escala al Top-k archivado. Los F1 internos están afectados por reutilización de datos de sintonización; sirven para desarrollo, no como estimación confirmatoria anidada.

## 3. P3: comprobación de cordura, no validación integral

Permutación única: DTD F1 0,022324 frente a 1/47=0,021277; Soil 0,132443 frente a 1/7=0,142857. La política se evalúa sobre sus filas de ajuste; no es un test formal de permutación del pipeline. PCA16 se construye pero no se utiliza en la política evaluada. La puerta omite criterios y no debe tomarse como autorización científica para cerrar P5.

## 4. P4: medición física limitada

| Magnitud reportada | Valor |
| --- | ---: |
| GPU | NVIDIA RTX4060 |
| Muestra | 20 imágenes DTD, todas banded |
| Extracción media | 41,1044 ms |
| Compuerta media | 2,4585 ms |
| Clasificador medio | 1,4695 ms |
| Suma de componentes | 45,0323 ms |
| Fracción atribuida a compuerta | 5,4594% |
| Acuerdo de estado/ruta final | 18/20 (90%) |
| Acuerdo de predicción | 19/20 (95%) |
| VRAM residente / pico | 1974,4 /2025,6 MiB |

No es temporización envolvente completa ni medición comparativa frente a Top-k/Completa. No hay dispersión ni secuencias/tiempos individuales persistidos para reauditar. El PASS al 90% no cumple el umbral 95% del helper general. No trasladar este resultado a la cascada seleccionada ni a otros datasets.

## 5. Estado posterior

La nueva [cascada seleccionada en 27 condiciones](REPORTE_CASCADA_ADAPTATIVA_CANONICA_27.md) constituye una evaluación externa exploratoria separada. No mezclar sus costos proxy, resultados externos y controles con los F1 internos de esta tabla o con P4. La decisión siguiente es una validación acotada con procedencia, predicciones y tiempos pareados completos, no declarar ganador por comparación entre tablas de distinto protocolo.
