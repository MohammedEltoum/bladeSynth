"""Synthetic blade-defect dataset generator (Corrosion, Dent, Nick, Normal, Scratch).

One script drives all five scenes headless. Each render produces an image and a
binary mask (0 = background, 255 = defect); Normal produces an all-black mask.

Render one defect type (run inside Blender, arguments go after "--"):

    blender -b --factory-startup Dent.blend --python generate_dataset.py -- --count 100 --seed 7

Render every type in one go (run with plain Python; it launches Blender per file):

    python generate_dataset.py --count 100 --seed 7

Options (both modes):
    --count N        images to render per type (default 10)
    --seed S         base random seed (default 0); same seed + index = same image
    --start I        first image index, for resuming or splitting a run (default 0)
    --out DIR        output folder; default is output/<Type>/ next to the .blend
    --resolution PX  square render size (default 1024)
    --max-angle DEG  view angle is drawn from [-DEG, DEG] (default 30, as in the paper)
Inside Blender only:
    --type T         defect type; default is taken from the .blend file name
Launcher only:
    --types T [T..]  which types to render (default: all five)
    --blend-dir DIR  folder holding the .blend files (default: this script's folder)
    --blender PATH   blender.exe to use (default: $BLENDER, then Blender 4.1 install)

Every image also gets a line in <out>/metadata.jsonl with the seed, background
and all randomized parameters, so any sample can be traced and re-rendered.
"""

import argparse
import json
import os
import struct
import sys
import zlib

try:
    import bpy
    import numpy as np  # bundled with Blender; the launcher doesn't need it
except ImportError:
    bpy = None

TYPES = ["Corrosion", "Dent", "Nick", "Normal", "Scratch"]
SCENE_NAME = "Scene.001"
BACKGROUND_EXTS = (".jpg", ".jpeg", ".png")
MASK_THRESHOLD = 0.5


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #

def write_gray_png(path, pixels):
    """Write an HxW uint8 array (top row first) as an 8-bit grayscale PNG."""
    h, w = pixels.shape
    raw = b"".join(b"\x00" + pixels[y].tobytes() for y in range(h))

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw, 6)))
        f.write(chunk(b"IEND", b""))


def common_args(parser):
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--out", default=None)
    parser.add_argument("--resolution", type=int, default=1024)
    parser.add_argument("--max-angle", type=float, default=30.0)


# --------------------------------------------------------------------------- #
# Per-type scene handles and randomization (runs inside Blender)
# --------------------------------------------------------------------------- #

def chance(rng):
    return rng.uniform() > 0.5


