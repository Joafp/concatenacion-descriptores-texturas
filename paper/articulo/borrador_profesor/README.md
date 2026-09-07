# Borrador completo del artículo para revisión

Proyecto LaTeX autocontenido basado en el template Elsevier CAS Single Column
(`cas-sc`). El contenido actual comprende la portada, el resumen,
los highlights, las palabras clave, la introducción, los trabajos relacionados,
la metodología, los resultados confirmatorios consolidados de DTD, FMD, CUReT
y la extensión Outex, el control top-k, los controles aleatorios, la
estabilidad, la discusión, las limitaciones y la conclusión del estudio. El
texto está cerrado como borrador académico:
solo permanecen pendientes las decisiones editoriales y los metadatos propios
de una futura entrega pública.

## Archivo principal

`main.tex`

## Compilación

Con una distribución TeX Live que incluya `latexmk`:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Alternativamente, con BibTeX y pdfLaTeX:

```bash
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

También puede compilarse con el motor autocontenido Tectonic:

```bash
../../../.tools/tectonic-0.16.9/tectonic main.tex
```

El binario Tectonic 0.16.9 se conserva localmente en `.tools/` dentro del
repositorio, por lo que no requiere permisos de administrador.

Los archivos `cas-sc.cls`, `cas-common.sty`, `cas-model2-names.bst` y
`references.bib` están incluidos localmente para que la carpeta no dependa del
directorio padre.

## Estado de validación

El archivo `main.pdf` fue generado con Tectonic 0.16.9. Se comprobaron las
páginas renderizadas, incluida la comparación explícita entre el mejor
descriptor individual y la mejor concatenación, la portada, las citas, la
bibliografía y la ausencia de referencias cruzadas sin resolver. La advertencia
de caja horizontal emitida al ejecutar `\maketitle` también está presente en el
template CAS original y no genera un desbordamiento visible.

## Elementos previos a una entrega pública

- Confirmar con el tutor el orden de autoría, el autor de correspondencia y la
  redacción CRediT.
- Sustituir la nota de borrador por la información exigida por el destino de
  publicación.
- Incorporar la URL pública y una versión archivada del código y los resultados.
- Adaptar extensión, estilo bibliográfico y declaraciones a la revista o
  congreso seleccionado.
