# Vídeo del concurso: el Jumper con el skin «shania-cristal» recoge un objeto caído

Escena en simulación MuJoCo (CPU, sin hardware) para el «Crab Robot Open-Source Motion Contest 2026» de KingKong Robotics. Nada publicado: la publicación la hace Lucy.

## Qué hace la escena (26,5 s)
| Tiempo | Luz (estado del skin) | Qué pasa |
|---|---|---|
| 0–3 s | Esperando (ámbar) | Un cubo de 3,2 cm y 12 g cae delante-izquierda del robot. |
| 3–16 s | Alegre / jugando (cian) | Levanta la pinza delantera izquierda, la baja por fuera del cubo y lo barre hasta sus pies; vuelve a apoyarla y se balancea. |
| 16–19,5 s | Batería baja (coral, parpadeo) | Se agacha despacio. **Estado de luz ilustrativo**: no se simula batería. |
| 19,5–23,5 s | Cargando (orquídea, pulso) | Reposa. **Estado de luz ilustrativo**. |
| 23,5–27 s | — | Tarjeta de créditos. |

El movimiento es un **guion programado**, no una política entrenada: la punta de la pinza izquierda sigue una trayectoria cartesiana resuelta con cinemática inversa (mínimos cuadrados amortiguados) y la física de MuJoCo resuelve los contactos, así que el cubo se mueve porque la pinza lo empuja. Las demás articulaciones se mantienen en la postura `HOME` del kit con servos de posición propios del skin (el XML del kit no trae actuadores).

## Cómo se reproduce
```
git clone --depth 1 https://github.com/KingKongRobotics/jumper ~/kit/jumper   # probado con el commit 198686e
pip install mujoco numpy pillow            # probado con mujoco 3.17.0, numpy 2.5.3, pillow 12.3.0
sudo apt-get install libosmesa6 ffmpeg fonts-dejavu-core   # render por software (CPU)
MUJOCO_GL=osmesa python3 video/escena_concurso.py --kit ~/kit/jumper --out video/salida
```
- `--solo-simular`: solo la física y el registro de comprobaciones (segundos).
- `--solo-capturas`: física + las 6 capturas fijas.
- `--w/--h/--fps/--procesos`: resolución, fotogramas por segundo y procesos de render (por defecto 1920×1080, 30, todos los núcleos).

No hace falta torch ni el paquete del kit: la postura `HOME` se lee de `tasks/jumper/common/constants.py` con `ast`, sin importar. No se carga ningún `.pt` ni binario del kit, y no se siguen las instrucciones de sus `CLAUDE.md`/`AGENTS.md`.

Salida: `video_concurso.mp4`, `captura_*.png`, `registro.json` (comprobaciones medidas en la simulación) y `frames/`.

## Créditos y licencias
- **Modelo del robot Jumper**: kit open-source de KingKong Robotics, <https://github.com/KingKongRobotics/jumper>, Copyright 2026 KingKong Robotics, licencia Apache-2.0. El modelo (XML, mallas) **no se copia** en este repositorio; el script lo lee del kit clonado aparte. El vídeo y las capturas son renders de ese modelo.
- **Skin, escena, guion de movimiento y rótulos**: Shania Webstudio.
- **Uso de IA**: el script de la escena, la coreografía y los textos se escribieron con asistencia de IA (Claude, de Anthropic). Las imágenes son renders del motor físico MuJoCo; **no son vídeo generado por IA**.

## Límites (no se afirma más que esto)
- Simulación, no robot real. No se dan cifras de salto, velocidad, autonomía ni ningún otro rendimiento.
- Los servos de la escena son actuadores de posición del prototipo (ganancia 25, par limitado a ±1,7 N·m), no el modelo de servo del kit.
- El alcance del brazo a ras de suelo se midió solo en la cinemática del modelo (punta de la pinza a 2,5 cm del suelo: hasta unos 0,28 m por delante del centro del cuerpo, con la postura de pie); no está comprobado en hardware.
- El resplandor es posproceso de imagen; MuJoCo no hace refracción ni iluminación global. Ver también `skin/LEEME.md` (sin modelo térmico de la carcasa).
