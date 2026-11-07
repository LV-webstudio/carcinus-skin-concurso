# Informe para legatus · CARCINUS, vídeo del concurso (07-11-2026)

De: sesión de la nube «Carcinus concurso video». Por encargo de Lorenzo, que pidió informar a legatus por PR. **No se ha publicado nada.**

## Estado
| Tema | Estado |
|---|---|
| Vídeo | **Terminado y aprobado por Lorenzo (02-11).** En `main`: `video/video_concurso.mp4` (1920×1080, 27 s, sin audio; commit `c56528a`, 01-11) y `video/video_concurso_vertical.mp4` (1080×1920, 27 s, sin audio; commit `bf4a980`, 02-11). |
| Repositorio | Público con Apache-2.0 (el cambio de licencia lo autorizó Lucy el 01-11). PR #1, #2 y #3 fusionados; último merge `e87080a` (02-11). Revisado sobre una copia limpia: sumas correctas, no hay modelo del kit copiado ni credenciales, y los enlaces funcionan. |
| Inscripción | Preparada en `docs/inscripcion/INSCRIPCION.md`. No hay formulario: se participa publicando en X o YouTube un vídeo de más de 15 s con `#Jumper #CrabRobot #OpenSourceRobot` y `@KingKong Robotics`. El concurso termina el **30-11-2026**. |
| Publicación | **Pendiente (la hace Lucy).** La tabla de publicación de `INSCRIPCION.md` sigue vacía: no consta ninguna URL. |
| Bases | **No se han leído en la fuente oficial**: <https://beunlimited.me/en/events/crab-robot-challenge-2026> no se puede abrir desde la red de la nube. Se usó la transcripción que hizo otro participante tras leer la página oficial el 28-10 (`github.com/Omshri07/crab-rave-jumper`, carpeta `5_RULES/`), contrastada con búsquedas web. Hay que verificarlas en la página oficial antes de publicar. |
| GPU | Aprobada por Lorenzo (02-11). El plan está en `docs/ideas/GPU-movimientos.md`: el cuaderno de Colab del kit, que tiene que lanzar una persona con su cuenta de Google. `skin/exportar_xml.py` hace que el reproductor y el entrenamiento del propio kit funcionen con nuestro skin (probado en CPU). No se ha entrenado nada en GPU ni hay cifras. |

## Lo que queda y de quién
1. **Lucy**: verificar las bases en la página oficial (sobre todo el usuario exacto de KingKong para la mención), publicar siguiendo `INSCRIPCION.md`, apuntar el enlace en su tabla y vigilar los mensajes privados de esa cuenta (si se gana, hay 5 días para responder).
2. **Quien tenga cuenta de Google**: lanzar el entrenamiento en Colab con los pasos de `docs/ideas/GPU-movimientos.md`; sin servicios de pago salvo permiso de Lorenzo.
3. **Entorno de la nube**: el script de preparación falla al comprobar `Godot_v4.7.2-stable_mono_linux_x86_64.zip`, que no se descarga. Hay que corregirlo en la configuración del entorno; no afecta a Carcinus.

## Consultas recibidas
- 06-11: praefectus (L-6764, orden de Lucy) preguntó por el estado del vídeo; se le respondió con lo mismo que este informe, sin publicar nada.
