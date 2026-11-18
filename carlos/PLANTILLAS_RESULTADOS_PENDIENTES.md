# Plantillas para integrar los resultados de Joaquín

Fecha: 2026-11-18. Uso interno de Carlos.

Cada sección dice dónde va el resultado en `carlos/main.tex`, qué texto
cambia y trae el LaTeX listo con marcadores `XX`. Los números de las
columnas «proyectado» ya están cargados desde la Tabla `tab:cascada`. Los
puntos siguen la numeración de [PENDIENTES_JOAQUIN.md](PENDIENTES_JOAQUIN.md).

Antes de pegar cualquier resultado:
1. Confirmar con Joaquín la carpeta canónica y anotarla en el Apéndice A.
2. Comparar las accuracies nuevas con las del paper. Si no coinciden, frenar y
   preguntar antes de reemplazar nada.
3. Después de integrarlo: compilar, revisar que no haya referencias rotas y
   repasar resumen, highlights, discusión, limitaciones y conclusión.

---

## P1. Latencia online de E1 (§4.9 «Medición física»)

**Dónde:** al comienzo de la subsección `sec:piloto`. Conviene renombrarla a
«Medición física de la activación por margen» y dejar el piloto anterior como
párrafo de antecedente.

**Texto que hay que cambiar cuando esté:**
- Resumen: «con un costo proyectado 75 % menor». Agregar el ahorro medido.
- Highlight 2: «con 75 % menos costo proyectado». Pasar a «medido» si se
  confirma.
- §4.9: «la cascada con Top-4 todavía no se midió en línea». Borrar.
- Discusión (tercer párrafo) y limitaciones: «La cascada con Top-4 no se midió
  en línea…». Borrar o reescribir.
- Conclusión: «Como siguientes pasos se plantea medir en línea…». Sacar ese
  paso.

```latex
\begin{table}[pos=htbp]
\centering
\caption{Latencia medida en línea de Top-4 directo y de la cascada por margen con SVM, en ms por imagen (RTX 4060, \texttt{batch=1}, modelos residentes). Ahorro: reducción de la latencia media frente a Top-4 directo. Coincidencia: proporción de llamadas cuya ruta y predicción coinciden con las calculadas sobre los embeddings almacenados.}
\label{tab:latencia-e1}
\footnotesize
\setlength{\tabcolsep}{3.5pt}
\begin{tabular}{@{}lrrrrrrrrrr@{}}
\toprule
 & & \multicolumn{3}{c}{Top-4 directo} & \multicolumn{3}{c}{Cascada} & \multicolumn{2}{c}{Ahorro} & \\
\cmidrule(lr){3-5}\cmidrule(lr){6-8}\cmidrule(lr){9-10}
Dataset & Llamadas & Media & Mediana & p95 & Media & Mediana & p95 & Medido & Proyectado & Coincidencia \\
\midrule
DTD & XX & XX & XX & XX & XX & XX & XX & XX\,\% & 73,6\,\% & XX\,\% \\
FMD & XX & XX & XX & XX & XX & XX & XX & XX\,\% & 75,8\,\% & XX\,\% \\
CUReT & XX & XX & XX & XX & XX & XX & XX & XX\,\% & 76,3\,\% & XX\,\% \\
Outex & XX & XX & XX & XX & XX & XX & XX & XX\,\% & 76,7\,\% & XX\,\% \\
Soil & XX & XX & XX & XX & XX & XX & XX & XX\,\% & 61,0\,\% & XX\,\% \\
KTH-TIPS2-b & XX & XX & XX & XX & XX & XX & XX & XX\,\% & 76,3\,\% & XX\,\% \\
\midrule
Media & XX & XX & & & XX & & & XX\,\% & 75,0\,\% & \\
\bottomrule
\end{tabular}
\end{table}
```

Párrafo (elegir la variante según el resultado):

