---
name: officehub-product-angles
description: Use when the user shares one photo of a furniture item (office chair, desk, workstation, storage cabinet, meeting table, sofa and so on) plus its dimensions and wants product images of it from other angles (front, 3/4, sides, back, top, detail) for the OfficeHub store. Also triggers in Arabic, e.g. صور المنتج من زوايا مختلفة. Writes the image prompts, checks the results and prepares file names, Arabic/English alt text and the AI label for upload. Works in Claude chat with no API key.
---

# OfficeHub Product Angles

Adapted from the multi-angle workflow in github.com/motiful/product-shots, re-aimed at office
furniture for officehub.sa and rewritten so it works entirely inside Claude chat with no API key.

## Important: how images get made

Claude cannot draw or output photos. So this skill splits the work:
1. **Claude** studies the photo, locks the item's details and proportions, and writes one
   precise, ready-to-paste prompt per angle.
2. **The user** pastes each prompt, together with the original photo, into a free image tool:
   **Gemini** (gemini.google.com, its image model "Nano Banana" is the same family product-shots uses)
   or **ChatGPT** image generation. Recommend Gemini first.
3. **The user uploads the results back** to this chat. Claude checks each one against the original
   and the dimensions, and rewrites the prompt for any view that came out wrong.
4. **Claude prepares the publish pack** for the approved images: file names, alt text in Arabic and
   English, export settings and the AI label (Step 7).

Say this in two or three lines at the start of the first reply, then get on with the work.

## Honest limits (mention once)
- The image tool re-draws the item for each angle; it does not rotate a 3D model. Shape, colour,
  upholstery and legs usually hold; fine grain, stitching, mesh weave, small logos and lever
  shapes can drift.
- Sides the photo doesn't show (back, far side, underside, chair mechanism) are invented from the
  user's description or defaults. Flag which images contain invented surfaces. A photo of the
  back helps the most.
- Proportions are checked to about ±10%, not millimetres. These are marketing images, not drawings.
- Product images must show the real product. An invented view is only published after someone
  has checked it against the real item (Rule 7).

## Inputs
Required: one photo, which side it shows (ask if unclear), and width (left↔right) × depth
(front↔back) × height with units. If given as "L×W×H", map it and confirm in one line. For chairs,
height = overall height at the lowest seat setting unless the user says otherwise.
Optional, ask only if it matters, with defaults: what the hidden sides look like, which angles,
background (default pure white), aspect ratio (default **1:1**, the Shopify/WooCommerce product
grid; 4:3 only if the user asks), the product's name and SKU (needed for Step 7).

For desks, ask which side is the **front**: the user side (where you sit, drawers) or the visitor
side (modesty panel). Use that word consistently in every prompt.

## Step 1 — Spec sheet (before any prompt)
Look closely at the photo and write a compact spec sheet. It goes verbatim into every prompt.
- TYPE and STYLE (e.g. "high-back ergonomic mesh office chair", "L-shaped executive desk")
- SOURCE VIEW and camera height
- MATERIALS and COLOURS per part, named concretely ("black mesh back, dark grey fabric seat",
  "walnut-veneer top 25 mm thick with black ABS edge", "matte black powder-coated steel frame")
- STRUCTURE, by category:
  - **Office chairs:** back (mesh/upholstered, lumbar support), headrest (yes/no, shape), seat,
    armrests (fixed / adjustable; loop or T-shape; pad material), mechanism under the seat
    (levers count and side), gas lift cover, base (5-star; nylon / polished aluminium / chrome;
    approx. diameter), castors (count, colour) or glides
  - **Desks and tables:** top (shape, thickness, edge), frame/legs (panel, sled, T-leg, A-leg,
    4-leg; count; finish), modesty panel, cable management (grommets: count and position;
    cable tray), return/pedestal attached (side), height-adjustable column and controller
  - **Workstations/benching:** seats (count and layout), shared spine, desk screens (height,
    material, colour), cable trays
  - **Storage (pedestals, filing cabinets, cupboards, lockers):** drawers/doors (count and
    layout), lock (yes/no, position), handles (type, finish), plinth or castors, shelves if open
  - **Reception counters:** front panel, transaction top height, desk-side layout
  - **Sofas and lounge seating:** arms, back shape, cushions (count, loose/fixed), legs
