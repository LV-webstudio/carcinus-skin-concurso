"""Escena del vídeo del concurso: el Jumper con el skin «shania-cristal» acerca a sus pies un objeto que se ha caído.

Todo es simulación MuJoCo en CPU (sin hardware). El modelo del robot se lee del kit público de KingKong Robotics
(https://github.com/KingKongRobotics/jumper, Apache-2.0) clonado aparte: este repositorio no lo copia.

Movimiento: guion programado a mano (no es una política entrenada). El brazo delantero izquierdo sigue una trayectoria
cartesiana de su pinza resuelta con cinemática inversa (mínimos cuadrados amortiguados) y la física de MuJoCo resuelve
los contactos: el objeto se mueve porque la pinza lo empuja, no se teletransporta.

Uso:
  MUJOCO_GL=osmesa python3 video/escena_concurso.py --kit RUTA_KIT --out DIR [--w 1920 --h 1080 --fps 30] [--procesos 4]
  --solo-simular   solo física y comprobaciones (rápido)
  --solo-capturas  física + las capturas fijas, sin vídeo
"""
from __future__ import annotations

import argparse, ast, json, math, os, pathlib, subprocess, sys, time
from multiprocessing import Pool

import numpy as np
import mujoco

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ / "skin" / "shania-cristal"))
import shania_cristal as sc  # noqa: E402

FPS_SIM = 500  # pasos de 2 ms

# ---------------------------------------------------------------- guion (segundos)
# Las luces siguen los 4 estados del skin; son ESTADOS ILUSTRATIVOS de la carcasa, no medidas de batería.
GUION_LUZ = [  # (inicio, estado)
    (0.0, "esperando"),
    (3.0, "alegre"),
    (16.0, "bateria_baja"),
    (19.5, "cargando"),
]
DURACION_ESCENA = 23.5
DURACION_CIERRE = 3.5  # tarjeta final con créditos
RUTULOS = [  # (inicio, fin, texto)
    (0.4, 3.0, "Se cae algo cerca del robot"),
    (3.2, 6.0, "Lo localiza"),
    (6.2, 13.6, "Lo acerca a sus pies"),
    (13.8, 16.0, "¡Hecho!"),
    (16.2, 19.4, "Estado de luz: batería baja (ilustrativo)"),
    (19.6, 23.4, "Estado de luz: cargando (ilustrativo)"),
]

OBJ_XY0 = np.array([0.175, 0.215])  # donde cae el objeto (marco del mundo; el robot mira a +x, su izquierda es +y)
OBJ_LADO = 0.032                     # cubo de 3,2 cm
OBJ_MASA = 0.012                     # 12 g
T_CAIDA = 0.6
Y_FIN_BARRIDO = 0.13


# trayectoria de la punta de la pinza izquierda (cuerpo LF_palm_pad_f_link) con el cuerpo en su postura de pie
# (t, xyz). Se interpola con suavizado coseno entre puntos. Barrido lateral: la pinza baja por fuera del objeto
# y lo empuja hacia el robot. Alcance medido del brazo a ras de suelo: x <= 0,28 m (ver parte).
def ruta_pinza(home: np.ndarray) -> list[tuple[float, np.ndarray]]:
    ox, oy = OBJ_XY0
    fuera = oy + OBJ_LADO / 2 + 0.040
    return [
        (0.0, home),
        (4.0, home),
        (5.4, np.array([0.22, 0.12, 0.10])),          # levanta la pinza
        (7.2, np.array([ox, fuera, 0.10])),          # pasa por encima, por fuera del objeto
        (8.6, np.array([ox, fuera, 0.022])),         # baja al suelo
        (12.4, np.array([ox + 0.005, Y_FIN_BARRIDO, 0.022])),  # barre hacia sus pies
        (13.4, np.array([ox + 0.02, Y_FIN_BARRIDO + 0.02, 0.09])),  # levanta
        (14.8, home),                                # vuelve a apoyar
        (99.0, home),
    ]


def leer_home(kit: pathlib.Path) -> dict[str, float]:
    """HOME del kit (tasks/jumper/common/constants.py) leído con ast, sin importar el paquete (que arrastra torch)."""
    src = (kit / "tasks/jumper/common/constants.py").read_text()
    for n in ast.parse(src).body:
        if isinstance(n, ast.AnnAssign) and getattr(n.target, "id", "") == "HOME":
            return ast.literal_eval(n.value)
    raise RuntimeError("no se encontró HOME en constants.py del kit")


