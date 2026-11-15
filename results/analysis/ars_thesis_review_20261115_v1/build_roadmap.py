"""Transport reviewer findings into a source-ordered roadmap; no author decisions."""
from pathlib import Path
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def finding(role, number):
    text = (HERE / f"reports/{role}_phase2.md").read_text()
    return re.search(rf"(?ms)^### W{number}: (.*?)(?=^### |\Z)", text).group(1)


def evidence(text):
    value = re.search(r"\*\*Evidence Anchor\*\*:\s*([^\n]+)", text).group(1)
    kind, locator = value.split(": ", 1)
    result = {"anchor_type": kind, "locator": locator}
    if kind == "text":
        result["quote"] = " / ".join(re.findall(r'"([^"\n]+)"', locator))
    elif kind == "absence":
        where, rest = locator.split(" — expected ", 1)
        expected, checked = rest.split("; checked ", 1)
        result.update(locator=where, absence_scope=expected, check_performed=checked)
    return result


specs = [
    ("eic",1,0,"Corregir ganancia ResMLP k=4→5", "must_fix", "sentence", ["B0125"], "Corregir con las medias fuente: aproximadamente 0,2305 puntos porcentuales de accuracy; conservar unidad y precisión.", "La resta de las medias fuente coincide con la frase y la Tabla 5.3."),
    ("eic",2,0,"Corregir referencia de tabla N-gramas", "should_fix", "sentence", ["B0129"], "Apuntar a la tabla principal de accuracy y separar el complemento macro-F1 C.9.", "Las referencias del PDF conducen a la tabla descrita y no tienen etiquetas duplicadas."),
    ("eic",3,0,"Actualizar pie de latencias a las métricas actuales", "should_fix", "sentence", ["B0134"], "Explicar que los tiempos corresponden a las mismas llamadas de accuracy y macro-F1; identificar sus tablas.", "Pie y referencias identifican Tablas 5.7 y C.11 sin confundir métricas."),
    ("eic",4,0,"Reducir bitácora en resultados E1", "should_fix", "section", ["B0154"], "Conservar criterio y alcance científico; trasladar serialización y secuencia operativa al anexo D con referencia.", "La evidencia y los fallos siguen documentados y el cuerpo prioriza la interpretación."),
    ("methodology",1,0,"Expresar variación e incertidumbre de diferencias", "must_fix", "re_analysis", ["B0148"], "Con datos guardados, mostrar diferencias por condición o rangos y sensibilidad; definir unidad y población de cualquier intervalo sin independencia ficticia.", "La variación que se resume y la dependencia están justificadas; no se concluye equivalencia."),
    ("methodology",2,0,"Sensibilidad del contraste principal de accuracy sin KTH", "must_fix", "re_analysis", ["B0109","B0243"], "Recalcular los mismos pares y familia de accuracy Individual/Completa-22/Top-4 sobre cinco medias; conservar KTH archivado en su registro.", "Se muestran estimando, biblioteca, familia y cambios al excluir KTH sin sustituirlo por otra variante."),
    ("methodology",3,0,"Precisar el OOF condicionado a Top-4 archivado en E1", "must_fix", "section", ["B0073","B0147"], "Explicar que se reajusta el SVM por pliegue manteniendo el subconjunto archivado; separar selección de representación y elección de ruta.", "No se presenta ese OOF como evaluación independiente del procedimiento completo de selección."),
    ("methodology",5,0,"Delimitar la reserva Outex por resultado", "must_fix", "section", ["B0090"], "Mapear bloque, archivo, protocolo, comprobación y tablas; distinguir correspondencias verificadas de desconocidas sin presumir daño.", "Cada alerta tiene alcance identificable y enlaces de procedencia."),
    ("methodology",5,1,"Sensibilidad Outex solo si se identifica una fila afectada", "must_fix", "re_analysis", ["B0090"], "Solo si el rastreo identifica una fila principal sin identidad comprobada: marcarla no validada y ofrecer sensibilidad sin ella. Si la condición no ocurre, documentarlo y no inventar el daño.", "La precondición queda resuelta por evidencia; solo se recalcula si corresponde."),
    ("domain",1,0,"Contextualizar selección de métodos de textura de Puig et al.", "must_fix", "section", ["B0040"], "Añadir antecedente y comparar unidad de selección, objetivo y protocolo con el estudio local.", "La comparación es fiel a la fuente y no exige ejecutar el método."),
    ("domain",1,1,"Contextualizar combinación y compresión de Khan et al.", "must_fix", "section", ["B0040"], "Explicar la diferencia entre comprimir representaciones combinadas, elegir pocos extractores y activarlos por imagen.", "Fuente primaria y diferencias técnicas quedan citadas sin ampliar la novedad."),
    ("domain",2,0,"Identificar comparadores dentro del PDF", "must_fix", "section", ["B0045"], "Tabla por comparador: representación/dimensión, pesos/capa, cabeza, reparto y diferencias verificadas/no verificadas con la publicación; versión de receta.", "Las cuatro columnas externas se interpretan sin salir del PDF y conservan las etiquetas de adaptación."),
    ("perspective",1,0,"Expandir SFFS, CNN y MLP", "should_fix", "sentence", ["B0016","B0081"], "Expandir siglas y explicar la función de SFFS y la diferencia extractor/cabeza.", "Primera aparición o glosario accesible y técnicamente correcto."),
    ("perspective",2,0,"Explicar similitud coseno y alcance de fidelidad", "should_fix", "sentence", ["B0153"], "Definir comparación extraído/cacheado de una misma imagen, escala y criterio 0,999; conservar que la muestra no acredita identidad global.", "El lector interpreta el mínimo sin atribuirle validación de todas las imágenes o procedencia completa."),
]
seat = {"eic":"EIC", "methodology":"R1", "domain":"R2", "perspective":"R3"}
items = []
for idx, (role, ordinal, sub, description, obligation, cost, blocks, action, verification) in enumerate(specs, 1):
    raw = finding(role, ordinal)
    confidence = int(re.search(r"\*\*Confidence\*\*:\s*(\d)", raw).group(1))
    items.append({"id":f"REV-{idx:02d}", "source_refs":[{"seat":seat[role],"channel":"finding","ordinal":ordinal,"subclaim_ordinal":sub}],
                  "description":description,"reviewer":seat[role],"sub_claim_ids":[f"SC-{idx}"],"obligation_class":obligation,
                  "severity":"minor","severity_source":f"reports/{role}_phase2.md W{ordinal}","evidence_anchor":evidence(raw),
                  "confidence":confidence,"competence_basis":"Transported from the named reviewer finding; not a calibrated probability.",
                  "cost_scope":{"kind":cost,"locator":evidence(raw)["locator"][:500]},
                  "consequence_if_unaddressed":{"code":"interpretive_ambiguity_remains","target":{"kind":"section","locator":evidence(raw)["locator"][:500]}},
                  "target_section":evidence(raw)["locator"][:1000],"suggested_action":action,"consensus_level":"SINGLE-VERIFIER",
                  "verification_criteria":verification,"proposed_targets":[{"block_id":b,"allowed_operations":["replace_block","insert_after"]} for b in blocks]})