- HARDWARE: handles, knobs, levers, buttons, castors (count, finish)
- DISTINCTIVE DETAILS a buyer would miss if gone (contrast stitching, logo plate, stitch pattern)
- VISIBLE vs HIDDEN surfaces
If something required can't be seen (e.g. drawer count, lever count), ask instead of guessing.

## Step 2 — Dimension lock
With W, D, H, the expected outline ratio (width ÷ height of the item in the image) is about:
- front / back: W/H
- left / right side: D/H
- 3/4 views: 0.7 × (W + D) / H
- top-down: W/D
Write it into each prompt in plain words: "160 cm wide × 80 cm deep × 75 cm tall; in this view the
item is about 2.1 times wider than it is tall."

## Step 3 — Hidden surfaces (defaults, list them so the user can correct)
Office furniture:
- **Office chair back:** same mesh or upholstery as the front, back frame in the frame colour,
  lumbar adjuster visible if the front shows one. **Underside/mechanism:** black mechanism with the
  same number of levers seen from the front; gas lift with a black cover; 5-star base repeats
  evenly, 5 castors.
- **Desk visitor side** (when the photo shows the user side): flat modesty panel in the frame or
  top finish, no drawers. **User side** (when the photo shows the visitor side): knee space, any
  pedestal on the same side as the photo suggests; ask if unsure.
- **Height-adjustable desk:** two columns in the frame colour, controller on the right front edge
  unless shown otherwise.
- **Pedestal / filing cabinet / cupboard back:** plain flat panel in the carcass colour, no handles.
- **Locker back:** plain flat steel or panel back.
- **Workstation:** screens and legs repeat symmetrically along the spine.
- **Reception counter back (staff side):** plain worktop with knee space, no front-panel graphics.
Home and lounge furniture:
- Sofa/armchair back: same upholstery, smooth, no cushions; legs repeat at the back.
- Cabinet/sideboard/dresser back: plain flat panel in the same finish, no handles.
- Table: legs and aprons repeat symmetrically.
- Bed/headboard back: flat upholstered or panel back.
Treat left and right as mirror images unless the photo shows asymmetry (L-desk return, chaise, one
arm, side drawer, levers on one side).

## Step 4 — Angle plan
Pick the set for the category, skipping the angle the photo already shows
(* = contains invented surfaces):

| Category | Default angles |
|---|---|
| Office chair | 01 front · 02 3/4 front-left · 03 side (one; the other is a mirror unless asymmetric) · 04 3/4 back* · 05 back* · 06 detail: mechanism and base* · 07 detail: armrest or lumbar. No top-down. |
| Desk / meeting table | 01 front · 02 3/4 front-left · 03 3/4 front-right · 04 side · 05 back (other side)* · 06 top-down · 07 detail: edge, grommet or leg |
| Height-adjustable desk | as desk, plus 08 detail: controller · 09 raised position only if the user supplies the max height |
| Workstation / benching | 01 3/4 high angle · 02 front · 03 side · 04 top-down (layout) · 05 detail: screen or cable tray |
| Storage / lockers | 01 front · 02 3/4 front-left · 03 side · 04 detail: lock or handle. Open-drawer views only if the user supplies a photo of the inside. |
| Sofa / lounge | 01 front · 02 3/4 front-left · 03 3/4 front-right · 04 side · 05 3/4 back* · 06 back* · 07 detail |

Show this as a short table with the expected ratio and the hidden-surface assumptions, then go
straight on to the prompts unless the user objects.

## Step 5 — Write the prompts
Give each angle its own code block so it's one tap to copy. Tell the user: **attach the original
photo with every prompt, and start a new chat for each angle** (stops the tool drifting).
Generate near angles first (3/4 and sides), back views last; for back views, tell the user they may
also attach their best approved side or 3/4 result alongside the original.

Template (the STYLE paragraph must be word-for-word identical in every prompt):

