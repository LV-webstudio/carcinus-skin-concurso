# Movimientos de CARCINUS entrenados con GPU

- 01-11-2026: idea apuntada a petición de Lorenzo y enviada a la sesión legatus.
- **02-11-2026: APROBADA por Lorenzo** («vídeo aprobado y gpu»). Este documento es ahora el plan de trabajo.

## Objetivo
Pasar del movimiento programado del vídeo actual (cinemática inversa + física, en CPU) a **movimientos entrenados con aprendizaje por refuerzo (RL)** en simulación, con el skin «shania-cristal», para las siguientes rondas del concurso (que termina el 30-11-2026). El vídeo actual, ya aprobado, no se toca: se publica tal cual.

## Dónde: Google Colab con GPU (ruta oficial del kit)
El kit de KingKong Robotics trae un cuaderno para entrenar en la GPU de Colab: `notebooks/jumper_colab.ipynb`, documentado en `docs/COLAB.md`.
- Enlace: <https://colab.research.google.com/github/KingKongRobotics/jumper/blob/main/notebooks/jumper_colab.ipynb>
- Hace falta **una cuenta de Google** y elegir un entorno con GPU. **Esta sesión de la nube no puede hacerlo**: no tiene GPU ni puede iniciar sesión en Google. Lo tiene que lanzar una persona desde el navegador.
- La capa gratuita de Colab asigna la GPU y la duración de la sesión según disponibilidad. Si se quiere Colab de pago u otro proveedor, hace falta permiso expreso, porque la regla es **no usar servicios de pago sin permiso**.
- Según el kit, la tarjeta T4 de Colab funciona (CUDA 12.6); el entorno ocupa unos 7,2 GiB de disco.

## Qué entrenar (por orden)
1. **Probar el circuito con una tarea del kit que ya existe**, sin tocar código: `jumper.gesture_paw` (se sienta, adelanta la pinza izquierda y «ofrece la pata»; es lo más parecido a nuestro gesto) o `jumper.gesture_hello`. El cuaderno: entrenar → curvas → reproducir → exportar → **descargar el ZIP de respaldo** antes de que se cierre la sesión.
2. **Reproducir con nuestro skin**: `scripts/play.py --model <XML con skin>` (ver abajo). El XML lo genera `skin/exportar_xml.py`.
3. **Tarea propia «acercar un objeto»** (más adelante): una tarea nueva en el marco del kit (`tasks/jumper/...`, mjlab) con un objeto en la escena y una recompensa por acercarlo a los pies. Es trabajo de código: se prepara en CPU y se entrena en GPU.
4. Gestos por estado de luz (alegre, esperando…) a partir de las tareas `gesture_*` del kit.

## Skin con el entrenamiento del kit
- `python3 skin/exportar_xml.py --kit RUTA_KIT --estado alegre` escribe `assets/jumper/jumper_shania_cristal_alegre.xml` **dentro del kit clonado**, no en este repositorio, porque deriva del modelo del kit.
- Se comprueba al exportar: misma cinemática y **misma masa** que el modelo del kit. Solo añade materiales, un emisor y LEDs visuales que no colisionan; no añade actuadores ni suelo. El color queda fijo en un estado; las luces animadas solo están en `video/escena_concurso.py`.
- En Colab: subir ese XML a la carpeta del kit y usar `--model assets/jumper/jumper_shania_cristal_alegre.xml` al reproducir (y al entrenar, si se quiere: la física es la misma).
- El resultado de la comprobación en CPU con el propio kit está en «Comprobado» (abajo).

## Reglas
- No se dan cifras de rendimiento ni de tiempo de entrenamiento hasta haberlo medido. El propio kit avisa de que su ejemplo de 500 iteraciones «demuestra el circuito, no una marcha convergida».
- Cualquier movimiento salido de un entrenamiento por RL se dirá así en el vídeo y en la publicación («política entrenada con RL en simulación»), igual que ahora se dice que el movimiento está programado con asistencia de IA.
- No se cargan checkpoints `.pt` de terceros (cargar uno puede ejecutar código); solo los que entrenemos nosotros.
- **Nemotron** (modelo de lenguaje de NVIDIA) no hace falta para esto. Si se quiere usar para redactar recompensas o guiones, se revisa su licencia antes.

## Comprobado
(se rellena con lo que se haya ejecutado de verdad)
