# LBP+dCellNN 2024: receta y compatibilidad de fuentes

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent; pdf.
- Origin Mode: auditoría técnica de candidato completo, sin benchmark.
- Origin Date: 2026-11-02, 14:16 UTC.
- Verification Status: ANALYZED; compatibilidad estática verificada.
- Version Label: cellnn2024_readiness_v1.

PDFlocal1-s2.0-S0957417423026027-main.pdf, DOI10.1016/j.eswa.2023.122100,
SHA256a9aaf78abb5e2d0414ae9f8d953875c34f6638b97f9484a49085d0fbe7123e0e.
PreflightPASS12páginas sinwarnings, stdoutguardado como sidecar. Texto derivado
cellnn2024.txt. Leídos métodos2/3, materiales4.1,training4.2 y disponibilidad;
página5 renderizada e inspeccionada(Fig4/5,ecuaciones8/9). No lectura humana
íntegra ni reproducción de porcentajes.

## Código primario y estado

El paper enlaza https://github.com/UESTC-nnLab/LBP_Contour . Código decontornos,
fusiónLBP,clasificador ycheckpoint disponibles, solo seisarchivos enárbol
inspeccionado. No LICENSE visible eneseárbol; no redistribución ni publicación
de códigoajeno. Consultas dearchivos pequeñas y10.311bytes decheckpoint;
sinclonar,instalar,descargarDRIVE ni entrenar extractor.

HEAD/commit89fc3d6097ab13f800c8d2828f4d6ed2225f3eb1 (2023-04-17) cambia
entrypoint a cellula(4), cuyo registrodeparámetros no corresponde alcheckpoint.
Block contiene parámetros compartidos a nivel declase ylista noModuleList;
no usar strict=False, inicializacionesaleatorias ni cambiar red paracargar.

Historialprimario permitió localizar commitdelautor
299502cbb2243ecb78018110236871f261aa92b2 (2022-06-17), entrypointmcellnn()
y mismo checkpointgitblob319d4deb633488c077f5193c99568e9c5ac7496c.
AuditoríaAST delarchivo sin ejecutarlo:20nombresdeparámetros coinciden
exactamente concheckpoint sinprefijo DataParallelmodule. Pesoscargados solo
con torch.load(weights_only=True,map_location=cpu), todosFP32/finitos.
SHA256checkpointaf56a7e939c93e4ec7b0e2c8af348bff756ac25267af4ca45b52005552fba65f.

Recibo reproducible cellnn_author_static_receipt.json, SHA256
86cb069539fd9807c2df5f44a2758d92f2879dc05ec278f3234bf1cd113560bc,
scripts/audit_cellnn_author_sources.py.40KBaproxleídos enmemoria porrecibo,
ceroimágenes extraídas,cero fits,cero llamadasonline,códigoautor noejecutado.
Es matchestático, NO prueba dereplaynumerico/fidelidaddelpaper.

## Receta candidata del código previo, diferencias a declarar

Pipelinecompleto preferible:6LBP+dCellNNs concheckpointautor congelado yMLP.
Seisescalas(P,R):(8,1),(16,2),(24,3),(8,3),(12,5),(16,7),LBPuniform/riu2.
Contornos en tresresoluciones; fusiónporpesos4/2/1 ybaseP+2; histogramas
80+144+208+80+112+144=768,concatenados sinnormalizaciónfeature añadida.
ClasificadorfuenteMLP400ocultas,max_iter10000; versiones/defaults nofijados
enrepositorio deben declararse localmente antes delfit.

getHist usa canalazulOpenCV,no luminanciacombinada; normalización porimagen,
CLAHEclip2/8×8,gamma1.2 paraCNN,LBPs sobrecanalsin ese preproceso. Fijar
resize128 yreglas numéricas/bordes prospectivamente para elpanelcomún;
fuenteOTC12 asume128original. Método no equivale a nuestroOutex13 niKTH
3train/1test. Paper utilizaDRIVE paracontornos yparticiónKTHporpose/luz/escala,
no muestrasfísicas disjuntas. Las reservas se conservan.

Pendientes antes dedespacho: portsin efectoslaterales, cargastrict de20tensores,
paridad decontornos e histogramas contraversiónautor sobre entradas sintéticas
antes deusardatasets, tests dedecode/768dim/classifier/cronómetro yprotocolo
adaptado conbibliotecas/semilla/presupuesto. NoF1históriconuevos tiempos.
No ejecutarentrypoint crudo(cargamodelos,recorreOTC12,entrena12variantes alimportar).
No benchmark ni omitir casos porconstantes/errores; errorcientífico requiere
revisiónsinretry. Estado AUTHOR_VERSION_SELECTED_IMPLEMENTATION_TESTS_PENDING.
