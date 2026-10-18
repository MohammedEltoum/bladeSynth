# BladeSynth Generator

Render synthetic images of aero engine blade defects, each paired with a pixel-exact
segmentation mask. This repository holds the Blender scenes and generator script behind
**BladeSynth: A High-Quality Rendering-Based Synthetic Dataset for Aero Engine Blade Defect
Inspection** (*Scientific Data*, 2025).

[![Paper](https://img.shields.io/badge/Paper-Scientific%20Data-blue)](https://www.nature.com/articles/s41597-025-05563-y)
[![Data](https://img.shields.io/badge/Dataset-Figshare-red)](https://doi.org/10.6084/m9.figshare.28658603)
[![Blender](https://img.shields.io/badge/Blender-4.1-orange)](https://download.blender.org/release/Blender4.1/)

<img width="1497" height="709" alt="Sample BladeSynth renders of normal, dented, nicked, scratched and corroded blades" src="https://github.com/user-attachments/assets/5768390f-50f6-4a56-bd60-0d5c2a9c22b0" />

## Why synthetic data?

Images of real defective blades are scarce, slow to annotate, and hard to capture under the
full range of lighting that polished metal reflects. BladeSynth renders them instead. A
3D-scanned blade with physically based materials is placed in a randomized inspection scene,
a defect is generated procedurally, and Blender outputs the image together with its mask.
Because the mask comes from the scene itself, the labels are exact and free.

The published dataset contains **12,500 images at 1024 × 1024**, 2,500 per class. It is
available on [Figshare](https://doi.org/10.6084/m9.figshare.28658603) under CC BY 4.0. Use
this repository to render more data, or variations of it.

## Quick start

1. Install [Blender 4.1](https://download.blender.org/release/Blender4.1/).
2. Clone the repository:

   ```bash
   git clone https://github.com/MohammedEltoum/bladeSynth.git
   cd bladeSynth
   ```

3. Render five dent images as a test:

   ```bash
   python generate_dataset.py --types Dent --count 5
   ```

The images, masks and a metadata file appear in `output/Dent/`.

## Defect classes

| Class | Scene | Appearance | How it is generated |
|---|---|---|---|
| Normal | `Normal.blend` | Intact, defect-free blade | The same scene with no defect applied |
| Dent | `Dent.blend` | Small, smooth, rounded depressions | A quadratic bowl, γ(αx² + βy²), plus Perlin noise, masked to the defect area; 1–5 dents per image |
| Nick | `Nick.blend` | Small, sharp notch in the blade edge | A noise-perturbed sphere is placed on the edge and subtracted from the blade mesh |
| Scratch | `Scratch.blend` | Thin, elongated marks of varying length and direction | γ(αx² + β\|y\|) plus noise; the \|y\| term gives the scratch its linear profile |
| Corrosion | `Corrosion.blend` | Rough, pitted, discolored patches | Masked noise drives a corrosion color ramp and a contrast-adjusted roughness map |

Dents, scratches and corrosion are built into the blade's material through its UV map, while
nicks change the mesh itself. The paper's Methods section gives the full derivation.

## How to run

The generator can run in two ways. Both take the same rendering options.

| | **With Python** | **Inside Blender** |
|---|---|---|
| Command | `python generate_dataset.py …` | `blender … Dent.blend --python generate_dataset.py -- …` |
| Classes | One, several or all (chosen with `--types`) | Only the `.blend` file you open |
| Needs | Python 3 (no extra packages) and Blender 4.1 | Blender 4.1 only |

Run all commands from the repository folder.

### Render every class

```bash
python generate_dataset.py --count 2500 --seed 7
```

This starts Blender once per scene. `--count 2500` matches the size of the published dataset.

### Render one class

Choose the class with `--types`. Class names are case-sensitive: `Corrosion`, `Dent`, `Nick`,
`Normal`, `Scratch`.

```bash
python generate_dataset.py --types Dent --count 500 --seed 7
```

To render several classes, list them: `--types Dent Nick`.

### Run inside Blender

Open the scene in Blender from the command line and hand it the script. The class comes from
the `.blend` file name, and everything after `--` is passed to the generator:

```bash
blender -b --factory-startup Dent.blend --python generate_dataset.py -- --count 500 --seed 7
```

On Windows, if `blender` isn't on your PATH, give its full path:

```bash
"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe" -b --factory-startup Dent.blend --python generate_dataset.py -- --count 500 --seed 7
```

### Common recipes

| Goal | Add |
|---|---|
| Quick preview | `--count 5` |
| Continue a run that stopped after image 499 | `--start 500 --count 500` |
| Split 2,000 images across two machines | `--start 0 --count 1000` on one and `--start 1000 --count 1000` on the other, with the same `--seed` |
| Wider camera angles | `--max-angle 50` |
| Different output folder | `--out D:/data/blades` |

### Options

| Option | Default | Description |
|---|---|---|
| `--count N` | `10` | Number of images per class |
| `--seed S` | `0` | Base random seed. The same seed, index and options always produce the same image |
| `--start I` | `0` | Index of the first image, for resuming a run or splitting it across machines |
| `--out DIR` | `output/<Class>/` | Output folder. With Python, each class goes to `DIR/<Class>/`; inside Blender, files go straight into `DIR` |
| `--resolution PX` | `1024` | Width and height of the render, in pixels |
| `--max-angle DEG` | `30` | The view angle is drawn uniformly from −DEG to +DEG |
| `--types T …` | all classes | *Python only.* Which classes to render |
| `--blender PATH` | see below | *Python only.* The Blender executable to use |

When run with Python, the script uses the `BLENDER` environment variable if it is set, then
the standard Windows install location, then `blender` on your PATH.

## Output

```
output/<Class>/
├── image_0.png       rendered blade over a background photo
├── mask_0.png        8-bit grayscale mask: 0 = background, 255 = defect
└── metadata.jsonl    one line per image with every randomized value
```

Masks are rendered without tone mapping or anti-aliasing and then thresholded, so every pixel
is exactly 0 or 255.

Each line of `metadata.jsonl` records the seed, view angle, lighting, background and defect
parameters used for that image, so any sample can be traced and re-rendered.



## Repository structure

```
├── Corrosion.blend, Dent.blend, Nick.blend, Normal.blend, Scratch.blend
│                       one scene per class; textures are linked, not packed
├── textures/           blade materials and the HDRI shared by all scenes
├── Backgrounds/        background photos, one picked at random per render
└── generate_dataset.py the generator
```

The HDRI in `textures/` never appears in the image, but it lights the blade and creates its
metallic reflections, so the scenes need it.

## Troubleshooting

- **Renders look different from the dataset.** Use Blender 4.1. Blender 4.2 replaced the EEVEE
  engine these scenes use, so newer versions render them differently.
- **`invalid choice: 'dent'`.** Class names are case-sensitive; use `Dent`.
- **`unrecognized arguments: --types`.** `--types` and `--blender` only work with Python. Inside
  Blender, choose the class by opening its `.blend` file.
- **Blender not found.** Set the `BLENDER` environment variable or pass `--blender` with the full
  path to the executable.


## License and third-party assets

- `textures/Metal010_*` and `textures/Metal011_*`: [ambientCG](https://ambientcg.com) metal materials (CC0).
- `textures/aerodynamics_workshop_4k.exr`: [Poly Haven](https://polyhaven.com) HDRI (CC0).

## Citation

If you use this generator or the dataset, please cite:

```bibtex
@article{mohammed2025bladesynth,
  title={BladeSynth: A High-Quality Rendering-Based Synthetic Dataset for Aero Engine Blade Defect Inspection},
  author={Mohammed Eltoum, MA and Iqbal, Ehtesham and Zweiri, Yahya and Moyo, Brain and Abdulrahman, Yusra},
  journal={Scientific Data},
  volume={12},
  number={1},
  pages={1268},
  year={2025},
  publisher={Nature Publishing Group UK London},
  doi={10.1038/s41597-025-05563-y}
}
```

## Acknowledgements

This work was funded by Sanad Aerotech and supported by the Advanced Research and Innovation
Center (ARIC), Khalifa University of Science and Technology, UAE.
