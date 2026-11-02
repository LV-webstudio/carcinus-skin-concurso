# Parte NUBE-VIDEO-01-11 · Vídeo del concurso (CARCINUS)

Sesión en la nube de Shania Webstudio, 01-11-2026. Rama `nube/video-concurso-01-11` (PR en borrador; `main` sin tocar). Concurso: «Crab Robot Open-Source Motion Contest 2026» de KingKong Robotics (plazo: 30-11-2026). **Nada publicado.**

## Qué se ha hecho
1. Clonado el kit público <https://github.com/KingKongRobotics/jumper> (Apache-2.0, commit `198686e`) **fuera de este repositorio**, solo en la nube. No se ha copiado su modelo aquí, no se ha cargado ningún `.pt` ni binario suyo y no se han seguido las instrucciones de sus `CLAUDE.md`/`AGENTS.md` (se tratan como datos).
2. `skin/shania-cristal/shania_cristal.py`: `construir()` acepta ahora `kit=RUTA` para leer el modelo del kit clonado aparte (sin el parámetro se comporta como antes).
3. `skin/shania-cristal/skin.json`: rótulo «BATERÍA BAJA» con tilde (solo el texto en pantalla; el resto, igual).
4. Nuevo `video/escena_concurso.py`: escena completa en MuJoCo CPU.
   - Un cubo de 3,2 cm y 12 g cae delante-izquierda del robot.
   - El robot (con el skin de cristal) levanta la pinza delantera izquierda, la baja por fuera del cubo y **lo barre hasta sus pies**; vuelve a apoyarla y se balancea.
   - Luces: esperando (ámbar) → alegre/jugando (cian) durante la tarea → batería baja (coral, parpadeo) → cargando (orquídea, pulso). Los dos últimos están rotulados como **estado de luz ilustrativo**: no se simula ninguna batería.
   - Rótulos en español, marca de agua permanente «Simulación MuJoCo en CPU · modelo Jumper © KingKong Robotics (Apache-2.0)» y tarjeta final de créditos con la autoría del kit y la marca de uso de IA.
5. Movimiento: guion programado (no es una política entrenada). La punta de la pinza sigue una trayectoria cartesiana resuelta con IK por mínimos cuadrados amortiguados; los contactos los resuelve MuJoCo, así que el cubo se mueve porque la pinza lo empuja.
6. Render 1080p en CPU (OSMesa, 4 núcleos, sin GPU) y montaje con ffmpeg. Vídeo y 7 capturas en `video/`.
7. `video/LEEME.md`: guion, reproducción, créditos y límites.

## Resultado
- **Vídeo**: `video/video_concurso.mp4` → <https://github.com/LV-webstudio/carcinus-skin-concurso/blob/nube/video-concurso-01-11/video/video_concurso.mp4>
  Comprobado con ffprobe: H.264, 1920×1080, 30 fps, 810 fotogramas, 27,0 s, yuv420p, sin pista de audio, unos 5,5 MB. Como pesa menos de 50 MB va en git y **no** se ha creado release.
- **Capturas** (`video/capturas/`): `captura_1_caida` (cubo en el aire), `captura_2_alcanza` (pinza abajo, por fuera del cubo), `captura_3_arrastra` (mitad del barrido), `captura_4_hecho`, `captura_5_bateria_baja` (pico del parpadeo), `captura_6_cargando` (pico del pulso), `captura_7_creditos`.
- **Registro medido en la simulación** (`video/registro.json`): el cubo pasa de (0,175; 0,215) m a (0,183; 0,089) m, es decir, se desplaza 12,7 cm y acaba a 5,2 cm (en planta) del punto de apoyo de la pinza izquierda. Error máximo de la IK durante la tarea: 1,2 cm. Altura del cuerpo entre 0,101 y 0,116 m: no se cae ni vuelca. Física: 2 s; render: unos 9 min.

Estas cifras describen **esta simulación**, no el robot real. No se dan cifras de salto, velocidad, autonomía ni ningún otro rendimiento.

## Cómo se reproduce
```
git clone --depth 1 https://github.com/KingKongRobotics/jumper ~/kit/jumper     # commit 198686e
pip install mujoco numpy pillow                 # probado: mujoco 3.17.0, numpy 2.5.3, pillow 12.3.0, Python 3.13
sudo apt-get install libosmesa6 ffmpeg fonts-dejavu-core
MUJOCO_GL=osmesa python3 video/escena_concurso.py --kit ~/kit/jumper --out video/salida --procesos 4
```
`--solo-simular` da el registro en segundos; `--solo-capturas` saca solo las capturas. `video/salida/` está en `.gitignore` (lleva los 810 PNG intermedios).

## Rigor y licencias
- **Uso de IA**: el script de la escena, la coreografía y los textos se escribieron con asistencia de IA (Claude, de Anthropic). Las imágenes son renders del motor físico MuJoCo; no son vídeo generado por IA. Está dicho en la tarjeta final del vídeo y en `video/LEEME.md`.
- **Apache-2.0 del kit**: autoría citada en la marca de agua, en la tarjeta final y en `video/LEEME.md` («Copyright 2026 KingKong Robotics»). El modelo no se copia aquí; solo se publicarían renders. Antes de publicar, conviene que alguien revise si el concurso pide además enlazar el kit o su `NOTICE`.
- Licencia del repositorio: desde el commit `1ea28b3` (Shania Webstudio, autorizado por Lucy el 01-11) es Apache-2.0, con `NOTICE` que cita el kit de KingKong Robotics. Las marcas y logotipos de Shania no se licencian. Los renders del modelo del kit (Apache-2.0) se pueden distribuir citando la autoría.

