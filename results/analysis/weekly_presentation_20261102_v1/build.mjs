import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import os from 'node:os';
import {pathToFileURL} from 'node:url';
const runtime='C:/Users/Joaquin/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const skill='C:/Users/Joaquin/.codex/plugins/cache/openai-primary-runtime/presentations/26.1026.10807/skills/presentations';
const {Presentation,PresentationFile}=await import(pathToFileURL(runtime+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs'));
const {resolvePresentationFont,finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs'));
const root=process.cwd(), out=path.join(root,'results/analysis/weekly_presentation_20261102_v1'), build=path.join(out,'.build'), deliver=path.join(out,'deliverables');
await fs.mkdir(build,{recursive:true});await fs.mkdir(deliver,{recursive:true});
const font=resolvePresentationFont();
const ownPath='results/analysis/blocker_resolution_20261101/full_panel_online_v1/dataset_summary.csv';
const extPath='results/analysis/external_adaptation_coverage_20261102_v1/coverage.csv';
const parse=s=>{const [h,...rows]=s.trim().split(/\r?\n/).map(r=>r.split(','));return rows.map(r=>Object.fromEntries(h.map((k,i)=>[k,r[i]])));};
const own=parse(await fs.readFile(path.join(root,ownPath),'utf8')), ext=parse(await fs.readFile(path.join(root,extPath),'utf8'));
const keys=['FMD','CUReT','DTD','Outex13Official1360','SoilOriginal','KTHTIPS2b'];
const labels=['FMD','CUReT','DTD*','Outex-13','Soil','KTH-TIPS2b'];
const find=(ds,head,m)=>own.find(r=>r.dataset===ds&&r.classifier===head&&r.method===m);
const fmt=(v,n=2)=>Number(v).toFixed(n);
const p=Presentation.create({slideSize:{width:1280,height:720}});
const navy='#112D3C', ink='#183642', muted='#526A75', teal='#007D7A', bg='#F7F9FA', amber='#8C4D16';
const tableOwners=[];
function text(s,str,x,y,w,h,size=26,color=ink,bold=false){const t=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});t.text=str;t.text.style={typeface:font,fontSize:size,color,bold};return t;}
function slide(title,kicker,notes){const s=p.slides.add();s.background.fill=bg;text(s,kicker.toUpperCase(),64,32,1152,30,18,teal,true);text(s,title,64,83,1152,97,40,navy,true);text(s,'AVANCE SEMANAL · CORTE 02 NOV 2026',64,670,1000,25,15,muted);text(s,String(p.slides.items.length),1160,665,55,30,20,muted);s.speakerNotes.text=notes;return s;}
function table(s,values,widths,top=190,height=370,size=23){tableOwners.push(p.slides.items.length);const t=s.tables.add({rows:values.length,columns:values[0].length,left:64,top,width:1152,height,columnWidths:widths,values});t.styleOptions={headerRow:true,bandedRows:false};t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({fill:'#FFFFFF',textStyle:{typeface:font,fontSize:size,color:ink},margins:{left:14,right:10,top:9,bottom:8}});for(let c=0;c<values[0].length;c++){t.getCell(0,c).fill=navy;t.getCell(0,c).text.style={typeface:font,fontSize:size,color:'#FFFFFF',bold:true};}t.borders.assign({fill:'#D9E2E5',width:1,style:'solid'});return t;}
const sources=`Fuentes locales (rutas relativas a /home/joaquin/tesis_claude):\n${ownPath}\n${extPath}\nresults/analysis/blocker_resolution_20261101/full_panel_online_v1/coverage.json\nresults/analysis/external_adaptation_coverage_20261102_v1/provenance.json`;
let s=slide('Panel local cerrado.\nComparación externa en ampliación.','Tesis · resultados y trabajo de la semana',sources+'\nApertura: cerramos la evaluación física de nuestras estrategias. La comparación externa avanza con adaptaciones completas de sistemas, no réplicas fieles de sus porcentajes publicados.');
text(s,'94 / 94',64,225,560,125,88,teal,true);text(s,'condiciones locales auditadas',64,355,700,50,32,ink,true);text(s,'6 datasets · 2 clasificadores · 5 estrategias evaluadas',64,442,1152,52,29,ink);text(s,'Dos sistemas externos adaptados: cinco datasets completos cada uno.\nTodavía no corresponde afirmar superioridad frente a los papers.',64,540,1120,85,25,muted);
s=slide('La pregunta: ¿cuándo vale la pena extraer más?','Propuesta y protocolo',sources+'\nSelección OOF sobre entrenamiento. Base escogida en entrenamiento, no una red base universal. El margen decide el rescate condicional. La diversidad genera candidatos y sirve de referencia. No presentar cada componente como novedoso.');
text(s,'Una representación base clasifica la imagen.',64,200,1120,55,32,ink,true);text(s,'Si el margen es insuficiente, se activa un rescate con más representaciones.',64,282,1120,95,30);text(s,'La selección se congela antes de medir; las extracciones compartidas se cuentan una vez.',64,397,1120,95,28);text(s,'Referencias internas: Completa-22 · Top-4 · Ens-diversidad · Ens-tómbola',64,535,1120,65,25,teal,true);text(s,'B60 es un presupuesto del modelo de selección, no una garantía de latencia por imagen.',64,610,1120,44,21,amber);
s=slide('Del costo proyectado a la medición física','Qué quedó cerrado esta semana',sources+'\nNo sumar las llamadas adicionales a las primarias como si fueran nuevas condiciones. Sin aislamiento físico de hardware. Sin inferencia global. Las cinco estrategias son evaluadas, no cinco propuestas novedosas.');
table(s,[['Alcance','Cierre verificado'],['Datasets / cabezas','6 / SVM y ResMLP'],['Particiones / condiciones','47 / 94'],['Estrategias / filas totales','5 / 470 condición × método'],['Llamadas primarias auditadas','362.640'],['Observaciones adicionales DTD','9.400 — separadas de las primarias']],[540,612],185,365,25);
text(s,'Macro-F1 y tiempo obtenidos de las mismas llamadas online individuales: archivo → clase.',64,580,1120,67,25,teal,true);
for(const head of ['svm','resmlp']){
 s=slide(`Adaptativo vs. Completa-22 · ${head==='svm'?'SVM':'ResMLP'}`,'Resultados propios · descripción, no prueba estadística',sources+'\nF1 en escala 0–1, promedio de macro-F1 de particiones. Tiempo: media de todas las llamadas individuales. Las dos agregaciones no son equivalentes. DTD conserva reserva física y observaciones adicionales separadas. KTH: partición física 3 muestras train / 1 test; sin reclamar equivalencia histórica de cascada.');
 const vals=[['Dataset','F1 adapt.','F1 completa','ms adapt.','ms completa'],...keys.map((ds,i)=>{const a=find(ds,head,'Adaptive-selection-margin'),b=find(ds,head,'Completa-22');return [labels[i],fmt(a.mean_split_macro_f1,4),fmt(b.mean_split_macro_f1,4),fmt(a.mean_ms_all_calls),fmt(b.mean_ms_all_calls)];})];
 table(s,vals,[270,215,215,215,237],190,360,24);
 text(s,'Menor tiempo medio en las seis comparaciones; la ganancia de F1 no es universal.',64,573,1120,54,26,teal,true);text(s,'* DTD mantiene reserva de medición física. F1: media por partición; ms: media por llamada.',64,630,1120,30,19,muted);
}
s=slide('Dos sistemas adaptados; ninguno cierra aún los seis datasets','Comparación externa · cobertura sin ocultar pendientes',sources+'\nValores F1 / ms. Comparación local bajo protocolo común, no reproducción de porcentajes publicados. HyTexNet integra descriptor local y DenseNet; LBP+dCellNN integra contornos, histogramas y clasificador. FMD CellNN 14/15: deliberadamente sin media de dataset.');
table(s,[['Dataset','HyTexNet adaptado · F1 / ms','LBP+dCellNN adaptado · F1 / ms'],...keys.map((ds,i)=>{return [labels[i].replace('*',''),...['HyTexNet adapted','LBP+dCellNN adapted'].map(m=>{const r=ext.find(v=>v.dataset===ds&&v.method===m);return r.full_dataset_complete==='True'?`${fmt(r.mean_split_macro_f1,4)} / ${fmt(r.mean_ms_all_calls)}`:m.startsWith('Hy')?'0/1 · requiere revisión':'14/15 · sin media completa';})];})],[240,456,456],190,360,23);
text(s,'Cada sistema: 46/47 condiciones. No se calcula una media global del panel incompleto.',64,576,1120,52,25,teal,true);text(s,'Son adaptaciones de sistemas completos; no prueba de superar los resultados originales de los papers.',64,632,1120,30,19,amber);
s=slide('El hallazgo es un compromiso, no “ganar en todo”','Lectura correcta de los resultados',sources+'\nEjemplo FMD SVM: adaptativo F1 .9776005, media 38.6298 ms, mediana 13.77 ms, p95 270.77 ms. Completa-22 F1 .9650718 y media 1759.5008 ms. Ejemplo KTH SVM: adaptativo .9389965 vs completa .9599280. Sin inferencia estadística ni causal.');
text(s,'Tiempo medio menor frente a Completa-22 en los 12 pares dataset × cabeza.',64,195,1120,92,31,teal,true);text(s,'Pero hay pérdidas de F1: por ejemplo, KTH/SVM baja de 0,9599 a 0,9390.',64,310,1120,90,29,ink,true);text(s,'La cola importa: FMD/SVM adaptativo tiene media 38,63 ms y p95 ≈270,77 ms.',64,425,1120,90,28);text(s,'Las diferencias frente a sistemas externos adaptados describen esta implementación y este protocolo; no equivalen a superar la literatura.',64,540,1120,90,25,amber);
s=slide('Tres bloqueos conservan evidencia y no se reintentan','Pendientes relevantes',sources+'\nFuentes: results/analysis/hytex_outex_external_queue_20261102_v1; results/analysis/cellnn_fmd_external_queue_20261102_v1; results/analysis/neshov_fmd_external_queue_20261102_v1. Sin workers experimentales activos en el último chequeo. Presentar causas distintas, no mezclar infraestructura con fallo científico.');
table(s,[['Caso','Motivo / estado'],['HyTexNet · Outex','Preflight: falta checkpoint_sha256. 0 llamadas.'],['LBP+dCellNN · FMD 42/f0','Serialización tras fit. 0 llamadas online.'],['Neshov · FMD','Paridad batch 1/8 fuera de tolerancia: requiere revisión.']],[370,782],200,265,24);
text(s,'No se relajaron tolerancias ni se reemplazaron los intentos fallidos.',64,500,1120,60,27,teal,true);text(s,'Límites: hardware compartido · reservas DTD/KTH · sin inferencia global\nSin repetición del panel propio ni cambios al manuscrito.',64,583,1120,66,23,muted);
s=slide('Lo que podemos defender hoy — y lo que sigue','Cierre y próximos pasos',sources+'\nNo prometer cierre de todos los papers ni pedir permiso implícito para repetir fallos. Próximos pasos sujetos a las reglas de revisión existentes. Se requiere receta verificable para cada sistema externo antes de medir.');
text(s,'Hoy: un panel propio completo, trazable y con costos físicos medidos.',64,195,1120,90,32,teal,true);text(s,'También: dos comparadores externos adaptados con cobertura explícita y resultados parciales identificados.',64,308,1120,100,29);text(s,'Sigue: resolver revisiones sin alterar el método; cerrar recetas verificables de otros papers; planificar contraste confirmatorio.',64,435,1120,110,28);text(s,'Integrar al manuscrito solo después de cerrar cobertura y validación.\nMensaje central: eficiencia observada con ganancias y pérdidas de calidad.',64,575,1120,75,26,ink,true);
const candidate=path.join(build,'candidate.pptx');await (await PresentationFile.exportPptx(p)).save(candidate);
for(let i=0;i<p.slides.items.length;i++){const b=await p.export({slide:p.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await b.arrayBuffer()));}
const finalPath=path.join(deliver,'Avance_semanal_tesis_2026-11-02.pptx');
// Windows cannot hard-link over the WSL UNC provider. Validate and publish on
// local NTFS, then copy the identical validated bytes to the task deliverables.
const localStage=await fs.mkdtemp(path.join(os.tmpdir(),'tesis-weekly-'));
await fs.mkdir(path.join(localStage,'.private'));
await fs.mkdir(path.join(localStage,'deliverables'));
const localCandidate=path.join(localStage,'candidate.pptx'),localFinal=path.join(localStage,'deliverables','final.pptx');
await fs.copyFile(candidate,localCandidate);
const result=await finalizePresentation({workspaceDir:localStage,candidatePath:localCandidate,finalPath:localFinal,pythonExecutable:runtime+'/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tableOwners.flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:tableOwners,fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,receiptPath:path.join(localStage,'.private','validation.json')});
await fs.copyFile(localFinal,finalPath);await fs.copyFile(path.join(localStage,'.private','validation.json'),path.join(build,'validation.json'));
if(!Buffer.from(await fs.readFile(localFinal)).equals(Buffer.from(await fs.readFile(finalPath))))throw new Error('Delivery copy differs from validated PPTX');
const pins=[];for(const rel of [ownPath,extPath,'results/analysis/blocker_resolution_20261101/full_panel_online_v1/coverage.json','results/analysis/external_adaptation_coverage_20261102_v1/coverage.json']){const b=await fs.readFile(path.join(root,rel));pins.push({path:rel,sha256:crypto.createHash('sha256').update(b).digest('hex')});}
await fs.writeFile(path.join(build,'sources.json'),JSON.stringify({date:'2026-11-02',font,sources:pins,slides:p.slides.items.length,finalPath},null,2));
console.log(JSON.stringify({finalPath,slides:p.slides.items.length,font,result}));
