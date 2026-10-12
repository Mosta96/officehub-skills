---
name: officehub-product-angles
description: Use when the user shares one photo of a furniture item plus its dimensions and wants product images of it from the other angles (front, 3/4, sides, back, top, detail). Works in Claude chat with no API key.
---

# OfficeHub Product Angles

Adapted from the multi-angle workflow in github.com/motiful/product-shots, re-aimed at furniture
and rewritten so it works entirely inside Claude chat with no API key.

## Important: how images get made

Claude cannot draw or output photos. So this skill splits the work:
1. **Claude** studies the photo, locks the item's details and proportions, and writes one
   precise, ready-to-paste prompt per angle.
2. **The user** pastes each prompt, together with the original photo, into a free image tool:
   **Gemini** (gemini.google.com, its image model "Nano Banana" is the same family product-shots uses)
   or **ChatGPT** image generation. Recommend Gemini first.
3. **The user uploads the results back** to this chat. Claude checks each one against the original
   and the dimensions, and rewrites the prompt for any view that came out wrong.

Say this in two or three lines at the start of the first reply, then get on with the work.

## Honest limits (mention once)
- The image tool re-draws the item for each angle; it does not rotate a 3D model. Shape, colour,
  upholstery and legs usually hold; fine grain, stitching, small logos and carving can drift.
- Sides the photo doesn't show (back, far side, underside) are invented from the user's description
  or defaults. Flag which images contain invented surfaces. A photo of the back helps the most.
- Proportions are checked to about ±10%, not millimetres. These are marketing images, not drawings.

## Inputs
Required: one photo, which side it shows (ask if unclear), and width (left↔right) × depth
(front↔back) × height with units. If given as "L×W×H", map it and confirm in one line.
Optional, ask only if it matters, with defaults: what the hidden sides look like, which angles,
background (default pure white), aspect ratio (default 4:3; 1:1 for marketplaces).

## Step 1 — Spec sheet (before any prompt)
Look closely at the photo and write a compact spec sheet. It goes verbatim into every prompt.
- TYPE and STYLE (e.g. "3-seat mid-century sofa")
- SOURCE VIEW and camera height
- MATERIALS and COLOURS per part, named concretely ("warm walnut, straight grain, satin finish",
  "oatmeal bouclé upholstery with self piping")
- STRUCTURE: arms, back shape, cushions (count, loose/fixed), doors, drawers (count, layout),
  shelves, legs (count, shape, material, height), base, feet
- HARDWARE: handles, knobs, buttons, nailheads, castors (count, finish)
- DISTINCTIVE DETAILS a buyer would miss if gone
- VISIBLE vs HIDDEN surfaces
If something required can't be seen (e.g. drawer count), ask instead of guessing.

## Step 2 — Dimension lock
With W, D, H, the expected outline ratio (width ÷ height of the item in the image) is about:
- front / back: W/H
- left / right side: D/H
- 3/4 views: 0.7 × (W + D) / H
- top-down: W/D
Write it into each prompt in plain words: "220 cm wide × 95 cm deep × 82 cm tall; in this view the
item is about 2.0 times wider than it is tall."

## Step 3 — Hidden surfaces (defaults, list them so the user can correct)
- Sofa/armchair back: same upholstery, smooth, no cushions; legs repeat at the back.
- Cabinet/sideboard/dresser back: plain flat panel in the same finish, no handles.
- Table: legs and aprons repeat symmetrically.
- Bed/headboard back: flat upholstered or panel back.
Treat left and right as mirror images unless the photo shows asymmetry (chaise, one arm, side drawer).

## Step 4 — Angle plan
Default set, skipping the angle the photo already shows:
01 front · 02 3/4 front-left · 03 3/4 front-right · 04 left side · 05 right side ·
06 3/4 back* · 07 back* · 08 top-down (tables, beds, sideboards only) · 09 detail close-up
(* contains invented surfaces). Show this as a short table with the expected ratio and the
hidden-surface assumptions, then go straight on to the prompts unless the user objects.

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

Keep identical colours, material texture and grain direction, upholstery weave, stitching,
cushion count, leg count/shape/finish, and handle/hardware count, position and finish.

STYLE: professional e-commerce studio photo, seamless pure white background, soft large softbox
light from upper front-left, gentle fill, soft natural shadow under the item, true-to-life
colours, 50mm lens look, whole item in frame with a small margin, sharp and highly detailed,
{ASPECT} aspect ratio.

Do not: change materials or colours, add or remove cushions/drawers/handles/legs, add props,
people, text or logos, crop the item, warp the shape, or change the background.
Output ONE single image showing the item once from this one angle. Not a grid, collage,
split screen or multiple views.
```
For the detail close-up, frame only the named material or hardware and drop the size sentence.
If the user wants a room scene, swap the background line once and reuse it in every prompt.

## Step 6 — Check the results the user uploads
For each image, compare with the original and the spec sheet:
- Same item? colours, materials, counts of cushions/drawers/handles/legs, hardware finish
- Correct angle? (a "left side" shows the item's left as seen from the front)
- Nothing added, whole item in frame, no warped geometry, same background and light as the set
- Proportions roughly match the expected ratio. If code execution is available, measure the
  outline on the white background with Pillow (bounding box of non-background pixels → width/height);
  otherwise judge by eye. More than ~12% off counts as a fail.
For each failure, give a corrected prompt with one specific fix line added
("the sofa has exactly 4 tapered walnut legs", "the back panel has no handles").
Finish with a short table: angle · pass/fix · invented surfaces yes/no.

## Rules
1. Every prompt tells the user to attach the original photo. Never rely on text alone.
2. Spec sheet and size sentence go verbatim into every prompt.
3. One STYLE paragraph, identical across the set.
4. Never add or remove parts the item doesn't have.
5. Always flag invented surfaces; never present them as real.
6. Never claim Claude generated the images itself.