def construir_modelo(kit: pathlib.Path) -> mujoco.MjModel:
    spec = sc.construir(kit=kit)
    mat = spec.add_material(name="objeto")
    mat.rgba = [1.0, 0.98, 0.94, 1.0]; mat.specular = 0.4; mat.shininess = 0.6; mat.emission = 0.25
    b = spec.worldbody.add_body(name="objeto", pos=[*OBJ_XY0, 0.32])
    b.add_freejoint(name="objeto_libre")
    h = OBJ_LADO / 2
    b.add_geom(name="objeto_geom", type=mujoco.mjtGeom.mjGEOM_BOX, size=[h, h, h], mass=OBJ_MASA,
               material="objeto", friction=[0.6, 0.005, 0.0001], group=0)
    return spec.compile()


def suave(a: float) -> float:
    a = min(max(a, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * a)


def interp(ruta, t):
    for (t0, p0), (t1, p1) in zip(ruta, ruta[1:]):
        if t0 <= t <= t1:
            return p0 + (p1 - p0) * suave((t - t0) / (t1 - t0))
    return ruta[-1][1]


class IKBrazo:
    """IK de posición de la pinza LF con el cuerpo fijo en la postura de pie (modelo cinemático aparte)."""

    def __init__(self, m: mujoco.MjModel, home: dict[str, float], z_pie: float):
        self.m = m; self.d = mujoco.MjData(m)
        self.jn = [f"LF_J{i}_joint" for i in range(4)]
        self.jid = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n) for n in self.jn]
        self.qadr = [m.jnt_qposadr[j] for j in self.jid]
        self.vadr = [m.jnt_dofadr[j] for j in self.jid]
        self.rng = np.array([m.jnt_range[j] for j in self.jid])
        self.bid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "LF_palm_pad_f_link")
        for n, v in home.items():
            self.d.qpos[m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)]] = v
        self.d.qpos[2] = z_pie; self.d.qpos[3:7] = [1, 0, 0, 0]
        mujoco.mj_kinematics(m, self.d)
        self.home_pinza = self.d.xpos[self.bid].copy()
        self.q = np.array([home[n] for n in self.jn])

    def resolver(self, objetivo: np.ndarray, iters: int = 60) -> tuple[np.ndarray, float]:
        m, d = self.m, self.d
        jacp = np.zeros((3, m.nv))
        for _ in range(iters):
            d.qpos[self.qadr] = self.q
            mujoco.mj_kinematics(m, d); mujoco.mj_comPos(m, d)
            err = objetivo - d.xpos[self.bid]
            if np.linalg.norm(err) < 2e-4:
                break
            mujoco.mj_jacBody(m, d, jacp, None, self.bid)
            Jm = jacp[:, self.vadr]
            dq = Jm.T @ np.linalg.solve(Jm @ Jm.T + 1e-4 * np.eye(3), err)
            self.q = np.clip(self.q + np.clip(dq, -0.2, 0.2), self.rng[:, 0] + 0.02, self.rng[:, 1] - 0.02)
        d.qpos[self.qadr] = self.q; mujoco.mj_kinematics(m, d)
        return self.q.copy(), float(np.linalg.norm(objetivo - d.xpos[self.bid]))


