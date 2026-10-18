# Memorando de Entrega: Versión de Tesis para Revisión de Tutoría

**Para:** Prof. José Vázquez (Tutor, Facultad Politécnica, Universidad Nacional de Asunción)  
**De:** Carlos Ayala y Joaquín Delgado (Tesistas)  
**Fecha:** 12 de octubre de 2026  
**Título del Trabajo:** *Concatenación sistemática y fusión adaptativa costo-consciente de descriptores visuales para clasificación de texturas: De la selección anidada de bloques a la adquisición secuencial guiada por incertidumbre*  
**Estado del Manuscrito:** Borrador para revisión del tutor (39 páginas, 6 capítulos). El alcance de cada resultado se delimita a continuación; esta nota no certifica una revisión integral de todas las referencias o figuras.  

---

## 1. Propósito del Documento

El presente memorando acompaña la entrega del borrador completo de la tesis de grado y su paquete fuente para Overleaf. Resume la evolución metodológica del trabajo, los resultados empíricos auditados, las decisiones epistemológicas adoptadas conforme al protocolo *Academic Research Suite* (ARS) y la estructura de los archivos entregables.

---

## 2. Evolución del Proyecto y Contribución Central

El trabajo aborda el problema de la combinación de descriptores heterogéneos para el reconocimiento de texturas visuales, transitando a través de dos fases complementarias:

1. **Fase 1 — Evaluación Sistemática de la Concatenación Estática:**  
   Se conformó una biblioteca unificada de **22 descriptores** (clásicos, estadísticas de color, CNNs supervisadas, Vision Transformers y modelos fundacionales multimodales y autosupervisados, totalizando **20.652 dimensiones**). Se evaluaron cinco estrategias de selección de bloques (Individual, Completa, Top-$k$, GFS y Homogénea) bajo un diseño de validación anidada (*nested cross-validation*) con dos clasificadores de sesgos disímiles (Linear SVM y ResMLP) sobre seis conjuntos de datos (DTD, FMD, CUReT, Outex13, SoilOriginal y KTH-TIPS-2b).
2. **Fase 2 — Formulación de la Cascada Adaptativa Costo-Consciente:**  
   Frente al costo prohibitivo de extraer todos los descriptores para cada imagen en tiempo real, se introdujo una **política de adquisición secuencial condicional**. La arquitectura evalúa primero una etapa económica ($e_1$, típicamente SigLIP o ResNet-50) y calcula el margen de incertidumbre en el clasificador. Si la confianza supera un umbral calibrado prospectivamente en entrenamiento ($\tau$), la predicción se emite de inmediato; si hay ambigüedad, se escala a la etapa costosa (subconjunto Top-$k$).

---

## 3. Resumen de Resultados Empíricos Auditados

### 3.1. Generalización y Calidad Predictiva (27 Condiciones Canónicas)
La cascada adaptativa tiene resultados descriptivos en 27 condiciones con Linear SVM:
* **Desempeño descriptivo:** Macro-F1 medio de **0,9345** (Cascada), **0,9341** (Top-$k$ de origen) y **0,9409** (Completa-22). En los cinco conjuntos reconciliados, las diferencias medias son $-0{,}0004$ frente a Top-$k$ y $-0{,}0046$ frente a Completa-22.
* **Unidad de inferencia:** las 27 condiciones contienen particiones repetidas de los mismos seis conjuntos; por ello, no se usan como 27 observaciones independientes. Los Wilcoxon exploratorios sobre esas filas ($p=4{,}15\times10^{-6}$ para costo y $p=0{,}2432$ para macro-F1) se retiran como evidencia inferencial. El costo del 75,5\% es una proyección analítica descriptiva, no una reducción física estadísticamente validada.
* **Comparación por datasets:** el análisis de rangos de rendimiento se limita a los cinco conjuntos reconciliados ($N=5$), con KTH-TIPS-2b excluido por la procedencia de su referencia Top-$k$. Friedman ($p=0{,}4518$), Iman--Davenport ($p=0{,}4922$) y los contrastes de Wilcoxon con Holm ($p_{\text{Holm}}=1{,}0000$) no rechazan igualdad de rangos. Estos resultados no prueban equivalencia ni no inferioridad.

