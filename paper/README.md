# Tesis: Top-k directo y activación por margen

**Actualizada el 15-11-2026.** El PDF vigente tiene **87 páginas** y usa
**accuracy (exactitud) como métrica principal**. Macro-F1, precisión macro y
recall macro son complementarias. Se conserva el título acordado y el recorrido
Top-k directo → optimización por margen.

**Cierre experimental posterior:** E1/E2 ya tiene **27/27 condiciones y seis
datasets**, con 98 pruebas aprobadas. El PDF todavía contiene el corte previo
de 25/27; falta integrar estas cifras nuevas y recompilar.
[Informe vigente del cierre](../docs/fsc_tex/CIERRE_FIDELIDAD_KTH_E1_E2_2026-11-15.md).

- [Abrir la tesis PDF](tesis.pdf) y [fuente principal](tesis.tex).
- [Informe del día y pendientes](../docs/fsc_tex/AVANCE_ACCURACY_E1_E2_2026-11-15.md).
- [Plan vigente](../docs/fsc_tex/PLAN_TOPK_MARGEN_2026-11-13.md).
- [Decisión de métrica y cronología](../docs/fsc_tex/DECISION_METRICA_ACCURACY_2026-11-15.md).

## Evidencia incluida en el PDF de este corte

1. Barrido de 21 tamaños × 47 condiciones por clasificador, seis datasets.
   Top-4/SVM: accuracy media por dataset 0,944214, frente al máximo descriptivo
   0,945090 en k=10; aproximadamente 15,42 % de dimensiones. No es un óptimo universal.
2. Comparaciones estáticas, N-gramas y adaptaciones externas reconstruidas con
   accuracy; las cifras históricas, online y los costos permanecen separados.
3. Cascada histórica de 27 condiciones con k heredado de uno a ocho, presentada
   separadamente de la ampliación nueva con cuatro bloques fijos.
4. **E1 nuevo:** 25/27 condiciones completadas. DTD, FMD, CUReT, Outex y Soil
   completos; KTH 2/4, sin media parcial. Accuracy media de cinco datasets:
   0,941839915 directa y 0,941830218 por margen. Adquisición proyectada 74,87 %
   menor; no es una medición nueva de latencia online de las políticas.
5. **E2:** margen, máximo y entropía con los mismos scores; se distinguen
   umbrales OOF y diagnóstico por lote de igual cantidad derivada. No hay
   pares significativos en accuracy tras Holm sobre cinco datasets completos.

El cambio de métrica principal se decidió después de observar resultados
históricos. El ranking y la selección de rutas históricos basados en macro-F1
siguen identificados; no se reetiquetan como selección por accuracy.

## Archivos y reservas

- [Reconstrucción de accuracy](../results/analysis/thesis_accuracy_primary_20261115_v3/summary.json): 144 fuentes con hashes, sin nuevas predicciones.
- [Auditoría E1/E2](../results/analysis/top4_fixed_e1_e2_audit_20261115_v1/summary.json).
- [Predicciones y scores E1/E2](../results/exploratory/topk_cascade/top4_fixed_primary22_20261115_v1/conditions/).
- [Bibliografía activa](articulo/borrador_profesor/references.bib).

Los dos fallos originales de fidelidad EVA-02/SigLIP conservan sus archivos.
Una ruta corregida autorizada superó 0,999 en las mismas 33 imágenes por red
y permitió completar los dos casos que no habían ajustado clasificadores.
Ese cierre nuevo tiene carpetas independientes y no reescribe el corte del PDF.
Se conservan también las reservas históricas KTH/DTD,
DeepLumina no convergente e incompleto, y diferencias de representación online.
Los estudios de ensamble y poda permanecen en un anexo complementario.

## Verificación y compilación

Pasaron **52 pruebas**. El PDF compila sin referencias indefinidas ni desbordes
horizontales y se revisaron visualmente sus 87 páginas. Es un borrador para
revisión de autores y tutor, no una aprobación académica.

Desde `paper`, en Ubuntu/WSL:

```sh
../.tools/tectonic-0.16.9/tectonic --keep-logs --keep-intermediates tesis.tex
```

La revisión ARS del 13-11 conserva su PDF/manifiesto histórico de 82 páginas;
la versión de accuracy la sucede. Los borradores de artículos, presentaciones
y paquetes anteriores conservan su alcance y no se actualizan por recompilar
este PDF. Pesos de extractores, embeddings y modelos joblib permanecen locales;
predicciones, scores y tablas permiten auditar las métricas publicadas.
