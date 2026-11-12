import fs from 'node:fs/promises';
import path from 'node:path';
const original=await fs.readFile('results/analysis/weekly_presentation_20261102_v1/build.mjs','utf8');
const insertion=String.raw`
const methods=['Adaptive-selection-margin','Top-4','Ens-diversidad','Ens-tombola','Completa-22'];
for(const head of ['svm','resmlp']){
 for(const metric of ['mean_split_macro_f1','mean_ms_all_calls']){
  const timing=metric==='mean_ms_all_calls';
  s=slide((timing?'Tiempo medio':'Macro-F1')+' de las cinco estrategias: '+(head==='svm'?'SVM':'ResMLP'),timing?'Milisegundos por llamada individual, menor es mejor':'Media por partición, mayor es mejor',sources+'\nTablas completas de seis datasets y cinco estrategias. Datos descriptivos. Hardware compartido y fechas distintas. DTD/SVM conserva reserva física. KTH 3 muestras train / 1 test. La latencia media no es un máximo garantizado.');
  const matrix=[['Dataset','Adaptativo','Top-4','Diversidad','Tómbola','Completa-22'],...keys.map((ds,i)=>[labels[i].replace('*',head==='svm'?'*':''),...methods.map(m=>fmt(find(ds,head,m)[metric],timing?2:4))])];
  const t=table(s,matrix,[232,184,184,184,184,184],190,360,23);
  for(let r=1;r<matrix.length;r++){
   const ds=keys[r-1], vals=methods.map(m=>Number(find(ds,head,m)[metric]));
   const best=timing?Math.min(...vals):Math.max(...vals);
   vals.forEach((v,c)=>{if(v===best){t.getCell(r,c+1).fill='#E3F0EE';t.getCell(r,c+1).text.style={typeface:font,fontSize:23,bold:true,color:teal};}});
  }
  text(s,timing?'El adaptativo tiene el menor tiempo medio observado en los seis datasets.':'La estrategia con mayor F1 cambia según el dataset y el clasificador.',64,575,1120,58,25,teal,true);
  text(s,'Resaltado: mejor valor sin redondear en cada fila. '+(head==='svm'?'* DTD conserva reserva física.':'Sin prueba de significancia estadística.'),64,632,1120,30,19,muted);
 }
}
s=slide('Fidelidad de los sistemas externos al paper','Alcance de las adaptaciones',sources+'\nFuentes: docs/fsc_tex/PROTOCOLO_HYTEX_ADAPTACION_FMD_2026-11-02.md y PROTOCOLO_CELLNN_ADAPTACION_FMD_2026-11-02.md. No atribuir parámetros locales a los autores.');
table(s,[['Sistema','Qué conservamos','Diferencias o límites'],['HyTexNet adaptado','Arquitectura de fusión: descriptor local y DenseNet con cabeza clasificadora.','Preprocesamiento y entrenamiento locales. Backbone congelado. Mismo checkpoint de autores sin verificar.'],['LBP+dCellNN adaptado','Código y pesos compatibles de autores. Contornos, seis histogramas LBP y MLP. Paridad comprobada.','Panel común y parámetros locales explícitos del clasificador. Sin reproducción de porcentajes publicados.']],[240,430,482],190,350,23);
text(s,'Ambos son sistemas completos adaptados. La comparación no reproduce los porcentajes originales.',64,570,1120,70,26,amber,true);
`;
const anchor="s=slide('Dos sistemas adaptados; ninguno cierra aún los seis datasets'";
if(!original.includes(anchor))throw new Error('Expected insertion point absent');
let updated=original.replace(anchor,insertion+'\n'+anchor)
 .replace("weekly_presentation_20261102_v1'), build=", "weekly_presentation_20261102_v2'), build=")
 .replace("Avance_semanal_tesis_2026-11-02.pptx", "Avance_semanal_tesis_2026-11-02_comparacion_completa.pptx")
 .replace('Tiempo medio menor frente a Completa-22 en los 12 pares dataset × cabeza.','Menor tiempo medio entre las cinco estrategias en los 12 pares dataset × cabeza.');
await import('data:text/javascript;base64,'+Buffer.from(updated).toString('base64'));
const src=path.join(process.cwd(),'results/analysis/weekly_presentation_20261102_v2/deliverables/Avance_semanal_tesis_2026-11-02_comparacion_completa.pptx');
const windows='C:/Users/Joaquin/Downloads/Tesis_reunion_2026-11-02/Avance_semanal_tesis_comparacion_completa_v2.pptx';
await fs.copyFile(src,windows);
if(!Buffer.from(await fs.readFile(src)).equals(Buffer.from(await fs.readFile(windows))))throw new Error('Windows copy mismatch');
console.log('WINDOWS_DELIVERY='+windows);
