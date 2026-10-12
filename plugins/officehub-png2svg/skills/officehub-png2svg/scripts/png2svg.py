#!/usr/bin/env python3
"""
High-detail raster (PNG/JPG/WebP) to SVG converter with automatic solid-background removal.

Pipeline (each step is reported in the JSON report):

  1. Load the image as RGBA.
  2. Background: detect a solid background colour from the image border and remove only
     the background that is connected to the border (flood fill), so same-coloured
     details inside the artwork (white text on a red badge) are kept. Enclosed
     background-coloured areas (inside an "O") are kept unless --holes remove.
  3. Upscale small images (premultiplied, bicubic) so the tracer gets sub-pixel edges.
  4. Defringe: anti-aliased edge pixels that blend artwork and background colour get the
     artwork colour back or become transparent (alpha-matting projection), so the SVG has
     no light/dark halo.
  5. Optional palette reduction (--colors N) for flat artwork.
  6. Trace with vtracer (colour, stacked, spline), using a detail-first preset.
  7. Fix the SVG root (viewBox + original width/height), optionally optimise with svgo.
  8. Verify: render the SVG back, compare with the source (shape IoU, colour error) and
     write a side-by-side preview PNG.

Requirements: Pillow, numpy, vtracer (pip install vtracer).
Optional: resvg-py or cairosvg (verification render), svgo (size optimisation).

Usage:
    python3 png2svg.py logo.png
    python3 png2svg.py logo.png -o logo.svg --preset balanced --json
    python3 png2svg.py icon.png --bg "#f4f4f4" --tolerance 6 --holes remove
    python3 png2svg.py a.png b.png --out-dir svg/
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Optional

try:
    import numpy as np
    from PIL import Image
except ImportError:  # pragma: no cover - environment check
    print("Error: Pillow and numpy are required (pip install pillow numpy).", file=sys.stderr)
    sys.exit(2)

# Pillow >= 9.1 moved resampling constants into an enum.
_RESAMPLE = getattr(Image, "Resampling", Image)

MAX_RGB_DIST = math.sqrt(3 * 255 ** 2)  # 441.67

# vtracer settings per preset. filter_speckle is in source pixels and is scaled by the
# upscale factor before tracing. gradient_colors: colour bands used for artwork that is
# not flat (vtracer cannot trace smooth gradients); colors: fixed palette size.
PRESETS = {
    # Default: keep every detail the source really has.
    "detail": dict(mode="spline", filter_speckle=2, color_precision=8, layer_difference=6,
                   corner_threshold=60, length_threshold=4.0, splice_threshold=45,
                   max_iterations=10, path_precision=3, gradient_colors=64),
    # Fewer tiny paths, still accurate. Good default for logos from screenshots or JPGs.
    "balanced": dict(mode="spline", filter_speckle=4, color_precision=7, layer_difference=12,
                     corner_threshold=60, length_threshold=4.0, splice_threshold=45,
                     max_iterations=10, path_precision=3, gradient_colors=32),
    # Upstream png2svg settings: smooth curves, small files, loses fine detail.
    "smooth": dict(mode="spline", filter_speckle=8, color_precision=8, layer_difference=16,
                   corner_threshold=120, length_threshold=6.0, splice_threshold=45,
                   max_iterations=10, path_precision=3, gradient_colors=24),
    # Flat artwork with few colours: palette reduction + clean shapes.
    "posterize": dict(mode="spline", filter_speckle=4, color_precision=6, layer_difference=16,
                      corner_threshold=60, length_threshold=4.0, splice_threshold=45,
                      max_iterations=10, path_precision=3, colors=12),
    # Pixel art / sharp-cornered UI icons.
    "pixel": dict(mode="polygon", filter_speckle=1, color_precision=8, layer_difference=4,
                  corner_threshold=180, length_threshold=3.5, splice_threshold=45,
                  max_iterations=10, path_precision=2, gradient_colors=0),
}

TRACE_KEYS = ("mode", "filter_speckle", "color_precision", "layer_difference",
              "corner_threshold", "length_threshold", "splice_threshold",
              "max_iterations", "path_precision")


# --------------------------------------------------------------------------- helpers

def _parse_hex(color: str) -> np.ndarray:
    c = color.strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", c):
        raise argparse.ArgumentTypeError(f"not a hex colour: {color!r}")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def _hex(rgb) -> str:
    return "#" + "".join(f"{int(round(v)):02x}" for v in rgb)


def _border_ring(h: int, w: int, width: int = 2) -> np.ndarray:
    ring = np.zeros((h, w), dtype=bool)
    k = max(1, min(width, h // 2, w // 2))
    ring[:k, :] = ring[-k:, :] = True
    ring[:, :k] = ring[:, -k:] = True
    return ring


def _shift(a: np.ndarray, dy: int, dx: int, fill) -> np.ndarray:
    """Shift a 2D/3D array by (dy, dx), filling the uncovered edge with ``fill``."""
    out = np.empty_like(a)
    out[...] = fill
    h, w = a.shape[:2]
    ys_src = slice(max(0, -dy), h - max(0, dy))
    ys_dst = slice(max(0, dy), h - max(0, -dy))
    xs_src = slice(max(0, -dx), w - max(0, dx))
    xs_dst = slice(max(0, dx), w - max(0, -dx))
    out[ys_dst, xs_dst] = a[ys_src, xs_src]
    return out


def _dilate(mask: np.ndarray, steps: int) -> np.ndarray:
    out = mask.copy()
    for _ in range(steps):
        out = (out | _shift(out, 1, 0, False) | _shift(out, -1, 0, False)
               | _shift(out, 0, 1, False) | _shift(out, 0, -1, False))
    return out


def _run_propagate(reached: np.ndarray, cand: np.ndarray) -> np.ndarray:
    """Extend ``reached`` to every horizontal run of ``cand`` that it touches."""
    h, w = cand.shape
    flat = cand.ravel()
    prev = np.zeros_like(flat)
    prev[1:] = flat[:-1]
    prev[::w] = False  # a run never continues across a row boundary
    starts = flat & ~prev
    run_id = np.where(flat, np.cumsum(starts), 0)
    hit = np.bincount(run_id, weights=(reached.ravel() & flat).astype(np.float64),
                      minlength=int(run_id.max()) + 1) > 0
    hit[0] = False
    return hit[run_id].reshape(h, w)


def border_connected(cand: np.ndarray) -> np.ndarray:
    """4-connected components of ``cand`` that touch the image border (pure numpy)."""
    h, w = cand.shape
    reached = cand & _border_ring(h, w, 1)
    while True:
        nxt = _run_propagate(reached, cand)
        nxt = _run_propagate(nxt.T.copy(), cand.T.copy()).T
        if np.array_equal(nxt, reached):
            return nxt
        reached = nxt


# --------------------------------------------------------------------------- steps

def detect_background(rgb: np.ndarray, alpha: np.ndarray, tol: float) -> dict:
    """Find the dominant border colour and how much of the border it covers."""
    h, w = alpha.shape
    ring = _border_ring(h, w, 2)
    ring_alpha = alpha[ring]
    transparent_share = float((ring_alpha < 0.5).mean())
    if transparent_share >= 0.5:
        return {"kind": "transparent", "border_transparent_share": round(transparent_share, 3)}
    px = rgb[ring & (alpha >= 0.5)]
    buckets = (px.astype(np.int32) >> 3)
    keys = buckets[:, 0] * 1024 + buckets[:, 1] * 32 + buckets[:, 2]
    vals, counts = np.unique(keys, return_counts=True)
    top = vals[np.argmax(counts)]
    color = np.median(px[keys == top], axis=0)
    dist = np.linalg.norm(px - color, axis=1)
    coverage = float((dist <= tol).mean())
    return {"kind": "solid" if coverage >= 0.5 else "varied",
            "color": color, "border_coverage": round(coverage, 3)}


def plain_resize(rgb: np.ndarray, alpha: np.ndarray, scale: int):
    """Upscale with the background colour still in the image (solid-background case).

    Anti-aliasing blends stay true artwork/background blends, so the defringe step can
    place every edge at its sub-pixel position instead of following the pixel staircase
    of the background mask.
    """
    if scale == 1:
        return rgb.copy(), alpha.copy()
    h, w = alpha.shape
    size = (w * scale, h * scale)
    chans = [np.asarray(Image.fromarray(rgb[..., c].astype(np.float32), mode="F")
                        .resize(size, _RESAMPLE.BICUBIC), dtype=np.float32) for c in range(3)]
    a_up = np.asarray(Image.fromarray(alpha.astype(np.float32), mode="F")
                      .resize(size, _RESAMPLE.BILINEAR), dtype=np.float32)
    return np.clip(np.stack(chans, axis=-1), 0, 255), np.clip(a_up, 0, 1)


def premultiplied_resize(rgb: np.ndarray, alpha: np.ndarray, scale: int):
    """Upscale RGB + alpha without letting transparent pixels' colour bleed into edges."""
    if scale == 1:
        return rgb.copy(), alpha.copy()
    h, w = alpha.shape
    size = (w * scale, h * scale)
    chans = []
    for c in range(3):
        im = Image.fromarray((rgb[..., c] * alpha).astype(np.float32), mode="F")
        chans.append(np.asarray(im.resize(size, _RESAMPLE.BICUBIC), dtype=np.float32))
    a_im = Image.fromarray(alpha.astype(np.float32), mode="F")
    a_up = np.clip(np.asarray(a_im.resize(size, _RESAMPLE.BICUBIC), dtype=np.float32), 0, 1)
    prem = np.stack(chans, axis=-1)
    safe = np.where(a_up > 1e-3, a_up, 1.0)[..., None]
    rgb_up = np.clip(prem / safe, 0, 255)
    return rgb_up, a_up


