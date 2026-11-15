# Perfil KTH corregido y aceptado

EVA-02 y SigLIP superan coseno 0,999 en las mismas 33 imágenes congeladas de
entrenamiento por red. [Estado](status.json), [sesiones y fuentes](protocol_frozen.json).

Son 66 llamadas evaluadas y diez calentamientos en total. EVA se conserva
del primer proceso; SigLIP se ejecutó después de corregir la serialización
del informe de carga, que había fallado antes de su primer forward. Ninguna
llamada científica se repitió. Los perfiles y fallos originales no cambian.

[EVA por imagen](eva02_base_calls.json) · [SigLIP por imagen](siglip_base_calls.json).
Los tiempos son de adquisición por componente, con el alcance registrado en
los protocolos. Las sesiones distintas se declaran; no se presentan como una
nueva latencia online de Top-4 directo/por margen.

[Informe de cierre y reservas](../../../docs/fsc_tex/CIERRE_FIDELIDAD_KTH_E1_E2_2026-11-15.md).
