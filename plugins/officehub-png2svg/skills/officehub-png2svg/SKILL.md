---
name: officehub-png2svg
description: Use when the user wants to turn a PNG (or JPG/WebP) - a logo, icon, badge, illustration or line drawing - into a high-quality SVG vector, usually with the background removed. Triggers include "PNG to SVG", "convert to SVG", "vectorize", "trace this logo", "make it a vector", "remove the white background", "transparent SVG", and Arabic requests such as حول الصورة إلى SVG، تحويل إلى فيكتور، إزالة الخلفية. Detects and removes any solid background automatically, keeps details inside the artwork, and checks the SVG against the original before delivering.
license: MIT (adapted from lovstudio/png2svg-skill, see LICENSE.txt)
---

# OfficeHub PNG → SVG

Careful, high-detail raster-to-vector conversion with automatic background removal.
Adapted from github.com/lovstudio/png2svg-skill (MIT), rewritten in English with a new
pipeline. The original removed every white pixel (including white details inside a logo)
and never checked the result.

Everything runs through one script, `scripts/png2svg.py` (path relative to this skill's
folder). It does:

1. **Background:** finds a solid background colour on the image border (white, off-white,
   black, any colour) and removes only the background connected to the border. Same-coloured
   details inside the artwork (white text on a red badge) stay. Areas enclosed by the
   artwork (inside an "O") also stay unless asked otherwise.
2. **Upscale** small images (2–4×) so edges get sub-pixel precision.
3. **Edge clean-up:** anti-aliased edge pixels are split into artwork and background, so the
   SVG has no white or dark halo and edges sit where the original edges are.
4. **Colours:** flat artwork is snapped to its real palette, which removes anti-aliasing
   blends and JPEG noise. Thin lines keep their own colour. Gradients are split into fine
   colour bands, because the tracer cannot trace smooth gradients.
5. **Trace** with vtracer (colour, stacked, spline) using a detail-first preset. The SVG gets
   a `viewBox` and the original pixel size.
6. **Verify:** renders the SVG and compares it with the original on its own background.
   Reports shape match, colour error and whether the removed background is really
   transparent, and writes a side-by-side preview PNG.

## Setup (once per environment)

Needs code execution with Python 3, Pillow and numpy.

```bash
pip install vtracer resvg-py     # vtracer: the tracer (required); resvg-py: verification render
```

Optional: `svgo` (`npm install -g svgo`) shrinks the SVG about 50%. With `--npx` the script
runs `npx --yes svgo` instead (downloads it). Without svgo the SVG is still valid, only larger.
If `pip install` is not possible, say so and stop. Never hand-write or "describe" an SVG
instead of tracing it.

## Workflow

**Step 1: Look at the input.** Note the size, whether it already has transparency, and what
it is: logo, icon, illustration, scan or photo. Photos and textured images trace into huge,
"painted" SVGs. Say so and suggest keeping a WebP/PNG unless the user still wants a vector.

**Step 2: Run with the defaults** (preset `detail`, background auto, colours auto):

```bash
python3 scripts/png2svg.py INPUT.png -o OUTPUT.svg --json
```

Several files: `python3 scripts/png2svg.py a.png b.png --out-dir svg/ --json`.

**Step 3: Read the report.**
- `background`: detected colour, `removed_pct`, `enclosed_bg_colour_pct`.
- `palette`: the colours found, or "colour bands" for gradients.
- `svg_bytes`, `svg_paths`, `svg_fill_colors`.
- `verification`: `grade` (excellent / good / check), `shape_iou` (1.0 = identical
  shape), `color_mae` (average colour error, 0–255), `background_clear` (1.0 = removed
  background is fully transparent), and `preview`.
- `soft_edges` / `edge_width_px`: the source is blurred or enlarged (edges wider than
  about 2 px). The SVG gets crisp edges, so a "good" grade is the expected result.
- `warnings`: always relay these to the user in plain words.

**Step 4: Check the preview** (`OUTPUT.preview.png`). Look at it if you can view images.
Left is the source. The middle is the SVG on a checkerboard, so checks mean transparent.
Right is the difference: red = colour error, magenta = shape mismatch, cyan = background
left behind. Check four things:
- the background is gone
- inner details are kept
- edges are smooth with no halo
- thin lines and small text are present

**Step 5: Fix what is wrong**, with the table below, and run again. Change one thing at a
time. Stop when the grade is excellent or good and the preview looks right. Two or three
rounds is normal for a difficult image.

**Step 6: Deliver.**
- The SVG file, plus the preview PNG so the user can see the check.
- A short summary: size in KB, number of colours, which background colour was removed, and
  the grade.
- Any caveat (enclosed areas kept, thin text, photo-like input).

If it is unclear whether enclosed areas (inside letters) should be transparent, deliver the
default and say how to get the other version, or ask once.

## Fixing problems

| What you see | What to change |
|---|---|
| Background not removed ("no solid background") | `--bg '#rrggbb'` with the colour you see, or a higher `--tolerance 12` |
| Light parts of the artwork eaten away (pale grey, soft shadow) | Lower `--tolerance 4` |
| Background colour still inside letters/shapes (the inside of O, A, e) | `--holes remove` (only if the artwork has no intended details in that colour) |
| White details inside the logo disappeared | Use the default `--holes keep`; check the `--bg` colour is right |
| Colours slightly off, or must match brand colours exactly | `--palette '#c81e28,#143ca0,#ffffff'` (list every colour in the artwork) |
| A colour from the artwork is missing (merged into another) | `--colors off`, or add it to `--palette` |
| Gradient shows visible banding | `--colors 128` (more bands, bigger file) |
| File too big (gradients, photos) | `--preset balanced` or `--preset smooth`, or `--colors 32` |
| Many tiny specks or dots | `--filter-speckle 4` (or 6–8) or `--preset balanced` |
| Fine detail lost (small dots, thin gaps) | `--filter-speckle 1` and `--upscale 4` |
| Corners rounded off | `--corner-threshold 40` (lower = sharper corners) |
| Pixel art or sharp UI icon | `--preset pixel` (polygon mode, no smoothing) |
| Halo or odd edge colour | Make sure `--defringe on` (default) and the `--bg` colour is right |
| Small text heavy or blurry ("thin strokes" warning) | Ask for a 2–4× larger source or the original vector/font; a trace cannot add pixels that are not there |

Presets: `detail` (default, keeps everything), `balanced` (fewer tiny paths, good for
screenshots and JPGs), `smooth` (the upstream settings: smooth curves, loses fine detail),
`posterize` (12 colours), `pixel` (pixel art).

Other flags:
- `--bg keep` keeps the background.
- `--upscale 1|2|3|4` overrides the automatic upscale.
- `--no-optimize` skips svgo.
- `--keep-temp` saves the prepared PNG that was traced.
- `--report file.json` writes the report to a file.
- Run `python3 scripts/png2svg.py --help` for all vtracer overrides.

## Rules

1. Always run the script; never write SVG paths by hand or claim a conversion that did not run.
2. Never put the raster inside the SVG (`<image href="data:...">`): that is not a vector.
3. Report the verification grade honestly. A "check" grade means: say what is off, and fix
   it or explain why it cannot be better (photo, tiny text).
4. Do not redraw, "improve" or AI-upscale the artwork. The SVG must match the original.
5. Keep the source file untouched. Write outputs next to it or where the user asks.
6. For OfficeHub assets, name files lowercase with hyphens (e.g. `officehub-logo-ar.svg`).