class Generator:
    # Light randomization per type: (sun light name, sun range, sun fallback,
    # world range, world fallback). Values come from the original scripts;
    # Nick's sun used `> 0.999` (almost never random) and is fixed to 50/50.
    LIGHTS = {
        "Corrosion": ("Sun.001", (200, 700), 700, (0.1, 0.8), 1.0),
        "Dent":      ("Sun.001", (200, 800), 500, (0.1, 0.3), 0.5),
        "Nick":      ("Sun",     (200, 800), 700, (0.1, 0.6), 0.5),
        "Normal":    ("Sun",     (200, 800), 900, (0.1, 1.0), 1.0),
        "Scratch":   ("Sun.001", (200, 700), 500, (0.1, 0.3), 0.5),
    }

    def __init__(self, defect_type, resolution):
        self.type = defect_type
        self.scene = bpy.data.scenes[SCENE_NAME]
        self.scene.render.resolution_x = resolution
        self.scene.render.resolution_y = resolution
        self.scene.render.resolution_percentage = 100

        gn = bpy.data.node_groups["Geometry Nodes"]
        gn1 = bpy.data.node_groups["Geometry Nodes.001"]
        comp = self.scene.node_tree.nodes
        self.background = comp["Image"]
        self.black_switch = comp["Switch"]

        sun_name, *self.light_ranges = self.LIGHTS[defect_type]
        self.sun = bpy.data.lights[sun_name]
        self.world = bpy.data.worlds["World.001"].node_tree.nodes["Background"].inputs[1]

        # Nick and Normal cut the defect out of the geometry; the other three
        # draw it in the material and switch to the mask via Value.001.
        if defect_type in ("Nick", "Normal"):
            self.angles = [gn.nodes["Transform Geometry.002"].inputs[2],
                           gn1.nodes["Transform Geometry"].inputs[2]]
            self.body_switch = gn1.nodes["Boolean"]
            self.cut_switch = gn.nodes["Boolean"]
            self.mask_value = None
        else:
            self.angles = [gn.nodes["Transform Geometry"].inputs[2],
                           gn1.nodes["Transform Geometry"].inputs[2]]
            self.body_switch = gn.nodes["Boolean"]
            self.cut_switch = None
            self.mask_value = bpy.data.materials["Steel - Satin.001"].node_tree.nodes["Value.001"].outputs[0]

        getattr(self, "_setup_" + defect_type.lower())(gn)

    # ---- per-type handles ------------------------------------------------- #

    def _setup_corrosion(self, gn):
        mat = bpy.data.materials["Steel - Satin.001"].node_tree.nodes
        self.noise_w = mat["Noise Texture.002"].inputs[1]
        self.noise_offset = mat["Mapping.007"].inputs[1]
        self.corrosion_ramp = mat["Color Ramp.005"].color_ramp.elements[2]

    def _setup_dent(self, gn):
        mat = bpy.data.materials["Steel - Satin.001"].node_tree.nodes
        self.dents = [mat[f"G{i}"] for i in range(1, 6)]
        self.dent_roughness = bpy.data.node_groups["NodeGroup.001"].nodes["Math.020"].inputs[1]

    def _setup_nick(self, gn):
        self.nick_pos = gn.nodes["Sample Curve"].inputs[2]
        self.nick_radius = gn.nodes["Group"].inputs[2]
        self.nick_size = gn.nodes["Group"].inputs[1]
        self.nick_shape = gn.nodes["Boolean.001"]

    def _setup_normal(self, gn):
        pass

    def _setup_scratch(self, gn):
        mat = bpy.data.materials["Steel - Satin.001"].node_tree.nodes
        self.scratch_offset = mat["Vector Math.001"].inputs[1]
        self.scratch_noise = mat["Group"].inputs[0]
        self.scratch_length = mat["Math.006"].inputs[1]

    # ---- per-type randomization ------------------------------------------- #

    def _randomize_corrosion(self, rng):
        offset = [rng.uniform(-1, 1), rng.uniform(-1, 1), 0.0]
        p = {"noise_w": rng.uniform(0, 10),
             "noise_offset": offset,
             "corrosion_threshold": rng.uniform(0.2, 0.6)}
        self.noise_w.default_value = p["noise_w"]
        self.noise_offset.default_value = offset
        self.corrosion_ramp.position = p["corrosion_threshold"]
        return p

    def _randomize_dent(self, rng):
        points = dent_points(rng, 5, min_dist=0.04, max_dist=0.5,
                             x_range=(0.21, 0.5), y_range=(0.6, 1.15))
        radii = rng.uniform(0.05, 0.4, 5)
        # G1 is always on; G2-G5 are each switched off half the time.
        active = [True] + [bool(rng.integers(0, 2)) for _ in range(4)]
        for node, (x, y), r, on in zip(self.dents, points, radii, active):
            node.inputs[1].default_value = x
            node.inputs[2].default_value = y
            node.inputs[3].default_value = r
            node.mute = not on
        roughness = rng.uniform(0.3, 2)
        self.dent_roughness.default_value = roughness
        return {"dents": [{"x": x, "y": y, "radius": float(r)}
                          for (x, y), r, on in zip(points, radii, active) if on],
                "roughness": roughness}

    def _randomize_nick(self, rng):
        p = {"position": rng.uniform(0, 0.98),
             "radius": rng.uniform(0.1, 0.25),
             "size_x": rng.uniform(0.2, 0.5),
             "size_z": rng.uniform(0.2, 0.5),
             "shape": int(rng.integers(0, 2))}
        self.nick_pos.default_value = p["position"]
        self.nick_radius.default_value = p["radius"]
        self.nick_size.default_value[0] = p["size_x"]
        self.nick_size.default_value[2] = p["size_z"]
        self.nick_shape.boolean = bool(p["shape"])
        return p

    def _randomize_normal(self, rng):
        return {}

    def _randomize_scratch(self, rng):
        p = {"offset_x": rng.uniform(0.1, 0.45),
             "offset_y": rng.uniform(0.06, 0.6),
             "noise_scale": rng.uniform(0, 10.2),
             "length": rng.uniform(2.5, 20.5)}
        self.scratch_offset.default_value[0] = p["offset_x"]
        self.scratch_offset.default_value[1] = p["offset_y"]
        self.scratch_noise.default_value = p["noise_scale"]
        self.scratch_length.default_value = p["length"]
        return p

    # ---- shared randomization --------------------------------------------- #

    def randomize(self, rng, backgrounds, max_angle):
        (sun_lo, sun_hi), sun_default, (w_lo, w_hi), w_default = self.light_ranges
        sun = rng.uniform(sun_lo, sun_hi) if chance(rng) else sun_default
        world = rng.uniform(w_lo, w_hi) if chance(rng) else w_default
        self.sun.energy = sun
        self.world.default_value = world

        angle = rng.uniform(-max_angle, max_angle)
        for socket in self.angles:
            socket.default_value[0] = np.radians(angle)

        bg_path = backgrounds[int(rng.integers(0, len(backgrounds)))]
        self.background.image = bpy.data.images.load(bg_path, check_existing=True)

        params = {"background": os.path.basename(bg_path),
                  "view_angle_deg": angle, "sun_energy": sun, "world_strength": world}
        params.update(getattr(self, "_randomize_" + self.type.lower())(rng))
        return params

    # ---- render modes ----------------------------------------------------- #

    def set_image_mode(self):
        self.black_switch.check = False
        self.body_switch.boolean = True
        if self.cut_switch is not None:
            self.cut_switch.boolean = True
        if self.mask_value is not None:
            self.mask_value.default_value = 0

    def set_mask_mode(self):
        self.black_switch.check = True
        self.body_switch.boolean = False
        if self.cut_switch is not None:
            self.cut_switch.boolean = False
        if self.mask_value is not None:
            self.mask_value.default_value = 1

    def render(self, path):
        self.scene.render.filepath = path
        bpy.ops.render.render(write_still=True, scene=self.scene.name)

    def render_image(self, path):
        self.set_image_mode()
        self.render(path)

    def render_mask(self, path):
        """Render the mask with no tone mapping or anti-aliasing, then threshold it."""
        r, vs, ee = self.scene.render, self.scene.view_settings, self.scene.eevee
        saved = (vs.view_transform, vs.look, vs.exposure, vs.gamma,
                 r.filter_size, ee.taa_render_samples)
        try:
            vs.view_transform, vs.look, vs.exposure, vs.gamma = "Standard", "None", 0.0, 1.0
            r.filter_size = 0.0
            ee.taa_render_samples = 1
            self.set_mask_mode()
            self.render(path)
        finally:
            (vs.view_transform, vs.look, vs.exposure, vs.gamma,
             r.filter_size, ee.taa_render_samples) = saved
            self.set_image_mode()
        threshold_mask(path)

    def write_empty_mask(self, path):
        size = self.scene.render.resolution_x, self.scene.render.resolution_y
        write_gray_png(path, np.zeros((size[1], size[0]), dtype=np.uint8))


