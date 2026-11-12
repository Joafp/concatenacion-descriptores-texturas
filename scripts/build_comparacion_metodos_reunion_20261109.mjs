import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const runtime='C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1105-1297-0_26.1105.1297.0_x64__3k8sg7r9htsxt/dependencies';
process.env.RUNTIME_NODE_MODULES=runtime+'/node/node_modules';
const skill='C:/Users/Joaquin/.codex/plugins/cache/openai-primary-runtime/presentations/26.1105.12137/skills/presentations';
const {Presentation,PresentationFile}=await import(pathToFileURL(runtime+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs').href);
const {finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs').href);
const repo=process.cwd();
const root='C:/Users/Joaquin/.codex/visualizations/2026/09/13/01a09d22-3321-7303-ade7-e5e03ee40e8b/reunion_metodos_20261109_v3';
const build=path.join(root,'build'),out=path.join(root,'output');
await fs.mkdir(build,{recursive:true}); await fs.mkdir(out,{recursive:true});
function csv(text){const lines=text.trim().split(/\r?\n/); const head=lines.shift().split(',');return lines.map(line=>Object.fromEntries(line.split(',').map((v,i)=>[head[i],v])));}
const rows=csv(await fs.readFile(path.join(repo,'results/analysis/reconciliation_full_panel_20261104_v1/comparison_by_dataset.csv'),'utf8'));
const scab=csv(await fs.readFile(path.join(repo,'results/exploratory/sota_timing/timing_all.csv'),'utf8'));
const p=Presentation.create({slideSize:{width:1280,height:720}});
const C={navy:'#10253D',ink:'#13243A',muted:'#516276',teal:'#087F8C',white:'#FFFFFF',warn:'#985B07'};
function box(s,t,x,y,w,h,size=25,color=C.ink,bold=false){let q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{style:'solid',fill:'none',width:0}});q.text=t;q.text.style={fontFamily:'Arial',fontSize:size,color,bold};return q;}
function page(title,sub=''){let s=p.slides.add();s.background.fill=C.white;box(s,title,60,38,1160,63,37,C.navy,true);if(sub)box(s,sub,62,108,1150,40,19,C.muted);return s;}
function note(s,text){s.speakerNotes.text=text;}
function table(s,values,x,y,w,h,widths,size=20){const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({textStyle:{fontFamily:'Arial',fontSize:size,color:C.ink},borders:{style:'solid',fill:'#DCE6E9',width:1}});t.cells.block({row:0,column:0,rowCount:1,columnCount:values[0].length}).assign({fill:C.navy,textStyle:{fontFamily:'Arial',fontSize:size,color:C.white,bold:true}});}
function fmt(v,d){let n=Number(v);if(!Number.isFinite(n))throw Error('Invalid numeric value '+v);return n.toFixed(d).replace('.',',');}
let s=p.slides.add();s.background.fill=C.navy;box(s,'Comparación de métodos de textura',72,172,1120,134,49,C.white,true);box(s,'F1 y tiempo de inferencia en seis datasets',74,330,1000,52,27,'#B7E0E0');box(s,'Reunión de tesis  ·  9 de noviembre de 2026',74,560,1000,40,20,'#DFE8EF');
note(s,'Fuente general: results/analysis/reconciliation_full_panel_20261104_v1/INFORME.md. El título final de tesis queda por confirmar.');
s=page('Cómo combinan descriptores los métodos propios','Cinco estrategias, evaluadas con SVM y ResMLP');
box(s,'Completa-22',70,165,240,40,26,C.teal,true);box(s,'Concatena los 22 bloques disponibles.',330,165,860,48,25);
box(s,'Top-4',70,240,240,40,26,C.teal,true);box(s,'Selecciona cuatro bloques y los concatena.',330,240,860,48,25);
box(s,'Ens. diversidad',70,315,240,40,26,C.teal,true);box(s,'Combina predicciones de subconjuntos diversos.',330,315,860,58,25);
box(s,'Ens. tómbola',70,390,240,40,26,C.teal,true);box(s,'Combina predicciones de subconjuntos sorteados.',330,390,860,58,25);
box(s,'Adaptativa',70,465,240,40,26,C.teal,true);box(s,'Empieza con una base y agrega bloques si hace falta.',330,465,860,68,25);
box(s,'Los bloques incluyen representaciones profundas y descriptores clásicos.',70,613,1100,35,19,C.muted);
note(s,'Fuente: docs/fsc_tex/INFORME_REUNION_PROFESOR_2026-11-09.md y decisiones congeladas del panel. La selección adaptativa depende de la política y condición.');
s=page('Cómo combinan información los papers','Implementaciones locales adaptadas al panel común');
box(s,'Neshov',70,162,235,42,26,C.teal,true);box(s,'Agrega representaciones de capas de BEiTv2 y clasifica con MLP.',315,162,885,66,24);
box(s,'HyTexNet',70,253,235,42,26,C.teal,true);box(s,'Concatena el descriptor de textura HyTex con rasgos de DenseNet.',315,253,885,68,24);
box(s,'6LBP+dCellNN',70,344,235,42,26,C.teal,true);box(s,'Combina LBP multiescala con información de contornos dCellNN.',315,344,885,68,24);
box(s,'DeepLumina',70,435,235,42,26,C.teal,true);box(s,'Fusiona características RGB y luminancia para clasificar con SVM.',315,435,885,68,24);
box(s,'Son adaptaciones; no se afirma identidad completa con el código original.',70,612,1100,40,20,C.warn,true);
note(s,'Fuentes: results/analysis/paper_code_availability_20261103_v1/INFORME.md y docs/fsc_tex/PROTOCOLO_DEEPLUMINA_ADAPTACION_FMD_2026-11-03.md. Variantes locales: Neshov 12 capas; HyTex DenseNet congelado. DeepLumina requiere revisión.');
const datasets=[['FMD','FMD'],['CUReT','CUReT'],['Outex13Official1360','Outex-13'],['SoilOriginal','Soil'],['KTHTIPS2b','KTH-TIPS2b'],['DTD','DTD']];
const own=[['Completa-22','Completa-22'],['Top-4','Top-4'],['Ens-diversidad','Ens. diversidad'],['Ens-tombola','Ens. tómbola'],['Adaptive-selection-margin','Adaptativa']];
const tableSlides=[];
for(const [id,label] of datasets){
  s=page(label+': resultados y tiempo de inferencia','Macro-F1 medio y milisegundos por llamada individual');tableSlides.push(p.slides.items.length);
  let a=[['Método propio','Clasif.','F1','ms']];
  for(const [method,display] of own)for(const clf of ['svm','resmlp']){
    let matches=rows.filter(r=>r.dataset===id&&r.local_method===method&&r.classifier===clf&&r.reference_method==='Neshov');
    if(matches.length!==1)throw Error(`Expected one local row ${id}/${method}/${clf}, got ${matches.length}`);
    let r=matches[0];a.push([display,clf==='svm'?'SVM':'ResMLP',fmt(r.local_mean_split_f1,4),fmt(r.local_mean_ms,2)]);
  }
  let b=[['Adaptación','F1','ms']];
  for(const [method,display] of [['Neshov','Neshov'],['HyTex','HyTexNet'],['CellNN','6LBP+dCellNN'],['DeepLumina','DeepLumina †']]){
    let matches=rows.filter(r=>r.dataset===id&&r.local_method==='Adaptive-selection-margin'&&r.classifier==='svm'&&r.reference_method===method);
    if(method==='DeepLumina'&&id==='DTD'){if(matches.length!==0)throw Error('DTD unexpected full coverage');b.push([display,'9/10','—']);continue;}
    if(matches.length!==1)throw Error(`Expected one comparator ${id}/${method}, got ${matches.length}`);
    b.push([display,fmt(matches[0].reference_mean_split_f1,4),fmt(matches[0].reference_mean_ms,2)]);
  }
  table(s,a,58,177,660,405,[272,125,130,133],19);
  table(s,b,746,177,480,211,[260,110,110],19);
  box(s,'† DeepLumina: bajo revisión por convergencia.',747,415,480,67,18,C.warn,true);
  box(s,'Mismas imágenes; tiempos medidos en fechas distintas y con hardware compartido.',59,616,1155,34,17,C.muted);
  box(s,id==='DTD'?'DTD: DeepLumina incompleto (9/10). Se conserva la reserva de medición local.':id==='KTHTIPS2b'?'KTH: mantener la reserva de reconciliación del protocolo histórico.':'Adaptaciones locales: los resultados no son porcentajes publicados por los papers.',59,658,1155,32,17,C.muted);
  note(s,`Fuente: results/analysis/reconciliation_full_panel_20261104_v1/comparison_by_dataset.csv, dataset ${id}; informe de reconciliación y reservas del 04-11. F1 y tiempo de las mismas llamadas. DeepLumina 46/46 condiciones terminadas con avisos.`);
}
s=page('Scabini: resultados exploratorios','Tiempos por imagen en lotes de 32, otra GPU; no comparables directamente con batch=1');
const sc=[['Dataset','Macro-F1 medio*','ms / imagen**']];
for(const [id,label] of [['FMD','FMD'],['KTHTIPS2b','KTH-TIPS2b'],['DTD','DTD'],['Outex13Official1360','Outex-13']]){
  const r=scab.filter(r=>r.dataset===id&&r.method==='scabini'&&r.classifier==='media3');if(r.length!==1)throw Error('Missing Scabini '+id);
  sc.push([label,fmt(r[0].macro_f1,4),fmt(r[0].predict_ms_without_reading,2)]);
}
table(s,sc,75,185,1080,290,[360,340,380],24);tableSlides.push(p.slides.items.length);
box(s,'* Promedio de KNN, LDA y SVM; FMD usa 10×10, no el split del panel propio.',75,518,1110,55,20,C.muted);
box(s,'** Costo amortizado por imagen sin lectura, no latencia individual online.',75,587,1110,55,20,C.warn,true);
note(s,'Fuente: results/exploratory/sota_timing/timing_all.csv y README.md. Métricas y tiempos obtenidos por componentes separados; FMD comparadores y métodos propios usan distintos folds.');
s=page('Qué muestran las comparaciones');
box(s,'FMD: Adaptativa SVM consigue más F1 que Neshov, con mayor tiempo medio.',72,158,1110,85,28);
box(s,'Soil: Top-4 SVM queda ligeramente por debajo de Neshov y tarda más.',72,270,1110,85,28);
box(s,'La estrategia completa, la selección y los ensambles tienen costos distintos.',72,385,1110,85,28);
box(s,'DeepLumina requiere revisión y DTD está incompleto. Hay reservas en KTH y Outex.',72,505,1110,84,25,C.warn,true);
note(s,'Fuentes: comparación por dataset auditada, informe del 04-11 y AVANCE_OUTEX_HUELLAS_2026-11-09.md. No se afirma significación ni dominancia universal.');
for(let i=0;i<p.slides.items.length;i++){let b=await p.export({slide:p.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await b.arrayBuffer()));}
const candidate=path.join(build,'candidate.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
const final=path.join(out,'Comparacion_metodos_6_datasets_v3.pptx');
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:final,pythonExecutable:runtime+'/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...tableSlides.flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:tableSlides,fontPolicy:{basis:'design',families:['Arial']},receiptPath:path.join(build,'validation.json'),verifyArtifactToolImport:true});
const dest=path.join(repo,'results/presentation_reunion_20261109/Comparacion_metodos_6_datasets_v3.pptx');await fs.copyFile(final,dest,(await import('node:fs')).constants.COPYFILE_EXCL);console.log(JSON.stringify({dest,slides:p.slides.items.length,validation:result.presentationLayout}));
