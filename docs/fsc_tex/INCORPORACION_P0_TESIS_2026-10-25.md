# Incorporación del control P0 al manuscrito

Fecha: 25 de octubre de 2026. Autorización: el autor solicitó «incorpora» después del dictamen de mesa simulada y de la propuesta de integrar P0. Alcance: incorporación editorial del análisis existente, no ejecución de los controles experimentales pendientes.

## Qué cambió

- Se sincronizaron resumen, abstract, introducción, diseño, resultados, discusión y conclusiones. Se retiraron las frases que declaraban inexistente la comparación del mismo rescate con y sin compuerta.
- La Sección 4.4.1 define las cuatro vistas: base, mismo rescate permanente eficiente, ruta forzada con base y ruta condicional. Distingue el control de una nueva selección estática optimizada.
- La Sección 5.5.1 y la Tabla 5.7 separan poda y activación en relevancia/B60. El Anexo C, Tabla C.6, conserva las doce configuraciones completas, incluidas las cuatro sin rescate.
- Se añadió la trazabilidad de P0 al Anexo D. El generador nuevo verifica las predicciones y crea las dos tablas; no modifica los archivos numéricos de origen.
- Se actualizaron README y plan de cierre para identificar P0 como incorporado. Los informes históricos y la primera mesa simulada conservan su corte anterior, sin reescribir sus dictámenes retrospectivamente.

## Resultado que queda escrito

| Comparación | F1 de origen → destino | Adquisición proyectada, ms | Reducción relativa |
| --- | --- | --- | --- |
| Completo permanente → rescate podado permanente, relevancia/B60 | 0,914389 → 0,911993 | 365,196 → 110,421 | 69,76 % |
| Mismo rescate podado permanente → condicional, relevancia/B60 | 0,911993 → 0,910742 | 110,421 → 53,316 | 51,72 % |
| Mismo rescate podado permanente → condicional, marginal/B60 | 0,905140 → 0,905140 | 97,282 → 55,365 | 43,09 % |

Los porcentajes de poda y activación se aplican sucesivamente: no se suman. La reducción conjunta frente al ensamble completo es 85,40 %. En relevancia/B60, las llamadas solo bajan un 0,79 % frente al mismo rescate podado; en marginal/B60 aumentan un 25,36 %. La compuerta no mejora F1 en las ocho configuraciones con rescate: siete disminuyen y una conserva exactamente las predicciones. La coincidencia de las 680 clases predichas en marginal/B60 no demuestra equivalencia poblacional.

## Verificaciones

- [Generador y verificador local](../../scripts/build_p0_thesis_tables.py): 156 campos numéricos recalculados desde las vistas por imagen, cobertura de las mismas 680 imágenes oficiales de entrenamiento, 68 clases balanceadas y concordancia de la ruta condicional con el piloto original.
- [Procedencia de las tablas](../../paper/generated_p0/provenance.json): hashes de cuatro artefactos numéricos P0, manifiesto de origen, piloto, pliegues productores, generador y las dos tablas nuevas. Los archivos de análisis se mantienen byte-idénticos.
- Verificación estructural: 120 celdas principales contra sus fuentes, siete capítulos, dependencias presentes, ninguna cita indefinida y preservación de 59 entradas archivadas y cuatro salidas editoriales anteriores.
- Compilación: PDF de 59 páginas, sin errores, referencias indefinidas ni cajas overfull/underfull. Inspección visual de resúmenes, diseño, resultados, discusión, conclusiones y tablas añadidas. Se condensó la redacción del Anexo D sin cambiar su alcance para evitar un párrafo aislado en otra página.
- Suite de software: 80 pruebas aprobadas en 47,46 s. No representa evaluación en imágenes nuevas.
- No se reentrenó, evaluó el test oficial, midió físicamente el híbrido ni calcularon pruebas inferenciales nuevas.

El respaldo previo contiene fuentes, PDF y documentación afectados: [revision_p0_20261025_before.tar.gz](../../paper/revision_p0_20261025_before.tar.gz). Se conservaron los cambios locales ajenos a esta incorporación. No se hizo commit, push ni paquete Overleaf.

## Relación con la mesa simulada y pendientes

Se atendió el componente editorial de J04: el manuscrito ya muestra P0 y distingue adquisición, llamadas y pérdida predictiva. Esto no es un nuevo dictamen de aceptación ni cierra por extensión las otras objeciones. Quedan pendientes la selección estática competitiva con presupuesto equivalente, réplica predefinida, medición física del híbrido, sensibilidad/procedencia KTH y entrega reproducible completa. El control no establece superioridad general ni novedad mundial.

Se utilizaron criterios de escritura y contención de afirmaciones de ARS. Como en las revisiones locales previas, se aplicaron parches acotados al proyecto LaTeX, con respaldo y comprobaciones propias; no se fabricaron una adjudicación exacta del autor, un pasaporte, un testigo de autorización #670 ni una certificación del flujo formal completo de ARS. Los resúmenes existentes se editaron localmente en español e inglés, sin invocar el generador bilingüe formal. No hay rúbrica institucional vinculada.
