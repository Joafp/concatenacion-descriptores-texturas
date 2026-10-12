# Transición a escritura y cierre experimental condicionado

**Fecha:** 11 de octubre de 2026  
**Proyecto:** FSC-Tex (*Fusión Secuencial Costo-consciente para Texturas*)  
**Autores:** Carlos Ayala, Joaquín Delgado  
**Tutor:** Prof. José Vázquez (FP-UNA)  
**Estado:** **ESCRITURA PARCIAL HABILITADA; CIERRE METODOLÓGICO PENDIENTE**. Reconciliado con el [plan v1.5](../PROPUESTA_TESIS_FUSION_SECUENCIAL_COSTO_RIESGO.md), corte de código `e0d3564`. El nombre de archivo se conserva para mantener referencias; no constituye certificación de cierre, equivalencia u originalidad.

---

## 1. Resumen de la decisión y su alcance

Se dispone de 27 condiciones archivadas, 31.984 observaciones de test acumuladas entre particiones y un benchmark físico pareado sobre 47 imágenes DTD en NVIDIA RTX 4060. La revisión recalculó 81 macro-F1 de tres métodos desde sus vectores sin discrepancias con los resultados guardados. Estos avances permiten redactar método, resultados y limitaciones, **pero no cierran los pendientes de procedencia KTH, anidamiento, paridad y generalización física**.

Se prioriza como candidata la **Cascada Adaptativa Costo-Consciente con Selección de Etapa Económica en Entrenamiento ($T_{\text{train}}$)**. Su utilidad local no certifica una contribución inédita ni una ventaja universal. La hipótesis multietapa H2 se conserva como experimento de contraste, no como requisito de éxito para esta cascada.

---

## 2. Evidencia Experimental Acumulada

### 2.1. Rendimiento Canónico Multidataset (27 Condiciones)

* **Rendimiento descriptivo, no equivalencia:** Macro-F1 medio de **0,9345** frente a **0,9341** del Top-$k$ de origen, **0,9409** de Completa-22 y **0,9353** de GFS-22, con igual peso por dataset. KTH combina referencias de distinta procedencia y se mantiene descriptivo separado de la inferencia reconciliada.
* **Costo proyectado:** reducción analítica de 75,5% frente a Top-$k$; no es una medición física multidataset ni debe confundirse con la parada temprana del piloto físico.
* **Selección económica en entrenamiento, no certificación integral de ausencia de fuga:**
  * `siglip_base`: seleccionado 20 veces.
  * `beitv2_base_final`: seleccionado 5 veces.
  * `resnet50`: seleccionado 1 vez.
  * `topk_direct`: seleccionado 1 vez.
* **Inferencia estadística exploratoria (5 datasets reconciliados; KTH excluido por procedencia):**
  * Friedman: $p = 0,4518$; Iman–Davenport: $F = 0,8515, p = 0,4922$.
  * Rango medio de la cascada: **2,200**, igual al de Completa-22; Top-$k$ de origen 2,300 y cascada ResNet 3,300. El orden descriptivo de rangos no prueba superioridad.
  * Los tres contrastes bilaterales Wilcoxon con Holm no rechazan ($p_{\text{Holm}}=1$). **No rechazo no demuestra igualdad ni no inferioridad.** La diferencia media es −0,000397 frente a Top-$k$ y −0,004567 frente a Completa-22. No se tratan 27 particiones solapadas como 27 datasets independientes.

La etapa económica y su umbral usan predicciones OOF de entrenamiento; el subconjunto Top-$k$ se hereda de selecciones anteriores y no se rehace en cada fold productor. Los benchmarks ya fueron observados durante el desarrollo. Véase el [reporte descriptivo y estadístico](REPORTE_CASCADA_ADAPTATIVA_CANONICA_27.md); su conclusión final sobre falta de predicciones y ausencia de benchmark de cascada quedó desactualizada por los commits posteriores y debe sincronizarse antes de importarla al manuscrito.

### 2.2. Validación Física en GPU Real (NVIDIA RTX 4060)

