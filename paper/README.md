# Manuscrito de tesis

**Tema central:** concatenación y selección de descriptores visuales heterogéneos para clasificación de texturas.

El manuscrito estudia cuándo la combinación de representaciones clásicas y modernas mejora al mejor descriptor individual. Los modelos particulares se analizan como componentes del espacio experimental; la contribución principal es la evaluación sistemática de las estrategias de combinación, especialmente la comparación entre concatenación completa, concatenación progresiva y Greedy Forward Selection.

## Estructura

- `chapters/`
  - `04_resultados.md` — Resultados experimentales
  - `05_discusion.md` — Discusión e interpretación
  - `06_conclusion.md` — Conclusión y trabajo futuro
- `references/` — bibliografía (a poblar)
- `figures/` — figuras finales (versiones "publicables" de las de `results/figures/`)
- `AI_DISCLOSURE.md` — declaración de uso de IA

## Datasets del alcance final
- DTD, FMD, Outex13, CUReT, Soil y VisTex

## Espacio de descriptores
- 17 extractores base: 5 clásicos, 6 CNN, 3 Vision Transformers y 3 variantes auto-supervisadas
- Extensión experimental: EVA-02, MAE y SigLIP, para un total de 20 extractores en el análisis SOTA

## Pipeline experimental
- Extracción de embeddings con `src/01_extract_features.py`
- Baseline con `src/02_baseline_individual.py`
- Concat progresiva con `src/03_concat_progressive.py`
- **Greedy Forward Selection**, estrategia central de selección de subconjuntos, con `src/05_greedy_subset_search.py`
- Análisis con `src/04_analyze_results.py`

## Outputs
- `../../results/tables/` — todas las tablas (CSV)
- `../../results/figures/` — todas las figuras (PNG)

## Conversión a LaTeX (cuando esté listo)
Usar `academic-research-skills:ars-format-convert` para convertir a LaTeX/DOCX/PDF.
