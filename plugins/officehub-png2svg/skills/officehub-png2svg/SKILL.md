---
name: officehub-png2svg
description: Use when the user wants to turn a PNG (or JPG/WebP) - a logo, icon, badge, illustration or line drawing - into a polished, publish-ready SVG, or to clean up an existing traced SVG (wobbly edges, lumpy circles, rounded corners). Triggers include "PNG to SVG", "convert to SVG", "vectorize", "trace this logo", "make it a vector", "fix/polish this SVG", "remove the white background", "transparent SVG", and Arabic requests such as حول الصورة إلى SVG، تحويل إلى فيكتور، إزالة الخلفية. Works geometry first (exact circles, arcs and straight lines, sharp corners, aligned edges), removes any solid background automatically, and checks the SVG against the original before delivering.
license: MIT (adapted from lovstudio/png2svg-skill, see LICENSE.txt)
---

# OfficeHub PNG → SVG

Careful, geometry-first raster-to-vector conversion with automatic background removal,
for SVGs that are ready to publish. Adapted from github.com/lovstudio/png2svg-skill (MIT),
rewritten in English with a new pipeline.

Everything runs through `scripts/png2svg.py`, which uses `scripts/geometry.py` (paths
relative to this skill's folder). Input can be a PNG/JPG/WebP or an **existing SVG to
polish**: an SVG is rendered large and rebuilt, and keeps its original `viewBox` and size.

## What the script does

1. **Background:** finds a solid background colour on the border (white, off-white, black,
   any colour) and removes only the background connected to the border. Same-coloured
   details inside the artwork (white text on a red badge) stay. Areas enclosed by the
   artwork (inside an "O") also stay unless asked otherwise.
2. **Edges and colours:**
   - small images are upscaled before tracing
   - anti-aliased edges are split into artwork and background, so there is no halo
   - flat artwork is snapped to its real palette, which removes blends and JPEG noise; thin
     lines keep their colour
3. **Geometry, in this order** (flat artwork, `--geometry auto`, the default):
   1. **Shapes:** a contour that is a circle or an ellipse becomes an exact circle or
      ellipse. Curves around a found circle (rings, rounded cut-outs) become exactly
      concentric arcs with one shared radius.
   2. **Straight lines:** straight runs become real lines, snapped to exact horizontal or
      vertical. Corners are rebuilt as exact intersections: sharp, with no notches or
      rounding. Bar and stroke ends become square caps.
   3. **Alignment:** edges with nearly the same x or y across the whole logo get one shared
      value (stems, frame lines, baselines). Near-equal circles share centre and radius.
      Coordinates snap to a 1/8 px grid.
   4. **Details:** everything else becomes smooth Bézier curves that meet the lines
      tangentially.
   5. **Safety net:** every shape is compared with its pixels. A shape that moved too far is
      refitted more cautiously, so polishing never changes the design.

   Gradients and photos skip geometry and are traced with vtracer as fine colour bands.
4. **Verify:** renders the SVG and compares it with the original on its own background. The
   report gives a grade, a side-by-side preview and zoomed tiles of the worst spots.

## Setup (once per environment)

Needs code execution with Python 3, Pillow and numpy.

```bash
pip install vtracer resvg-py     # resvg-py: rendering (SVG input + checks); vtracer: gradients/photos
```

Flat logos and icons need only resvg-py; vtracer is used for gradients, photos and
`--geometry off`. Optional: `svgo` (`npm i -g svgo`, or `--npx`) shrinks the file further.
If `pip install` is not possible, say so and stop. Never hand-write or "describe" an SVG
instead of running the script.

## Workflow: the polish pass

**Step 1: Look at the input.** Check four things:
- the size, and whether it already has transparency
- what it is: logo, icon, illustration, scan or photo
- for an SVG: is it an old trace (wobbly) or a clean design file?

Photos and textured images trace into huge, "painted" SVGs. Say so, and suggest keeping a
WebP/PNG.

**Step 2: Run.**

```bash
python3 scripts/png2svg.py INPUT.png -o OUTPUT.svg --json      # PNG/JPG/WebP
python3 scripts/png2svg.py OLD.svg  -o POLISHED.svg --json     # polish an existing SVG
```

SVG input uses strict snapping by default, because old traces are wobbly. Raster input uses
the default tolerances. For a clean, simple logo raster that still looks wobbly, add
`--geometry strict`.

**Step 3: Read the report.**
- `geometry`:
  - counts of circles, ellipses, arcs, lines and curves
  - `snapped_lines` and `aligned_edges`
  - fallbacks: shapes kept cautious because snapping moved them too far
- `background` and `palette`: as found.
- `verification`:
  - `grade` (excellent / good / check)
  - `shape_iou` (1.0 = identical shape), `color_mae`, `background_clear`
  - `preview`, plus `details` (zoomed tiles of the worst spots)
- `warnings`: relay them in plain words.

When polishing a wobbly source, "good" is expected: the SVG is straighter than the source
on purpose.

**Step 4: Inspect in the same order as the geometry.** Look at the preview and the detail
tiles if you can view images. Each tile shows the source on the left and the SVG on the
right.
1. **Shapes:** circles round, rings even, rounded cut-outs concentric with their circle.
2. **Straight lines:** edges straight, horizontals and verticals exact, corners sharp (or
   rounded only where the design is rounded), square ends on bars.
3. **Alignment:** stems and baselines line up, matching parts have equal widths, the
   artwork is symmetric where the design is.
4. **Details:** small text, dots, chamfers and terminals present and clean, no specks.
5. **Background and colours:** the background is fully gone, colours are exact, there is no
   halo.

**Step 5: Fix what is wrong** with the table below and run again, one change at a time.
Stop when every item in Step 4 passes and the grade is excellent or good.

**Step 6: Deliver.**
- The SVG, plus the preview (and details) PNG.
- A short summary: KB, colours, the geometry counts (e.g. "2 exact circles, 116 straight
  lines snapped and aligned"), the grade, and any caveat.

## Fixing problems

| What you see | What to change |
|---|---|
| Edges still wavy, circle still lumpy (wobbly source) | `--geometry strict` (larger snap tolerances) |
| A line that should be horizontal/vertical is slightly tilted | `--snap-angle 3` (or `strict`) |
| Stems, frame lines or baselines nearly but not exactly aligned | `--align-tol 1.5` (display px) |
| A deliberate slight angle or offset got straightened | Lower `--snap-angle 0.5` / `--align-tol 0.3`, or `--geometry auto` instead of strict |
| Rounded corners that should be sharp | `--geometry strict` (sharpens rounding up to about 3 px) |
| Shape changed too much / looks redrawn | `--geometry auto` instead of strict; as a last resort `--geometry off` |
| Background not removed ("no solid background") | `--bg '#rrggbb'` with the colour you see, or a higher `--tolerance 12` |
| Light parts of the artwork eaten away | Lower `--tolerance 4` |
| Background colour still inside letters (the inside of O, A, e) | `--holes remove` (only if no intended details in that colour) |
| Colours slightly off, or must match brand colours exactly | `--palette '#c81e28,#143ca0,#ffffff'` (list every colour) |
| A colour from the artwork is missing | Add it to `--palette`, or `--colors off` |
| Small text heavy or blurry ("thin strokes" warning) | Geometry is skipped for it. Ask for a 2–4× larger source or the original vector/font |
| Gradient banding / file too big (no geometry) | `--colors 128` / `--preset balanced` |
| Pixel art | `--geometry off --preset pixel` |

Other flags:
- `--bg keep` keeps the background.
- `--upscale 1|2|3|4` overrides the automatic upscale.
- `--no-optimize` skips svgo.
- `--keep-temp` saves the prepared PNG.
- `--report file.json` writes the report to a file.
- `--help` lists the vtracer overrides.

## Rules

1. Always run the script; never write SVG paths by hand or claim a result that did not run.
2. Never put the raster inside the SVG (`<image href="data:...">`): that is not a vector.
3. Report the verification grade and geometry counts honestly. A "check" grade means: say
   what is off, and fix it or explain why it cannot be better (photo, tiny text).
4. Polish, do not redesign. Snapping only corrects tracing error within the tolerances.
   Never change proportions, letterforms or spacing on purpose.
5. Keep the source file untouched. Write outputs next to it or where the user asks.
6. For OfficeHub assets, name files lowercase with hyphens (e.g. `officehub-logo-ar.svg`).