* **Muestra y alcance:** DTD official1, una imagen por cada una de 47 clases, modelos residentes, imagen RGB ya decodificada $\to$ predicción con `torch.cuda.synchronize()`. No incluye lectura/decodificación del archivo ni carga inicial de modelos.
* **Latencia Media Wall-Clock:** **88,75 ms** para la Cascada Adaptativa frente a **283,33 ms** de la concatenación Top-$k$ directa (**68,7% de reducción física real de latencia**).
* **Aceleración agregada:** **3,19×**, calculada como cociente de tiempos totales. **15,98×** es la media de cocientes por imagen y **20,60×** su mediana; no son la aceleración agregada del lote.
* **Exactitud y concordancia locales:** ambos métodos aciertan 41/47 (87,2%) y producen las mismas predicciones físicas en 47/47. No prueba equivalencia fuera de esta muestra. La cascada evita escalar en 34/47 imágenes (72,3%).
* **Paridad con caché:** 45/47 rutas (95,74%) y 46/47 predicciones (97,87%) para cada método. Cumple el umbral piloto ≥95%, sin identidad exacta. Investigar rutas de índices 1261 y 2016 y predicción de 4551.
* **Límites del diseño:** una pareja por imagen y orden fijo cascada→Top-$k$, sin repeticiones aleatorizadas. No mide Completa/GFS/ResNet ni otros datasets; no extrapolar el 68,7% a toda la tesis.

Fuente: [mediciones por imagen](../../results/exploratory/fsc_tex/cascade_physical_paired_benchmark.json) y [ejecutor](../../scripts/benchmark_cascade_physical_pareado.py). Las afirmaciones más amplias del reporte físico anterior requieren corrección, no una reinterpretación de sus datos.

### 2.3. Auditoría de Reproducibilidad (A7)

* 27 archivos `{dataset}_{protocol}_predictions.json` persistidos.
* 31.984 observaciones acumuladas de test, con etiquetas, índices, predicciones y decisiones de escalado de tres métodos; no necesariamente 31.984 imágenes únicas entre particiones.
* Recálculo de 81 macro-F1 sin discrepancias. El generador reconstruye los vectores reajustando modelos desde caché con selecciones guardadas; no equivale a recuperar los checkpoints originales.
* El conteo anterior de «57 tests» no se toma como certificado: falta adjuntar comando, commit, entorno y salida verificable. La comprobación de métricas no reemplaza los tests de aislamiento o de selección anidada.

Fuentes: [vectores por condición](../../results/exploratory/topk_cascade/cheap_stage_selected_primary22/) y [generador](../../scripts/generate_cascade_predictions.py). Completar manifiestos y hashes según P1a del plan.

---

## 3. Investigación de Literatura y Estado del Arte (2024–2026)

La versión anterior de este documento formulaba diagnósticos universales sobre estos antecedentes. **No se ratifican esas afirmaciones en esta actualización local.** La revisión dirigida del plan aporta un punto de partida, no una búsqueda exhaustiva que pruebe originalidad. Pendientes concretos:

1. **Clasificación de Texturas (*Texture Classification*, 2024–2026):**
   * Trabajos representativos: *HyTexNet* (Knowledge-Based Systems 2026), *AsTexNet* (Applied Sciences 2026), *DeepLumina* (2022), fusiones multiescala LBP/CellNN (2024).
   * **Por verificar artículo por artículo:** qué bloques se extraen, si hay selección por muestra y cómo se mide costo. No afirmar que todos los trabajos de textura son estáticos o extraen siempre el 100% de sus bloques sin evidencia específica.
2. **Adquisición Activa de Características (*Active Feature Acquisition - AFA*, 2025–2026):**
   * Trabajos de frontera: *BRiG-AFA* (Bellman Risk-to-Go, agosto 2026), *SynAFA* (Partial Information Decomposition, septiembre 2026), *EDDI* (ICML).
   * **Por verificar:** dominio, unidad de adquisición, costos, regla de parada y evaluación física de cada antecedente. Las limitaciones de un paper concreto no demuestran que ningún trabajo haya tratado bloques heterogéneos o latencia GPU.
3. **Inferencia Dinámica y Salida Temprana (*Early-Exit Networks*):**
   * *BranchyNet*, *BlockDrop*, *Early-Exit Vision Transformers*.
   * **Por verificar:** distinguir salida temprana, omisión de bloques y selección entre modelos; comparar con el mecanismo realmente implementado, sin atribuir a todos los trabajos una arquitectura idéntica.

**Estado de novedad:** aporte candidato pendiente de contraste específico con fuentes primarias y métodos cercanos. No afirmar «no publicado previamente», ni usar una medición GPU como prueba suficiente de novedad algorítmica. El plan conserva antecedentes, solapamientos y criterios de comparación; no se realizó una nueva búsqueda bibliográfica en esta actualización.

---

## 4. Registro narrativo ROCF en DTD — no verificado

La versión previa narraba un piloto sobre DTD official10 (1.880 imágenes, 47 clases). En esta revisión no se localizaron artefactos específicos suficientes para verificar ROCF y sus variantes: código, configuración, log, particiones y predicciones. Se conserva el registro siguiente para reconciliarlo, **no como evidencia validada ni como autorización para incorporarlo a la tesis**.

