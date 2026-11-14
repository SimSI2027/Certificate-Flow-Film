"""V5a realistic hardware (amendment V5-A1): rack cabinets with 1U/2U devices, the root's locked cage and offline machine, the HSM
key module, the laptop, desk and office chair. Procedural ``bmesh`` geometry; faces go to material slots (``blender.actors.slots``)
whose finishes live in ``blender.finishes``. Every shell built here stays inside its declared box (``cff.stage.hardware``).

Conventions: a rack's local frame has its origin at the base centre and its front toward -Y; sizes are full extents in metres.
No brand marks, text or logos anywhere.
"""

from __future__ import annotations

import math

import bmesh
from mathutils import Matrix, Vector

from blender.actors import primitives as p
from blender.actors import slots as s
from cff.stage import hardware as hw
from cff.stage import layout as lo

U = hw.RACK_UNIT_M
GAP = 0.0015  # between stacked devices
EAR = 0.02  # rack-ear width each side of a device
BODY_W = hw.DEVICE_WIDTH_M - 2 * EAR
PLATE = 0.006  # faceplate thickness
PROUD = 0.003  # how far small front parts stand proud of the faceplate


def span(bm: bmesh.types.BMesh, slot_index: int, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> None:
    with p.slot(bm, slot_index):
        p.box_span(bm, min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1))


# --- devices --------------------------------------------------------------------------------------------------------


def _bays(bm: bmesh.types.BMesh, cx: float, fy: float, z0: float, z1: float, cols: int, rows: int, width: float) -> None:
    """Drive caddies: a caddy face, a latch line and an activity LED each."""
    pitch_x, pitch_z = width / cols, (z1 - z0) / rows
    for r in range(rows):
        for c in range(cols):
            x0 = cx - width / 2 + c * pitch_x + 0.0012
            x1 = x0 + pitch_x - 0.0024
            zb = z0 + r * pitch_z + 0.0012
            zt = zb + pitch_z - 0.0024
            span(bm, s.CADDY, x0, x1, fy - PROUD, fy, zb, zt)
            if pitch_z > pitch_x:  # vertical small-form-factor caddy: latch along its length
                span(bm, s.BEZEL, (x0 + x1) / 2 - 0.0015, (x0 + x1) / 2 + 0.0015, fy - PROUD - 0.0015, fy - PROUD, zb + 0.008, zt - 0.012)
                span(bm, s.LED, x0 + 0.002, x0 + 0.005, fy - PROUD - 0.001, fy - PROUD, zt - 0.006, zt - 0.003)
            else:
                span(bm, s.BEZEL, x0 + 0.01, x1 - 0.022, fy - PROUD - 0.0015, fy - PROUD, zb + 0.004, zb + 0.007)
                span(bm, s.LED, x1 - 0.012, x1 - 0.008, fy - PROUD - 0.001, fy - PROUD, zt - 0.007, zt - 0.004)


def _vents(bm: bmesh.types.BMesh, x0: float, x1: float, fy: float, z0: float, z1: float, count: int) -> None:
    step = (x1 - x0) / count
    for i in range(count):
        span(bm, s.VENT, x0 + i * step + step * 0.25, x0 + i * step + step * 0.75, fy - 0.0008, fy, z0, z1)


