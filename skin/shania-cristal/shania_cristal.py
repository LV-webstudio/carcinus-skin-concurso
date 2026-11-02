"""Skin «shania-cristal» (prototipo en simulacion): carcasa de cristal + emisor interior con 4 estados.

Aplica el skin sobre assets/jumper/jumper.xml con MjSpec (sin tocar el XML original) y ofrece
`Estado.color_intensidad(t)` para animar parpadeo y pulso. Solo MuJoCo + numpy.
"""
from __future__ import annotations
import json, math, pathlib
import numpy as np
import mujoco

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
MANIFIESTO = json.loads((AQUI / "skin.json").read_text())


def hex_rgb(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


PALETA = {k: hex_rgb(v["hex"]) for k, v in MANIFIESTO["palette"].items()}
ESTADOS = MANIFIESTO["states"]


def intensidad(est: dict, t: float) -> float:
    """0..1 segun el patron del estado: breath (respira), blink (parpadeo on/off), pulse (pulso suave)."""
    p, hz, lo, hi = est["pattern"], est["hz"], est["min"], est["max"]
    fase = (t * hz) % 1.0
    if p == "blink":
        # parpadeo con rampa corta (~40 ms) para que no sea un salto de un fotograma
        on = fase < est.get("duty", 0.5)
        return hi if on else lo
    if p == "pulse":
        # pulso asimetrico: sube rapido (25 % del ciclo) y baja lento, como un latido
        x = math.sin(0.5 * math.pi * fase / 0.25) if fase < 0.25 else 0.5 + 0.5 * math.cos(math.pi * (fase - 0.25) / 0.75)
        return lo + (hi - lo) * x
    return lo + (hi - lo) * (0.5 - 0.5 * math.cos(2 * math.pi * fase))  # breath


def _mat(spec, name, rgba, specular=0.5, shininess=0.5, reflectance=0.0, emission=0.0):
    m = spec.add_material(name=name)
    m.rgba = rgba
    m.specular, m.shininess, m.reflectance, m.emission = specular, shininess, reflectance, emission
    return m


def construir(suelo: bool = True, kit: str | pathlib.Path | None = None, actuadores: bool = True) -> mujoco.MjSpec:
    """Devuelve el MjSpec del Jumper con el skin aplicado, actuadores de posicion y escena de estudio.

    `kit`: carpeta del kit público de KingKong Robotics (github.com/KingKongRobotics/jumper). El modelo se lee
    de ahí y no se copia a este repositorio. Por defecto, la raíz de este repo (uso antiguo, copia local del kit).
    """
    base = pathlib.Path(kit) if kit is not None else RAIZ
    spec = mujoco.MjSpec.from_file(str(base / MANIFIESTO["base_model"]))
    g = MANIFIESTO["glass"]
    for nombre, clave in (("cristal_carcasa", "shell"), ("cristal_miembro", "limbs"), ("grafito", "frame")):
        c = g[clave]
        _mat(spec, nombre, c["rgba"], c.get("specular", .5), c.get("shininess", .5), c.get("reflectance", 0.0))
    _mat(spec, "pantalla", g["display"]["rgba"], 0.9, 0.9)
    _mat(spec, "nucleo", [1, 1, 1, 1], 0.0, 0.0, 0.0, emission=1.0)
    _mat(spec, "led", [1, 1, 1, 1], 0.0, 0.0, 0.0, emission=1.0)

    # materiales en las geometrias VISUALES (las de colision no se dibujan)
    for geom in spec.geoms:
        if not geom.name.endswith("_visual"):
            continue
        n = geom.name[:-7]
        geom.rgba = [0.5, 0.5, 0.5, 1]  # por defecto -> manda el material
        if n == "upper_shell_link":
            geom.material = "cristal_carcasa"
        elif n == "base_link":
            geom.material = "grafito"
        elif n in ("display_module_link", "tof_sensor_link", "camera_link"):
            geom.material = "pantalla"
        else:
            geom.material = "cristal_miembro"

    # emisor interior: nucleo (elipsoide luminoso) + una cuenta LED por cadera, dentro de la carcasa
    shell = spec.body("upper_shell_link")
    e = MANIFIESTO["emitters"]["core"]
    c = shell.add_geom(name="skin_nucleo", type=mujoco.mjtGeom.mjGEOM_ELLIPSOID, pos=e["pos"], size=e["size"],
                       material="nucleo", contype=0, conaffinity=0, group=2)
    for i, (x, y) in enumerate([(0.035, 0.05), (0.035, -0.05), (-0.002, 0.07), (-0.002, -0.07), (-0.04, 0.05), (-0.04, -0.05)]):
        shell.add_geom(name=f"skin_led{i}", type=mujoco.mjtGeom.mjGEOM_SPHERE, pos=[x, y, 0.012], size=[0.0065, 0, 0],
                       material="led", contype=0, conaffinity=0, group=2)
    L = MANIFIESTO["emitters"]["light"]
    shell.add_light(name="skin_luz", pos=L["pos"], dir=[0, 0, -1], diffuse=[1, 1, 1], specular=[0, 0, 0],
                    castshadow=False, attenuation=[1, 0, 25], mode=mujoco.mjtCamLight.mjCAMLIGHT_FIXED)

    # actuadores de posicion (el XML del kit no trae; los de entrenamiento los pone el marco rl/mjrl)
    for j in (spec.joints if actuadores else []):
        if j.name.endswith("_joint") and j.type == mujoco.mjtJoint.mjJNT_HINGE:
            spec.add_actuator(name=j.name, target=j.name, trntype=mujoco.mjtTrn.mjTRN_JOINT,
                              gainprm=[25, 0, 0, 0, 0, 0, 0, 0, 0, 0], biasprm=[0, -25, -1.0, 0, 0, 0, 0, 0, 0, 0],
                              biastype=mujoco.mjtBias.mjBIAS_AFFINE, forcerange=[-1.7, 1.7], forcelimited=True)

    # estudio
    if suelo:
        spec.add_texture(name="grid", type=mujoco.mjtTexture.mjTEXTURE_2D, builtin=mujoco.mjtBuiltin.mjBUILTIN_CHECKER,
                         rgb1=[0.10, 0.11, 0.16], rgb2=[0.15, 0.16, 0.22], width=512, height=512)
        mm = spec.add_material(name="suelo"); mm.textures[mujoco.mjtTextureRole.mjTEXROLE_RGB] = "grid"
        mm.texrepeat = [8, 8]; mm.reflectance = 0.25; mm.specular = 0.3
        spec.worldbody.add_geom(name="suelo", type=mujoco.mjtGeom.mjGEOM_PLANE, size=[2, 2, 0.05], material="suelo",
                                friction=[1, .005, .0001])
    spec.worldbody.add_light(name="clave", pos=[0.6, -0.6, 1.2], dir=[-0.5, 0.5, -1], diffuse=[.35, .35, .4], specular=[.2, .2, .2], castshadow=True)
    spec.worldbody.add_light(name="relleno", pos=[-0.8, 0.5, 0.6], dir=[0.8, -0.4, -0.5], diffuse=[.2, .22, .3], specular=[0, 0, 0], castshadow=False)
    spec.add_texture(name="cielo", type=mujoco.mjtTexture.mjTEXTURE_SKYBOX, builtin=mujoco.mjtBuiltin.mjBUILTIN_GRADIENT,
                     rgb1=[0.10, 0.12, 0.20], rgb2=[0.01, 0.01, 0.03], width=512, height=512)
    spec.visual.rgba.haze = [0.02, 0.025, 0.04, 1]
    spec.visual.headlight.ambient = [0.10, 0.11, 0.15]
    spec.visual.headlight.diffuse = [0.12, 0.12, 0.15]
    spec.visual.global_.offwidth, spec.visual.global_.offheight = 1920, 1080
    spec.visual.quality.shadowsize = 4096
    spec.option.timestep = 0.002
    return spec


class Piel:
    """Pone color/intensidad del emisor en el modelo ya compilado."""

    def __init__(self, model: mujoco.MjModel):
        self.m = model
        mid = lambda n: mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_MATERIAL, n)
        self.shell, self.limbs, self.core, self.led = (mid(n) for n in ("cristal_carcasa", "cristal_miembro", "nucleo", "led"))
        self.luz = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_LIGHT, "skin_luz")
        g = MANIFIESTO["glass"]
        self.base_shell, self.base_limbs = np.array(g["shell"]["rgba"]), np.array(g["limbs"]["rgba"])
        self.mix_shell, self.mix_limbs = g["shell"]["glow_mix"], g["limbs"]["glow_mix"]
        self.gain = MANIFIESTO["emitters"]["light"]["diffuse_gain"]

    def aplicar(self, color: np.ndarray, inten: float):
        m = self.m
        # nucleo y LEDs: color puro, brillo = intensidad (apagado casi total en la fase "off" del parpadeo)
        for i in (self.core, self.led):
            m.mat_rgba[i] = [*(color * (0.10 + 0.90 * inten)), 1.0]
            m.mat_emission[i] = 0.15 + 0.45 * inten
        # el cristal se tine un poco del color (luz atrapada en el vidrio), sin perder transparencia
        for i, base, mix in ((self.shell, self.base_shell, self.mix_shell), (self.limbs, self.base_limbs, self.mix_limbs)):
            rgb = base[:3] * (1 - mix * inten) + color * (mix * inten)
            m.mat_rgba[i] = [*rgb, base[3] + 0.10 * inten]
            m.mat_emission[i] = 0.30 * inten * mix
        m.light_diffuse[self.luz] = color * inten * self.gain


def color_estado(clave: str, t: float):
    est = ESTADOS[clave]
    return PALETA[est["color"]], intensidad(est, t)


def aplicar_spec(spec: mujoco.MjSpec, clave: str, inten: float | None = None) -> None:
    """Fija en el MjSpec (antes de compilar) el color de un estado, para exportar un XML estático."""
    est = ESTADOS[clave]
    color = PALETA[est["color"]]
    inten = est["max"] if inten is None else inten
    g = MANIFIESTO["glass"]
    for nombre in ("nucleo", "led"):
        m = spec.material(nombre)
        m.rgba = [*(color * (0.10 + 0.90 * inten)), 1.0]; m.emission = 0.15 + 0.45 * inten
    for nombre, clave_g in (("cristal_carcasa", "shell"), ("cristal_miembro", "limbs")):
        base, mix = np.array(g[clave_g]["rgba"]), g[clave_g]["glow_mix"]
        m = spec.material(nombre)
        m.rgba = [*(base[:3] * (1 - mix * inten) + color * (mix * inten)), base[3] + 0.10 * inten]
        m.emission = 0.30 * inten * mix
    spec.light("skin_luz").diffuse = color * inten * MANIFIESTO["emitters"]["light"]["diffuse_gain"]
