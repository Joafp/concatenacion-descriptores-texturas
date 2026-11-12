import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const runtime = 'C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1105-1297-0_26.1105.1297.0_x64__3k8sg7r9htsxt/dependencies';
process.env.RUNTIME_NODE_MODULES = runtime + '/node/node_modules';
const skill = 'C:/Users/Joaquin/.codex/plugins/cache/openai-primary-runtime/presentations/26.1105.12137/skills/presentations';
const { Presentation, PresentationFile } = await import(pathToFileURL(runtime + '/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs').href);
const { finalizePresentation } = await import(pathToFileURL(skill + '/container_tools/artifact_tool_utils.mjs').href);
const repoRoot = process.cwd();
const root = 'C:/Users/Joaquin/.codex/visualizations/2026/09/13/01a09d22-3321-7303-ade7-e5e03ee40e8b/reunion_20261109';
const build = path.join(root, '.codex_reunion_20261109');
const out = path.join(root, 'results', 'presentation_reunion_20261109');
await fs.mkdir(build, {recursive:true});
await fs.mkdir(out, {recursive:true});
await fs.mkdir(path.join(repoRoot,'results','presentation_reunion_20261109'), {recursive:true});
const p = Presentation.create({slideSize:{width:1280,height:720}});
const C = {ink:'#13243A', navy:'#10253D', teal:'#087F8C', muted:'#516276', light:'#E8F2F2', white:'#FFFFFF', amber:'#9A5C07'};
function box(s,t,x,y,w,h,size=26,color=C.ink,bold=false) {
  const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{style:'solid',fill:'none',width:0}});
  q.text=t; q.text.style={fontFamily:'Arial',fontSize:size,color,bold}; return q;
}
function page(title, subtitle='') {
  const s=p.slides.add(); s.background.fill=C.white;
  box(s,title,68,48,1144,68,39,C.navy,true);
  if(subtitle) box(s,subtitle,70,123,1120,42,20,C.muted);
  return s;
}
function note(s,t){s.speakerNotes.text=t;}
let s=p.slides.add(); s.background.fill=C.navy;
box(s,'Avances de tesis',76,170,1080,90,57,C.white,true);
box(s,'Reunión con el profesor',78,277,1040,50,30,'#B7E0E0');
box(s,'Resultados de la semana  •  9 de noviembre de 2026',78,537,1000,40,21,'#DFE8EF');
note(s,'Fuente: docs/fsc_tex/INFORME_REUNION_PROFESOR_2026-11-09.md. El título aprobado de la tesis está pendiente de confirmación.');

s=page('Esta semana: panel cerrado y comparaciones auditadas');
box(s,'94 / 94',75,165,430,85,64,C.teal,true); box(s,'condiciones del panel propio',75,253,520,42,24,C.ink);
box(s,'6 datasets',720,165,450,80,54,C.navy,true); box(s,'FMD, CUReT, Outex, Soil, KTH y DTD',720,253,490,70,23,C.ink);
box(s,'Se reconstruyeron 1.780 comparaciones por condición y 230 por dataset.',75,375,1100,76,27,C.ink);
box(s,'Las adaptaciones de Neshov, HyTexNet y 6LBP+dCellNN cubren 47/47 condiciones cada una.',75,476,1100,83,25,C.ink);
note(s,'Fuente: results/analysis/reconciliation_full_panel_20261104_v1/INFORME.md y docs/fsc_tex/PLAN_MAESTRO_ACTUALIZADO_2026-11-04.md. Las filas de comparación no son datasets independientes.');

s=page('Seis datasets: F1 y tiempo por imagen','Política adaptativa con SVM frente a Neshov adaptado');
const values=[['Dataset','F1 adaptativa','F1 Neshov','ms adapt. / Neshov'],['DTD','0,86686','0,80203','54,35 / 16,79'],['FMD','0,97760','0,94213','38,63 / 16,89'],['CUReT','0,99840','0,99396','36,83 / 14,27'],['Outex-13','0,92758','0,91930','40,33 / 14,61'],['Soil','0,87254','0,86310','38,48 / 19,17'],['KTH-TIPS2b','0,93900','0,92448','30,95 / 16,48']];
const t=s.tables.add({rows:7,columns:4,left:70,top:184,width:1130,height:345,values,columnWidths:[260,220,220,430]});
t.cells.block({row:0,column:0,rowCount:7,columnCount:4}).assign({textStyle:{fontFamily:'Arial',fontSize:23,color:C.ink},borders:{style:'solid',fill:'#DBE4E9',width:1}});
t.cells.block({row:0,column:0,rowCount:1,columnCount:4}).assign({fill:C.navy,textStyle:{fontFamily:'Arial',fontSize:21,color:C.white,bold:true}});
box(s,'Macro-F1 medio por condición; tiempos de llamadas individuales, medidos en fechas distintas.',72,562,1120,60,18,C.muted);
box(s,'DTD y KTH conservan reservas de medición y protocolo.',72,620,1120,35,18,C.muted);
note(s,'Fuente: docs/fsc_tex/PROPUESTA_GUION_Y_TABLERO_VERIFICADO_2026-11-04.md. Tiempos descriptivos; hardware compartido y fechas diferentes.');

