# Neshov FMD: aproximación prospectiva al protocolo 10 × 10

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: experimento separado de aproximación al protocolo publicado.
- Origin Date: 2026-11-02, America/Asuncion.
- Verification Status: prospectivo, antes de extraer o evaluar condiciones.

## Objetivo y límites

La fuente `10.3390/electronics14234779` informa 96,7 % de **accuracy** en FMD,
con 10 repeticiones de validación cruzada de 10 pliegues. Este experimento está
separado del panel común de 3 semillas × 5 pliegues y de nuestro panel local.
No compara F1 histórico con tiempos nuevos ni afirma superioridad pareada con
nuestros métodos, pues aquí las particiones difieren. Medir accuracy, macro-F1
y tiempos individuales desde las mismas predicciones, sin mezclar métricas.

## Decisiones fijadas antes de medir

Se usa la rama BEiTv2 ya implementada, peso local y extracción individual; MLP
de 64 unidades con BN/ReLU/dropout 0,2, cabeza final por fold, 100 épocas, batch
32, Adam con tasa 0,001 y weight decay 0,0001. No hay selección por test, cambio
de umbral o búsqueda de resultados. Para aproximar los detalles que el artículo
no especifica suficientemente, se fija `StratifiedKFold(10, shuffle=True)` y se
numeran las repeticiones del 1 al 10, con semillas 42,84,...,420. Cada cabeza
se inicializa de nuevo con la semilla de su repetición. Estas son decisiones
locales: el índice base, el estratificado y el estado exacto del generador al
inicializar cada fold no están verificados contra el código de autores.

La fuente declara Python 3.10.16, PyTorch 2.5.1, NumPy 2.0.1 y timm 1.0.15;
se registra la diferencia con el entorno disponible y no se llama reproducción
fiel. Tampoco se presupone igualdad exacta de precisión o entorno de GPU. El
checkpoint y las implementaciones se fijan por hash antes del primer modelo.

Cada una de las diez repeticiones cubre exactamente las 1000 imágenes una vez
en test; cada condición usa 900 fit y 100 test, y una semilla/partición única.
Los grupos y hashes de imagen se comprueban. La primera condición y su auditoría
habilitan las 99 restantes. Si una condición falla, conservar evidencia y no
reintentar automáticamente. Lock GPU global, CPU dos hilos y sin otro benchmark
o fit concurrente. Warmup y reloj son los mismos del panel común. Guardar índices,
características de fit, paridad, cabeza, predicciones y latencia, errores y hashes.

El criterio no es forzar 96,7 %: se informará la accuracy observada, su modo
de agregación y sus diferencias con las elecciones publicadas. No se utilizarán
resultados parciales como media de las 100 condiciones. Si una reconstrucción
posterior verifica el código, versiones y particiones de autores, debe
ejecutarse como otra versión, sin sobrescribir esta aproximación.