```latex
La Tabla~\ref{tab:latencia-e1} mide en línea las dos políticas de la Tabla~\ref{tab:cascada} con el protocolo del panel. En XX condiciones y XX llamadas, la cascada tardó en promedio XX ms por imagen frente a XX ms de Top-4 directo, una reducción del XX\,\%, frente al 75,0\,\% proyectado. [Si coincide: La medición confirma el orden de magnitud de la proyección.] [Si difiere: La diferencia con la proyección proviene de XX (por ejemplo, el costo fijo de la etapa barata o la carga de bloques en GPU).] El percentil 95 de la cascada fue XX ms frente a XX ms, porque las imágenes escaladas pagan la etapa barata y Top-4. Las rutas y predicciones coincidieron con las calculadas sobre los embeddings almacenados en el XX\,\% de las llamadas, y el coseno mínimo por bloque fue XX.
```

---

## P2. DeepLumina (§4.11, tabla de métodos recientes)

**Dónde:** la fila de DeepLumina, la columna de DTD y la nota ‡ de la tabla
`tab:sota`. También el párrafo de recetas externas de §4.11 y la frase de
limitaciones «DeepLumina presenta problemas de convergencia».

Nota ‡ según el resultado:

```latex
% Si B converge en todas las condiciones:
$^{\ddagger}$DeepLumina se ajustó con rasgos estandarizados con el entrenamiento de cada condición y hasta 100.000 iteraciones; ningún clasificador binario alcanzó el límite. La versión original, sin escalar y con 10.000 iteraciones, obtuvo XX y se informa en el Apéndice~\ref{app:reproducibilidad}. Se presenta como adaptación local, no como réplica de la implementación en MATLAB.

% Si solo se completa DTD f3 (A) y la convergencia sigue igual:
$^{\ddagger}$DeepLumina queda sujeto a revisión: en todas sus condiciones al menos un clasificador binario alcanzó el máximo de iteraciones. DTD se completó (10/10) sin el límite de tiempo original, con una accuracy media de XX. Se presenta como adaptación local descriptiva, no como réplica validada.
```

---

## P3. E4: cascada con ResMLP (§4.7) — integrado el 18-11

> Ya se usó: E4 está en §4.7, la discusión, la conclusión y la Tabla 14, con
> las cifras de `carlos/analisis_paper/e4_e5_resumen.txt`. Si Joaquín manda la
> etapa barata, los costos o las predicciones por imagen (pendiente 15),
> agregarlos ahí. La plantilla original se conserva abajo como referencia.

**Dónde:** después de la Tabla `tab:cascada`. Una tabla corta o un párrafo,
según la cantidad de condiciones. Si se agrega, borrar de las limitaciones
«La comparación pareada entre uso directo y activación por margen usa solo
SVM» y de la conclusión «repetir la comparación con ResMLP».

```latex
Con ResMLP, el margen se calcula sobre sus logits con la misma regla de ruta. En XX condiciones, la cascada obtuvo una accuracy media de XX frente a XX de Top-4 directo (diferencia por dataset entre XX y XX), escalando el XX\,\% de las imágenes, con un costo proyectado de XX frente a XX ms. [Wilcoxon exacto bilateral: $p=$XX.] [Si aplica: Con el margen de no inferioridad $\delta=0{,}01$, la cota inferior unilateral al 95\,\% es XX.]
```

---

## P4. Reservas de KTH y Outex (§4.1, §4.3, limitaciones)

- **Si Joaquín certifica KTH:** borrar de §4.3 «En KTH-TIPS2-b, la evaluación
  estática conserva los resultados archivados… por eso se informa también la
  sensibilidad…» y la frase correspondiente de las limitaciones. Las
  sensibilidades pueden quedar en el apéndice.
- **Si se resuelve Outex:** si el arreglo correcto es el del panel y cambia
  Completa-22, hay que recalcular la Tabla `tab:top4`, la no inferioridad de
  Top-4 frente a Completa-22 y la discusión sobre la ventaja de Completa-22 en
  Outex. **Revisar antes de tocar:** cambia una conclusión.

---

## P5. Costo de cada descriptor (estilo Tablas 7 y 8 de HyTexNet)

**Dónde:** como tabla nueva en §3 (Método, después de las tablas de
extractores) o en §4.11 junto a la comparación con métodos recientes.