def threshold_mask(path):
    """Replace a rendered mask with a 0/255 grayscale PNG."""
    img = bpy.data.images.load(path, check_existing=False)
    try:
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
    finally:
        bpy.data.images.remove(img)
    rgb = px.reshape(h, w, 4)[::-1, :, :3]  # Blender stores rows bottom-up
    write_gray_png(path, np.where(rgb.max(axis=2) > MASK_THRESHOLD, 255, 0).astype(np.uint8))


def dent_points(rng, n, min_dist, max_dist, x_range, y_range, attempts=1000):
    """Points whose pairwise distances all lie in [min_dist, max_dist]."""
    for _ in range(100):
        points = []
        for _ in range(attempts):
            p = np.array([rng.uniform(*x_range), rng.uniform(*y_range)])
            if all(min_dist <= np.linalg.norm(p - q) <= max_dist for q in points):
                points.append(p)
                if len(points) == n:
                    return [(float(x), float(y)) for x, y in points]
    raise RuntimeError("could not place dent positions; loosen min_dist/max_dist")


# --------------------------------------------------------------------------- #
# Entry points
# --------------------------------------------------------------------------- #

def run_in_blender(argv):
    parser = argparse.ArgumentParser(prog="generate_dataset.py (inside Blender)")
    common_args(parser)
    parser.add_argument("--type", choices=TYPES, default=None)
    args = parser.parse_args(argv)

    blend = bpy.data.filepath
    defect_type = args.type or next(
        (t for t in TYPES if t.lower() == os.path.splitext(os.path.basename(blend))[0].lower()), None)
    if defect_type is None:
        sys.exit(f"Cannot tell the defect type from {blend!r}; pass --type.")
    type_id = TYPES.index(defect_type)
    if args.max_angle < 0:
        sys.exit("--max-angle must be >= 0")

    out_dir = bpy.path.abspath(args.out or f"//output/{defect_type}/")
    os.makedirs(out_dir, exist_ok=True)
    bg_dir = bpy.path.abspath("//Backgrounds/")
    backgrounds = sorted(os.path.join(bg_dir, f) for f in os.listdir(bg_dir)
                         if f.lower().endswith(BACKGROUND_EXTS))
    if not backgrounds:
        sys.exit(f"No background images in {bg_dir}")

    gen = Generator(defect_type, args.resolution)
    print(f"[{defect_type}] rendering {args.count} image(s) from index {args.start} "
          f"(seed {args.seed}) into {out_dir}")

    with open(os.path.join(out_dir, "metadata.jsonl"), "a") as meta:
        for idx in range(args.start, args.start + args.count):
            # Seeded per image, so any index can be re-rendered on its own.
            rng = np.random.default_rng([args.seed, type_id, idx])
            gen.set_image_mode()
            params = gen.randomize(rng, backgrounds, args.max_angle)

            image_path = os.path.join(out_dir, f"image_{idx}.png")
            mask_path = os.path.join(out_dir, f"mask_{idx}.png")
            gen.render_image(image_path)
            if defect_type == "Normal":
                gen.write_empty_mask(mask_path)
            else:
                gen.render_mask(mask_path)

            meta.write(json.dumps({"index": idx, "type": defect_type, "seed": args.seed,
                                   "max_angle": args.max_angle,
                                   "image": os.path.basename(image_path),
                                   "mask": os.path.basename(mask_path), **params}) + "\n")
            meta.flush()
            print(f"[{defect_type}] {idx - args.start + 1}/{args.count} done: image_{idx}.png")


