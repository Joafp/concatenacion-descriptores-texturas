# HyTexNet ADAPTADO: extensión DTD, v1

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: extensión común prospectiva autorizada, sin ajuste por calidad.
- Origin Date: 2026-11-02, America/Asuncion.
- Verification Status: protocolo antes de nueva extracción/predicción DTD.
- Version Label: hytex_dtd_adaptation_v1.

Hereda método/hiperparámetros/transformaciones/FP32/batch1/cabezaCPU del protocolo
PROTOCOLO_HYTEX_ADAPTACION_FMD_2026-11-02.md, sin cambios porFMD/CUReT. Mismos
pesos/timm, descriptor y100épocas finales; no selección por test. Se etiqueta
HyTexNetadaptado, configuraciónlocal, no código deautores ni cifraspublicadas.

10splits oficiales DTD, semilla42/outerfold0–9,47clases,1880test por split,
18800llamadas externas por sistema. Manifiesto5640filas, mismas imágenes/orden/
labels y grupos del panel local. Reutilizar índicesfit/test congelados de cada
condición, con identidad exacta entre SVM/ResMLP; no reconstruir con un splitter.

La evaluaciónlocal purga de fit los grupos presentes en test. Son exclusiones
HEREDADAS y auditables, no filtros nuevos por error/latencia. Conteosfit:
3753,3753,3757,3754,3754,3753,3752,3752,3751,3749. Excluidosfit por split:
7,7,3,6,6,7,8,8,9,11. Todos pertenecen a grupos de test, sin overlap de grupos
fit/test. No agregar esas filas alfit ni quitar duplicados dentro de test:
test completo1880preservado. Ledger de exclusiones y hashes obligatorio.
Verificar quefit es exactamente(train∨val)oficial menos gruposde test.

CSVoriginaltiene label textual/source_path/source_sha256. Adaptador de schema
produceCSVnuevo con path/hash/intlabel/class_name, conservaoriginal_label y todos
los camposfuente, orden yrow_id. Mapeo enteroclase se deriva de verdad archivada
verificada porhash, no de scores/predicciones/hyperparametersearch; ambasheads y
todos lossplits deben coincidir. Cubrir5640filas con verdad de referencias.
No tocar CSVfuente ni corpus. Canonical CSV/hash/mapeo/exclusiones se sellan antes
de modelo, junto a software/pesos/receta/argv y manifiestos originales.

Precisión de preflight antes de cargar modelo: la unión de los10tests oficiales
cubre5546filas distintas, no5640;94nuncaaparecen en test en esos10splits, pero
pueden estar enfit. No añadir un undécimosplit para completar una unión que el
protocolo oficial no define. Validar etiquetas de las5640filas con arraycanónico
histórico cuyo hashdtype/shape/bytes coincide con provenance.labels_sha256 de
ambosheads en todos lossplits. Contrastar mapeo textual de47clases con todas
lasverdadesexternas observadas y arraycompleto; registrar94índices nuncaentest.
Un guard inicial depreparación exigía erróneamente que toda fila fuera test al
menosuna vez; se corrigió SOLOpreparación con esta verificación más completa,
antes de cualquier extracción/entrenamiento/evaluación. No cambia índices,
F1, método, toleranciafidelidad ni tamaño1880de cada test.

Nueva cola hytex_dtd_external_queue_20261102_v1/; cuatro etapas extract/train/
online/audit con timeouts7200/1800/14400/300s. LockGPUglobal para todas, CPU2hilos,
sin competidores propios ni nuevas descargas.5warmupsprimerfit excluidas;
timestamp/logits/pred/truth/row/ns por llamadaarchivo-a-clase. Fidelityprimer/
últimofit batch1→batch1 maxabs≤1e-4, vectoresguardados antes de decidir.
Fallo requires_review, no retry/relajar umbral/método ni omitir casos.
Primera auditoría completa habilita otros9splits. Ventana12h de despacho.

Solo consolidar10auditorías y18800llamadas, con rawcalls y hashes. Mostrar ambos
heads y cinco métodos locales, mantener reserva física original DTD/SVMsplit7
sin sustituir su tiempo por observaciónadicional. Nuevo tiempoHyTex no limpia
episodiohistórico ni permite afirmarcomparación temporalaislada. Semillas/splits
no son datasets nuevos. No inferenciaestadística ni medias globales parciales.
FMD/CUReTcerrados yNeshovfallido no se repiten. Sin manuscrito/commits/push.