Ya están cargados:
- las dimensiones de las tablas de extractores;
- los ms de los 10 bloques que tienen perfil de costo en E1
  (`component_costs_ms` de `protocol_frozen.json`).

Faltan los parámetros y los GFLOPs (Joaquín) y los ms de los bloques sin
perfil. Si los ms de esos bloques no se miden, dejar «—» y explicarlo en la
leyenda.

```latex
\begin{table}[pos=htbp]
\centering
\caption{Costo de cada bloque de la biblioteca: dimensión del vector, parámetros de la red, GFLOPs por imagen a la resolución de entrada usada y tiempo de extracción en el perfil de costos de la Sección~\ref{sec:resultados-margen} (Outex, usado para cinco datasets, y KTH-TIPS2-b). «—»: bloque sin perfil, porque no forma parte de Top-4 ni es etapa barata candidata en E1.}
\label{tab:costo-bloques}
\footnotesize
\begin{tabular}{@{}lrrrrr@{}}
\toprule
Bloque & Dim. & Parámetros (M) & GFLOPs & ms (Outex) & ms (KTH) \\
\midrule
ResNet-50 & 2.048 & XX & XX & 24,1 & 14,3 \\
SigLIP-B & 768 & XX & XX & 26,1 & 14,4 \\
BEiTv2-B & 768 & XX & XX & 26,3 & 15,1 \\
ConvNeXt V2-T & 768 & XX & XX & 27,6 & 12,2 \\
Swin-T & 768 & XX & XX & 33,6 & — \\
EVA-02 base & 768 & XX & XX & 34,3 & 25,7 \\
DINOv2-S & 384 & XX & XX & 55,9 & 24,7 \\
ViT-B/16 & 768 & XX & XX & 60,1 & — \\
DINOv2-B & 768 & XX & XX & 129,3 & 60,6 \\
DINOv2-L & 1.024 & XX & XX & 397,2 & 176,8 \\
VGG16 & 4.096 & XX & XX & — & — \\
ResNet-101 & 2.048 & XX & XX & — & — \\
DenseNet-121 & 1.024 & XX & XX & — & — \\
EfficientNet-B0 & 1.280 & XX & XX & — & — \\
DeiT-S & 384 & XX & XX & — & — \\
MAE-B & 768 & XX & XX & — & — \\
\midrule
LBP / LBP-rot / Gabor / GLCM / HOG / N-gramas & 54 / 80 / 48 / 18 / 1.764 / 256 & — & — & — & — \\
\bottomrule
\end{tabular}
\end{table}
```

> En KTH, los tiempos de SigLIP-B (14,4 ms) y EVA-02 (25,7 ms) son las dos
> constantes validadas por separado:
> `results/analysis/kth_reference_validated_profile_20261115_v1/profile.json`.
> Son los mismos valores que usa el protocolo de las dos particiones de KTH
> completadas después (`top4_fixed_kth_completion_20261115_v1`).

---

## P6 y P7. Ejemplos mal clasificados y t-SNE

- **P6 ya está hecho:** es la Figura 5 de §4.8, con 8 imágenes de KTH tomadas
  del repo local. Joaquín no tiene que hacer nada.
- **P7, t-SNE:** cuando Joaquín mande la imagen, agregarla después de la
  Figura 5:

```latex
\begin{figure}[pos=htbp]
\centering
\includegraphics[width=0.6\textwidth]{figures/tsne_kth_top4.pdf}
\caption{t-SNE de los vectores Top-4 concatenados en el test de KTH-TIPS2-b (partición XX), coloreados por clase. Perplejidad XX, semilla XX. Las imágenes de algodón de la muestra b se ubican junto al lino.}
\label{fig:tsne}
\end{figure}
```

Antes de escribir la última frase de la leyenda, verificar en la imagen que de
verdad se ve eso.

---

## P11. E1 con otras semillas (§4.7 y limitaciones)

```latex
Con las semillas 123 y 2026 en FMD y Soil, la diferencia entre la cascada y Top-4 directo fue XX y XX, del mismo orden que con la semilla 42 (XX y XX).
```

Si se agrega, ajustar en las limitaciones «La comparación pareada… usa solo
SVM y una semilla».
