"""
Geometry-first vector fitting for flat artwork (logos, icons, line art).

Turns a binary colour-layer mask into clean SVG path data, in this order:

  1. Contours: exact pixel boundaries (outer shapes and holes) of the mask.
  2. Shapes: a contour that is a circle or an axis-aligned ellipse becomes an exact
     circle/ellipse.
  3. Straight lines: straight runs become real line segments (total least squares),
     snapped to exact horizontal/vertical (and optionally 45°) when they are within
     the snap angle. Corners between lines are rebuilt as exact intersections.
  4. Curves between lines: a circular arc when one fits, otherwise smooth cubic Béziers
     (Schneider fit) that join the lines tangentially.
  5. Alignment across the whole artwork: horizontal edges with nearly the same y and
     vertical edges with nearly the same x share one value; near-equal circles share
     centre and radius; coordinates snap to a fine grid.
  6. Safety net: each fitted contour is rasterized and compared with its pixels. If it
     moved too far it is refitted without alignment, then curves-only, then as a
     faithful polygon, so polishing never changes the design.

All tolerances are in "display pixels" (px of the final image size) and converted with
``k`` = working pixels per display pixel.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw


# --------------------------------------------------------------------------- params

@dataclass
class GeoParams:
    k: float                      # working px per display px
    line_tol: float = 0.4         # max distance of points from a straight line
    shape_tol: float = 0.5        # max radial error for whole circles/ellipses
    arc_tol: float = 0.35         # max radial error for arcs between lines
    curve_tol: float = 0.35       # max error of Bézier fits
    min_line: float = 4.0         # shortest straight segment kept as a line
    corner_angle: float = 30.0    # degrees; sharper turns are corners
    snap_angle: float = 1.5       # degrees from H/V (and 45° if snap45) to snap
    snap45: bool = False
    align_tol: float = 0.75       # cluster tolerance for shared edges / circles
    grid: float = 0.125           # coordinate grid
    corner_gap: float = 2.0       # small rounding between two lines → sharp corner
    check_dev: float = 0.3        # max mean deviation of a fitted contour
    check_area: float = 0.01      # max relative area change of a fitted contour

    def px(self, v: float) -> float:
        return v * self.k


def strict(p: GeoParams) -> GeoParams:
    """Larger tolerances for clean logos whose source is wobbly (old traces, scans)."""
    return GeoParams(k=p.k, line_tol=0.8, shape_tol=1.0, arc_tol=0.7, curve_tol=0.5,
                     min_line=3.0, corner_angle=28.0, snap_angle=3.0, snap45=True,
                     align_tol=1.25, grid=0.125, corner_gap=3.0, check_dev=0.6,
                     check_area=0.02)


# --------------------------------------------------------------------------- contours

def trace_contours(mask: np.ndarray, min_area_px: float = 2.0) -> list[np.ndarray]:
    """Closed boundary loops of a binary mask, as midpoints of unit pixel edges.

    Loops are oriented with the inside on the right (y down), so outer boundaries and
    holes alternate as needed for the even-odd fill rule.
    """
    m = np.pad(mask.astype(bool), 1)
    edges: dict[tuple[int, int], list[tuple[int, int]]] = {}
    # horizontal edges at y=r between rows r-1 (above) and r (below), x from c to c+1
    above, below = m[:-1, :], m[1:, :]
    rr, cc = np.nonzero(below & ~above)          # inside below → walk east
    for r, c in zip(rr.tolist(), cc.tolist()):
        edges.setdefault((c, r + 1), []).append((c + 1, r + 1))
    rr, cc = np.nonzero(above & ~below)          # inside above → walk west
    for r, c in zip(rr.tolist(), cc.tolist()):
        edges.setdefault((c + 1, r + 1), []).append((c, r + 1))
    left, right = m[:, :-1], m[:, 1:]
    rr, cc = np.nonzero(left & ~right)           # inside left → walk south
    for r, c in zip(rr.tolist(), cc.tolist()):
        edges.setdefault((c + 1, r), []).append((c + 1, r + 1))
    rr, cc = np.nonzero(right & ~left)           # inside right → walk north
    for r, c in zip(rr.tolist(), cc.tolist()):
        edges.setdefault((c + 1, r + 1), []).append((c + 1, r))

    loops: list[np.ndarray] = []
    while edges:
        start = next(iter(edges))
        cur = start
        prev_dir = None
        pts = []
        while True:
            outs = edges.get(cur)
            if not outs:
                break
            if len(outs) == 1:
                nxt = outs.pop()
            else:  # saddle: turn right (keeps diagonal pixels separate)
                def turn(o):
                    d = (o[0] - cur[0], o[1] - cur[1])
                    if prev_dir is None:
                        return 0
                    cross = prev_dir[0] * d[1] - prev_dir[1] * d[0]
                    return -cross
                outs.sort(key=turn)
                nxt = outs.pop(0)
            if not outs:
                del edges[cur]
            pts.append(((cur[0] + nxt[0]) / 2.0, (cur[1] + nxt[1]) / 2.0))
            prev_dir = (nxt[0] - cur[0], nxt[1] - cur[1])
            cur = nxt
            if cur == start and (start not in edges):
                break
            if cur == start and prev_dir is not None and len(pts) > 2:
                break
        if len(pts) >= 4:
            p = np.asarray(pts, dtype=np.float64) - 1.0  # undo padding
            if abs(_area(p)) >= min_area_px:
                loops.append(p)
    return loops


def _area(p: np.ndarray) -> float:
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def _smooth_closed(p: np.ndarray, w: int) -> np.ndarray:
    if w <= 0 or len(p) < 2 * w + 3:
        return p.copy()
    out = np.zeros_like(p)
    for s in range(-w, w + 1):
        out += np.roll(p, s, axis=0)
    return out / (2 * w + 1)


# --------------------------------------------------------------------------- fits

def fit_circle(p: np.ndarray):
    x, y = p[:, 0], p[:, 1]
    a = np.column_stack([x, y, np.ones_like(x)])
    b = x * x + y * y
    sol, *_ = np.linalg.lstsq(a, b, rcond=None)
    cx, cy = sol[0] / 2, sol[1] / 2
    r = math.sqrt(max(sol[2] + cx * cx + cy * cy, 0.0))
    res = np.abs(np.hypot(x - cx, y - cy) - r)
    return cx, cy, r, float(res.max()) if len(res) else 0.0


def fit_ellipse_axis(p: np.ndarray):
    """Axis-aligned ellipse A x² + C y² + D x + E y = 1."""
    x, y = p[:, 0], p[:, 1]
    mx, my = x.mean(), y.mean()
    xs, ys = x - mx, y - my
    a = np.column_stack([xs * xs, ys * ys, xs, ys])
    sol, *_ = np.linalg.lstsq(a, np.ones_like(xs), rcond=None)
    A, C, D, E = sol
    if A <= 0 or C <= 0:
        return None
    cx, cy = -D / (2 * A), -E / (2 * C)
    rhs = 1 + A * cx * cx + C * cy * cy
    if rhs <= 0:
        return None
    rx, ry = math.sqrt(rhs / A), math.sqrt(rhs / C)
    ang = np.arctan2((ys - cy) / ry, (xs - cx) / rx)
    ex, ey = cx + rx * np.cos(ang), cy + ry * np.sin(ang)
    res = np.hypot(xs - ex, ys - ey)
    return cx + mx, cy + my, rx, ry, float(res.max())


def fit_line(p: np.ndarray):
    """Total least squares line: (centroid, unit direction, max distance)."""
    c = p.mean(axis=0)
    _, _, vt = np.linalg.svd(p - c, full_matrices=False)
    u = vt[0]
    n = np.array([-u[1], u[0]])
    dist = np.abs((p - c) @ n)
    return c, u, float(dist.max()) if len(dist) else 0.0


def _chord_dev(p: np.ndarray) -> float:
    a, b = p[0], p[-1]
    ab = b - a
    ln = math.hypot(*ab)
    if ln < 1e-9:
        return float(np.hypot(*(p - a).T).max())
    n = np.array([-ab[1], ab[0]]) / ln
    return float(np.abs((p - a) @ n).max())


# --- Schneider cubic Bézier fitting ------------------------------------------------

def _bez(ctrl, t):
    t = t[:, None]
    mt = 1 - t
    return (mt ** 3) * ctrl[0] + 3 * (mt ** 2) * t * ctrl[1] + 3 * mt * (t ** 2) * ctrl[2] + (t ** 3) * ctrl[3]


def _bez_d1(ctrl, t):
    t = t[:, None]
    mt = 1 - t
    return 3 * (mt ** 2) * (ctrl[1] - ctrl[0]) + 6 * mt * t * (ctrl[2] - ctrl[1]) + 3 * (t ** 2) * (ctrl[3] - ctrl[2])


def _bez_d2(ctrl, t):
    t = t[:, None]
    return 6 * (1 - t) * (ctrl[2] - 2 * ctrl[1] + ctrl[0]) + 6 * t * (ctrl[3] - 2 * ctrl[2] + ctrl[1])


def _chord_param(d):
    seg = np.hypot(*np.diff(d, axis=0).T)
    u = np.concatenate([[0.0], np.cumsum(seg)])
    return u / u[-1] if u[-1] > 0 else np.linspace(0, 1, len(d))


def _gen_bezier(d, u, t1, t2):
    p0, p3 = d[0], d[-1]
    b1 = 3 * u * (1 - u) ** 2
    b2 = 3 * u ** 2 * (1 - u)
    a1 = b1[:, None] * t1
    a2 = b2[:, None] * t2
    c00 = float((a1 * a1).sum())
    c01 = float((a1 * a2).sum())
    c11 = float((a2 * a2).sum())
    base = _bez(np.array([p0, p0, p3, p3]), u)
    tmp = d - base
    x0 = float((a1 * tmp).sum())
    x1 = float((a2 * tmp).sum())
    det = c00 * c11 - c01 * c01
    seg = math.hypot(*(p3 - p0))
    if abs(det) > 1e-12:
        al = (x0 * c11 - x1 * c01) / det
        ar = (c00 * x1 - c01 * x0) / det
    else:
        al = ar = seg / 3
    eps = 1e-6 * seg
    if al < eps or ar < eps:
        al = ar = seg / 3
    return np.array([p0, p0 + t1 * al, p3 + t2 * ar, p3])


def _max_err(d, ctrl, u):
    dist = np.hypot(*(_bez(ctrl, u) - d).T)
    i = int(np.argmax(dist))
    return float(dist[i]), i


def _reparam(d, ctrl, u):
    q = _bez(ctrl, u) - d
    q1 = _bez_d1(ctrl, u)
    q2 = _bez_d2(ctrl, u)
    num = (q * q1).sum(axis=1)
    den = (q1 * q1).sum(axis=1) + (q * q2).sum(axis=1)
    un = u - np.where(np.abs(den) > 1e-12, num / np.where(np.abs(den) > 1e-12, den, 1), 0)
    return np.clip(un, 0, 1)


def _unit(v):
    n = math.hypot(*v)
    return v / n if n > 1e-12 else np.array([1.0, 0.0])


def fit_beziers(d: np.ndarray, t1: np.ndarray, t2: np.ndarray, tol: float, depth: int = 0):
    """Fit cubic Béziers to points d with end tangents t1 (out of d[0]) and t2 (into d[-1],
    pointing backwards). Returns a list of 4×2 control arrays."""
    if len(d) <= 2:
        seg = math.hypot(*(d[-1] - d[0])) / 3
        return [np.array([d[0], d[0] + t1 * seg, d[-1] + t2 * seg, d[-1]])]
    u = _chord_param(d)
    ctrl = _gen_bezier(d, u, t1, t2)
    err, split = _max_err(d, ctrl, u)
    if err <= tol:
        return [ctrl]
    if err <= tol * 4:
        for _ in range(12):
            u = _reparam(d, ctrl, u)
            ctrl = _gen_bezier(d, u, t1, t2)
            err, split = _max_err(d, ctrl, u)
            if err <= tol:
                return [ctrl]
    if depth > 12 or len(d) < 6:
        return [ctrl]
    split = min(max(split, 2), len(d) - 3)
    tc = _unit(d[split - 1] - d[split + 1])
    return (fit_beziers(d[:split + 1], t1, tc, tol, depth + 1)
            + fit_beziers(d[split:], -tc, t2, tol, depth + 1))


def _end_tangent(d: np.ndarray, at_start: bool, span: int) -> np.ndarray:
    span = max(1, min(span, len(d) - 1))
    if at_start:
        return _unit(d[span] - d[0])
    return _unit(d[-1 - span] - d[-1])


# --------------------------------------------------------------------------- segments

@dataclass
class Seg:
    kind: str                      # "L", "A", "C"
    a: np.ndarray                  # start point
    b: np.ndarray                  # end point
    c: Optional[np.ndarray] = None  # line: centroid; arc: centre
    u: Optional[np.ndarray] = None  # line: unit direction
    r: float = 0.0                 # arc radius
    sweep: int = 1
    large: int = 0
    ctrl: list = field(default_factory=list)  # Bézier controls
    length: float = 0.0
    concentric: bool = False


@dataclass
class Contour:
    segs: list                     # list[Seg], or empty for full shapes
    shape: Optional[tuple] = None  # ("circle", cx, cy, r) / ("ellipse", cx, cy, rx, ry)
    raw: Optional[np.ndarray] = None
    method: str = ""


def _corner_scores(p: np.ndarray, w: int) -> np.ndarray:
    a = p - np.roll(p, w, axis=0)
    b = np.roll(p, -w, axis=0) - p
    ang = np.degrees(np.abs(np.arctan2(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0],
                                       (a * b).sum(axis=1))))
    return ang


def _find_lines(p: np.ndarray, tol: float, min_len: float) -> list[tuple[int, int]]:
    """Greedy maximal straight runs on an open point sequence (indices inclusive)."""
    n = len(p)
    out = []
    i = 0
    while i < n - 2:
        # exponential + binary search for the furthest j with chord deviation ≤ tol
        lo, hi = i + 1, i + 2
        while hi < n and _chord_dev(p[i:hi + 1]) <= tol:
            lo = hi
            hi = min(n - 1, i + (hi - i) * 2)
            if hi == lo:
                break
        hi = min(hi, n - 1)
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if _chord_dev(p[i:mid + 1]) <= tol:
                lo = mid
            else:
                hi = mid
        j = lo
        if math.hypot(*(p[j] - p[i])) >= min_len:
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


def _bow(q: np.ndarray, c: np.ndarray, u: np.ndarray) -> float:
    """Systematic bend of a run around its fitted line (quadratic sagitta, px)."""
    if len(q) < 6:
        return 0.0
    n = np.array([-u[1], u[0]])
    s = (q - c) @ u
    e = (q - c) @ n
    a = np.polyfit(s, e, 2)[0]
    half = (s.max() - s.min()) / 2
    return abs(a) * half * half


def _intersect(c1, u1, c2, u2):
    m = np.array([u1, -u2]).T
    if abs(np.linalg.det(m)) < 1e-9:
        return None
    t = np.linalg.solve(m, c2 - c1)
    return c1 + u1 * t[0]


def _proj(c, u, q):
    return c + u * float((q - c) @ u)


def _arc_seg(a, b, pts, cx, cy, r) -> Seg:
    # sweep: SVG sweep-flag=1 means positive-angle direction (clockwise on screen, y down)
    v0 = pts[0] - (cx, cy)
    vm = pts[len(pts) // 2] - (cx, cy)
    v1 = pts[-1] - (cx, cy)
    a0 = math.atan2(v0[1], v0[0])
    am = math.atan2(vm[1], vm[0])
    a1 = math.atan2(v1[1], v1[0])

    def norm(x):
        return (x + 2 * math.pi) % (2 * math.pi)

    d_pos = norm(a1 - a0)
    sweep = 1 if norm(am - a0) <= d_pos else 0
    span = d_pos if sweep == 1 else 2 * math.pi - d_pos
    return Seg("A", a.copy(), b.copy(), c=np.array([cx, cy]), r=r, sweep=sweep,
               large=1 if span > math.pi else 0, length=r * span)


def _fit_curve_run(pts, t_start, t_end, prm: GeoParams, allow_arc=True,
                   centres=None) -> list[Seg]:
    """Fit an open run: an arc concentric with a known circle, else one free arc,
    else Béziers split at sharp corners."""
    tol_arc = prm.px(prm.arc_tol)
    if centres and len(pts) >= 6:
        best = None
        n = len(pts)
        mid = slice(n // 5, n - n // 5) if n >= 10 else slice(0, n)
        for cx, cy in centres:
            rr = np.hypot(pts[:, 0] - cx, pts[:, 1] - cy)
            r = float(np.median(rr[mid]))
            ok = np.abs(rr - r) <= prm.px(prm.shape_tol)
            # longest contiguous stretch on the circle
            bi = bj = -1
            i = 0
            while i < n:
                if ok[i]:
                    j = i
                    while j + 1 < n and ok[j + 1]:
                        j += 1
                    if j - i > bj - bi:
                        bi, bj = i, j
                    i = j + 1
                else:
                    i += 1
            if bi < 0 or bj - bi + 1 < max(6, int(0.6 * n)) or r <= prm.px(2):
                continue
            a0 = math.atan2(pts[bi][1] - cy, pts[bi][0] - cx)
            a1 = math.atan2(pts[bj][1] - cy, pts[bj][0] - cx)
            span = abs((a1 - a0 + math.pi) % (2 * math.pi) - math.pi)
            if math.degrees(span) < 10:
                continue
            cover = (bj - bi + 1) / n
            if best is None or cover > best[0]:
                best = (cover, cx, cy, r, bi, bj)
        if best:
            _, cx, cy, r, bi, bj = best
            short = max(3, int(prm.px(1.0)))
            if bi <= short:
                bi = 0
            if n - 1 - bj <= short:
                bj = n - 1
            c = np.array([cx, cy])

            def on_circle(q):
                v = q - c
                return c + v / max(math.hypot(*v), 1e-9) * r

            a_pt, b_pt = on_circle(pts[bi]), on_circle(pts[bj])
            arc = _arc_seg(a_pt, b_pt, pts[bi:bj + 1], cx, cy, r)
            arc.concentric = True
            sgn = 1 if arc.sweep == 1 else -1

            def tangent(q):  # direction of travel along the arc at q (y down)
                v = (q - c) / max(math.hypot(*(q - c)), 1e-9)
                return np.array([-v[1], v[0]]) * sgn

            out: list[Seg] = []
            if bi > 0:
                pre = np.vstack([pts[:bi], a_pt[None, :]])
                out += _fit_curve_run(pre, t_start, -tangent(a_pt), prm, allow_arc=False)
            out.append(arc)
            if bj < n - 1:
                post = np.vstack([b_pt[None, :], pts[bj + 1:]])
                out += _fit_curve_run(post, tangent(b_pt), t_end, prm, allow_arc=False)
            return out
    if allow_arc and len(pts) >= 8:
        cx, cy, r, err = fit_circle(pts)
        chord = math.hypot(*(pts[-1] - pts[0]))
        if err <= tol_arc and r < 50 * max(chord, 1) and r > prm.px(1.0):
            return [_arc_seg(pts[0], pts[-1], pts, cx, cy, r)]
    w = max(2, int(round(prm.px(1.5))))
    segs: list[Seg] = []
    # split at internal sharp corners
    cuts = [0]
    if len(pts) > 2 * w + 2:
        sc = np.zeros(len(pts))
        a = pts[w:-w] - pts[:-2 * w]
        b = pts[2 * w:] - pts[w:-w]
        sc[w:-w] = np.degrees(np.abs(np.arctan2(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0],
                                                (a * b).sum(axis=1))))
        i = w
        while i < len(pts) - w:
            if sc[i] > prm.corner_angle + 15:
                j = i + int(np.argmax(sc[i:i + w]))
                cuts.append(j)
                i = j + w
            else:
                i += 1
    cuts.append(len(pts) - 1)
    span = max(2, int(round(prm.px(1.0))))
    for s, e in zip(cuts[:-1], cuts[1:]):
        d = pts[s:e + 1]
        if len(d) < 2:
            continue
        t1 = t_start if s == 0 and t_start is not None else _end_tangent(d, True, span)
        t2 = t_end if e == len(pts) - 1 and t_end is not None else _end_tangent(d, False, span)
        for ctrl in fit_beziers(d, t1, t2, prm.px(prm.curve_tol)):
            segs.append(Seg("C", ctrl[0].copy(), ctrl[3].copy(), ctrl=[c.copy() for c in ctrl]))
    return segs


def fit_contour(raw: np.ndarray, prm: GeoParams, use_lines: bool = True,
                centres=None) -> Contour:
    n = len(raw)
    p = _smooth_closed(raw, 1 if prm.k < 3 else 2)
    # 1. whole shapes
    if n >= 16:
        cx, cy, r, err = fit_circle(p)
        if r >= prm.px(2.0) and err <= prm.px(prm.shape_tol):
            return Contour([], ("circle", cx, cy, r), raw, "circle")
        el = fit_ellipse_axis(p)
        if el and min(el[2], el[3]) >= prm.px(2.0) and el[4] <= prm.px(prm.shape_tol):
            return Contour([], ("ellipse",) + el[:4], raw, "ellipse")
    w = max(2, int(round(prm.px(1.5))))
    scores = _corner_scores(p, w)
    # rotate so the loop starts at its sharpest point (never in the middle of a line)
    s0 = int(np.argmax(scores))
    p = np.roll(p, -s0, axis=0)
    loop = np.vstack([p, p[:1]])
    lines = _find_lines(loop, prm.px(prm.line_tol), prm.px(prm.min_line)) if use_lines else []

    segs: list[Seg] = []
    if not lines:
        t = _unit(loop[1] - loop[-2])
        cs = _fit_curve_run(loop, t, -t, prm, allow_arc=False)
        return Contour(cs, None, raw, "curves")

    # refine each line with TLS on its interior points
    fitted = []
    for i, j in lines:
        q = loop[i:j + 1]
        trim = min(len(q) // 4, max(1, int(prm.px(0.5))))
        core = q[trim:len(q) - trim] if len(q) - 2 * trim >= 2 else q
        c, u, _ = fit_line(core)
        if (q[-1] - q[0]) @ u < 0:
            u = -u
        # a gentle curve also stays within the tolerance of its chord: reject runs
        # that bend systematically (they belong to a curve, not a line)
        bow = _bow(core, c, u)
        if bow > prm.px(prm.line_tol) * 0.75:
            continue
        # shapes first: a run that follows a known circle (ring, rounded cut-out) better
        # than a straight line is an arc of that circle, not a line
        if centres and len(q) >= 6:
            dev_l = float(np.abs((q - c) @ np.array([-u[1], u[0]])).max())
            arc_like = False
            for cx, cy in centres:
                rr = np.hypot(q[:, 0] - cx, q[:, 1] - cy)
                dev_c = float(np.abs(rr - np.median(rr)).max())
                if dev_c <= prm.px(prm.shape_tol) and dev_c < 0.7 * dev_l:
                    arc_like = True
                    break
            if arc_like:
                continue
        fitted.append((i, j, c, u, bow))

    # merge neighbouring collinear lines (a tiny wobble split one edge in two)
    merged = True
    while merged and len(fitted) > 1:
        merged = False
        for k in range(len(fitted) - 1):
            i1, j1, c1, u1, _ = fitted[k]
            i2, j2, c2, u2, _ = fitted[k + 1]
            short = min(math.hypot(*(loop[j1] - loop[i1])),
                        math.hypot(*(loop[j2] - loop[i2]))) < 3 * prm.px(prm.min_line)
            max_ang = 6.0 if short else 2.0
            # offset measured at the junction (a short piece's centroid is far away)
            jn = (loop[j1] + loop[i2]) / 2
            off = abs(float((jn - c1) @ np.array([-u1[1], u1[0]])))
            if (abs(float(u1 @ u2)) > math.cos(math.radians(max_ang))
                    and off <= prm.px(prm.line_tol) * 1.5
                    and i2 - j1 <= max(3, int(prm.px(1.0)))):
                c, u, dev = fit_line(loop[i1:j2 + 1])
                if dev <= prm.px(prm.line_tol) * (2.0 if short else 1.5):
                    if (loop[j2] - loop[i1]) @ u < 0:
                        u = -u
                    fitted[k] = (i1, j2, c, u, _bow(loop[i1:j2 + 1], c, u))
                    del fitted[k + 1]
                    merged = True
                    break

    # bowed runs are lines only between two real corners (a stem end, a bar end):
    # elsewhere a bend means curve
    bow_tight = max(0.6, prm.px(0.12))
    ext = np.vstack([loop, loop[1:]])
    changed = True
    while changed and fitted:
        changed = False
        mm = len(fitted)
        for k in range(mm):
            i, j, c, u, bow = fitted[k]
            if bow <= bow_tight:
                continue
            ok = mm >= 3
            if ok:
                pi_, pj, pc, pu, _ = fitted[k - 1]
                ni_, nj, nc, nu, _ = fitted[(k + 1) % mm]
                g_in = ext[pj:i + 1] if i >= pj else ext[pj:i + len(p) + 1]
                g_out = ext[j:ni_ + 1] if ni_ >= j else ext[j:ni_ + len(p) + 1]
                for g, a, b in ((g_in, pu, u), (g_out, u, nu)):
                    turn = math.degrees(math.acos(float(np.clip(a @ b, -1, 1))))
                    chord = math.hypot(*(g[-1] - g[0])) if len(g) > 1 else 0.0
                    if not (turn >= 60 and chord <= prm.px(prm.corner_gap)):
                        ok = False
            if not ok:
                del fitted[k]
                changed = True
                break
    fitted = [f[:4] for f in fitted]

    # drop facets: short lines joined smoothly at both ends are pieces of a curve
    facet_len = prm.px(8.0)
    tspan = max(2, int(prm.px(1.0)))
    changed = True
    while changed and fitted:
        changed = False
        mm = len(fitted)
        for k in range(mm):
            i, j, c, u = fitted[k]
            if math.hypot(*(loop[j] - loop[i])) >= facet_len:
                continue
            pi_, pj, pc, pu = fitted[k - 1]
            ni_, nj, nc, nu = fitted[(k + 1) % mm]
            ext = np.vstack([loop, loop[1:]])
            # tangent of the neighbouring geometry at each end of this line
            if mm == 1:
                t_in = _end_tangent(ext[j:i + len(p) + 1], False, tspan) * -1
                t_out = _end_tangent(ext[j:i + len(p) + 1], True, tspan)
            else:
                g_in = ext[pj:i + 1] if i >= pj else ext[pj:i + len(p) + 1]
                g_out = ext[j:ni_ + 1] if ni_ >= j else ext[j:ni_ + len(p) + 1]
                short_in = len(g_in) <= 3 or math.hypot(*(g_in[-1] - g_in[0])) <= prm.px(prm.corner_gap)
                short_out = len(g_out) <= 3 or math.hypot(*(g_out[-1] - g_out[0])) <= prm.px(prm.corner_gap)
                t_in = pu if short_in else -_end_tangent(g_in, False, tspan)
                t_out = nu if short_out else _end_tangent(g_out, True, tspan)
            ang_in = math.degrees(math.acos(float(np.clip(t_in @ u, -1, 1))))
            ang_out = math.degrees(math.acos(float(np.clip(u @ t_out, -1, 1))))
            if ang_in < prm.corner_angle and ang_out < prm.corner_angle:
                del fitted[k]
                changed = True
                break
    if not fitted:
        t = _unit(loop[1] - loop[-2])
        return Contour(_fit_curve_run(loop, t, -t, prm, allow_arc=False), None, raw, "curves")

    m = len(fitted)
    for idx in range(m):
        i, j, c, u = fitted[idx]
        segs.append(Seg("L", _proj(c, u, loop[i]), _proj(c, u, loop[j]), c=c, u=u))
        ni, nj, nc, nu = fitted[(idx + 1) % m]
        gap_end = ni if idx + 1 < m else ni + len(p)
        gap = np.vstack([loop, loop[1:]])[j:gap_end + 1] if gap_end > j else loop[j:j + 1]
        cos_t = float(np.clip(u @ nu, -1, 1))
        turn = math.degrees(math.acos(cos_t))
        gap_len = math.hypot(*(gap[-1] - gap[0])) if len(gap) > 1 else 0.0
        if turn >= 150 and len(gap) >= 2 and gap_len <= prm.px(prm.corner_gap) * 2:
            # U-turn between parallel edges (end of a bar or thin line): flat end cap
            cc, cu, _ = fit_line(gap) if len(gap) >= 3 else ((gap[0] + gap[-1]) / 2, _unit(gap[-1] - gap[0]), 0)
            if (gap[-1] - gap[0]) @ cu < 0:
                cu = -cu
            # square ends unless the cap is clearly angled
            perp = np.array([-u[1], u[0]])
            if perp @ cu < 0:
                perp = -perp
            if math.degrees(math.acos(float(np.clip(perp @ cu, -1, 1)))) < 20:
                cu = perp
                cc = gap.mean(axis=0)
            segs.append(Seg("corner", gap[0], gap[0]))
            segs.append(Seg("L", gap[0].copy(), gap[-1].copy(), c=cc, u=cu))
            segs.append(Seg("corner", gap[-1], gap[-1]))
            continue
        if (gap_len <= prm.px(1.0) or len(gap) <= 3
                or (gap_len <= prm.px(prm.corner_gap) and turn >= 45)):
            segs.append(Seg("corner", gap[0], gap[-1]))
            continue
        # curve between two lines: tangent-continuous where the turn is smooth
        d_in = _end_tangent(gap, True, max(2, int(prm.px(1.0))))
        d_out = _end_tangent(gap, False, max(2, int(prm.px(1.0))))
        t1 = u if math.degrees(math.acos(float(np.clip(d_in @ u, -1, 1)))) < 25 else d_in
        t2 = -nu if math.degrees(math.acos(float(np.clip(d_out @ -nu, -1, 1)))) < 25 else d_out
        segs.extend(_fit_curve_run(gap, t1, t2, prm, centres=centres))
    return Contour(segs, None, raw, "lines+curves")


# --------------------------------------------------------------------------- assembly

def resolve(ct: Contour) -> None:
    """Rebuild junctions: corners as line intersections, curves attached to lines."""
    if ct.shape or not ct.segs:
        return
    segs = list(ct.segs)
    n = len(segs)
    for idx in range(n):
        s = segs[idx]
        if s.kind != "corner":
            continue
        prv = segs[(idx - 1) % n]
        nxt = segs[(idx + 1) % n]
        if prv.kind == "L" and nxt.kind == "L":
            x = _intersect(prv.c, prv.u, nxt.c, nxt.u)
            if x is not None and math.hypot(*(x - s.a)) < 25 * max(1.0, math.hypot(*(s.b - s.a))):
                prv.b = x
                nxt.a = x
    segs = [s for s in segs if s.kind != "corner"]
    n = len(segs)
    for idx in range(n):
        s = segs[idx]
        nxt = segs[(idx + 1) % n]
        if s.kind == "L" and nxt.kind != "L":
            q = _proj(s.c, s.u, nxt.a)
            _move_start(nxt, q)
            s.b = q
        elif s.kind != "L" and nxt.kind == "L":
            q = _proj(nxt.c, nxt.u, s.b)
            _move_end(s, q)
            nxt.a = q
        elif s.kind == "L" and nxt.kind == "L":
            if math.hypot(*(s.b - nxt.a)) > 1e-6:
                x = _intersect(s.c, s.u, nxt.c, nxt.u)
                if x is not None and math.hypot(*(x - s.b)) < 4 * max(1e-3, math.hypot(*(s.b - nxt.a))) + 2:
                    s.b = x
                    nxt.a = x
                else:
                    nxt.a = s.b
        else:
            if math.hypot(*(s.b - nxt.a)) > 1e-9:
                mid = (s.b + nxt.a) / 2
                _move_end(s, mid)
                _move_start(nxt, mid)
    for s in segs:
        if s.kind == "L":
            s.length = math.hypot(*(s.b - s.a))
    ct.segs = segs


def _move_start(s: Seg, q):
    if s.kind == "C":
        delta = q - s.ctrl[0]
        s.ctrl[0] = q.copy()
        s.ctrl[1] = s.ctrl[1] + delta
    s.a = q.copy()


def _move_end(s: Seg, q):
    if s.kind == "C":
        delta = q - s.ctrl[3]
        s.ctrl[3] = q.copy()
        s.ctrl[2] = s.ctrl[2] + delta
    s.b = q.copy()


def snap_lines(contours: list[Contour], prm: GeoParams) -> int:
    """Exact H/V (and 45°) for lines within the snap angle. Returns the count."""
    n = 0
    targets = [0, 90, 180, 270] + ([45, 135, 225, 315] if prm.snap45 else [])
    for ct in contours:
        for s in ct.segs:
            if s.kind != "L":
                continue
            ang = math.degrees(math.atan2(s.u[1], s.u[0])) % 360
            for t in targets:
                if abs((ang - t + 180) % 360 - 180) <= prm.snap_angle and abs((ang - t + 180) % 360 - 180) > 1e-9:
                    rad = math.radians(t)
                    s.u = np.array([round(math.cos(rad), 12), round(math.sin(rad), 12)])
                    n += 1
                    break
    return n


def align(contours: list[Contour], prm: GeoParams) -> int:
    """Shared x for vertical edges, shared y for horizontal edges, unified circles."""
    tol = prm.px(prm.align_tol)
    changed = 0
    for axis in (0, 1):  # 0: vertical lines share x; 1: horizontal lines share y
        items = []
        for ct in contours:
            for s in ct.segs:
                if s.kind == "L":
                    is_v = abs(s.u[0]) < 1e-9
                    is_h = abs(s.u[1]) < 1e-9
                    if (axis == 0 and is_v) or (axis == 1 and is_h):
                        items.append((float(s.c[axis]), max(math.hypot(*(s.b - s.a)), 1e-3), s))
        items.sort(key=lambda t: t[0])
        groups: list[list] = []
        for it in items:
            if groups and it[0] - groups[-1][0][0] <= tol:
                groups[-1].append(it)
            else:
                groups.append([it])
        for g in groups:
            if len(g) < 2:
                continue
            wsum = sum(t[1] for t in g)
            val = sum(t[0] * t[1] for t in g) / wsum
            for _, _, s in g:
                if abs(s.c[axis] - val) > 1e-9:
                    changed += 1
                s.c = s.c.copy()
                s.c[axis] = val
    # arcs around the same centre: one radius per ring
    arcs = [s for ct in contours for s in ct.segs if s.kind == "A" and s.concentric]
    arcs.sort(key=lambda a: (round(a.c[0], 3), round(a.c[1], 3), a.r))
    groups = []
    for a in arcs:
        if groups and np.allclose(groups[-1][0].c, a.c) and a.r - groups[-1][-1].r <= tol:
            groups[-1].append(a)
        else:
            groups.append([a])
    for g in groups:
        if len(g) > 1:
            r = sum(a.r * max(a.length, 1) for a in g) / sum(max(a.length, 1) for a in g)
            for a in g:
                a.r = r
            changed += len(g)
    # circles
    shapes = [ct for ct in contours if ct.shape and ct.shape[0] == "circle"]
    for i, a in enumerate(shapes):
        for b in shapes[i + 1:]:
            if abs(a.shape[3] - b.shape[3]) <= tol and math.hypot(a.shape[1] - b.shape[1], a.shape[2] - b.shape[2]) <= tol:
                cx = (a.shape[1] + b.shape[1]) / 2
                cy = (a.shape[2] + b.shape[2]) / 2
                r = (a.shape[3] + b.shape[3]) / 2
                a.shape = b.shape = ("circle", cx, cy, r)
                changed += 1
    return changed


def _line_circle(c, u, cc, r, near):
    """Intersection of line (c, u) with circle (cc, r) closest to ``near``."""
    f = c - cc
    b = float(f @ u)
    disc = b * b - (float(f @ f) - r * r)
    if disc < 0:
        return None
    sq = math.sqrt(disc)
    cands = [c + u * (-b - sq), c + u * (-b + sq)]
    return min(cands, key=lambda q: math.hypot(*(q - near)))


def apply_line_geometry(ct: Contour) -> None:
    """Recompute line endpoints after snapping/aligning (projection on the new line)."""
    if ct.shape:
        return
    n = len(ct.segs)
    for s in ct.segs:
        if s.kind == "L":
            s.a = _proj(s.c, s.u, s.a)
            s.b = _proj(s.c, s.u, s.b)
    for idx in range(n):
        s = ct.segs[idx]
        nxt = ct.segs[(idx + 1) % n]
        if s.kind == "L" and nxt.kind == "L":
            x = _intersect(s.c, s.u, nxt.c, nxt.u)
            if x is not None and math.hypot(*(x - s.b)) <= 3 * max(1.0, math.hypot(*(nxt.a - s.b))) + 3:
                s.b = x.copy()
                nxt.a = x.copy()
            else:
                nxt.a = s.b.copy()
        elif s.kind == "L":
            if nxt.kind == "A":
                q = _line_circle(s.c, s.u, nxt.c, nxt.r, s.b)
                if q is not None and math.hypot(*(q - s.b)) <= 4 * max(1.0, nxt.r * 0.05):
                    s.b = q
            _move_start(nxt, s.b)
        elif nxt.kind == "L":
            if s.kind == "A":
                q = _line_circle(nxt.c, nxt.u, s.c, s.r, nxt.a)
                if q is not None and math.hypot(*(q - nxt.a)) <= 4 * max(1.0, s.r * 0.05):
                    nxt.a = q
            _move_end(s, nxt.a)


def sample(ct: Contour, step: float = 1.0) -> np.ndarray:
    if ct.shape:
        if ct.shape[0] == "circle":
            _, cx, cy, r = ct.shape
            rx = ry = r
        else:
            _, cx, cy, rx, ry = ct.shape
        n = max(32, int(2 * math.pi * max(rx, ry) / step))
        t = np.linspace(0, 2 * math.pi, n, endpoint=False)
        return np.column_stack([cx + rx * np.cos(t), cy + ry * np.sin(t)])
    pts = []
    for s in ct.segs:
        if s.kind == "L":
            pts.append(s.a)
        elif s.kind == "C":
            ln = sum(math.hypot(*(s.ctrl[i + 1] - s.ctrl[i])) for i in range(3))
            t = np.linspace(0, 1, max(4, int(ln / step)), endpoint=False)
            pts.extend(_bez(np.array(s.ctrl), t))
        elif s.kind == "A":
            a0 = math.atan2(s.a[1] - s.c[1], s.a[0] - s.c[0])
            a1 = math.atan2(s.b[1] - s.c[1], s.b[0] - s.c[0])
            d = (a1 - a0) % (2 * math.pi)
            if s.sweep == 0:
                d = d - 2 * math.pi
            nn = max(4, int(abs(d) * s.r / step))
            for t in np.linspace(0, 1, nn, endpoint=False):
                ang = a0 + d * t
                pts.append(np.array([s.c[0] + s.r * math.cos(ang), s.c[1] + s.r * math.sin(ang)]))
    return np.asarray(pts) if pts else np.zeros((0, 2))


def deviation(ct: Contour) -> tuple[float, float]:
    """(mean deviation in working px, relative area change) of fitted vs raw contour."""
    raw = ct.raw
    fit = sample(ct, 0.5)
    if len(fit) < 3:
        return float("inf"), 1.0
    allp = np.vstack([raw, fit])
    x0, y0 = np.floor(allp.min(axis=0)) - 2
    x1, y1 = np.ceil(allp.max(axis=0)) + 2
    ss = 2  # supersample
    w, h = int((x1 - x0) * ss), int((y1 - y0) * ss)
    if w * h > 40_000_000:
        ss = 1
        w, h = int(x1 - x0), int(y1 - y0)

    def rast(poly):
        im = Image.new("1", (max(w, 1), max(h, 1)), 0)
        ImageDraw.Draw(im).polygon([((x - x0) * ss, (y - y0) * ss) for x, y in poly], fill=1)
        return np.asarray(im, dtype=bool)

    a = rast(raw)
    b = rast(fit)
    xor = float((a ^ b).sum()) / (ss * ss)
    perim = float(np.hypot(*np.diff(np.vstack([raw, raw[:1]]), axis=0).T).sum())
    # exact (shoelace) areas: raster areas are biased for thin shapes
    area_a = abs(_area(raw))
    area_b = abs(_area(fit))
    return xor / max(perim, 1.0), abs(area_b - area_a) / max(area_a, 1.0)


def grid_round(v: float, g: float) -> float:
    return round(v / g) * g


def to_path(contours: list[Contour], scale: float, ox: float, oy: float, grid: float,
            decimals: int = 3) -> str:
    """SVG path data in output units (working px / scale + offset), grid-snapped."""
    def P(q):
        x = grid_round(q[0] / scale + ox, grid)
        y = grid_round(q[1] / scale + oy, grid)
        return x, y

    def f(v):
        s = f"{v:.{decimals}f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s

    out = []
    for ct in contours:
        if ct.shape:
            if ct.shape[0] == "circle":
                _, cx, cy, r = ct.shape
                rx = ry = r
            else:
                _, cx, cy, rx, ry = ct.shape
            cx, cy = P((cx, cy))
            rx, ry = grid_round(rx / scale, grid / 2), grid_round(ry / scale, grid / 2)
            out.append(f"M{f(cx - rx)} {f(cy)}A{f(rx)} {f(ry)} 0 1 0 {f(cx + rx)} {f(cy)}"
                       f"A{f(rx)} {f(ry)} 0 1 0 {f(cx - rx)} {f(cy)}Z")
            continue
        if not ct.segs:
            continue
        x0, y0 = P(ct.segs[0].a)
        cmd = [f"M{f(x0)} {f(y0)}"]
        cur = (x0, y0)
        for s in ct.segs:
            bx, by = P(s.b)
            if s.kind == "L":
                if abs(by - cur[1]) < 1e-9 and abs(bx - cur[0]) > 1e-9:
                    cmd.append(f"H{f(bx)}")
                elif abs(bx - cur[0]) < 1e-9 and abs(by - cur[1]) > 1e-9:
                    cmd.append(f"V{f(by)}")
                elif (bx, by) != cur:
                    cmd.append(f"L{f(bx)} {f(by)}")
            elif s.kind == "C":
                c1 = P(s.ctrl[1])
                c2 = P(s.ctrl[2])
                cmd.append(f"C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(bx)} {f(by)}")
            elif s.kind == "A":
                r = s.r / scale
                cmd.append(f"A{f(r)} {f(r)} 0 {s.large} {s.sweep} {f(bx)} {f(by)}")
            cur = (bx, by)
        cmd.append("Z")
        out.append("".join(cmd))
    return "".join(out)


def polish_layers(masks: list[np.ndarray], prm: GeoParams) -> tuple[list[list[Contour]], dict]:
    """Fit every contour of every colour layer, shapes first.

    Pass 1 finds whole circles/ellipses; their centres are then used in pass 2 so arcs
    elsewhere in the artwork (rings, rounded cut-outs) become exactly concentric.
    Snapping, alignment and the safety check run over all layers together.
    """
    min_area = max(2.0, (0.75 * prm.k) ** 2)  # specks under ~0.75 display px
    layer_loops = [trace_contours(m, min_area_px=min_area) for m in masks]
    centres = []
    for loops in layer_loops:
        for lp in loops:
            if len(lp) >= 16:
                cx, cy, r, err = fit_circle(_smooth_closed(lp, 1))
                if r >= prm.px(2.0) and err <= prm.px(prm.shape_tol):
                    if not any(math.hypot(cx - a, cy - b) <= prm.px(prm.align_tol) for a, b in centres):
                        centres.append((cx, cy))
    layers = []
    for loops in layer_loops:
        cts = [fit_contour(lp, prm, centres=centres) for lp in loops]
        for ct in cts:
            resolve(ct)
        layers.append(cts)
    flat = [ct for cts in layers for ct in cts]
    stats = finalize(flat, prm, centres)
    # finalize may replace contours (fallbacks): write them back per layer
    it = iter(flat)
    layers = [[next(it) for _ in cts] for cts in layers]
    stats["contours"] = len(flat)
    stats["circle_centres"] = len(centres)
    return layers, stats


def finalize(all_contours: list[Contour], prm: GeoParams, centres=None) -> dict:
    """Snap, align and safety-check all contours (all layers together)."""
    snapped = snap_lines(all_contours, prm)
    aligned = align(all_contours, prm)
    for ct in all_contours:
        apply_line_geometry(ct)
    stats = {"circles": 0, "ellipses": 0, "lines": 0, "arcs": 0, "curves": 0,
             "snapped_lines": snapped, "aligned_edges": aligned,
             "refit_without_alignment": 0, "fallback_curves": 0, "fallback_polygon": 0,
             "worst_contour_dev_px": 0.0}
    dev_lim = prm.px(prm.check_dev)
    for idx, ct in enumerate(all_contours):
        dev, darea = deviation(ct)
        if dev > dev_lim or darea > prm.check_area:
            # 1) refit locally, snapping but without global alignment
            alt = fit_contour(ct.raw, prm, centres=centres)
            resolve(alt)
            snap_lines([alt], prm)
            apply_line_geometry(alt)
            d2, a2 = deviation(alt)
            if d2 <= dev_lim and a2 <= prm.check_area:
                all_contours[idx] = alt
                stats["refit_without_alignment"] += 1
                dev = d2
            else:
                alt = fit_contour(ct.raw, prm, use_lines=False)
                resolve(alt)
                d3, a3 = deviation(alt)
                if d3 <= dev_lim and a3 <= prm.check_area:
                    all_contours[idx] = alt
                    stats["fallback_curves"] += 1
                    dev = d3
                else:
                    all_contours[idx] = _polygon_contour(ct.raw, prm)
                    stats["fallback_polygon"] += 1
                    dev = deviation(all_contours[idx])[0]
        stats["worst_contour_dev_px"] = max(stats["worst_contour_dev_px"], round(dev / prm.k, 3))
    for ct in all_contours:
        if ct.shape:
            stats["circles" if ct.shape[0] == "circle" else "ellipses"] += 1
        for s in ct.segs:
            stats[{"L": "lines", "A": "arcs", "C": "curves"}[s.kind]] += 1
    return stats


def _polygon_contour(raw: np.ndarray, prm: GeoParams) -> Contour:
    """Faithful fallback: Douglas–Peucker polygon of the raw contour."""
    eps = prm.px(0.2)
    keep = _rdp(np.vstack([raw, raw[:1]]), eps)[:-1]
    segs = []
    for i in range(len(keep)):
        a, b = keep[i], keep[(i + 1) % len(keep)]
        u = _unit(b - a)
        segs.append(Seg("L", a.copy(), b.copy(), c=(a + b) / 2, u=u))
    return Contour(segs, None, raw, "polygon")


def _rdp(p: np.ndarray, eps: float) -> np.ndarray:
    if len(p) < 3:
        return p
    a, b = p[0], p[-1]
    ab = b - a
    ln = math.hypot(*ab)
    if ln < 1e-12:
        d = np.hypot(*(p - a).T)
    else:
        d = np.abs((p - a) @ np.array([-ab[1], ab[0]]) / ln)
    i = int(np.argmax(d))
    if d[i] > eps:
        left = _rdp(p[:i + 1], eps)
        right = _rdp(p[i:], eps)
        return np.vstack([left[:-1], right])
    return np.vstack([a, b])