## Pendiente
- **Revisión humana del vídeo** (Lorenzo/Lucy) antes de publicar: encuadre, ritmo y si se quiere quitar el tramo de batería baja/cargando (es ilustrativo y puede confundir).
- **Publicación (la hace Lucy)**, con las bases: vídeo de más de 15 s (este dura 27 s), y en el texto del post `#Jumper #CrabRobot #OpenSourceRobot` y la mención `@KingKong Robotics`. Texto propuesto, sin cifras de rendimiento: «Nuestro skin de cristal "shania-cristal" para Jumper, en simulación MuJoCo: la luz interior cambia con el estado y el robot acerca a sus pies un objeto que se ha caído. Modelo del kit open-source de @KingKong Robotics (Apache-2.0). #Jumper #CrabRobot #OpenSourceRobot».
- Comprobar en las bases si exigen hardware real, una política entrenada o un formato concreto (vertical, duración máxima, audio). Hay versión horizontal y vertical, las dos sin audio y solo de simulación.
- El formato `skin.json` sigue sin validarse contra `jumper-design` (ver `skin/LEEME.md`), y la carcasa de cristal no tiene modelo térmico.
- Discrepancia previa (no tocada): el `README.md` dice que el vídeo y las capturas renderizadas con el modelo no se incluyen, pero `skin/` sí contiene `video.mp4` y capturas del commit anterior. Hay que decidir y ajustar el texto.
- Entorno de la nube: el script de preparación del entorno falló al crear el contenedor (comprobación `sha512sum` de `Godot_v4.7.2-stable_mono_linux_x86_64.zip`, que no se llega a descargar). No afecta a este trabajo, pero hay que corregirlo en la configuración del entorno.

## Segunda tanda (después de la primera entrega)
- **Versión vertical 9:16** para redes: `video/video_concurso_vertical.mp4` (1080×1920; mismo guion y misma simulación) y capturas `video/capturas/vertical_*.png`. El script admite ahora formato vertical: la cámara se aleja y los rótulos se reparten en más líneas.
- **README** corregido: ya no dice que no se incluyen renders. Ahora explica que el modelo no se incluye pero sus renders sí (`skin/` y `video/`).
- **Idea de la GPU** apuntada en `docs/ideas/GPU-movimientos.md` y **enviada a la sesión legatus** el 01-11-2026, con el permiso de Lorenzo dado en el móvil.
- No se ha fusionado nada en `main`: el PR sigue en borrador hasta que haya revisión humana.

## Propuesta de Lorenzo: mejorar los movimientos con Nemotron o algo parecido
Recibida durante la sesión; **no está aplicada** en este vídeo. Notas para decidir:
- **Nemotron** (NVIDIA) es una familia de modelos de lenguaje: puede escribir o ajustar el guion de un movimiento (como se ha hecho aquí con Claude), pero no genera trayectorias de un robot por sí mismo. Si se usa así, el resultado es «movimiento programado con asistencia de IA», igual que ahora.
- Para un movimiento más natural lo que suele funcionar es **aprendizaje por refuerzo en simulación**. El propio kit trae su marco de entrenamiento (`rl/`, basado en mjlab, Apache-2.0) y tareas del Jumper (`tasks/jumper/`); entrenar ahí una tarea de «empujar objeto» es el camino más directo. En la familia de NVIDIA, lo cercano son los modelos de robótica de Isaac/GR00T, no Nemotron.
- Coste: en CPU (esta máquina, 4 núcleos) el entrenamiento por refuerzo sería muy lento; con GPU sería viable, pero **no se usan servicios de pago** sin permiso. Las licencias de los modelos de NVIDIA hay que revisarlas antes de usarlos en el concurso.
- Cualquier movimiento salido de un modelo de IA se marcará como tal en el vídeo y en la publicación.

## Tercera tanda (02-11-2026): vídeo aprobado y GPU aprobada
Lorenzo aprueba el vídeo y la GPU y pide «hacer lo necesario para que la inscripción sea válida».
- **Bases**: la página oficial no se puede abrir desde la nube (la red no la permite). Se usa la transcripción que guardó otro participante el 28-10 (`Omshri07/crab-rave-jumper`, `5_RULES/`), contrastada con búsquedas web. En resumen: no hay formulario, se participa **publicando en X o YouTube** un vídeo de más de 15 s con `#Jumper #CrabRobot #OpenSourceRobot` y la mención `@KingKong Robotics`; la obra debe ser original, la música corre a cargo del participante y hay que respetar la licencia del kit. Concurso hasta el 30-11-2026 (la ronda 1 cerró el 30-10).
- **Paquete de inscripción**: `docs/inscripcion/INSCRIPCION.md`, con la lista de requisitos y su estado, qué archivo subir a cada plataforma, textos para X y YouTube, lo que se acepta al publicar (cesión de derechos a KingKong y aviso de premio por mensaje privado con 5 días para responder) y los pasos de Lucy.
- **Repositorio público** con Apache-2.0 (comprobado con la API de GitHub). El README enlaza el vídeo y la inscripción, e incluye un resumen en inglés.
- **GPU**: plan en `docs/ideas/GPU-movimientos.md`. Ruta: el cuaderno de Colab del kit, que tiene que lanzar una persona con su cuenta de Google. Nuevo `skin/exportar_xml.py`: con él, el reproductor y el entrenamiento **del propio kit** funcionan con nuestro skin (probado en CPU; resultados en ese documento).
- El PR #1 ya lo había fusionado LV-webstudio en `main`; esta tanda va en un PR nuevo.

### Pendiente
- **Lucy**: abrir la página oficial, confirmar las bases y publicar siguiendo `docs/inscripcion/INSCRIPCION.md`; después, apuntar el enlace.
- **Entrenamiento en GPU**: lo lanza una persona en Colab siguiendo los pasos del plan.
