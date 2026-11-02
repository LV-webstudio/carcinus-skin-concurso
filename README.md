<p align="center"><img src="assets/marca/banner.png" alt="carcinus-skin-concurso · Shania Webstudio" width="100%"></p>

# carcinus-skin-concurso

Prototipo en simulacion del skin «shania-cristal» para el concurso: carcasa de cristal translucida con un emisor de luz interior que cambia de color segun 4 estados (alegre, esperando, bateria baja, cargando). Solo simulación MuJoCo en CPU; sin hardware. El formato `skin.json` es propio de prototipo y no esta validado contra el esquema real. Detalle en `skin/LEEME.md`. El modelo del robot Jumper (kit open-source de KingKong Robotics, Apache-2.0) no se incluye: los scripts lo leen del kit clonado aparte. Sí se incluyen renders hechos con él: `skin/video.mp4` y sus capturas (demostración de estados, uso interno) y `video/` (vídeo del concurso, ver `video/LEEME.md`). Ideas en estudio: `docs/ideas/`.

Hecho para el «Crab Robot Open-Source Motion Contest 2026» de KingKong Robotics.

**Vídeo del concurso**: [`video/video_concurso.mp4`](video/video_concurso.mp4) (1920×1080) y [`video/video_concurso_vertical.mp4`](video/video_concurso_vertical.mp4) (1080×1920), 27 s, sin audio. Cómo se hizo: [`video/LEEME.md`](video/LEEME.md). Inscripción: [`docs/inscripcion/INSCRIPCION.md`](docs/inscripcion/INSCRIPCION.md).

*In English:* glass-shell skin for the Jumper crab robot (KingKong Robotics open-source kit, Apache-2.0). The inner light changes with 4 states, and in the video the robot sweeps a dropped object back to its feet. MuJoCo simulation on CPU; the motion is scripted (inverse kinematics + contact physics), written with AI assistance (Claude). Not real hardware, not AI-generated video. #Jumper #CrabRobot #OpenSourceRobot

Licencia: Apache 2.0 (ver [LICENSE](LICENSE) y [NOTICE](NOTICE)). © 2026 Shania Webstudio. Las marcas y logotipos de Shania no se licencian.