def simular(kit: pathlib.Path, fps: int):
    """Física completa. Devuelve qpos por fotograma y un registro de comprobaciones."""
    home = leer_home(kit)
    m = construir_modelo(kit); d = mujoco.MjData(m)
    z_pie = 0.1055
    ik = IKBrazo(m, home, z_pie)
    ruta = ruta_pinza(ik.home_pinza)
    act = {mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, i): i for i in range(m.nu)}
    for n, v in home.items():
        d.qpos[m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)]] = v
        d.ctrl[act[n]] = v
    d.qpos[2] = z_pie; d.qpos[3:7] = [1, 0, 0, 0]
    oq = m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "objeto_libre")]
    ov = m.jnt_dofadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "objeto_libre")]
    d.qpos[oq:oq + 3] = [*OBJ_XY0, 0.32]
    mujoco.mj_forward(m, d)
    sub = int(round(1 / fps / m.opt.timestep))
    nfr = int(round(DURACION_ESCENA * fps))
    qs, err_max = [], 0.0
    sostener = True
    for f in range(nfr):
        t = f / fps
        # objeto sujeto en el aire hasta T_CAIDA (sin velocidad), después cae libre
        if t < T_CAIDA:
            d.qpos[oq:oq + 7] = [*OBJ_XY0, 0.32, 1, 0, 0, 0]; d.qvel[ov:ov + 6] = 0
        objetivo = interp(ruta, t)
        q, e = ik.resolver(objetivo)
        if 4.0 <= t <= 14.8:
            err_max = max(err_max, e)
        ctrl = dict(home)
        for n, v in zip(ik.jn, q):
            ctrl[n] = v
        # «alegre» al final de la tarea: pequeño balanceo de cuerpo con las patas medias
        if 13.8 <= t < 16.0:
            s = 0.08 * math.sin(2 * math.pi * 1.0 * (t - 13.8)) * suave((t - 13.8) / 0.4) * suave((16.0 - t) / 0.4)
            for p, sg in (("LM", 1), ("RM", -1), ("LR", 1), ("RR", -1)):
                ctrl[f"{p}_J1_joint"] = home[f"{p}_J1_joint"] + sg * s
        # batería baja y cargando: se agacha despacio y reposa (solo gesto, no simula batería)
        if t >= 16.0:
            a = suave((t - 16.0) / 3.0) * 0.18
            for p, sg in (("LM", 1), ("RM", -1), ("LR", 1), ("RR", -1)):
                ctrl[f"{p}_J1_joint"] = home[f"{p}_J1_joint"] - sg * a
        for n, v in ctrl.items():
            d.ctrl[act[n]] = v
        for _ in range(sub):
            mujoco.mj_step(m, d)
        qs.append(d.qpos.copy())
    qs = np.array(qs)
    obj = qs[:, oq:oq + 3]
    def en(t):
        return obj[min(int(t * fps), len(obj) - 1)]
    reg = {
        "mujoco": mujoco.__version__,
        "fotogramas_escena": nfr,
        "error_ik_max_m": round(err_max, 4),
        "objeto_tras_caer_xyz": np.round(en(3.0), 4).tolist(),
        "objeto_final_xyz": np.round(obj[-1], 4).tolist(),
        "objeto_desplazamiento_m": round(float(np.linalg.norm(en(3.0)[:2] - obj[-1][:2])), 4),
        "objeto_dist_xy_a_pinza_izq_en_reposo_m": round(float(np.linalg.norm(obj[-1][:2] - ik.home_pinza[:2])), 4),
        "cuerpo_z_min_max": [round(float(qs[:, 2].min()), 4), round(float(qs[:, 2].max()), 4)],
        "cuerpo_xy_final": np.round(qs[-1, :2], 4).tolist(),
    }
    return m, qs, reg


def estado_en(t: float):
    est, t0 = GUION_LUZ[0][1], 0.0
    prev = None
    for i, (ti, e) in enumerate(GUION_LUZ):
        if t >= ti:
            prev = GUION_LUZ[i - 1][1] if i > 0 else None
            est, t0 = e, ti
    return est, t0, prev


# ---------------------------------------------------------------- render en paralelo
_G = {}


def _init(kit, w, h):
    m = construir_modelo(pathlib.Path(kit))
    _G.update(m=m, d=mujoco.MjData(m), r=mujoco.Renderer(m, h, w), piel=sc.Piel(m), w=w, h=h)
    _G["r"].scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW] = 1
    _G["r"].scene.flags[mujoco.mjtRndFlag.mjRND_REFLECTION] = 1


def camara(t: float, base_xy: np.ndarray) -> mujoco.MjvCamera:
    """Plano general para la caída, acercamiento frontal durante el barrido y se abre al final."""
    cam = mujoco.MjvCamera(); cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    acerc = suave((t - 3.5) / 3.0) - suave((t - 14.0) / 3.0)
    cam.lookat[:] = np.array([base_xy[0] + 0.12, base_xy[1] + 0.10, 0.035 + 0.02 * acerc])
    cam.distance = 0.70 - 0.17 * acerc + 0.04 * suave((t - 16.0) / 7.0)
    cam.azimuth = 165 + 12 * acerc + 18 * suave((t - 14.0) / 9.5)
    cam.elevation = -28 - 9 * acerc
    return cam


