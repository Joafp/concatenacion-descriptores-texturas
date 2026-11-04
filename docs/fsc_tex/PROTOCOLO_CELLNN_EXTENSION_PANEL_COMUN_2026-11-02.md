# LBP+dCellNN ADAPTADO: extensiones nunca ejecutadas a cinco datasets

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: extensión independiente autorizada, receta inalterada.
- Origin Date: 2026-11-02.
- Verification Status: prospectivo, antes de features/fits de estas condiciones.
- Version Label: cellnn_common_panel_extension_v1.

Hereda PROTOCOLO_CELLNN_ADAPTACION_FMD_2026-11-02.md yelpuenteJSONv2 probado
CELLNN_INFRA_CONDICIONES_NO_INICIADAS_2026-11-02.md, sin cambios de método,
pesos,blue128/INTER_LINEAR,CLAHE/gamma,red20pasos,6LBP768,MLP400/params/seed42,
presupuesto10000maxiter,cronómetro,predict_proba,tolerancias yfallosterminales.
Clases de salida se ajustan al conjunto canónico de entrenamiento, no altest.
No modificar receta segúnF1 observado; no tocarFMD42/f0requires_review.

Extensiones por separado, condiciones NUNCA ejecutadas para LBP+dCellNN:

| Dataset | Condiciones | Train/test | Llamadas externas |
|---|---:|---|---:|
| CUReT | 2direccionesseed42 | 2806/2806cadauna | 5612 |
| DTD | 10oficialesseed42 | train+valpurged histórico/1880 | 18800 |
| Outex13Official1360 | 1oficialseed42 | 680/680 | 680 |
| SoilOriginal | 3semillas×5folds | índicesarchivados/227–229 | 3420 |
| KTHTIPS2b | 4muestras-testseed42 | 3564/1188 | 4752 |

No confundir OutexCellNN nuncaejecutado conintentoHyTexOutexrequires_review;
este último permanece intacto yno se repite. Leer solo particiones/manifiestos
normalizados depreflightsHyTex, verificar susrecibos/hash yfuentes locales,
no reutilizar features,prediccionescomoetiquetas niheads. Labels/path/hash/grupo
yorden se conservan; CSVnormalizado ya autorizado no altera imágenes.

Cada cola nueva fija fuentes,paquetes,checkpoint,headparams,particiones yargv.
Preflight debe comprobar conteos/clases/filas,disjuncióngrupos ycomplemento de
universo salvoexclusionesDTD justificadas; paridad entreheadslocales ya fijada
enfuentesreferenciadas. KTHtresmuestrastrain/unatest,porloque preservareserva
históricadecascadas ynoequivalencia conpapers1/3. DTDconserva exclusiones
de3–11filasfit,1.880test yreserva física localSVM. Outex68clases/1360filas,
Soil7/1140,CUReT61/5612,KTH11/4752,DTD47/5640. NoVisTex.

Porcada dataset,primeranuevaauditoría habilita restantes. GlobalGPUlock,
CPU2hilos durantecuatroetapas ysin benchmark/fit/extracciónconcurrentes;
timeouts7200/3600/14400/300s,window12h. Gateprimer/últimofitfeaturesexactas,
pesosstrict20tensores,clasificadorconverge enpresupuesto; errorrequiere revisión
sinretry,relajación,cambio deprecisión/método uomisión deimágenes.

Reagregar cada dataset solo alcompletar suscondiciones yllamadas,validando
probabilidades,argmax,truth,elapsed_ns/ms yrecibos/cadenas. Comparar ambosheads
locales×cincométodos conganancias ypérdidas. Hardwarecompartido yfechasdistintas,
sinclaimventajafísicaaislada,nuevainferenciaglobal nireproducción deporcentajes.
FMD14/15permanece parcial aunque secierren otrasextensiones; no mediaglobal
de seisdatasets completos. No manuscrito/commits/push/descargasgrandes.