### 3.2. Medición física pareada en GPU en los seis conjuntos de datos (NVIDIA GeForce RTX 4060)
Para contrastar la reducción analítica de costos con la latencia física real de reloj de pared en hardware de inferencia, se ejecutó un benchmark pareado completo en una GPU NVIDIA GeForce RTX 4060 sobre los seis conjuntos de datos de referencia (DTD, CUReT, KTH-TIPS-2b, Outex13, SoilOriginal y FMD):
* **Protocolo y cobertura:** se evaluó una condición fija por dataset con una muestra balanceada estratificada de una imagen por clase (semilla 42) y tres repeticiones pareadas con orden aleatorizado en cada par (Cascada vs. Top-$k$), acumulando 204 imágenes de prueba únicas y 612 parejas de inferencia medidas.
* **Reducción de latencia media:** 90,25 ms para la cascada frente a 291,21 ms para Top-$k$, equivalente a un **69,0% de reducción física en reloj de pared** y a una razón agregada de latencias de **3,23$\times$** (oscilando localmente entre 2,60$\times$ / 61,5% en SoilOriginal y 16,00$\times$ / 93,7% en FMD).
* **Fidelidad funcional y salida temprana:** en las 612 parejas evaluadas, tanto las decisiones de escalado condicional (`route_matches_cache`) como las predicciones emitidas (`cascade_matches_cache` y `topk_matches_cache`) coincidieron al **100,0%** con los resultados calculados fuera de línea. Asimismo, el **74,0% de las inferencias (453 de 612)** se resolvieron tempranamente en la Etapa 1 económica sin invocar la etapa densa.
* **Trazabilidad estricta:** cada medición individual está persistida con ruta de imagen, hash SHA-256 verificado, repetición, orden de ejecución, latencia en ms, ruta tomada y predicción emitida en `results/exploratory/fsc_tex/physical_six_20261012/`.

---

## 4. Rigor Metodológico y Cierre de Brechas (ARS)

Estado de documentación y límites metodológicos relevantes para la lectura del manuscrito:

1. **Procedencia de Top-$k$ en KTH-TIPS-2b:**  
   Se documentó el mapa de las cuatro particiones y se completó la ejecución de los pliegues restantes (pliegues 0 a 3) del control Top-$k$ con agrupación por muestra física en la validación interna (`innergrp-sample`, media de macro-F1 = **0,9445**, coincidente con el 0,9445 de la cascada). Dado que el archivo original de la cascada en KTH empleó los subconjuntos de la variante previa (media Top-$k$ de origen = 0,9400), KTH se reporta con ambas referencias transparentes y los contrastes primarios de Demšar se mantienen sobre los cinco conjuntos reconciliados desde el archivo original ($N=5$).
2. **Exclusión de Métodos no Verificados (ROCF):**  
   No se localizaron resultados ejecutables de *Residual Orthogonal Complement Fusion* (ROCF). Sus cifras se excluyen de la evidencia; cualquier mención conceptual queda delimitada a trabajo futuro y no se presenta como un método evaluado.
3. **Resolución y Auditoría de Fidelidad Físico vs. Caché:**  
   En el benchmark de seis datasets con 612 mediciones pareadas, la concordancia con las predicciones y rutas archivadas en caché alcanzó el **100,0%**. Variaciones numéricas puntuales en el descriptor secundario ViT-B/16 (debidas a la inicialización de la capa `pooler` en el cargador de HuggingFace frente a la extracción original) no afectaron ninguna decisión de escalamiento ni predicción en el test.
4. **Delimitación de Afirmaciones Epistémicas:**  
   El texto no afirma "equivalencia demostrada" (lo que requeriría una prueba formal de no-inferioridad con margen especificado a priori) ni "superioridad global frente a Completa", sino que defiende rigurosamente el **compromiso práctico calidad--costo** de la adquisición condicional.

---

## 5. Inventario de Entregables

| Archivo / Recurso | Ruta en el Repositorio | Descripción |
| :--- | :--- | :--- |
| **Manuscrito de Tesis (PDF)** | `paper/tesis.pdf` | Compilación local exitosa, 39 páginas; no se detectan citas o referencias indefinidas ni errores de compilación. |
| **Paquete para Overleaf (ZIP)** | `paper/tesis_overleaf.zip` | Paquete fuente actualizado y autocontenido (1,9 MB); verificado para compilar limpiamente con BibTeX. |
| **Código Fuente LaTeX** | [`paper/tesis.tex`](file:///home/joaquin/tesis_claude/paper/tesis.tex) y [`paper/chapters/`](file:///home/joaquin/tesis_claude/paper/chapters/) | Estructura modular en 6 capítulos en español con bibliografía en BibTeX. |
| **Pruebas automatizadas (60 tests)** | `tests/` | 60 pruebas unitarias automatizadas (100% aprobadas), incluyendo pruebas de invariancia del benchmark físico. |
| **Predicciones Canónicas** | `results/exploratory/topk_cascade/cheap_stage_selected_primary22/` | Registro de las 31.984 inferencias de test de las 27 condiciones. |
| **Benchmark Físico Multiconjunto** | `results/exploratory/fsc_tex/physical_six_20261012/` | 612 mediciones pareadas registradas en GPU RTX 4060 sobre los seis datasets. |
| **Plan de Tesis v1.7** | `docs/PROPUESTA_TESIS_FUSION_SECUENCIAL_COSTO_RIESGO.md` | Documento maestro de diseño y trazabilidad del camino crítico; VisTex queda fuera del manuscrito por decisión del autor. |

Quedamos a entera disposición para reunirnos, revisar las observaciones del borrador y acordar las fechas para la presentación preliminar y defensa final.