def find_blender():
    if os.environ.get("BLENDER"):
        return os.environ["BLENDER"]
    for version in ("4.1", "4.2"):
        path = rf"C:\Program Files\Blender Foundation\Blender {version}\blender.exe"
        if os.path.exists(path):
            return path
    return "blender"


def run_launcher(argv):
    import subprocess

    parser = argparse.ArgumentParser(description="Render every defect type by launching Blender per .blend file.")
    common_args(parser)
    parser.add_argument("--types", nargs="+", choices=TYPES, default=TYPES)
    parser.add_argument("--blend-dir", default=os.path.dirname(os.path.abspath(__file__)))
    parser.add_argument("--blender", default=find_blender())
    args = parser.parse_args(argv)

    failed = []
    for defect_type in args.types:
        blend = os.path.join(args.blend_dir, f"{defect_type}.blend")
        cmd = [args.blender, "-b", "--factory-startup", blend,
               "--python-exit-code", "1", "--python", os.path.abspath(__file__), "--",
               "--type", defect_type, "--count", str(args.count), "--seed", str(args.seed),
               "--start", str(args.start), "--resolution", str(args.resolution),
               "--max-angle", str(args.max_angle)]
        if args.out:
            cmd += ["--out", os.path.join(os.path.abspath(args.out), defect_type)]
        print("Running:", " ".join(f'"{c}"' if " " in c else c for c in cmd), flush=True)
        if subprocess.run(cmd).returncode != 0:
            failed.append(defect_type)
    if failed:
        sys.exit(f"Failed: {', '.join(failed)}")


if __name__ == "__main__":
    if bpy is not None:
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        try:
            run_in_blender(argv)
        except Exception:
            import traceback
            traceback.print_exc()
            sys.exit(1)  # Blender exits 0 on script errors unless told otherwise
    else:
        run_launcher(sys.argv[1:])