items[0]["source_refs"].extend([{"seat":"R1","channel":"finding","ordinal":4,"subclaim_ordinal":0}, {"seat":"DA","channel":"finding","ordinal":2,"subclaim_ordinal":0}])
da = (HERE / "reports/da_phase2.md").read_text()
paragraph = da.split("Observación menor m1 —",1)[1].split("Observación menor m2",1)[0]
anchor = paragraph.split("Evidencia: text: ",1)[1].split(". Confianza:",1)[0]
items.append({"id":"REV-15","source_refs":[{"seat":"DA","channel":"finding","ordinal":1,"subclaim_ordinal":0}],
              "description":"Traer al método principal la dependencia OOF de la cascada histórica","reviewer":"DA","sub_claim_ids":["SC-15"],
              "obligation_class":"must_fix","severity":"minor","severity_source":"reports/da_phase2.md, Observación menor m1",
              "evidence_anchor":{"anchor_type":"text","locator":anchor,"quote":re.search(r'"([^"]+)"',anchor).group(1)},
              "confidence":4,"competence_basis":"DA checked the explicit historical annex statement, not the E1 implementation.",
              "cost_scope":{"kind":"section","locator":"§3.6 and historical annex E.7"},
              "consequence_if_unaddressed":{"code":"interpretive_ambiguity_remains","target":{"kind":"section","locator":"§3.6"}},
              "target_section":"§3.6; paper/chapters/F_estudios_complementarios.tex:173",
              "suggested_action":"Explicar selección histórica fija por OOF y distinguirla de E1; no afirmar contaminación del test ni exigir una repetición plenamente anidada para el alcance descriptivo.",
              "consensus_level":"SINGLE-VERIFIER","verification_criteria":"Los dos niveles de selección y ambos archivos se distinguen; no se oculta la limitación histórica.",
              "proposed_targets":[{"block_id":"B0073","allowed_operations":["replace_block","insert_after"]}]})
roadmap = {"schema_version":"revision-roadmap/1.0","revision_round":1,
           "base_draft_sha256":sha(HERE/"inputs/review_working_draft.md"),"block_manifest_sha256":sha(HERE/"inputs/block_manifest.json"),
           "items":items,"total_items":len(items),"obligation_counts":{"must_fix":10,"should_fix":5,"consider":0},
           "editorial_decision":"Major Revision", "consensus_summary":"No CONSENSUS-3/4 or SPLIT established. Arithmetic is corroborated by EIC and R1 (2/4 non-DA), plus DA separately. All original observations retained in reports; roadmap is source-ordered, not a work ranking. All finding severities remain Minor.",
           "dissenting_opinions":[]}
(HERE/"revision_roadmap.json").write_text(json.dumps(roadmap,ensure_ascii=False,indent=2)+"\n")
print("Roadmap transported:", len(items), "items; no author triage or manuscript edit")
