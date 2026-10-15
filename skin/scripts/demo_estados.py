"""Recorre los 4 estados del skin shania-cristal mientras el Jumper hace un gesto sencillo (saluda con las patas
delanteras y se balancea) en MuJoCo CPU. Render sin ventana (MUJOCO_GL=egl/osmesa) y MP4 con ffmpeg.

Uso: MUJOCO_GL=egl python scripts_skin/demo_estados.py --out DIR [--seg 4.5] [--fps 30] [--w 1280 --h 720] [--solo-capturas]
"""
import argparse, os, pathlib, subprocess, sys
import numpy as np
import mujoco
RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skins" / "shania-cristal"))
import shania_cristal as sc
sys.path.insert(0, str(RAIZ))
from tasks.jumper.common.constants import HOME

ORDEN = ["alegre", "esperando", "bateria_baja", "cargando"]


def objetivo(t, estado):
    """Gesto sencillo. alegre: saluda con el brazo izquierdo; resto: balanceo suave en el sitio."""
    q = dict(HOME)
    if estado == "alegre":
        q["LF_J1_joint"] = HOME["LF_J1_joint"] - 0.9
        q["LF_J0_joint"] = HOME["LF_J0_joint"] + 0.45 * np.sin(2 * np.pi * 1.2 * t)
        q["RF_J0_joint"] = HOME["RF_J0_joint"] - 0.15 * np.sin(2 * np.pi * 1.2 * t)
    elif estado == "esperando":
        s = np.sin(2 * np.pi * 0.35 * t)
        for p in ("LF", "RF"):
            q[f"{p}_J1_joint"] = HOME[f"{p}_J1_joint"] + 0.10 * s
    elif estado == "bateria_baja":
        s = np.sin(2 * np.pi * 0.2 * t)
        for p in ("LM", "RM", "LR", "RR"):
            q[f"{p}_J1_joint"] = HOME[f"{p}_J1_joint"] + (0.06 if p[0] == "L" else -0.06) * s * -1
    else:  # cargando: quieto, solo respira con el cuerpo
        s = np.sin(2 * np.pi * 0.25 * t)
        for p in ("LF", "RF"):
            q[f"{p}_J1_joint"] = HOME[f"{p}_J1_joint"] + 0.05 * s
    return q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True); ap.add_argument("--seg", type=float, default=4.5)
    ap.add_argument("--fps", type=int, default=30); ap.add_argument("--w", type=int, default=1280); ap.add_argument("--h", type=int, default=720)
    ap.add_argument("--solo-capturas", action="store_true")
    a = ap.parse_args()
    out = pathlib.Path(a.out); (out / "frames").mkdir(parents=True, exist_ok=True)
    spec = sc.construir(); m = spec.compile(); d = mujoco.MjData(m)
    piel = sc.Piel(m)
    jid = {mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, i): i for i in range(m.nu)}
    # pose inicial: HOME, cuerpo a la altura de pie
    for n, v in HOME.items():
        d.qpos[m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)]] = v
    d.qpos[2] = 0.13; d.qpos[3:7] = [1, 0, 0, 0]
    mujoco.mj_forward(m, d)
    r = mujoco.Renderer(m, a.h, a.w)
    r.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW] = 1; r.scene.flags[mujoco.mjtRndFlag.mjRND_REFLECTION] = 1
    cam = mujoco.MjvCamera(); cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    opt = mujoco.MjvOption(); opt.geomgroup[:] = [1, 0, 1, 0, 0, 0]  # sin colision (grupo 1)
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    try:
        fuente = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(a.h * 0.055))
        fchica = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(a.h * 0.028))
    except Exception:
        fuente = fchica = ImageFont.load_default()
    nframes_seg = int(a.seg * a.fps); sub = int(round(1 / a.fps / m.opt.timestep)); fade = 0.5
    nfr = 0; t = 0.0; caps = {}
    prev_col = None
    for k, est in enumerate(ORDEN):
        for i in range(nframes_seg):
            ts = i / a.fps
            q = objetivo(t, est)
            for n, v in q.items():
                d.ctrl[jid[n]] = v
            for _ in range(sub):
                mujoco.mj_step(m, d)
            col, inten = sc.color_estado(est, ts)
            # fundido de color al entrar en el estado
            if prev_col is not None and ts < fade:
                w = ts / fade; col = prev_col * (1 - w) + col * w
            piel.aplicar(col, inten)
            # camara: orbita lenta alrededor del robot
            cam.lookat[:] = d.qpos[:3] + [0, 0, 0.02]; cam.distance = 0.55
            cam.azimuth = 125 + 22 * np.sin(2 * np.pi * t / 18) + 12 * (t / 18); cam.elevation = -17
            r.update_scene(d, camera=cam, scene_option=opt)
            img = Image.fromarray(r.render())
            # brillo (bloom): desenfoque de los pixeles muy luminosos y saturados
            arr = np.asarray(img).astype(np.float32)
            lum = arr.max(2); mask = np.clip((lum - 170) / 85, 0, 1)[..., None] * (arr / 255.0)
            glow = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(a.h * 0.018))
            img = Image.fromarray(np.clip(arr + np.asarray(glow).astype(np.float32) * 0.55 * (0.4 + 0.6 * inten), 0, 255).astype(np.uint8))
            dr = ImageDraw.Draw(img)
            nombre = sc.ESTADOS[est]["label"]; hexc = sc.MANIFIESTO["palette"][sc.ESTADOS[est]["color"]]["hex"]
            rc = tuple(int(c * 255) for c in sc.PALETA[sc.ESTADOS[est]["color"]])
            dr.rounded_rectangle([a.w * .03, a.h * .05, a.w * .03 + a.w * .36, a.h * .05 + a.h * .12], 14, fill=(5, 8, 14, 230), outline=rc, width=3)
            dr.ellipse([a.w * .045, a.h * .085, a.w * .045 + a.h * .05, a.h * .085 + a.h * .05], fill=tuple(int(c * (0.15 + .85 * inten)) for c in rc))
            dr.text((a.w * .045 + a.h * .07, a.h * .066), nombre, font=fuente, fill=(235, 240, 250))
            dr.text((a.w * .045 + a.h * .07, a.h * .066 + a.h * .06), f"{hexc}  ·  simulacion CPU", font=fchica, fill=(150, 160, 180))
            if ts > 1.6 and inten >= 0.9 * sc.ESTADOS[est]['max'] and est not in caps:
                img.save(out / f"captura_{k+1}_{est}.png"); caps[est] = True
            if not a.solo_capturas:
                img.save(out / "frames" / f"f{nfr:05d}.png")
            nfr += 1; t += 1 / a.fps
        prev_col = sc.PALETA[sc.ESTADOS[est]["color"]]
    print("frames", nfr, "altura final cuerpo z=%.3f" % d.qpos[2])
    if not a.solo_capturas:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps), "-i", str(out / "frames" / "f%05d.png"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-an", "-movflags", "+faststart",
                        str(out / "video.mp4")], check=True)


if __name__ == "__main__":
    main()
