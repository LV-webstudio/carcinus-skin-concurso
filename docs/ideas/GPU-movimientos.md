# Idea: movimientos de CARCINUS entrenados con GPU

Apuntada el 01-11-2026 a petición de Lorenzo (sesión nube «Carcinus concurso video»). **Es solo una idea: no hay nada aplicado ni contratado.**

## Situación actual
- El vídeo del concurso (`video/`) usa un **movimiento programado**: la trayectoria de la pinza se calcula con IK y MuJoCo resuelve los contactos. Funciona, pero es rígido, y solo se mueve un brazo; las patas se quedan en la postura `HOME`.
- Todo corre en CPU (4 núcleos, sin GPU). El render 1080p tarda unos 9 min.

## Propuesta
Entrenar con **aprendizaje por refuerzo (RL) en simulación** y con GPU una política para el Jumper con el skin «shania-cristal». Tareas candidatas:
1. Acercar a sus pies un objeto caído, con el cuerpo entero (girar y caminar un paso, no solo el brazo).
2. Caminar hasta el objeto y traerlo.
3. Gestos para cada estado de luz (alegre, esperando…), más naturales que los de ahora.

## Con qué
- El kit público de KingKong Robotics (`github.com/KingKongRobotics/jumper`, Apache-2.0) ya trae su marco de entrenamiento (`rl/`, basado en mjlab) y tareas del Jumper (`tasks/jumper/`). Es el camino más directo: misma física y mismo modelo que el concurso.
- **Nemotron** (NVIDIA) es un modelo de lenguaje: serviría para escribir o ajustar guiones y recompensas, no para generar el movimiento. Para robótica, NVIDIA tiene Isaac/GR00T; habría que revisar licencias y requisitos antes de usarlos.

## Qué hace falta decidir (Lorenzo)
- **GPU**: ¿cuál? ¿Un equipo propio con GPU NVIDIA o un servicio en la nube? Los servicios de GPU suelen ser de pago y la regla es **no usar servicios de pago sin permiso**. Las capas gratuitas tienen límites de tiempo, y habría que mirar sus condiciones antes de subir el kit o el skin.
- Si merece la pena antes del 30-11-2026 (plazo del concurso) o queda para después.
- Revisar las bases: si valoran una política entrenada frente a un movimiento programado.

## Rigor
- No hay estimación de tiempos de entrenamiento ni de resultados: no se ha probado. No se inventan cifras.
- Si el movimiento sale de un modelo de IA o de RL, se dirá así en el vídeo y en la publicación.
- No se copia el modelo del kit en este repositorio (Apache-2.0: se cita su autoría).
