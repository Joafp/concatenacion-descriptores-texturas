#!/usr/bin/env python3
"""Stage, compile and activate the reviewed Overleaf snapshot, preserving history."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/articulo/borrador_profesor'
TARGET = ROOT / 'overleaf_upload_consolidado'


def main():
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    stage = ROOT / f'overleaf_preparacion_{stamp}'
    stage.mkdir()

    def copy(source, relative):
        destination = stage / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    for name in ['main.tex', 'references.bib', 'cas-sc.cls', 'cas-common.sty']:
        copy(PAPER/name, name)
    bst = subprocess.check_output(['kpsewhich', 'unsrtnat.bst'], text=True).strip()
    copy(Path(bst), 'unsrtnat.bst')
    auxiliary = {'ngram_svm.tex','ngram_resmlp.tex','ngram_resmlp_source_rows.csv','reference20_source_rows.csv','individual_identity.tex'}
    for source in (PAPER/'generated').iterdir():
        if source.is_file():
            copy(source, ('historial_comparacion_bibliotecas/' if source.name in auxiliary else 'generated/')+source.name)
    shutil.copytree(PAPER/'thumbnails', stage/'thumbnails')
    for name in ['concatenacion_v02.pdf', 'concatenacion_v02.tex', 'concatenacion_v02.png',
                 'concatenacion_v02_qa.md', 'texture_banded_0045.jpg', 'gfs_pasos.pdf']:
        copy(PAPER/'figures'/name, 'figures/'+name)
    copy(PAPER/'figures/tikz_v01/gfs.tex', 'figures/gfs_fuente.tex')
    # Mechanical path adaptation only; both entry points compile from the root.
    for source, relative in [(ROOT/'paper/tesis.tex', 'tesis.tex')]+[
            (p, 'chapters/'+p.name) for p in sorted((ROOT/'paper/chapters').glob('*.tex'))]:
        destination = stage/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source.read_text().replace('articulo/borrador_profesor/', ''))
    for name in ['REVISION_SVM_NGRAMAS_20260907.md', 'AUDITORIA_PROFESOR_CONCATENACION_20260907.md']:
        copy(ROOT/'paper'/name, 'documentacion/'+name)
    # Historical guides are preserved, but never presented as the current matrix.
    history = TARGET/'historial_estadistico_otros_protocolos'
    if history.is_dir():
        shutil.copytree(history, stage/'historial_estadistico_otros_protocolos')
    stats = ROOT/'results/confirmatory/ngram21/nonparametric'
    for kind, suffix in [('ControlTest', 'controltest'), ('MultipleTest', 'multipletest')]:
        for mode in ['primary', 'sensitivity']:
            copy(stats/f'{mode}_{suffix}.tex', f'resultados_estadisticos/{kind}/macro_f1/{mode}.tex')
    for name in ['primary_by_dataset.csv', 'sensitivity_dataset_classifier.csv', 'validation.json']:
        copy(stats/name, 'resultados_estadisticos/'+name)
    for source in (ROOT/'results/confirmatory/nonparametric').iterdir():
        if source.is_file() and source.name in {'primary_by_dataset.csv','sensitivity_dataset_classifier.csv','primary_controltest.tex','primary_multipletest.tex','sensitivity_controltest.tex','sensitivity_multipletest.tex'}:
            copy(source, 'historial_comparacion_bibliotecas/estadistica20/'+source.name)
    for name in ['build_paper_revision_tables.py', 'build_ngram21_nonparametric.py', 'build_nonparametric_analysis.py', 'package_overleaf_revision.py']:
        copy(ROOT/'scripts'/name, 'reproducibilidad/'+name)
    (stage/'README.md').write_text('''# Versión revisada para Overleaf — 7 de septiembre de 2026

## Qué subir

Esta carpeta completa o `overleaf_upload_consolidado.zip`. En Overleaf, elegir **main.tex** como documento principal del artículo y **pdfLaTeX** como compilador. Para la tesis, elegir **tesis.tex**, también en la raíz. No seleccionar las salidas Java como documento principal.

- `main.tex`, `main.pdf`: artículo revisado.
- `tesis.tex`, `tesis.pdf`, `chapters/`: tesis sincronizada con el artículo; solo se adaptaron las rutas locales.
- `generated/`: tablas compartidas, CSV de las filas efectivamente reportadas y hashes de procedencia.
- `figures/`: figuras vigentes, fuentes y ejemplo de textura.
- `resultados_estadisticos/`: salidas originales Java que respaldan el análisis de referencia vigente, separadas por programa.
- `documentacion/REVISION_SVM_NGRAMAS_20260907.md`: evaluación metodológica ARS, hallazgos y correcciones.
- `documentacion/AUDITORIA_PROFESOR_CONCATENACION_20260907.md`: lectura final del argumento, escritura y evidencia; incluye la limitación de LBP-rot.
- `historial_estadistico_otros_protocolos/`: archivo de informes y pruebas anteriores. No es la fuente de las tablas actuales; algunas métricas y protocolos son distintos.
- `reproducibilidad/`: generadores para el repositorio completo, no necesarios para compilar en Overleaf.
- `VALIDACION_ENTREGA.json`: comprobaciones de compilación y hashes del paquete.

## Qué resultados incluye

Biblioteca única de 21 descriptores: cuatro datasets, SVM y ResMLP, cinco estrategias; 56 condiciones externas y 280 filas de resultados. Macro-F1 y exactitud. La inferencia principal usa cuatro filas en total, una por dataset (promediando los clasificadores). Friedman p=0,1074; Quade p=0,0705; ningún par significativo con Holm a 0,05.

`generated/ngram21_source_rows.csv` conserva las 280 filas de la biblioteca completa. Las pruebas actuales corresponden a 21. La tabla frente a Individual presenta los cuatro contrastes de interés con el ajuste de Holm para diez pares. Las comparaciones previas de bibliotecas se conservan en `historial_comparacion_bibliotecas/`, fuera del artículo. N-gramas se trata como un descriptor más y el texto utiliza únicamente el nombre Outex.

## Compilación local

Desde esta carpeta: `pdflatex main.tex`, `bibtex main` y dos pasadas de `pdflatex main.tex`. Sustituir `main` por `tesis` para compilar la tesis. Están incluidas la clase, sus dependencias locales, el estilo bibliográfico, las tablas y las figuras. Se conservó el mismo motor pdfLaTeX; no se rasteriza el texto. La configuración actual usa babel inglés por disponibilidad del entorno local, con nombres de tablas, figuras y referencias en español.

## Límites de esta entrega

Es el borrador correcto para revisión con el profesor, no una publicación enviada. SVM, ResMLP y Top-k están completos para ambas bibliotecas, y la estadística conjunta fue regenerada. Queda confirmar con los autores las declaraciones y los metadatos finales. No se ha subido automáticamente al sitio de Overleaf. La carpeta y el ZIP anteriores se conservaron con sufijo de respaldo fuera de esta carpeta.
''')
    (stage/'resultados_estadisticos/README.md').write_text('''# Salidas estadísticas de referencia vigentes

Los cuatro `.tex` de esta carpeta son copias byte a byte de `results/confirmatory/ngram21/nonparametric/` del repositorio.

| Archivo | Comparación y alcance |
|---|---|
| `ControlTest/macro_f1/primary.tex` | Cuatro datasets; pruebas globales y comparaciones contra el control. |
| `MultipleTest/macro_f1/primary.tex` | Misma matriz; diez pares, incluidos GFS–Individual y Top-k–Individual. Fuente de Holm en el artículo. |
| `ControlTest/macro_f1/sensitivity.tex` | Ocho filas dataset–clasificador dependientes; análisis secundario. |
| `MultipleTest/macro_f1/sensitivity.tex` | Diez pares sobre esas ocho filas; no sustituye al análisis principal. |

`primary_by_dataset.csv` y `sensitivity_dataset_classifier.csv` contienen las entradas respectivas. Todos corresponden a **21 descriptores con SVM y ResMLP completos**. El artículo presenta Friedman, Quade y Holm con nombres estadísticos; ControlTest y MultipleTest identifican los programas.

Los originales Java no se editaron: pueden imprimir valores ajustados mayores que 1 y texto automático de umbrales. Para leer Holm, consultar la columna de p ajustados; el artículo limita su presentación a 1. `historial_estadistico_otros_protocolos/` conserva las otras métricas y guías históricas, sin mezclarlas con estas tablas.
''')
    validation = {'timestamp_local': stamp, 'entrypoints': {}, 'source_checks': {},
                  'ngram_svm_included': True, 'primary_library_size': 21, 'historical_results_are_separate': True}
    for entry in ['main', 'tesis']:
        build = Path(tempfile.mkdtemp(prefix=f'ars_overleaf_{entry}_'))
        commands = [
            ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', f'-output-directory={build}', entry+'.tex'],
            ['bibtex', entry],
            ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', f'-output-directory={build}', entry+'.tex'],
            ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', f'-output-directory={build}', entry+'.tex'],
        ]
        env = os.environ.copy()
        env['BIBINPUTS'] = str(stage)+os.pathsep
        env['BSTINPUTS'] = str(stage)+os.pathsep
        for command in commands:
            result = subprocess.run(command, cwd=build if command[0]=='bibtex' else stage,
                                    env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode:
                raise RuntimeError(f'Build failed; staged files retained at {stage}:\n{result.stdout[-5000:]}')
        log = (build/(entry+'.log')).read_text(errors='replace')
        assert not re.search(r'Overfull \\[hv]box|There were undefined references|Citation .+ undefined|Reference .+ undefined', log), log[-3000:]
        copy(build/(entry+'.pdf'), entry+'.pdf')
        validation['entrypoints'][entry] = {'compiled': True, 'overfull_or_undefined': False,
                                          'build_log': str(build/(entry+'.log'))}
    assert (stage/'main.tex').read_bytes() == (PAPER/'main.tex').read_bytes()
    validation['source_checks']['main_identical_to_borrador_profesor'] = True
    assert (stage/'tesis.tex').read_text() == (ROOT/'paper/tesis.tex').read_text().replace('articulo/borrador_profesor/', '')
    validation['source_checks']['tesis_only_relative_paths_adapted'] = True
    validation['files_sha256'] = {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(stage.rglob('*')) if p.is_file()}
    (stage/'VALIDACION_ENTREGA.json').write_text(json.dumps(validation, ensure_ascii=False, indent=2)+'\n')
    archive = ROOT/f'overleaf_preparacion_{stamp}.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(stage.rglob('*')):
            if p.is_file():
                z.write(p, str(p.relative_to(stage)))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert 'main.tex' in z.namelist() and 'tesis.tex' in z.namelist()
    backup = ROOT/f'overleaf_respaldo_antes_revision_{stamp}'
    if TARGET.exists():
        TARGET.rename(backup)
    zip_target = ROOT/'overleaf_upload_consolidado.zip'
    if zip_target.exists():
        zip_target.rename(ROOT/f'overleaf_respaldo_antes_revision_{stamp}.zip')
    stage.rename(TARGET)
    archive.rename(zip_target)
    print(json.dumps({'folder': str(TARGET), 'zip': str(zip_target), 'backup': str(backup),
                      'file_count': len(validation['files_sha256'])+1, 'compiled': list(validation['entrypoints'])}, indent=2))


if __name__ == '__main__':
    main()