s=page('La ganancia de F1 puede costar más tiempo','Ejemplo en FMD');
box(s,'0,97760',86,190,430,76,60,C.teal,true);box(s,'F1 adaptativa SVM',88,275,470,40,24,C.ink);
box(s,'0,94213',750,190,430,76,60,C.navy,true);box(s,'F1 Neshov adaptado',752,275,460,40,24,C.ink);
box(s,'38,63 ms',86,365,430,65,47,C.teal,true);box(s,'16,89 ms',750,365,430,65,47,C.navy,true);
box(s,'Diferencia observada: +0,03547 F1 y +21,74 ms para la adaptativa.',86,502,1100,64,25,C.ink);
box(s,'Tiempos descriptivos, medidos en momentos distintos.',86,605,1100,34,19,C.muted);
note(s,'Fuente: results/analysis/reconciliation_full_panel_20261104_v1/INFORME.md. No se afirma significación ni superioridad universal.');

s=page('Las comparaciones también muestran pérdidas');
box(s,'Soil  ·  Top-4 con SVM frente a Neshov',75,150,1100,48,27,C.muted);
box(s,'0,85940',75,235,480,82,58,C.navy,true); box(s,'Top-4: macro-F1',75,323,470,42,23,C.ink);
box(s,'0,86310',740,235,430,82,58,C.teal,true); box(s,'Neshov: macro-F1',740,323,430,42,23,C.ink);
box(s,'70,98 ms frente a 19,17 ms',75,438,1040,59,34,C.ink,true);
box(s,'La diferencia de F1 es −0,00370 para Top-4. No demuestra significación estadística.',75,545,1100,72,22,C.muted);
note(s,'Fuente: docs/fsc_tex/PROPUESTA_GUION_Y_TABLERO_VERIFICADO_2026-11-04.md. Tiempos descriptivos, no simultáneos.');

s=page('Comparación con los papers','Resultados aproximados; las recetas y los protocolos no son idénticos');
box(s,'Neshov  ·  FMD 10×10',75,170,620,40,27,C.navy,true);
box(s,'94,22 % de accuracy frente a 96,7 % publicado',75,217,1050,52,29,C.ink);
box(s,'HyTexNet  ·  KTH',75,310,620,40,27,C.navy,true);
box(s,'Carlos informa 98,7 % en una aproximación al paper y 85,0 % con muestra física separada.',75,360,1090,86,26,C.ink);
box(s,'Scabini: valores cercanos a los publicados en cuatro datasets, según el estudio de Carlos.',75,496,1100,80,24,C.ink);
box(s,'Cercanía numérica no confirma por sí sola una reproducción fiel.',75,620,1100,34,19,C.muted);
note(s,'Fuentes: results/analysis/neshov_paperlike_fmd_10x10_consolidated_20261103_v1/INFORME.md; results/exploratory/sota_timing/README.md; docs/fsc_tex/CONCILIACION_CARLOS_SOTA_TIMING_2026-11-08.md. Accuracy y macro-F1 son métricas diferentes.');

s=page('Trabajo de Carlos y estado de Outex');
box(s,'Carlos incorporó Scabini y midió extracción y entrenamiento en cuatro datasets.',75,156,1100,75,27,C.ink);
box(s,'Sus tiempos por imagen provienen de lotes de 32 en otra GPU.',75,254,1100,62,27,C.ink);
box(s,'Outex: se señalaron cinco filas de ViT y DeiT para verificación.',75,357,1100,62,27,C.ink);
box(s,'El panel usó un DeiT regenerado; el ViT normalizado coincide con el registro del panel.',75,451,1100,86,26,C.ink);
box(s,'La alerta y su posible impacto siguen bajo revisión.',75,603,1100,38,20,C.amber,true);
note(s,'Fuentes: docs/fsc_tex/AVANCE_OUTEX_HUELLAS_2026-11-09.md y TRAZABILIDAD_OUTEX_CARLOS_2026-11-08.md. Coincidir por hash no confirma origen ni cuantifica impacto.');

s=page('Pendientes para acordar con el profesor');
box(s,'1. Mensaje principal: equilibrio entre F1 y tiempo, con ganancias y pérdidas.',75,155,1100,82,27,C.ink);
box(s,'2. DeepLumina: revisar convergencia y una condición faltante en DTD.',75,265,1100,75,27,C.ink);
box(s,'3. Outex: definir el alcance de una verificación independiente.',75,370,1100,75,27,C.ink);
box(s,'4. Acordar el grado de fidelidad exigido a las réplicas y el título final.',75,475,1100,78,27,C.ink);
box(s,'No se repitieron los paneles cerrados ni se modificó la tesis.',75,617,1100,35,19,C.muted);
note(s,'Fuente: docs/fsc_tex/INFORME_REUNION_PROFESOR_2026-11-09.md. DeepLumina: avisos en 46 condiciones y DTD 9/10.');

for(let i=0;i<p.slides.items.length;i++){
  let blob=await p.export({slide:p.slides.items[i],format:'png',scale:1});
  await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await blob.arrayBuffer()));
}
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(candidate);
const final=path.join(out,'Avances_tesis_reunion_2026-11-09.pptx');
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:final,
 pythonExecutable:runtime+'/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',
 layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--require-native-table-slide','3'],
 requiredNativeTableOwnerSlides:[3],fontPolicy:{basis:'design',families:['Arial']},
 receiptPath:path.join(build,'validation.json'),verifyArtifactToolImport:true});
const destination=path.join(repoRoot,'results','presentation_reunion_20261109','Avances_tesis_reunion_2026-11-09.pptx');
await fs.copyFile(final,destination, (await import('node:fs')).constants.COPYFILE_EXCL);
console.log(JSON.stringify({destination,result}));
