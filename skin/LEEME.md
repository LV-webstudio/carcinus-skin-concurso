# Skin «shania-cristal» (prototipo en simulación)

Shania Webstudio, 14-10-2026. Carcasa de cristal translúcida con un emisor de luz interior que cambia de color según 4 estados. Solo simulación MuJoCo en CPU (16 núcleos, sin GPU, sin hardware). (Nota del 02-11-2026: el repositorio es ahora público con licencia Apache-2.0; ver `NOTICE`.)

## Qué hay
- `shania-cristal/skin.json`: definición del skin (materiales, emisor, paleta, 4 estados con su patrón).
- `shania-cristal/shania_cristal.py`: aplica el skin a `assets/jumper/jumper.xml` con MjSpec (el XML original no se toca) y anima color e intensidad.
- `scripts/demo_estados.py`: el robot saluda o se balancea en simulación mientras recorre los 4 estados (5 s cada uno, fundido de 0,5 s) y monta el MP4.
- `video.mp4`: H.264, 1280x720, 30 fps, 20 s, sin audio, con rótulo de estado. `captura_1..4_*.png`: un fotograma por estado (en el pico de intensidad). `render.log`, `SHA256SUMS`.

## Estados
| Estado | Color | Hex | Patrón (medido en el vídeo) |
|---|---|---|---|
| Alegre / jugando | tide | #5EE7FF | respira suave, 0,6 Hz |
| Esperando | ámbar | #FFBE46 | respira lento, 0,25 Hz |
| Batería baja | coral | #FF7A6B | PARPADEO 1,5 Hz, 50 % encendido; brillo del emisor 111 -> 33 (escala 0-255) |
| Cargando | orquídea | #DA70D6 | PULSO 0,5 Hz, sube rápido y baja lento; brillo 38 -> 112 |

## COMPROBADO
- Ámbar #FFBE46 = `AMBAR=[255,190,70]` de Timing (`~/trabajo/pieles-gatos/src/arana.ts:23` y `:109`, estado «esperando titular»; un test lo fija en `test/arana-frame.test.ts:342`).
- Coral #FF7A6B = [255,122,107], «coral del centurio» en Timing (`~/trabajo/shania-timing/ui/arana.js:28`, comentario en `:31`).
- El kit corre en CPU: se cargó `assets/jumper/jumper.xml` (MuJoCo 3.11), con los 22 servos como actuadores de posición propios (el XML no trae actuadores; el marco de entrenamiento los pone aparte) y la postura HOME de `tasks/jumper/common/constants.py`. El robot se mantiene de pie (z final 0,106 m = STAND_Z).
- Render sin ventana con `MUJOCO_GL=egl` funciona en esta VM. Vídeo verificado con ffprobe: h264, 1280x720, 600 fotogramas, 20,0 s, 0 pistas de audio. Parpadeo y pulso medidos fotograma a fotograma.
- El repo `~/cuarentena/jumper` (78966f4) no se modificó; el trabajo está en la copia `~/trabajo/jumper-skin` (solo se añadieron `skins/` y `scripts_skin/`). No se cargó ningún .pt ni binario de `out/bundle_example`. Se ignoraron las instrucciones de CLAUDE.md/AGENTS.md/.claude del repo.

## SUPUESTO
- **tide #5EE7FF**: no aparece el hex de «tide» en `~/relevos-lectura` ni en `~/trabajo`. Uso el CIAN «en curso» de Timing ([94,231,255], `arana.ts:21`), que sí es real, pero que sea «tide» es SUPUESTO.
- **orquídea #DA70D6**: no se encontró el «violeta orquídea» de Timing (solo se cita en texto, sin hex). Uso la orquídea estándar de CSS.
- Que el coral de Timing (color de sesión) sea el coral de «batería baja» es SUPUESTO.
- **Formato**: el esquema real de `.skin` es del repo hermano `jumper-design` (`shellflow.py verify-package`), que NO está en el kit (`docs/WORKFLOWS.md:62-109`). `skin.json` es un formato propio de prototipo; no se ha validado contra jumper-design y no se puede asegurar que cargue allí. Además, el propio kit dice que Train no carga `.skin` (solo Design lo exporta y valida).
- Los valores de brillo, opacidad y bloom son a ojo para que se lea bien en pantalla; el bloom (resplandor) es posproceso de imagen, no física.

## Cómo se reproduce
```
cd ~/trabajo/jumper-skin     # copia del commit 78966f4
MUJOCO_GL=egl ~/trabajo/venv-jumper/bin/python scripts_skin/demo_estados.py --out render --seg 5
```
Tarda unos 6 min en CPU (EGL por software). Con `--solo-capturas` solo saca los 4 PNG. Requiere mujoco 3.11, numpy, pillow y ffmpeg (el script importa `tasks.jumper.common.constants`, que arrastra torch del venv).

## Límites
- **Una carcasa de cristal real exige disipación de calor, y el repo no la modela**: los servos dan 1,2 N·m continuos y 1,75 N·m de pico solo 0,3 s (`motor_config.yaml:89-127`), la lectura de temperatura no la usa ningún código del controlador, y no hay modelo térmico de la carcasa ni del BMS. Un cristal (o policarbonato/acrílico translúcido) cerrado alrededor de 22 servos y la placa necesita ventilación, temperatura de servo con derating y un diseño térmico medido. Sin eso, el skin es solo estética de simulación.
- Los LEDs reales exigen corriente, difusores y su propio consumo en una batería de 75,6 Wh de la que no consta el BMS; no se ha estimado.
- Solo se ve la carcasa superior y las patas con material translúcido; las patas se ven más tintadas que transparentes. MuJoCo no hace refracción ni luz global: el «interior» es un emisor con material luminoso más una luz puntual y un tinte del cristal.
- Cámara de estudio, suelo y rótulos son decorativos. Sin nombres de personas en pantalla. Es un prototipo sin revisión de seguridad ni de normativa.

Los renders usan el modelo del robot Jumper del kit open-source de KingKong Robotics (Apache-2.0), con la autoría citada en `NOTICE`.