def _render(args):
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    f, qpos, fps, out = args
    m, d, r, piel, w, h = (_G[k] for k in ("m", "d", "r", "piel", "w", "h"))
    t = f / fps
    d.qpos[:] = qpos; mujoco.mj_forward(m, d)
    est, t0, prev = estado_en(t)
    col, inten = sc.color_estado(est, t - t0)
    if prev is not None and t - t0 < 0.5:
        wgt = (t - t0) / 0.5; col = sc.PALETA[sc.ESTADOS[prev]["color"]] * (1 - wgt) + col * wgt
    piel.aplicar(col, inten)
    opt = mujoco.MjvOption(); opt.geomgroup[:] = [1, 0, 1, 0, 0, 0]
    r.update_scene(d, camera=camara(t, qpos[:2]), scene_option=opt)
    arr = r.render().astype(np.float32)
    # resplandor (posproceso de imagen, no física)
    lum = arr.max(2); mask = np.clip((lum - 170) / 85, 0, 1)[..., None] * (arr / 255.0)
    glow = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(h * 0.018))
    img = Image.fromarray(np.clip(arr + np.asarray(glow).astype(np.float32) * 0.55 * (0.4 + 0.6 * inten), 0, 255).astype(np.uint8))
    rotular(img, t, est, inten)
    img.save(out / "frames" / f"f{f:05d}.png")
    return f


def fuentes(h):
    from PIL import ImageFont
    base = "/usr/share/fonts/truetype/dejavu/"
    return (ImageFont.truetype(base + "DejaVuSans-Bold.ttf", int(h * 0.042)),
            ImageFont.truetype(base + "DejaVuSans.ttf", int(h * 0.024)),
            ImageFont.truetype(base + "DejaVuSans-Bold.ttf", int(h * 0.036)))


def rotular(img, t, est, inten):
    from PIL import ImageDraw
    w, h = img.size
    fg, fc, fr = fuentes(h)
    dr = ImageDraw.Draw(img, "RGBA")
    e = sc.ESTADOS[est]; hexc = sc.MANIFIESTO["palette"][e["color"]]["hex"]
    rc = tuple(int(c * 255) for c in sc.PALETA[e["color"]])
    x0, y0 = w * .03, h * .05
    dr.rounded_rectangle([x0, y0, x0 + w * .30, y0 + h * .105], 14, fill=(5, 8, 14, 210), outline=rc, width=3)
    dr.ellipse([x0 + h * .02, y0 + h * .03, x0 + h * .065, y0 + h * .075], fill=tuple(int(c * (0.15 + .85 * inten)) for c in rc))
    dr.text((x0 + h * .085, y0 + h * .012), e["label"], font=fg, fill=(235, 240, 250))
    dr.text((x0 + h * .085, y0 + h * .064), f"skin shania-cristal  ·  {hexc}", font=fc, fill=(150, 160, 180))
    # marca de agua permanente
    dr.text((w * .97, h * .955), "Simulación MuJoCo en CPU · modelo Jumper © KingKong Robotics (Apache-2.0)",
            font=fc, fill=(170, 178, 195, 200), anchor="rs")
    for a, b, txt in RUTULOS:
        if a <= t <= b:
            al = int(255 * min(1, (t - a) / 0.3, (b - t) / 0.3))
            tw = dr.textlength(txt, font=fr)
            cx, cy = w / 2, h * .86
            dr.rounded_rectangle([cx - tw / 2 - 24, cy - h * .035, cx + tw / 2 + 24, cy + h * .035], 18, fill=(5, 8, 14, int(al * .8)))
            dr.text((cx, cy), txt, font=fr, fill=(240, 244, 252, al), anchor="mm")


