"""Exporta el Jumper con el skin «shania-cristal» como XML de MuJoCo, para usarlo con el kit (`--model`).

Solo cambia el aspecto: materiales de cristal, un emisor interior y una luz. No añade actuadores, suelo ni masa
(las geometrías del skin no colisionan, y los cuerpos del kit declaran su inercia, así que la masa no cambia). El color
queda fijo en un estado; las luces animadas solo están en `video/escena_concurso.py`.

El XML se escribe DENTRO del kit clonado (junto a `assets/jumper/jumper.xml`, para que las rutas de las mallas sigan
valiendo). No se copia a este repositorio: es un derivado del modelo Apache-2.0 de KingKong Robotics.

Uso: python3 skin/exportar_xml.py --kit RUTA_KIT [--estado alegre|esperando|bateria_baja|cargando]
"""
import argparse, pathlib, sys
import numpy as np
import mujoco

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "shania-cristal"))
import shania_cristal as sc  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", required=True)
    ap.add_argument("--estado", default="alegre", choices=list(sc.ESTADOS))
    a = ap.parse_args()
    kit = pathlib.Path(a.kit).resolve()
    spec = sc.construir(suelo=False, kit=kit, actuadores=False)
    # sin luces de estudio ni ajustes de render de la escena del vídeo: solo el robot
    for nombre in ("clave", "relleno"):
        spec.delete(spec.light(nombre))
    sc.aplicar_spec(spec, a.estado)
    m = spec.compile()
    orig = mujoco.MjModel.from_xml_path(str(kit / sc.MANIFIESTO["base_model"]))
    # comprobaciones: misma cinemática y misma masa que el modelo del kit
    assert (m.nbody, m.njnt, m.nq, m.nv, m.nu) == (orig.nbody, orig.njnt, orig.nq, orig.nv, orig.nu), "cambia la cinemática"
    assert np.allclose(m.body_mass, orig.body_mass), "cambia la masa"
    nuevas = {mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, i) for i in range(m.ngeom)} - \
             {mujoco.mj_id2name(orig, mujoco.mjtObj.mjOBJ_GEOM, i) for i in range(orig.ngeom)}
    assert all(n.startswith("skin_") for n in nuevas), nuevas
    destino = kit / pathlib.Path(sc.MANIFIESTO["base_model"]).parent / f"jumper_shania_cristal_{a.estado}.xml"
    destino.write_text(spec.to_xml())
    mujoco.MjModel.from_xml_path(str(destino))  # el XML escrito carga
    print(f"{destino}  (cuerpos {m.nbody}, articulaciones {m.njnt}, masa {m.body_mass.sum():.4f} kg igual que el kit, "
          f"geometrías nuevas solo visuales: {sorted(nuevas)})")


if __name__ == "__main__":
    main()