```
Use the attached photo as the exact product. It shows the {SOURCE VIEW}.
Create a new photo of this exact same {TYPE} from this angle: {VIEW, camera position and height}.
It must be the same physical object, not a similar one.

Product details to keep exactly: {SPEC SHEET}

Size: {W} × {D} × {H} {unit} (width × depth × height). In this view the item is about {RATIO}
times wider than it is tall. Keep these proportions.

Newly visible surfaces: {hidden-surface description or "none"}. {symmetry note}

Keep identical colours, material texture and grain direction, mesh or upholstery weave, stitching,
cushion count, leg/castor count, base shape and finish, lever and handle count, position and finish.

STYLE: professional e-commerce studio photo, seamless pure white background, soft large softbox
light from upper front-left, gentle fill, soft natural shadow under the item, true-to-life
colours, 50mm lens look, whole item in frame with a small margin, sharp and highly detailed,
{ASPECT} aspect ratio.

Do not: change materials or colours, add or remove cushions/drawers/handles/levers/legs/castors,
add props, people, text or logos, crop the item, warp the shape, or change the background.
Output ONE single image showing the item once from this one angle. Not a grid, collage,
split screen or multiple views.
```
For the detail close-up, frame only the named material, mechanism or hardware and drop the size
sentence. If the user wants a room scene (e.g. a Saudi office interior), swap the background line
once and reuse it in every prompt; keep the white-background set as the main images.

## Step 6 — Check the results the user uploads
For each image, compare with the original and the spec sheet:
- Same item? colours, materials, counts of cushions/drawers/handles/levers/legs/castors, base
  shape, hardware finish
- Correct angle? (a "left side" shows the item's left as seen from the front)
- Nothing added, whole item in frame, no warped geometry, same background and light as the set
- Proportions roughly match the expected ratio. If code execution is available, measure the
  outline on the white background with Pillow (bounding box of non-background pixels → width/height);
  otherwise judge by eye. More than ~12% off counts as a fail.
For each failure, give a corrected prompt with one specific fix line added
("the chair has exactly 5 black castors on a polished aluminium 5-star base", "the back panel has
no handles").
Finish with a short table: angle · pass/fix · invented surfaces yes/no.

## Step 7 — Publish pack (for the approved images)
Ask for the product name (Arabic and English), SKU and colour if not given. Then give one table
row per image, in upload order:

| Order | File name | Alt text (AR) | Alt text (EN) | AI-generated | Invented surfaces |
|---|---|---|---|---|---|

- **Order:** main image first: front or 3/4 front on white, whichever shows the product best (use
  the original photo if it is a clean studio shot). Then 3/4, side, back, details, room scene last.
- **File name:** lowercase English, hyphens, no spaces or Arabic:
  `{brand}-{model}-{product-type}-{colour}-{angle}.webp`, e.g.
  `officehub-ergo-pro-mesh-office-chair-black-3-4-front.webp`.
- **Alt text:** describe what the image shows, product type + key feature + colour + angle, under
  ~125 characters, no "image of". Arabic in Modern Standard Arabic, e.g.
  "كرسي مكتب شبكي أسود بمسند رأس وقاعدة خماسية، منظر جانبي".
- **Export:** keep a 2048 × 2048 px master (1:1); upload WebP at quality ~80 (most files land
  around 100–300 KB). Same canvas size and margins for the whole set.
- **AI label:** every generated image (not the user's original photo) gets the IPTC
  DigitalSourceType label before upload. Google Merchant Center requires it for AI-generated
  product images. Tell the user to put only the generated files in a folder named `ai` and run
  this on their computer (exiftool, free from exiftool.org):

  ```
  exiftool -overwrite_original -XMP-iptcExt:DigitalSourceType="http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia" ai/
  ```
  Some image editors and upload tools strip metadata. Label the final WebP files, and don't
  re-save them afterwards. More on labelling: the officehub-seo skill's images workflow.
- **Invented surfaces:** list them again. Those images go up only after someone at OfficeHub has
  checked them against the real product (Rule 7).

## Rules
1. Every prompt tells the user to attach the original photo. Never rely on text alone.
2. Spec sheet and size sentence go verbatim into every prompt.
3. One STYLE paragraph, identical across the set.
4. Never add or remove parts the item doesn't have.
5. Always flag invented surfaces; never present them as real.
6. Never claim Claude generated the images itself.
7. Don't recommend publishing an image with invented surfaces until the user confirms it matches
   the real product; a product image that misrepresents the item breaks marketplace and Merchant
   Center rules and causes returns.
8. Every AI-generated image in the publish pack carries the IPTC AI label.