def tarjeta_cierre(out: pathlib.Path, w: int, h: int, fps: int, f0: int):
    from PIL import Image, ImageDraw
    fg, fc, fr = fuentes(h)
    ultimo = Image.open(out / "frames" / f"f{f0 - 1:05d}.png").convert("RGB")
    logo = None
    lp = RAIZ / "assets" / "marca" / "logo.png"
    if lp.exists():
        logo = Image.open(lp).convert("RGBA"); logo.thumbnail((int(h * .16), int(h * .16)))
    lineas = [
        (fr, "Skin «shania-cristal» · prototipo en simulación", (235, 240, 250)),
        (fc, "Robot: modelo Jumper del kit open-source de KingKong Robotics (Apache-2.0)", (190, 198, 215)),
        (fc, "Skin, escena y movimiento: Shania Webstudio", (190, 198, 215)),
        (fc, "Movimiento programado y escena escritos con asistencia de IA (Claude).", (190, 198, 215)),
        (fc, "Render físico de MuJoCo; no es vídeo generado por IA. Sin hardware real.", (190, 198, 215)),
    ]
    n = int(DURACION_CIERRE * fps)
    for i in range(n):
        a = min(1.0, i / (0.6 * fps))
        img = Image.blend(ultimo, Image.new("RGB", (w, h), (6, 8, 14)), 0.88 * a)
        dr = ImageDraw.Draw(img, "RGBA")
        y = h * .30
        if logo is not None:
            lg = logo.copy(); lg.putalpha(lg.getchannel("A").point(lambda v: int(v * a)))
            img.paste(lg, (int(w / 2 - lg.width / 2), int(h * .12)), lg); y = h * .36
        for fnt, txt, c in lineas:
            dr.text((w / 2, y), txt, font=fnt, fill=(*c, int(255 * a)), anchor="mm"); y += h * (0.075 if fnt is fr else 0.055)
        img.save(out / "frames" / f"f{f0 + i:05d}.png")
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--w", type=int, default=1920); ap.add_argument("--h", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=30); ap.add_argument("--procesos", type=int, default=os.cpu_count())
    ap.add_argument("--solo-simular", action="store_true"); ap.add_argument("--solo-capturas", action="store_true")
    a = ap.parse_args()
    kit, out = pathlib.Path(a.kit).resolve(), pathlib.Path(a.out).resolve()
    (out / "frames").mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    m, qs, reg = simular(kit, a.fps)
    reg["segundos_simulacion"] = round(time.time() - t0, 1)
    print(json.dumps(reg, ensure_ascii=False, indent=1))
    if a.solo_simular:
        return
    # instantes elegidos: caída en el aire, pinza abajo, mitad del barrido, final, pico del parpadeo y del pulso
    capt = {"captura_1_caida": 0.72, "captura_2_alcanza": 8.6, "captura_3_arrastra": 10.6,
            "captura_4_hecho": 15.0, "captura_5_bateria_baja": 16.75, "captura_6_cargando": 22.0}
    idx = list(range(len(qs))) if not a.solo_capturas else sorted({int(v * a.fps) for v in capt.values()})
    t1 = time.time()
    with Pool(a.procesos, initializer=_init, initargs=(str(kit), a.w, a.h)) as p:
        for i, _ in enumerate(p.imap_unordered(_render, [(f, qs[f], a.fps, out) for f in idx], chunksize=4)):
            if i % 60 == 0:
                print(f"render {i}/{len(idx)}  {time.time() - t1:.0f} s", flush=True)
    from PIL import Image
    for nombre, ts in capt.items():
        Image.open(out / "frames" / f"f{int(ts * a.fps):05d}.png").save(out / f"{nombre}.png")
    if a.solo_capturas:
        return
    n_cierre = tarjeta_cierre(out, a.w, a.h, a.fps, len(qs))
    Image.open(out / "frames" / f"f{len(qs) + n_cierre - 1:05d}.png").save(out / "captura_7_creditos.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps), "-i", str(out / "frames" / "f%05d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "slow", "-an", "-movflags", "+faststart",
                    str(out / "video_concurso.mp4")], check=True)
    reg["segundos_render"] = round(time.time() - t1, 1)
    reg["fotogramas_total"] = len(qs) + n_cierre
    (out / "registro.json").write_text(json.dumps(reg, ensure_ascii=False, indent=1))
    print("vídeo:", out / "video_concurso.mp4")


if __name__ == "__main__":
    main()