def _palette_matte(c: np.ndarray, bg: np.ndarray, palette: np.ndarray, max_dist: float):
    """For edge colours C, find the palette colour F that best explains C as a blend of F
    and the background B. Returns (F, a, ok): a is F's share, ok marks good fits."""
    best_d = np.full(len(c), np.inf, np.float32)
    best_a = np.ones(len(c), np.float32)
    best_f = np.zeros_like(c)
    for f in palette:
        fb = f - bg
        den = float(fb @ fb)
        if den < 20.0 ** 2:  # palette colour equals the background: cannot be a blend
            continue
        a = np.clip(((c - bg) @ fb) / den, 0, 1)
        d = np.linalg.norm(c - (bg + a[:, None] * fb), axis=1)
        better = d < best_d
        best_d = np.where(better, d, best_d)
        best_a = np.where(better, a, best_a)
        best_f = np.where(better[:, None], f, best_f)
    # A pixel that already is a palette colour stays that colour (a light palette colour
    # also lies on the line between a darker one and the background). Next to the removed
    # background, a pixel matching the background colour is background, even when the
    # artwork also uses that colour (white details on a white page).
    d_bg = np.linalg.norm(c - bg, axis=1)
    is_bg = d_bg <= 12.0
    art = palette[np.linalg.norm(palette - bg, axis=1) > 20]
    if len(art):
        d_pt = np.sqrt(((c[:, None, :] - art[None, :, :]) ** 2).sum(axis=2))
        exact = (d_pt.min(axis=1) <= 12.0) & ~is_bg
        best_f = np.where(exact[:, None], art[np.argmin(d_pt, axis=1)], best_f)
        best_a = np.where(exact, 1.0, best_a)
    else:
        exact = np.zeros(len(c), bool)
    best_a = np.where(is_bg, 0.0, best_a)
    return best_f, best_a, exact | is_bg | (best_d <= max_dist)