def _ports(bm: bmesh.types.BMesh, x0: float, x1: float, fy: float, z0: float, z1: float, cols: int, rows: int, leds: bool) -> None:
    """RJ45-style jacks in groups of six, with a link LED above each column (switch) or none (patch panel)."""
    pitch = (x1 - x0) / (cols + cols // 6)
    row_h = (z1 - z0) / rows
    for c in range(cols):
        x = x0 + (c + c // 6) * pitch
        for r in range(rows):
            zb = z0 + r * row_h
            span(bm, s.VENT, x + 0.0008, x + pitch - 0.0008, fy - 0.0012, fy, zb + 0.0012, zb + row_h - 0.0012)
        if leds and c % 2 == 0:
            span(bm, s.LED, x + 0.002, x + 0.0045, fy - 0.001, fy, z1 + 0.001, z1 + 0.0035)


def device(bm: bmesh.types.BMesh, d: hw.Device, cx: float, fy: float, z0: float, depth: float, accent: bool) -> None:
    """One rack-mounted device: body behind the faceplate ``fy`` (front toward -Y), ears, and its kind's front details."""
    h = d.height_u * U - GAP
    z1 = z0 + h
    span(bm, s.STEEL, cx - BODY_W / 2, cx + BODY_W / 2, fy + PLATE, fy + depth, z0, z1)
    for side in (-1, 1):
        span(bm, s.STEEL_LIGHT, cx + side * (BODY_W / 2), cx + side * (BODY_W / 2 + EAR), fy, fy + 0.003, z0, z1)
    face = s.STEEL if d.kind in ("blank_1u", "patch_1u") else s.BEZEL
    span(bm, face, cx - BODY_W / 2, cx + BODY_W / 2, fy, fy + PLATE, z0, z1)
    inner = BODY_W - 0.05
    if d.kind == "server_1u":
        _bays(bm, cx + 0.01, fy, z0 + 0.007, z1 - 0.007, 4, 1, inner - 0.08)
        _vents(bm, cx - BODY_W / 2 + 0.01, cx - inner / 2 + 0.03, fy, z0 + 0.01, z1 - 0.01, 4)
    elif d.kind == "server_2u":
        _bays(bm, cx + 0.015, fy, z0 + 0.006, z1 - 0.006, 24, 1, inner - 0.03)
    elif d.kind == "storage_2u":
        _bays(bm, cx, fy, z0 + 0.004, z1 - 0.004, 4, 3, inner)
    elif d.kind == "switch_1u":
        _ports(bm, cx - inner / 2, cx + inner / 2 - 0.07, fy, z0 + 0.008, z1 - 0.012, 24, 2, True)
        for i in range(4):  # uplink cages
            x = cx + inner / 2 - 0.065 + i * 0.016
            span(bm, s.STEEL_LIGHT, x, x + 0.013, fy - 0.0015, fy, z0 + 0.012, z1 - 0.016)
    elif d.kind == "patch_1u":
        _ports(bm, cx - inner / 2 + 0.02, cx + inner / 2 - 0.02, fy, z0 + 0.012, z1 - 0.012, 24, 1, False)
    elif d.kind == "manager_1u":
        for i in range(5):  # cable rings
            x = cx - inner / 2 + 0.02 + i * (inner - 0.04) / 4
            span(bm, s.STEEL_LIGHT, x - 0.012, x + 0.012, fy - 0.03, fy, z1 - 0.008, z1 - 0.003)
            span(bm, s.STEEL_LIGHT, x - 0.012, x - 0.008, fy - 0.03, fy, z0 + 0.004, z1 - 0.003)
    elif d.kind == "blank_1u":
        _vents(bm, cx - inner / 2, cx + inner / 2, fy, z0 + 0.016, z1 - 0.016, 18)
    elif d.kind == "ups_2u":
        span(bm, s.GLASS, cx - 0.06, cx + 0.03, fy - 0.001, fy, z0 + 0.045, z1 - 0.015)
        for i in range(4):
            span(bm, s.CADDY, cx + 0.05 + i * 0.016, cx + 0.062 + i * 0.016, fy - PROUD, fy, z0 + 0.05, z0 + 0.062)
            span(bm, s.LED, cx + 0.054 + i * 0.016, cx + 0.058 + i * 0.016, fy - 0.001, fy, z0 + 0.07, z0 + 0.074)
        _vents(bm, cx - inner / 2, cx + inner / 2, fy, z0 + 0.008, z0 + 0.032, 30)
    # control panel on the left ear: power and status LEDs; the accent device carries the rack's identity
    span(bm, s.LED, cx - BODY_W / 2 + 0.006, cx - BODY_W / 2 + 0.01, fy - 0.001, fy, z1 - 0.012, z1 - 0.008)
    if d.kind not in ("blank_1u", "patch_1u", "manager_1u"):
        span(bm, s.ACCENT_LED if accent and d.accent else s.LED, cx - BODY_W / 2 + 0.014, cx - BODY_W / 2 + 0.018, fy - 0.001, fy, z1 - 0.012, z1 - 0.008)
    if accent and d.accent:  # identity stripe across the named server's bezel
        span(bm, s.SIGNAL, cx - inner / 2, cx + inner / 2, fy - PROUD - 0.001, fy - PROUD, z1 - 0.004, z1 - 0.0015)
        span(bm, s.ACCENT_LED, cx + BODY_W / 2 - 0.02, cx + BODY_W / 2 - 0.006, fy - 0.0015, fy, z0 + 0.006, z1 - 0.006)


def rack_interior(bm: bmesh.types.BMesh, spec: hw.RackSpec, ox: float = 0.0, oy: float = 0.0, oz: float = 0.0) -> None:
    """Rails, rail holes, every device of every column and the vertical cable managers (offset by ``ox, oy, oz``)."""
    fy = oy + spec.face_y
    top = spec.base_z + spec.units * U
    depth = min(0.6, spec.depth / 2 - spec.face_y - 0.03)
    for cx_local, column in zip(spec.columns, spec.fill, strict=True):
        cx = ox + cx_local
        for side in (-1, 1):
            rx = cx + side * (hw.DEVICE_WIDTH_M / 2 + 0.009)
            span(bm, s.STEEL_LIGHT, rx - 0.009, rx + 0.009, fy + 0.003, fy + 0.03, oz + spec.base_z, oz + top)
            for u in range(spec.units):
                zc = oz + spec.base_z + (u + 0.5) * U
                span(bm, s.VENT, rx - 0.0035, rx + 0.0035, fy + 0.0025, fy + 0.003, zc - 0.0035, zc + 0.0035)
        for d in column:
            device(bm, d, cx, fy, oz + spec.base_z + d.u * U, depth, True)
    if len(spec.columns) > 1:  # central and side vertical cable managers with fingers
        for x in (ox, ox - spec.width / 2 + 0.075, ox + spec.width / 2 - 0.075):
            span(bm, s.BEZEL, x - 0.035, x + 0.035, fy + 0.0, fy + 0.08, oz + spec.base_z, oz + top)
            for i in range(int((top - spec.base_z) / 0.09)):
                z = oz + spec.base_z + 0.045 + i * 0.09
                span(bm, s.BEZEL, x - 0.03, x + 0.03, fy - 0.035, fy, z - 0.006, z + 0.006)


def cabinet(bm: bmesh.types.BMesh, w: float, d: float, h: float, front: str, ox: float = 0.0, oy: float = 0.0, oz: float = 0.0, signal_frame: bool = True) -> None:
    """A rack cabinet shell: plinth with levelling feet, corner posts, side and top panels, perforated rear door, front frame.

    ``front`` is "open" (the door is another object) or "door" (a closed perforated front door with a handle)."""
    x0, x1, y0, y1 = ox - w / 2, ox + w / 2, oy - d / 2, oy + d / 2
    for fx in (x0 + 0.03, x1 - 0.07):
        for fy_ in (y0 + 0.03, y1 - 0.07):
            span(bm, s.STEEL_LIGHT, fx, fx + 0.04, fy_, fy_ + 0.04, oz, oz + 0.025)
    span(bm, s.STEEL, x0 + 0.01, x1 - 0.01, y0 + 0.01, y1 - 0.01, oz + 0.025, oz + 0.1)
    span(bm, s.VENT, x0 + 0.03, x1 - 0.03, y0 + 0.009, y0 + 0.012, oz + 0.04, oz + 0.085)
    for px in (x0, x1 - 0.035):
        for py in (y0, y1 - 0.035):
            span(bm, s.STEEL, px, px + 0.035, py, py + 0.035, oz + 0.1, oz + h - 0.03)
    for px in (x0, x1 - 0.012):  # side panels
        span(bm, s.STEEL, px, px + 0.012, y0 + 0.035, y1 - 0.035, oz + 0.1, oz + h - 0.03)
    span(bm, s.STEEL, x0, x1, y0, y1, oz + h - 0.03, oz + h)
    span(bm, s.PERFORATED, x0 + 0.035, x1 - 0.035, y1 - 0.012, y1 - 0.004, oz + 0.12, oz + h - 0.05)  # rear door
    frame = s.SIGNAL if signal_frame else s.STEEL
    span(bm, frame, x0, x1, y0, y0 + 0.03, oz + h - 0.1, oz + h - 0.03)
    span(bm, frame, x0, x1, y0, y0 + 0.03, oz + 0.1, oz + 0.14)
    for px in (x0, x1 - 0.04):
        span(bm, frame, px, px + 0.04, y0, y0 + 0.03, oz + 0.14, oz + h - 0.1)
    if front == "door":
        span(bm, s.STEEL, x0 + 0.045, x1 - 0.045, y0 + 0.004, y0 + 0.02, oz + 0.15, oz + 0.18)
        span(bm, s.STEEL, x0 + 0.045, x1 - 0.045, y0 + 0.004, y0 + 0.02, oz + h - 0.14, oz + h - 0.11)
        span(bm, s.PERFORATED, x0 + 0.045, x1 - 0.045, y0 + 0.008, y0 + 0.014, oz + 0.18, oz + h - 0.14)
        span(bm, s.STEEL_LIGHT, x1 - 0.09, x1 - 0.07, y0 + 0.0, y0 + 0.004, oz + h * 0.45, oz + h * 0.6)  # handle
        span(bm, s.BEZEL, x1 - 0.092, x1 - 0.068, y0 + 0.001, y0 + 0.004, oz + h * 0.52, oz + h * 0.54)  # lock


def rack(bm: bmesh.types.BMesh, spec: hw.RackSpec, front: str, ox: float = 0.0, oy: float = 0.0, oz: float = 0.0, signal_frame: bool = True) -> None:
    cabinet(bm, spec.width, spec.depth, spec.height, front, ox, oy, oz, signal_frame)
    rack_interior(bm, spec, ox, oy, oz)


# --- the root: a locked cage with one offline machine -----------------------------------------------------------------


def _mesh_panel(bm: bmesh.types.BMesh, axis: str, fixed: float, a0: float, a1: float, b0: float, b1: float) -> None:
    """Welded wire mesh in a plane: ``axis`` is the plane normal ("x", "y" or "z"); a and b are the in-plane ranges."""
    t, pitch = hw.CAGE_BAR_M, hw.CAGE_BAR_PITCH_M
    n_flat = (fixed - t / 2, fixed + t / 2)

    def bar(ra: tuple[float, float], rb: tuple[float, float]) -> None:
        """A bar spanning ``ra`` along the plane's first axis and ``rb`` along its second."""
        if axis == "y":
            p.box_span(bm, *ra, *n_flat, *rb)
        elif axis == "x":
            p.box_span(bm, *n_flat, *ra, *rb)
        else:
            p.box_span(bm, *ra, *rb, *n_flat)

    with p.slot(bm, s.STEEL_LIGHT):
        n_a, n_b = int((a1 - a0) / pitch), int((b1 - b0) / pitch)
        for i in range(1, n_b):
            c = b0 + (b1 - b0) * i / n_b
            bar((a0, a1), (c - t / 2, c + t / 2))
        for i in range(1, n_a):
            c = a0 + (a1 - a0) * i / n_a
            bar((c - t / 2, c + t / 2), (b0, b1))


def root_cage(bm: bmesh.types.BMesh, size: tuple[float, float, float]) -> None:
    """The Root CA: a locked cage (gold frame, steel mesh, padlocked door) holding one offline, air-gapped machine on a stand.
    Nothing is connected to it: no port in use, no cable (AR-01; ``tests/test_v5.py``, in Blender ``root_no_cables``)."""
    sx, sy, sz = size
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    post = hw.CAGE_POST_M
    inset = post / 2
    span(bm, s.STEEL, -hx, hx, -hy, hy, -hz, -hz + 0.06)  # floor plate
    for x in (-hx, hx - post):
        for y in (-hy, hy - post):
            span(bm, s.SIGNAL, x, x + post, y, y + post, -hz, hz)
    for z0 in (-hz + 0.06, hz - 0.06, hw.CAGE_MID_RAIL_Z):  # bottom, top and mid rails on all four sides
        span(bm, s.SIGNAL, -hx, hx, -hy, -hy + post, z0, z0 + 0.06)
        span(bm, s.SIGNAL, -hx, hx, hy - post, hy, z0, z0 + 0.06)
        span(bm, s.SIGNAL, -hx, -hx + post, -hy, hy, z0, z0 + 0.06)
        span(bm, s.SIGNAL, hx - post, hx, -hy, hy, z0, z0 + 0.06)
    span(bm, s.SIGNAL, -hx, hx, -hy, hy, hz - 0.012, hz)  # top frame plate edge
    door = hw.CAGE_DOOR_WIDTH_M / 2
    _mesh_panel(bm, "y", -hy + inset, -hx + post, -door, -hz + 0.06, hz - 0.06)
    _mesh_panel(bm, "y", -hy + inset, door, hx - post, -hz + 0.06, hz - 0.06)
    _mesh_panel(bm, "y", -hy + inset + 0.02, -door + 0.04, door - 0.04, -hz + 0.1, hz - 0.1)  # the door's own mesh
    _mesh_panel(bm, "y", hy - inset, -hx + post, hx - post, -hz + 0.06, hz - 0.06)
    _mesh_panel(bm, "x", -hx + inset, -hy + post, hy - post, -hz + 0.06, hz - 0.06)
    _mesh_panel(bm, "x", hx - inset, -hy + post, hy - post, -hz + 0.06, hz - 0.06)
    _mesh_panel(bm, "z", hz - 0.03, -hx + post, hx - post, -hy + post, hy - post)
    for x in (-door, door - 0.04):  # door frame and hinges
        span(bm, s.SIGNAL, x, x + 0.04, -hy + 0.005, -hy + 0.045, -hz + 0.08, hz - 0.08)
    for z in (-hz + 0.08, hz - 0.12):
        span(bm, s.SIGNAL, -door, door, -hy + 0.005, -hy + 0.045, z, z + 0.04)
    for z in (-hz + 0.3, 0.0, hz - 0.35):
        span(bm, s.STEEL_LIGHT, -door - 0.03, -door + 0.01, -hy, -hy + 0.04, z, z + 0.08)
    span(bm, s.STEEL_LIGHT, door - 0.01, door + 0.06, -hy, -hy + 0.02, -0.16, -0.1)  # hasp
    span(bm, s.SIGNAL, door + 0.005, door + 0.065, -hy, -hy + 0.03, -0.26, -0.18)  # padlock body (brass)
    span(bm, s.STEEL_LIGHT, door + 0.015, door + 0.022, -hy + 0.005, -hy + 0.025, -0.18, -0.12)
    span(bm, s.STEEL_LIGHT, door + 0.048, door + 0.055, -hy + 0.005, -hy + 0.025, -0.18, -0.12)
    span(bm, s.STEEL_LIGHT, door + 0.015, door + 0.055, -hy + 0.005, -hy + 0.025, -0.125, -0.115)
    # the stand and the offline machine (a tower), beside the door so the seal never hides it, its upper half above the mid rail
    st_w, st_d, st_h = hw.ROOT_STAND_SIZE
    base = -hz + 0.06
    cx, cy = hw.ROOT_MACHINE_X, 0.15
    span(bm, s.STEEL, cx - st_w / 2, cx + st_w / 2, cy - st_d / 2, cy + st_d / 2, base + st_h - 0.04, base + st_h)
    for x in (cx - st_w / 2 + 0.02, cx + st_w / 2 - 0.06):
        for y in (cy - st_d / 2 + 0.02, cy + st_d / 2 - 0.06):
            span(bm, s.STEEL_LIGHT, x, x + 0.04, y, y + 0.04, base, base + st_h - 0.04)
    mw, md, mh = hw.ROOT_MACHINE_SIZE
    z0 = base + st_h
    span(bm, s.STEEL_LIGHT, cx - mw / 2, cx + mw / 2, cy - md / 2, cy + md / 2, z0 + 0.02, z0 + mh)
    for x in (cx - mw / 2 + 0.03, cx + mw / 2 - 0.07):  # feet
        span(bm, s.BEZEL, x, x + 0.04, cy - md / 2 + 0.03, cy - md / 2 + 0.09, z0, z0 + 0.02)
        span(bm, s.BEZEL, x, x + 0.04, cy + md / 2 - 0.09, cy + md / 2 - 0.03, z0, z0 + 0.02)
    fy = cy - md / 2
    span(bm, s.BEZEL, cx - mw / 2, cx + mw / 2, fy - 0.012, fy, z0 + 0.02, z0 + mh)
    span(bm, s.GLASS, cx - mw / 2 + 0.04, cx + mw / 2 - 0.1, fy - 0.014, fy - 0.012, z0 + 0.12, z0 + mh - 0.08)
    span(bm, s.ACCENT_LED, cx + mw / 2 - 0.085, cx + mw / 2 - 0.05, fy - 0.015, fy - 0.012, z0 + 0.06, z0 + mh - 0.04)  # gold identity light bar
    span(bm, s.LED, cx + mw / 2 - 0.04, cx + mw / 2 - 0.025, fy - 0.015, fy - 0.012, z0 + mh - 0.06, z0 + mh - 0.045)  # power
    _vents(bm, cx - mw / 2 + 0.04, cx + mw / 2 - 0.1, fy - 0.012, z0 + 0.05, z0 + 0.09, 16)
    span(bm, s.LED, -hx + post, hx - post, -hy + post + 0.02, -hy + post + 0.05, hz - 0.075, hz - 0.065)  # inspection light under the roof


# --- the HSM key module ------------------------------------------------------------------------------------------------


def hsm(bm: bmesh.types.BMesh, size: tuple[float, float, float]) -> None:
    """An HSM-style sealed key module: steel body, bezel, a status display and tamper-evident bands that carry the glow
    channel, a keypad, a smart-card slot and identity LEDs. Front toward -Y, centred."""
    sx, sy, sz = size
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    span(bm, s.STEEL, -hx + 0.02, hx - 0.02, -hy + 0.02, hy - 0.02, -hz + 0.02, hz - 0.02)
    for z in (hz * 0.44, -hz * 0.44):  # tamper bands round the body
        span(bm, s.SIGNAL, -hx, hx, -hy, hy, z - 0.03, z + 0.03)
    span(bm, s.STEEL_LIGHT, -hx + 0.01, hx - 0.01, -hy + 0.01, hy - 0.01, hz - 0.02, hz)  # lid
    span(bm, s.STEEL_LIGHT, -hx + 0.01, hx - 0.01, -hy + 0.01, hy - 0.01, -hz, -hz + 0.02)
    fy = -hy + 0.01
    span(bm, s.BEZEL, -hx + 0.04, hx - 0.04, fy - 0.008, fy + 0.002, -hz + 0.05, hz * 0.44 - 0.04)
    span(bm, s.SIGNAL, -hx + 0.08, 0.06, fy - 0.011, fy - 0.008, -0.03, 0.08)  # status display
    for r in range(4):
        for c in range(3):
            x = 0.12 + c * 0.05
            z = 0.06 - r * 0.045
            span(bm, s.CADDY, x, x + 0.035, fy - 0.014, fy - 0.008, z - 0.03, z)
    span(bm, s.VENT, -hx + 0.08, 0.06, fy - 0.009, fy - 0.008, -0.2, -0.185)  # smart-card slot
    for i in range(3):
        span(bm, s.ACCENT_LED, -hx + 0.08 + i * 0.035, -hx + 0.1 + i * 0.035, fy - 0.011, fy - 0.008, 0.11, 0.125)
    for side in (-1, 1):
        for i in range(8):
            z = -hz * 0.3 + i * 0.03
            x = side * (hx - 0.02)
            span(bm, s.VENT, x - 0.001, x + 0.001, -hy * 0.6, hy * 0.6, z, z + 0.012)


# --- client: laptop, desk, chair, the RDP client on screen -----------------------------------------------------------


def laptop(bm: bmesh.types.BMesh, size: tuple[float, float, float]) -> None:
    """A thin modern laptop with no logo. Width along Y, depth along X; the user sits on +X. The key tops stay at or below
    ``cff.stage.character.KEYBOARD_TOP_Z`` so the hand clearance the V4 check measures is unchanged."""
    width, depth, _ = size
    hx, hy = depth / 2, width / 2
    top = 0.0205
    with p.slot(bm, s.ALUMINIUM):
        p.box_span(bm, -hx, hx, -hy, hy, 0.003, top)
    span(bm, s.BEZEL, -hx + 0.02, hx - 0.02, -hy + 0.02, hy - 0.02, 0.0, 0.003)  # rubber foot strip
    span(bm, s.BEZEL, -0.112, 0.032, -0.152, 0.152, top - 0.0005, top + 0.0003)  # keyboard well
    rows = (-0.077, -0.058, -0.039, -0.02, -0.001, 0.018)
    for r, x in enumerate(rows):
        h = 0.009 if r == 0 else 0.0165
        n = 15 if r else 16
        pitch = 0.296 / n
        for c in range(n):
            y0 = -0.148 + c * pitch
            if r == 5 and 5 <= c <= 9:  # the space bar spans five keys
                if c == 5:
                    span(bm, s.BEZEL, x - h / 2, x + h / 2, y0 + 0.001, y0 + 5 * pitch - 0.001, top, 0.0245)
                continue
            span(bm, s.BEZEL, x - h / 2, x + h / 2, y0 + 0.001, y0 + pitch - 0.001, top, 0.0245)
    span(bm, s.GLASS, 0.045, 0.14, -0.065, 0.065, top - 0.0002, top + 0.0004)  # trackpad
    span(bm, s.VENT, -hx + 0.004, -hx + 0.03, -hy + 0.06, hy - 0.06, top - 0.0004, top + 0.0002)  # hinge grille
    # the lid, rotated about the hinge; its inner bezel faces the user
    hxz, hz = lo.LAPTOP_HINGE_XZ
    tilt = math.radians(lo.LAPTOP_LID_TILT_DEG)
    pivot = Matrix.Translation(Vector((hxz, 0.0, hz))) @ Matrix.Rotation(-tilt, 4, "Y")
    t, length = lo.LAPTOP_LID_THICKNESS, lo.LAPTOP_LID_LENGTH

    def lid_box(slot_index: int, n0: float, n1: float, y0: float, y1: float, a0: float, a1: float) -> None:
        with p.slot(bm, slot_index):
            centre = pivot @ Vector(((n0 + n1) / 2, (y0 + y1) / 2, (a0 + a1) / 2))
            m = Matrix.Translation(centre) @ Matrix.Rotation(-tilt, 4, "Y") @ Matrix.Diagonal((n1 - n0, y1 - y0, a1 - a0, 1.0))
            p.cube(bm, m)

    face = 0.003  # the lid's inner face; the idle screen (layout.LAPTOP_LID_X_OFFSET) lies on it
    lid_box(s.ALUMINIUM, face - t, face, -hy, hy, 0.0, length)
    lid_box(s.BEZEL, face, face + 0.0006, -hy + 0.004, hy - 0.004, 0.004, length - 0.003)
    lid_box(s.VENT, face + 0.0006, face + 0.001, -0.004, 0.004, length - 0.0075, length - 0.0035)  # webcam
    lid_box(s.ALUMINIUM, -0.004, 0.004, -0.17, 0.17, -0.004, 0.006)  # hinge barrel


def screen_ui(bm: bmesh.types.BMesh, size: tuple[float, float, float]) -> None:
    """The laptop's idle screen: the local desktop with the RDP client's connection dialog open (no text, no logo).
    Every part glows with the screen's glow channel, each in its own tint."""
    sx, sy, sz = size
    hx, hz = sx / 2, sz / 2
    with p.slot(bm, s.SIGNAL):
        p.box(bm, sx, sy, sz)
    f = -sy / 2

    def layer(slot_index: int, depth: float, x0: float, x1: float, z0: float, z1: float) -> None:
        span(bm, slot_index, x0, x1, f - depth - 0.0004, f - depth, z0, z1)

    layer(s.UI_DESKTOP, 0.0002, -hx + 0.004, hx - 0.004, -hz + 0.02, hz - 0.004)  # local desktop
    layer(s.UI_TASKBAR, 0.0002, -hx + 0.004, hx - 0.004, -hz + 0.004, -hz + 0.02)  # taskbar
    for i in range(5):
        layer(s.UI_ICON, 0.0006, -hx + 0.03 + i * 0.022, -hx + 0.044 + i * 0.022, -hz + 0.007, -hz + 0.017)
    for i in range(4):  # desktop icons
        layer(s.UI_ICON, 0.0006, -hx + 0.012, -hx + 0.03, hz - 0.03 - i * 0.034, hz - 0.012 - i * 0.034)
    # the connection dialog
    layer(s.UI_ICON, 0.0006, -0.11, 0.11, -0.07, 0.07)
    layer(s.UI_TITLE, 0.001, -0.11, 0.11, 0.05, 0.07)
    layer(s.UI_TASKBAR, 0.001, -0.095, 0.095, 0.012, 0.03)  # computer-name field
    layer(s.UI_TASKBAR, 0.001, -0.095, 0.02, -0.02, -0.006)  # user field
    layer(s.UI_TITLE, 0.001, 0.03, 0.095, -0.06, -0.035)  # Connect button
    layer(s.UI_TASKBAR, 0.001, -0.095, -0.03, -0.06, -0.035)  # Options button


def desk(bm: bmesh.types.BMesh, size: tuple[float, float, float]) -> None:
    sx, sy, sz = size
    span(bm, s.DESK, -sx / 2, sx / 2, -sy / 2, sy / 2, sz - 0.028, sz)
    span(bm, s.BEZEL, -sx / 2 - 0.002, sx / 2 + 0.002, -sy / 2 - 0.002, sy / 2 + 0.002, sz - 0.03, sz - 0.026)  # edge band
    for x in (-sx / 2 + 0.06, sx / 2 - 0.1):  # C-frame legs: post, foot, top bearer
        span(bm, s.STEEL_LIGHT, x, x + 0.04, -0.03, 0.03, 0.03, sz - 0.03)
        span(bm, s.STEEL_LIGHT, x - 0.01, x + 0.05, -sy / 2 + 0.05, sy / 2 - 0.05, 0.0, 0.03)
        span(bm, s.STEEL_LIGHT, x - 0.01, x + 0.05, -sy / 2 + 0.05, sy / 2 - 0.05, sz - 0.06, sz - 0.03)
        for y in (-sy / 2 + 0.05, sy / 2 - 0.08):
            span(bm, s.BEZEL, x - 0.005, x + 0.045, y, y + 0.03, -0.0, 0.006)
    span(bm, s.STEEL, -sx / 2 + 0.1, sx / 2 - 0.1, -0.01, 0.01, sz * 0.45, sz - 0.06)  # modesty panel


def office_chair(bm: bmesh.types.BMesh) -> None:
    """An office chair (local +X faces the desk); the seat top stays at 0.475 m, where the V4 character sits."""
    with p.slot(bm, s.FABRIC):
        p.box(bm, 0.5, 0.46, 0.06, (-0.12, 0.0, 0.445))
        p.box(bm, 0.06, 0.44, 0.5, (-0.38, 0.0, 0.77))
    span(bm, s.BEZEL, -0.36, -0.33, -0.05, 0.05, 0.47, 0.6)  # back support
    span(bm, s.BEZEL, -0.3, 0.06, -0.12, 0.12, 0.39, 0.415)  # seat pan
    with p.slot(bm, s.STEEL_LIGHT):
        p.cylinder(bm, 0.025, 0.3, 12, (-0.12, 0.0, 0.24))  # gas lift
    with p.slot(bm, s.BEZEL):
        for i in range(5):
            a = 2 * math.pi * i / 5
            m = Matrix.Translation(Vector((-0.12 + 0.16 * math.cos(a), 0.16 * math.sin(a), 0.07))) @ Matrix.Rotation(a, 4, "Z")
            p.cube(bm, m @ Matrix.Diagonal((0.32, 0.045, 0.035, 1.0)))
            p.cylinder(bm, 0.025, 0.03, 10, (-0.12 + 0.3 * math.cos(a), 0.3 * math.sin(a), 0.025), "Y")
    # no armrests: the seated character's forearms reach forward to the keyboard over the seat edge