* **Hipótesis descritas en el registro previo, ejecución por verificar:**
  1. *Fusión Residual Ortogonal (ROCF):* Proyectar los descriptores costosos sobre el complemento ortogonal del subespacio de SigLIP vía regresión Ridge para eliminar redundancia y colinealidad.
  2. *Stacking de Funciones de Decisión:* Pasar las puntuaciones de margen de la Etapa 1 como prior al clasificador de la Etapa 2.
  3. *Ponderación por Incertidumbre:* Entrenar la Etapa 2 dando mayor peso a las muestras con menor margen en la Etapa 1.
  4. *Interacción Bilineal de Segundo Orden:* Producto tensorial exterior compacto ($24 \times 24 = 576$ dimensiones) normalizado con raíz con signo y norma L2 para modelar correlaciones cruzadas de textura.

* **Cifras narradas pendientes de trazabilidad:** los valores de Top-$k$ y cascada official10 coinciden con el reporte canónico; eso no valida las otras filas. Las latencias no deben transferirse del piloto físico official1 a official10 y no sustentan comparaciones ROCF.

| Estrategia Evaluada | Macro-F1 Test | Exactitud (Acc) | Tasa de Escalado | Latencia Estimada |
| :--- | :---: | :---: | :---: | :---: |
| 1. Modelo Individual Solo (`siglip_base`) | 0,8367 | 84,04% | 0,0% | ~11 ms |
| 2. Concatenación Top-$k$ Directa | 0,8604 | 86,22% | 100,0% | ~283 ms |
| **3. Cascada Adaptativa Actual (Candidata)** | **0,8650** | **86,70%** | **24,5%** | **~88 ms** |
| 4. Fusión Ortogonal ($\gamma = 0,8$) | 0,8644 | 86,70% | 24,5% | ~90 ms |
| 5. Stacking de Funciones de Decisión | 0,8637 | 86,60% | 24,5% | ~90 ms |
| 6. Ponderación por Incertidumbre | 0,8523 | 85,48% | 24,5% | ~90 ms |
| 7. Interacción Bilineal Compacta (2º Orden) | 0,8650 | 86,76% | 24,5% | ~92 ms |

* **Interpretación permitida:** en official10, la diferencia descriptiva registrada cascada–Top-$k$ es +0,004529 de macro-F1 (aproximadamente +0,453 puntos porcentuales), no evidencia de superioridad global. No demuestra que la causa sea evitar ruido dimensional. Sin artefactos ROCF y una comparación validada, no concluir optimalidad de la regularización, insignificancia estadística de variantes ni un costo adicional medido. Si los artefactos no se recuperan, estas filas quedan fuera del manuscrito.

---

## 5. Próximos pasos para un cierre defendible

1. **Preservar artefactos:** no sobrescribir resultados, repetir corridas terminadas ni abrir nuevas arquitecturas por defecto. Registrar versiones y diferencias de protocolo.
2. **Resolver procedencia y validación:** P0a–P3a del plan cubren Top-$k$ KTH, manifiestos, ROCF, anidamiento y puerta histórica H2. Documentar lo pendiente sin presentarlo como cerrado.
3. **Delimitar eficiencia:** P4a investiga discrepancias cache/online y define una eventual ampliación pareada autorizada. La evidencia actual demuestra ahorro local frente a Top-$k$, no dominancia global sobre Completa/GFS ni equivalencia de calidad.
4. **Escritura en paralelo, cuando se solicite:**
   * [Resultados](../../paper/chapters/04_resultados.tex): tablas descriptivas auditadas, KTH identificado por procedencia, contrastes exploratorios de cinco datasets y piloto físico de 47 imágenes con límites.
   * [Discusión](../../paper/chapters/05_discusion.tex): compromiso calidad–costo, resultados negativos H2, tamaño muestral, exposición previa al test y comparación específica con antecedentes. No afirmar causalmente saturación ni superioridad universal frente a Bellman.
   * [Conclusión](../../paper/chapters/06_conclusion.tex): alcance demostrado y pendientes; ROCF solo si se recupera evidencia verificable, nunca como experimento confirmado por esta narración.
   * Compilar y revisar visualmente [la tesis](../../paper/tesis.tex) después de editarla. Esta actualización solo modifica documentación de planificación; no modifica LaTeX ni produce un nuevo PDF.
5. **Cierre final:** una decisión de usar la cascada como método principal no elimina las limitaciones. Completar P5a o limitar explícitamente las afirmaciones a las que ya tienen evidencia; no certificar originalidad o no inferioridad por decreto.