def defringe(rgb: np.ndarray, opaque: np.ndarray, bg: Optional[np.ndarray], band: int,
             palette: Optional[np.ndarray] = None):
    """Clean the anti-aliased edge band next to transparent areas.

    Each edge pixel C is treated as a blend of an artwork colour F and the background B:
    a = (C-B)·(F-B) / |F-B|². a < 0.5 → transparent; otherwise the pixel gets the pure
    artwork colour F. For flat artwork F comes from the palette, which also works for
    1–2 px strokes; otherwise F is the nearest interior colour, and thin features with no
    interior are left as they are. Returns (rgb, opaque, recolored_px, cleared_px).
    """
    transparent = ~opaque
    if not transparent.any() or not opaque.any():
        return rgb, opaque, 0, 0
    band_mask = _dilate(transparent, band) & opaque
    if palette is not None and bg is not None:
        # Soft (blurred) edges are wider than the fixed band: follow every blend pixel that
        # touches the background, up to where the solid artwork colour starts.
        art = palette[np.linalg.norm(palette - bg, axis=1) > 20]
        if len(art):
            solid = np.zeros(opaque.shape, bool)
            for start in range(0, opaque.shape[0], 256):
                blk = rgb[start:start + 256]
                dmin = np.sqrt(((blk[..., None, :] - art) ** 2).sum(axis=-1)).min(axis=-1)
                solid[start:start + 256] = dmin <= 12.0
            grow = opaque & ~solid
            zone = transparent.copy()
            for _ in range(8 * band + 8):
                nxt = _dilate(zone, 1) & (grow | transparent)
                if np.array_equal(nxt, zone):
                    break
                zone = nxt
            band_mask |= zone & opaque
        rgb = rgb.copy()
        opaque = opaque.copy()
        ys, xs = np.nonzero(band_mask)
        c = rgb[ys, xs]
        f, a, ok = _palette_matte(c, bg, palette, max_dist=32.0)
        clear = ok & (a < 0.5)
        recolor = ok & (a >= 0.5)
        opaque[ys[clear], xs[clear]] = False
        rgb[ys[recolor], xs[recolor]] = f[recolor]
        return rgb, opaque, int(recolor.sum()), int(clear.sum())
    interior = opaque & ~band_mask
    fill = np.where(interior[..., None], rgb, 0.0)
    filled = interior.copy()
    for _ in range(band + 2):
        todo = band_mask & ~filled
        if not todo.any():
            break
        acc = np.zeros_like(rgb)
        cnt = np.zeros(filled.shape, dtype=np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            f_s = _shift(filled, dy, dx, False)
            acc += np.where(f_s[..., None], _shift(fill, dy, dx, 0.0), 0.0)
            cnt += f_s
        newly = todo & (cnt > 0)
        fill[newly] = acc[newly] / cnt[newly][:, None]
        filled |= newly
    target = band_mask & filled
    if not target.any():
        return rgb, opaque, 0, 0
    rgb = rgb.copy()
    opaque = opaque.copy()
    if bg is None:
        rgb[target] = fill[target]
        return rgb, opaque, int(target.sum()), 0
    c = rgb[target]
    f = fill[target]
    fb = f - bg
    denom = (fb * fb).sum(axis=1)
    usable = denom > 20.0 ** 2  # artwork colour clearly different from background
    a = np.where(usable, ((c - bg) * fb).sum(axis=1) / np.where(usable, denom, 1.0), 1.0)
    clear = usable & (a < 0.5)
    recolor = usable & (a >= 0.5) & (a < 0.97)
    ys, xs = np.nonzero(target)
    opaque[ys[clear], xs[clear]] = False
    rgb[ys[recolor], xs[recolor]] = f[recolor]
    return rgb, opaque, int(recolor.sum()), int(clear.sum())


def _segment_distance(px: np.ndarray, anchors: np.ndarray) -> np.ndarray:
    """Distance from each colour to the nearest straight blend between two anchor colours."""
    d = np.full(len(px), np.inf, np.float32)
    for i in range(len(anchors)):
        for j in range(i + 1, len(anchors)):
            a, b = anchors[i], anchors[j]
            ab = b - a
            t = np.clip(((px - a) @ ab) / max(float(ab @ ab), 1e-6), 0, 1)
            d = np.minimum(d, np.linalg.norm(px - (a + t[:, None] * ab), axis=1))
    if len(anchors) == 1:
        d = np.linalg.norm(px - anchors[0], axis=1)
    return d


def detect_flat_palette(rgb: np.ndarray, opaque: np.ndarray, bg: Optional[np.ndarray] = None,
                        max_colors: int = 24,
                        merge_dist: float = 28.0, fit_dist: float = 24.0,
                        min_fit: float = 0.98) -> Optional[np.ndarray]:
    """Return the palette if the artwork is flat (logo/icon style), else None.

    Flat means: ignoring edge pixels (anti-aliasing blends between two colours), at least
    ``min_fit`` of the opaque pixels lie within ``fit_dist`` of a small set of colours.
    Gradients and photos fail this test, so their shading is never snapped.
    """
    if opaque.sum() < 16:
        return None
    # Edge = both pixels of every visible colour step (and the step to transparency),
    # widened by one pixel: anti-aliasing blends live there.
    edge = np.zeros(opaque.shape, bool)
    dy = np.abs(rgb[1:, :] - rgb[:-1, :]).max(axis=2) > 24
    dy |= opaque[1:, :] != opaque[:-1, :]
    dx = np.abs(rgb[:, 1:] - rgb[:, :-1]).max(axis=2) > 24
    dx |= opaque[:, 1:] != opaque[:, :-1]
    edge[1:, :] |= dy
    edge[:-1, :] |= dy
    edge[:, 1:] |= dx
    edge[:, :-1] |= dx
    edge = _dilate(edge, 1)
    core = opaque & ~edge
    px = rgb[core]
    if len(px) < 16:
        return None
    rng = np.random.default_rng(0)
    if len(px) > 200_000:
        px = px[rng.choice(len(px), 200_000, replace=False)]
    sample = Image.fromarray(np.clip(px, 0, 255).astype(np.uint8).reshape(-1, 1, 3), "RGB")
    q = sample.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    idx = np.asarray(q).ravel()
    pal = np.asarray(q.getpalette()[:64 * 3], dtype=np.float32).reshape(-1, 3)
    counts = np.bincount(idx, minlength=len(pal)).astype(np.float64)
    centroids: list[np.ndarray] = []
    weights: list[float] = []
    for i in np.argsort(-counts):
        if counts[i] == 0:
            break
        for j, c in enumerate(centroids):
            if np.linalg.norm(pal[i] - c) <= merge_dist:
                tot = weights[j] + counts[i]
                centroids[j] = (c * weights[j] + pal[i] * counts[i]) / tot
                weights[j] = tot
                break
        else:
            centroids.append(pal[i].copy())
            weights.append(float(counts[i]))
    total = float(sum(weights))
    kept = [(c, wgt) for c, wgt in zip(centroids, weights) if wgt / total >= 0.001]
    # Drop small colours that are only blends: on the line between two heavier colours
    # (or a heavier colour and the background), away from both ends.
    kept.sort(key=lambda cw: -cw[1])
    pruned: list[tuple[np.ndarray, float]] = []
    for c, wgt in kept:
        if wgt / total >= 0.02:  # a real area, even if its colour sits between two others
            pruned.append((c, wgt))
            continue
        ends = [k for k, _ in pruned] + ([bg] if bg is not None else [])
        is_blend = False
        for i in range(len(ends)):
            for j in range(i + 1, len(ends)):
                a, b = ends[i], ends[j]
                ab = b - a
                t = float((c - a) @ ab) / max(float(ab @ ab), 1e-6)
                if 0.1 < t < 0.9 and np.linalg.norm(c - (a + t * ab)) <= fit_dist / 2:
                    is_blend = True
                    break
            if is_blend:
                break
        if not is_blend:
            pruned.append((c, wgt))
    keep = [c for c, _ in pruned]
    if not keep or len(keep) > max_colors:
        return None
    palette = np.stack(keep)
    # Fit is measured on the sampled core pixels (exact, not the quantized indices).
    # Blurry edges (soft logos, enlarged JPGs) leave blend pixels in the core: they count
    # as fitting when they lie between two palette colours (or a colour and the
    # background), but most pixels must be exact palette colours, so a real gradient
    # (mostly in-between colours) never passes.
    d = np.sqrt(((px[:, None, :] - palette[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
    exact_share = float((d <= fit_dist).mean())
    if exact_share < min_fit:
        anchors0 = palette if bg is None else np.vstack([palette, bg[None, :]])
        blend = (d > fit_dist) & (_segment_distance(px, anchors0) <= fit_dist / 2)
        if exact_share < 0.85 or exact_share + float(blend.mean()) < min_fit:
            return None

    # Thin details (1–2 px lines, small text) are all "edge" and never reach the core
    # sample. Add any colour that is neither near the palette nor a blend between two
    # palette colours (or a palette colour and the removed background).
    edge_px = rgb[opaque & edge]
    if len(edge_px) > 200_000:
        edge_px = edge_px[rng.choice(len(edge_px), 200_000, replace=False)]
    anchors = palette if bg is None else np.vstack([palette, bg[None, :]])
    min_cluster = max(12, int(0.01 * len(edge_px)))
    for _ in range(8):
        if not len(edge_px):
            break
        d_pal = np.sqrt(((edge_px[:, None, :] - palette[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
        far = edge_px[d_pal > fit_dist]
        if not len(far):
            break
        d_seg = _segment_distance(far, anchors)
        unexplained = far[d_seg > fit_dist]
        if len(unexplained) < min_cluster:
            break
        extra = Image.fromarray(np.clip(unexplained, 0, 255).astype(np.uint8).reshape(-1, 1, 3),
                                "RGB").quantize(colors=8, method=Image.Quantize.MEDIANCUT,
                                                dither=Image.Dither.NONE)
        e_idx = np.asarray(extra).ravel()
        e_pal = np.asarray(extra.getpalette()[:8 * 3], dtype=np.float32).reshape(-1, 3)
        e_cnt = np.bincount(e_idx, minlength=len(e_pal))
        cands = [i for i in range(len(e_pal))
                 if e_cnt[i] >= min_cluster
                 and np.min(np.linalg.norm(palette - e_pal[i], axis=1)) > merge_dist]
        if not cands:
            break
        # One colour per round, the most extreme first (a thin dark line before its grey
        # blends): blends of the new colour are then explained in the next round.
        ext = _segment_distance(e_pal[cands], anchors)
        added = [e_pal[cands[int(np.argmax(ext))]]]
        palette = np.vstack([palette, added[0][None, :]])
        anchors = palette if bg is None else np.vstack([palette, bg[None, :]])
        if len(palette) > max_colors:
            return None
    return palette


def edge_width(rgb: np.ndarray, opaque: np.ndarray, palette: np.ndarray,
               fit_dist: float = 24.0) -> float:
    """Average width (px) of colour transitions in flat artwork: about 1 for crisp
    anti-aliasing, 2+ for blurred or enlarged sources."""
    label = np.full(opaque.shape, -2, np.int32)  # -2 = transparent
    for start in range(0, opaque.shape[0], 256):
        blk = rgb[start:start + 256]
        dd = np.sqrt(((blk[..., None, :] - palette) ** 2).sum(axis=-1))
        lab = np.where(dd.min(axis=-1) <= fit_dist, dd.argmin(axis=-1), -1)
        label[start:start + 256] = np.where(opaque[start:start + 256], lab, -2)
    blend = int((label == -1).sum())
    solid = label != -1
    diff = np.zeros(opaque.shape, bool)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = _shift(label, dy, dx, -3)
        diff |= (nb != label) & (nb != -3)
    boundary = int((solid & diff).sum())
    return blend / max(1.0, boundary / 2.0)


def snap_to_palette(rgb: np.ndarray, opaque: np.ndarray, palette: np.ndarray,
                    bg: Optional[np.ndarray] = None, exact: float = 12.0) -> np.ndarray:
    """Snap opaque pixels to the palette.

    A pixel close to a palette colour takes it. Otherwise, if it is a blend on the line
    between two palette colours (or a palette colour and the background), it takes the
    nearer end of that line instead of some unrelated colour that happens to be close.
    """
    out = rgb.copy()
    ys, xs = np.nonzero(opaque)
    k = len(palette)
    pairs = [(i, j) for i in range(k) for j in range(i + 1, k)] if k <= 12 else []
    # If a palette colour equals the background (white details on a white page), the
    # background lines duplicate palette lines and would make edge decisions random.
    use_bg = bg is not None and float(np.min(np.linalg.norm(palette - bg, axis=1))) > 20
    for start in range(0, len(ys), 500_000):
        sl = slice(start, start + 500_000)
        px = rgb[ys[sl], xs[sl]]
        d_pt = np.sqrt(((px[:, None, :] - palette[None, :, :]) ** 2).sum(axis=2))
        best = np.argmin(d_pt, axis=1)
        best_d = d_pt[np.arange(len(px)), best]
        locked = best_d <= exact
        segs = [(palette[i], palette[j], i, j) for i, j in pairs]
        if use_bg:
            segs += [(palette[i], bg, i, i) for i in range(k)]
        for a, b, i, j in segs:
            ab = b - a
            t = np.clip(((px - a) @ ab) / max(float(ab @ ab), 1e-6), 0, 1)
            d = np.linalg.norm(px - (a + t[:, None] * ab), axis=1)
            better = (~locked) & (d < best_d)
            best = np.where(better, np.where(t < 0.5, i, j), best)
            best_d = np.where(better, d, best_d)
        out[ys[sl], xs[sl]] = palette[best]
    return out


def reduce_palette(rgb: np.ndarray, opaque: np.ndarray, colors: int) -> np.ndarray:
    """Quantize opaque pixels to ``colors`` colours (median cut + k-means refinement).

    Also used for gradients: vtracer merges a smooth gradient into one flat shape, so it is
    split into fine colour bands first.
    """
    px = np.clip(rgb[opaque], 0, 255).astype(np.uint8)
    if not len(px):
        return rgb
    rng = np.random.default_rng(0)
    sample = px if len(px) <= 300_000 else px[rng.choice(len(px), 300_000, replace=False)]
    pal_img = Image.fromarray(sample.reshape(-1, 1, 3), "RGB").quantize(
        colors=colors, method=Image.Quantize.MEDIANCUT, kmeans=2, dither=Image.Dither.NONE)
    full = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")
    mapped = np.asarray(full.quantize(palette=pal_img, dither=Image.Dither.NONE).convert("RGB"),
                        dtype=np.float32)
    return np.where(opaque[..., None], mapped, rgb)


def trace(png_path: str, svg_path: str, params: dict) -> str:
    """Run vtracer. Supports the 0.6 Python API (pip install vtracer), the 1.0 Python API
    (Config + convert_file) and both CLI flag styles. Returns the engine used."""
    try:
        import vtracer  # type: ignore
    except ImportError:
        vtracer = None
    if vtracer is not None and hasattr(vtracer, "convert_image_to_svg_py"):
        vtracer.convert_image_to_svg_py(
            png_path, svg_path, colormode="color", hierarchical="stacked",
            mode=params["mode"], filter_speckle=int(params["filter_speckle"]),
            color_precision=int(params["color_precision"]),
            layer_difference=int(params["layer_difference"]),
            corner_threshold=int(params["corner_threshold"]),
            length_threshold=float(params["length_threshold"]),
            max_iterations=int(params["max_iterations"]),
            splice_threshold=int(params["splice_threshold"]),
            path_precision=int(params["path_precision"]))
        return "vtracer (python 0.6 API)"
    if vtracer is not None and hasattr(vtracer, "Config") and hasattr(vtracer, "convert_file"):
        cfg = vtracer.Config(
            clustering="color-cluster", hierarchical="stacked", mode=params["mode"],
            filter_speckle=int(params["filter_speckle"]),
            color_precision=int(params["color_precision"]),
            layer_difference=int(params["layer_difference"]),
            corner_threshold=int(params["corner_threshold"]),
            length_threshold=float(params["length_threshold"]),
            max_iterations=int(params["max_iterations"]),
            splice_threshold=int(params["splice_threshold"]),
            path_precision=int(params["path_precision"]))
        vtracer.convert_file(png_path, svg_path, cfg)
        return "vtracer (python 1.x API)"
    exe = shutil.which("vtracer")
    if not exe:
        raise RuntimeError("vtracer is not installed. Install it with: pip install vtracer "
                           "(or: cargo install vtracer)")
    help_text = subprocess.run([exe, "--help"], capture_output=True, text=True)
    help_text = help_text.stdout + help_text.stderr
    kebab = "--filter-speckle" in help_text  # vtracer 1.x CLI; 0.6 uses underscores

    def flag(name: str) -> str:
        return "--" + (name.replace("_", "-") if kebab else name)

    cmd = [exe, "--input", png_path, "--output", svg_path]
    if "--colormode" in help_text:
        cmd += ["--colormode", "color"]
    cmd += ["--hierarchical", "stacked", flag("mode"), params["mode"],
            flag("filter_speckle"), str(int(params["filter_speckle"])),
            flag("color_precision"), str(int(params["color_precision"])),
            flag("gradient_step"), str(int(params["layer_difference"])),
            flag("corner_threshold"), str(int(params["corner_threshold"])),
            flag("segment_length"), str(float(params["length_threshold"])),
            flag("splice_threshold"), str(int(params["splice_threshold"])),
            flag("path_precision"), str(int(params["path_precision"]))]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return "vtracer (cli)"


def fix_svg_root(svg: str, view_w: int, view_h: int, out_w: int, out_h: int) -> str:
    """Give the root a viewBox (so it scales) and the original pixel size."""
    m = re.search(r"<svg\b[^>]*>", svg)
    if not m:
        raise RuntimeError("tracer output has no <svg> root")
    tag = m.group(0)
    new = re.sub(r'\s(width|height|viewBox)="[^"]*"', "", tag)
    new = new[:-1].rstrip("/").rstrip() + (
        f' width="{out_w}" height="{out_h}" viewBox="0 0 {view_w} {view_h}">')
    return svg[:m.start()] + new + svg[m.end():]


def optimize_svg(path: str, allow_npx: bool) -> Optional[str]:
    """Run svgo if available. Returns the tool used, or None when skipped."""
    exe = shutil.which("svgo")
    if exe:
        cmd = [exe]
    elif allow_npx and shutil.which("npx"):
        cmd = ["npx", "--yes", "svgo"]
    else:
        return None
    try:
        subprocess.run(cmd + ["--multipass", "-p", "3", path, "-o", path],
                       check=True, capture_output=True, text=True, timeout=180)
        return " ".join(cmd)
    except (subprocess.SubprocessError, OSError):
        return None


def render_svg(svg_text: str, w: int, h: int) -> Optional[tuple[np.ndarray, str]]:
    """Render SVG to RGBA float array at w×h. Tries resvg-py, cairosvg, then CLIs."""
    png: Optional[bytes] = None
    engine = None
    try:
        import resvg_py  # type: ignore
        png = bytes(resvg_py.svg_to_bytes(svg_string=svg_text, width=w, height=h))
        engine = "resvg-py"
    except Exception:
        pass
    if png is None:
        try:
            import cairosvg  # type: ignore
            png = cairosvg.svg2png(bytestring=svg_text.encode("utf-8"),
                                   output_width=w, output_height=h)
            engine = "cairosvg"
        except Exception:
            pass
    if png is None:
        for exe, args in (("resvg", ["-w", str(w), "-h", str(h)]),
                          ("rsvg-convert", ["-w", str(w), "-h", str(h)])):
            path = shutil.which(exe)
            if not path:
                continue
            with tempfile.TemporaryDirectory() as td:
                src = os.path.join(td, "in.svg")
                dst = os.path.join(td, "out.png")
                with open(src, "w", encoding="utf-8") as fh:
                    fh.write(svg_text)
                try:
                    if exe == "resvg":
                        subprocess.run([path, *args, src, dst], check=True,
                                       capture_output=True, timeout=120)
                    else:
                        subprocess.run([path, *args, "-o", dst, src], check=True,
                                       capture_output=True, timeout=120)
                    with open(dst, "rb") as fh:
                        png = fh.read()
                    engine = exe
                    break
                except (subprocess.SubprocessError, OSError):
                    continue
    if png is None:
        return None
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    if im.size != (w, h):
        im = im.resize((w, h), _RESAMPLE.LANCZOS)
    return np.asarray(im, dtype=np.float32), engine


def _checker(h: int, w: int, cell: int = 8) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w]
    light = ((yy // cell + xx // cell) % 2 == 0)
    return np.where(light[..., None], 236.0, 204.0) * np.ones((1, 1, 3), np.float32)


def _over_checker(rgba: np.ndarray) -> np.ndarray:
    h, w = rgba.shape[:2]
    a = rgba[..., 3:4] / 255.0
    return rgba[..., :3] * a + _checker(h, w) * (1 - a)


def _composite(rgba: np.ndarray, color) -> np.ndarray:
    a = rgba[..., 3:4] / 255.0
    return rgba[..., :3] * a + np.asarray(color, np.float32) * (1 - a)


def verify(src_rgba: np.ndarray, removed: Optional[np.ndarray], bg: Optional[np.ndarray],
           svg_text: str, preview_path: Optional[str], soft_edges: bool = False) -> dict:
    """Render the SVG and compare it with the source the way a viewer would see it.

    - Solid background removed: the SVG is placed on the original background colour and
      compared with the original image; ``background_clear`` checks that the removed
      area really is transparent in the SVG.
    - Otherwise both are compared on white and on black (alpha matters).
    shape_iou compares the "ink" (pixels clearly different from the background);
    color_mae / color_p95 are RGB errors (0–255) inside the ink area.
    """
    h, w = src_rgba.shape[:2]
    rendered = render_svg(svg_text, w, h)
    if rendered is None:
        return {"verified": False,
                "note": "no SVG renderer found; install one with: pip install resvg-py"}
    out, engine = rendered
    result: dict = {"verified": True, "renderer": engine}
    if bg is not None:
        pairs = [(_composite(src_rgba, bg), _composite(out, bg), bg)]
    else:
        pairs = [(_composite(src_rgba, c), _composite(out, c), np.asarray(c, np.float32))
                 for c in ((255, 255, 255), (0, 0, 0))]
    ious, maes, p95s = [], [], []
    ink_t_any = np.zeros((h, w), bool)
    ink_r_any = np.zeros((h, w), bool)
    for comp_t, comp_r, base in pairs:
        if bg is not None:
            ink_t = np.linalg.norm(comp_t - base, axis=2) > 40
            ink_r = np.linalg.norm(comp_r - base, axis=2) > 40
        else:
            ink_t = src_rgba[..., 3] >= 128
            ink_r = out[..., 3] >= 128
        union = ink_t | ink_r
        ious.append(float((ink_t & ink_r).sum() / union.sum()) if union.any() else 1.0)
        region = _dilate(union, 1)
        err = np.abs(comp_r - comp_t).max(axis=2)[region]
        maes.append(float(np.abs(comp_r - comp_t)[region].mean()) if region.any() else 0.0)
        p95s.append(float(np.percentile(err, 95)) if region.any() else 0.0)
        ink_t_any |= ink_t
        ink_r_any |= ink_r
    iou, mae, p95 = min(ious), max(maes), max(p95s)
    result.update({"shape_iou": round(iou, 4), "color_mae": round(mae, 2),
                   "color_p95": round(p95, 1)})
    clear = 1.0
    leak = np.zeros((h, w), bool)
    if removed is not None and removed.any():
        inner = removed & ~_dilate(~removed, 2)  # ignore the 2 px next to the artwork
        if inner.any():
            leak = inner & (out[..., 3] > 25)
            clear = float(1 - leak.sum() / inner.sum())
        result["background_clear"] = round(clear, 4)
    # A crisp SVG of a blurred source differs along every edge by design.
    good_iou = 0.90 if soft_edges else 0.93
    if iou >= 0.97 and mae <= 6 and clear >= 0.995:
        grade = "excellent"
    elif iou >= good_iou and mae <= 12 and clear >= 0.98:
        grade = "good"
    else:
        grade = "check"
    result["grade"] = grade
    if preview_path:
        comp_t, comp_r, _ = pairs[0]
        diff = np.abs(comp_r - comp_t).max(axis=2)
        heat = np.zeros((h, w, 3), np.float32)
        heat[..., 0] = np.clip(diff * 4, 0, 255)
        heat[ink_t_any ^ ink_r_any] = (255, 0, 255)
        heat[leak] = (0, 220, 255)
        gap = np.full((h, max(4, w // 50), 3), 255.0, np.float32)
        sheet = np.concatenate([_over_checker(src_rgba), gap, _over_checker(out), gap, heat],
                               axis=1)
        im = Image.fromarray(np.clip(sheet, 0, 255).astype(np.uint8), "RGB")
        if im.width > 2400:
            im = im.resize((2400, max(1, round(im.height * 2400 / im.width))), _RESAMPLE.LANCZOS)
        im.save(preview_path)
        result["preview"] = preview_path
        result["preview_legend"] = ("left: source, middle: SVG on a checkerboard (checks = "
                                    "transparent), right: difference (red = colour error, "
                                    "magenta = shape mismatch, cyan = background not removed)")
    return result


# --------------------------------------------------------------------------- main flow

def convert(inp: str, out_svg: str, args: argparse.Namespace) -> dict:
    report: dict = {"input": inp, "output": out_svg, "warnings": []}
    src = Image.open(inp)
    src.load()
    report["input_mode"] = src.mode
    rgba = np.asarray(src.convert("RGBA"), dtype=np.float32)
    h, w = rgba.shape[:2]
    report["input_size"] = [w, h]
    rgb = rgba[..., :3]
    alpha = rgba[..., 3] / 255.0

    # Photo-like input check (SVG tracing is meant for logos, icons, flat illustrations).
    thumb = np.asarray(src.convert("RGB").resize((min(w, 256), min(h, 256))), dtype=np.int32) >> 3
    n_colors = len(np.unique(thumb[..., 0] * 1024 + thumb[..., 1] * 32 + thumb[..., 2]))
    if n_colors > 3000:
        report["warnings"].append(
            f"photo-like image ({n_colors} distinct colour buckets): the SVG will be large and "
            "will look painted. Consider --preset posterize or keeping the raster.")

    # ---- background
    tol = args.tolerance / 100.0 * MAX_RGB_DIST
    bg_color = None
    bg_info: dict = {"mode": args.bg}
    if args.bg == "keep":
        bg_info["action"] = "kept"
    else:
        det = detect_background(rgb, alpha, tol)
        if args.bg != "auto":
            det = {"kind": "solid", "color": _parse_hex(args.bg),
                   "border_coverage": det.get("border_coverage")}
        bg_info["detected"] = det["kind"]
        if det["kind"] == "transparent":
            bg_info["action"] = "none (already transparent)"
        elif det["kind"] == "varied":
            bg_info["action"] = "kept (no solid background on the border)"
            bg_info["border_coverage"] = det["border_coverage"]
            report["warnings"].append(
                "no solid background found: the border is varied (photo, gradient or "
                "artwork touching the edges). Pass --bg '#rrggbb' to force a colour.")
        else:
            bg_color = np.asarray(det["color"], dtype=np.float32)
            dist = np.linalg.norm(rgb - bg_color, axis=2)
            cand = (dist <= tol) | (alpha < 0.5)
            region = border_connected(cand)
            enclosed = cand & ~region & (alpha >= 0.5)
            if args.holes == "remove":
                region = region | enclosed
            removed = region & (alpha >= 0.5)
            alpha = np.where(region, 0.0, alpha)
            bg_info.update({
                "color": _hex(bg_color),
                "border_coverage": det.get("border_coverage"),
                "tolerance_pct": args.tolerance,
                "removed_pct": round(100.0 * removed.sum() / (h * w), 2),
                "enclosed_bg_colour_pct": round(100.0 * enclosed.sum() / (h * w), 2),
                "holes": args.holes,
                "action": "removed (border-connected only)" if args.holes == "keep"
                else "removed (border-connected + enclosed)",
            })
            if args.holes == "keep" and enclosed.sum() > 0.001 * h * w:
                report["warnings"].append(
                    f"{bg_info['enclosed_bg_colour_pct']}% of the image has the background "
                    "colour but is enclosed by artwork (inside letters or shapes). It was kept. "
                    "Re-run with --holes remove if those areas should be transparent.")
    report["background"] = bg_info
    removed_mask = (alpha < 0.5) & (rgba[..., 3] >= 128) if bg_color is not None else None

    # ---- upscale
    if args.upscale == "auto":
        long_side = max(w, h)
        scale = 1 if long_side >= 1200 else min(4, math.ceil(1200 / long_side))
        while scale > 1 and (w * scale) * (h * scale) > 16_000_000:
            scale -= 1
    else:
        scale = int(args.upscale)
    report["upscale"] = scale
    if bg_color is not None:
        rgb_up, a_up = plain_resize(rgb, alpha, scale)
    else:
        rgb_up, a_up = premultiplied_resize(rgb, alpha, scale)
    opaque = a_up >= 0.5

    # ---- preset + overrides
    params = dict(PRESETS[args.preset])
    preset_colors = params.pop("colors", 0)
    gradient_colors = params.pop("gradient_colors", 0)
    for key in TRACE_KEYS:
        val = getattr(args, key, None)
        if val is not None:
            params[key] = val

    # ---- palette: flat artwork (logo/icon) is snapped to its real colours, which removes
    # anti-aliasing blends and JPEG noise. Detected at the source resolution.
    palette = None
    if args.palette:
        palette = np.stack([_parse_hex(c) for c in args.palette.split(",") if c.strip()])
    elif args.colors == "auto" and not preset_colors:
        palette = detect_flat_palette(rgb, alpha >= 0.5, bg_color)
        width = edge_width(rgb, alpha >= 0.5, palette) if palette is not None else 0.0
        if palette is not None:
            report["edge_width_px"] = round(width, 2)
        if width > 2.0:
            report["soft_edges"] = True
            report["warnings"].append(
                "the source has soft (blurred) edges: the SVG uses crisp edges at the same "
                "positions, so the comparison shows small edge differences. That is expected.")

    # ---- defringe
    if args.defringe == "on":
        rgb_up, opaque, recolored, cleared = defringe(rgb_up, opaque, bg_color,
                                                      band=scale + 1, palette=palette)
        report["defringe"] = {"recolored_px": recolored, "cleared_px": cleared,
                              "band_px": scale + 1,
                              "method": "palette" if palette is not None and bg_color is not None
                              else "interior colour"}
    else:
        report["defringe"] = "off"

    # ---- colours
    if args.colors in ("0", "off"):
        report["palette"] = "off"
    elif palette is not None:
        rgb_up = snap_to_palette(rgb_up, opaque, palette, bg_color)
        report["palette"] = {"mode": "fixed (--palette)" if args.palette else "auto (flat artwork)",
                             "colors": [_hex(c) for c in palette]}
    elif args.colors == "auto" and not preset_colors and gradient_colors:
        rgb_up = reduce_palette(rgb_up, opaque, gradient_colors)
        report["palette"] = {"mode": f"auto (gradients/photo: {gradient_colors} colour bands)"}
    elif args.colors == "auto" and not preset_colors:
        report["palette"] = "auto: not flat artwork, colours kept as traced"
    else:
        n = preset_colors if args.colors == "auto" else int(args.colors)
        rgb_up = reduce_palette(rgb_up, opaque, n)
        report["palette"] = {"mode": f"reduced to {n} colours"}
    trace_params = dict(params)
    trace_params["filter_speckle"] = max(1, int(round(params["filter_speckle"] * scale)))
    report["preset"] = args.preset
    report["trace_params"] = {**params, "filter_speckle_scaled": trace_params["filter_speckle"]}

    # ---- trace
    out_dir = os.path.dirname(os.path.abspath(out_svg))
    os.makedirs(out_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        prep = os.path.join(td, "prepared.png")
        a8 = np.where(opaque, 255, 0).astype(np.uint8)
        rgb8 = np.where(opaque[..., None], np.clip(np.rint(rgb_up), 0, 255), 0).astype(np.uint8)
        Image.fromarray(np.dstack([rgb8, a8]), "RGBA").save(prep)
        if args.keep_temp:
            keep = os.path.splitext(out_svg)[0] + ".prepared.png"
            shutil.copyfile(prep, keep)
            report["prepared_png"] = keep
        raw_svg = os.path.join(td, "raw.svg")
        report["tracer"] = trace(prep, raw_svg, trace_params)
        with open(raw_svg, encoding="utf-8") as fh:
            svg = fh.read()

    svg = fix_svg_root(svg, w * scale, h * scale, w, h)
    svg = re.sub(r'<path d=""[^>]*/>\s*', "", svg)  # vtracer emits empty paths
    with open(out_svg, "w", encoding="utf-8") as fh:
        fh.write(svg)

    # ---- optimise
    if args.optimize:
        tool = optimize_svg(out_svg, allow_npx=args.npx)
        report["optimizer"] = tool or "skipped (svgo not available)"
        with open(out_svg, encoding="utf-8") as fh:
            svg = fh.read()
        if tool and 'viewBox="' not in svg:
            svg = fix_svg_root(svg, w * scale, h * scale, w, h)
            with open(out_svg, "w", encoding="utf-8") as fh:
                fh.write(svg)
    else:
        report["optimizer"] = "off"

    report["svg_bytes"] = os.path.getsize(out_svg)
    report["svg_paths"] = len(re.findall(r"<path\b", svg))
    report["svg_fill_colors"] = len(set(re.findall(r'fill="(#[0-9a-fA-F]{3,8})"', svg)))
    if report["svg_paths"] > 5000:
        report["warnings"].append(
            f"{report['svg_paths']} paths: heavy for the web. Try --preset balanced or "
            "--colors N.")

    # ---- verify
    preview = None if args.no_preview else os.path.splitext(out_svg)[0] + ".preview.png"
    report["verification"] = verify(rgba, removed_mask, bg_color, svg, preview,
                                    soft_edges=bool(report.get("soft_edges")))

    # Thin strokes / small text: most artwork pixels are edge pixels at the source size.
    ink = alpha >= 0.5
    if ink.sum() > 50:
        thin = 1 - float((ink & ~_dilate(~ink, 1)).sum()) / float(ink.sum())
        if thin > 0.35:
            report["warnings"].append(
                f"thin strokes or small text ({round(thin * 100)}% of the artwork is edge "
                "pixels): the source has too few pixels for an exact trace. Use a 2–4× larger "
                "PNG, or the original vector/font, for text that must be pixel-perfect.")
    return report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="High-detail PNG/JPG/WebP → SVG with automatic solid-background removal.")
    p.add_argument("inputs", nargs="+", help="Input raster image(s)")
    p.add_argument("-o", "--output", help="Output SVG (single input only)")
    p.add_argument("--out-dir", help="Folder for outputs (default: next to each input)")
    p.add_argument("--bg", default="auto",
                   help="auto (detect from border), keep, or a hex colour like '#ffffff'")
    p.add_argument("--tolerance", type=float, default=8.0,
                   help="Background colour tolerance in %% of max RGB distance (default 8)")
    p.add_argument("--holes", choices=("keep", "remove"), default="keep",
                   help="Background-coloured areas enclosed by artwork (default keep)")
    p.add_argument("--preset", choices=sorted(PRESETS), default="detail")
    p.add_argument("--colors", default="auto",
                   help="auto (snap flat artwork to its palette; default), 0/off, or N to "
                        "reduce to N colours before tracing")
    p.add_argument("--palette",
                   help="Exact colours to snap to, e.g. '#c81e28,#143ca0,#ffffff' (brand "
                        "colours). Every artwork colour must be listed")
    p.add_argument("--upscale", default="auto", choices=("auto", "1", "2", "3", "4"))
    p.add_argument("--defringe", choices=("on", "off"), default="on")
    p.add_argument("--no-optimize", dest="optimize", action="store_false",
                   help="Skip svgo even if installed")
    p.add_argument("--npx", action="store_true",
                   help="Allow 'npx --yes svgo' (downloads svgo) when svgo is not installed")
    p.add_argument("--no-preview", action="store_true", help="Do not write the preview PNG")
    p.add_argument("--keep-temp", action="store_true",
                   help="Keep the prepared (background-removed, upscaled) PNG")
    p.add_argument("--json", action="store_true", help="Print the report as JSON")
    p.add_argument("--report", help="Also write the JSON report to this file")
    g = p.add_argument_group("vtracer overrides")
    g.add_argument("--mode", choices=("spline", "polygon", "none"))
    g.add_argument("--filter-speckle", dest="filter_speckle", type=int)
    g.add_argument("--color-precision", dest="color_precision", type=int)
    g.add_argument("--layer-difference", dest="layer_difference", type=int)
    g.add_argument("--corner-threshold", dest="corner_threshold", type=int)
    g.add_argument("--length-threshold", dest="length_threshold", type=float)
    g.add_argument("--splice-threshold", dest="splice_threshold", type=int)
    g.add_argument("--max-iterations", dest="max_iterations", type=int)
    g.add_argument("--path-precision", dest="path_precision", type=int)
    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.bg not in ("auto", "keep"):
        try:
            _parse_hex(args.bg)
        except argparse.ArgumentTypeError as exc:
            parser.error(f"--bg: {exc}")
    if args.palette:
        try:
            [_parse_hex(c) for c in args.palette.split(",") if c.strip()]
        except argparse.ArgumentTypeError as exc:
            parser.error(f"--palette: {exc}")
    if args.colors not in ("auto", "off") and not args.colors.isdigit():
        print("Error: --colors must be auto, off or a number.", file=sys.stderr)
        return 2
    if args.output and len(args.inputs) > 1:
        print("Error: -o/--output works with one input; use --out-dir for several.",
              file=sys.stderr)
        return 2
    reports = []
    status = 0
    for inp in args.inputs:
        if args.output:
            out = args.output
        else:
            base = os.path.splitext(os.path.basename(inp))[0] + ".svg"
            out = os.path.join(args.out_dir or os.path.dirname(os.path.abspath(inp)), base)
        try:
            rep = convert(inp, out, args)
        except Exception as exc:  # report and continue with the next file
            rep = {"input": inp, "error": f"{type(exc).__name__}: {exc}"}
            status = 1
        reports.append(rep)
        if not args.json:
            _print_human(rep)
    result = reports[0] if len(reports) == 1 else reports
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, default=str)
    return status


def _print_human(rep: dict) -> None:
    if "error" in rep:
        print(f"✗ {rep['input']}: {rep['error']}")
        return
    v = rep.get("verification", {})
    bg = rep.get("background", {})
    print(f"✓ {rep['input']} → {rep['output']}")
    print(f"  size {rep['input_size'][0]}×{rep['input_size'][1]}, upscale ×{rep['upscale']}, "
          f"preset {rep['preset']}, tracer {rep['tracer']}")
    print(f"  background: {bg.get('action')}"
          + (f" ({bg.get('color')}, removed {bg.get('removed_pct')}%)" if bg.get("color") else ""))
    print(f"  svg: {rep['svg_bytes']:,} bytes, {rep['svg_paths']} paths, "
          f"{rep['svg_fill_colors']} colours, optimizer {rep['optimizer']}")
    if v.get("verified"):
        print(f"  check: {v['grade']} (shape IoU {v['shape_iou']}, colour MAE {v['color_mae']}, "
              f"p95 {v['color_p95']}) via {v['renderer']}"
              + (f"; preview {v['preview']}" if v.get("preview") else ""))
    else:
        print(f"  check: not verified ({v.get('note')})")
    for w in rep.get("warnings", []):
        print(f"  ! {w}")


if __name__ == "__main__":
    sys.exit(main())
