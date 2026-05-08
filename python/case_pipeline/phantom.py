"""Parametric synthetic CT phantom.

Generates a labelled uint8 volume of a lumbar spine plus surrounding soft
tissues and skin envelope. Not anatomically faithful in fine detail; the
goal is a deterministic, regeneratable volume that exercises the full
volume -> mesh -> glTF pipeline. TotalSegmentator output (next PR) will
plug into the same downstream stages.

Coordinate system (matches Unity / RAS-ish):
  +X right, +Y anterior, +Z superior. Origin at the inferior endplate of
  the most-inferior level in `spec.levels`. The volume is built so the
  inferior level (e.g. S1) sits near z=0 and the superior level (e.g. L1)
  sits near z=column_height_mm.

Pathologies (degenerative disc, spondylolisthesis, scoliosis) are layered
in `_apply_pathology_offsets` before the level placement loop, so the
loop itself stays simple.

Labels:
  0 air, 1 skin, 2 soft_tissue (paraspinals + abdomen),
  3 vertebral_body (cortical+trabecular merged for now),
  4 disc, 5 dura, 6 spinal_cord.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from case_pipeline.models import (
    LUMBAR_LEVELS,
    Pathology,
    PhantomSpec,
    _disc_pair_keys,
)


# Label IDs. Per-level vertebrae get IDs 10..15 so each can be meshed
# independently and the surgeon can select an individual vertebra in
# Unity for screw planning. Soft-tissue labels keep low IDs so the bone
# block has room to grow (thoracic/cervical levels would extend upward).
LABEL_AIR = 0
LABEL_SKIN = 1
LABEL_SOFT_TISSUE = 2
LABEL_DISC = 4
LABEL_DURA = 5
LABEL_CORD = 6

VERTEBRA_LABEL_BASE = 10


def vertebra_label(level: str) -> int:
    """Map a level name (e.g. 'L4', 'S1') to its uint8 label ID.

    The ordering follows `LUMBAR_LEVELS` so labels stay contiguous and
    deterministic across runs.
    """
    if level not in LUMBAR_LEVELS:
        raise ValueError(
            f"unknown level {level!r}; expected one of {LUMBAR_LEVELS}"
        )
    return VERTEBRA_LABEL_BASE + LUMBAR_LEVELS.index(level)


def vertebra_structure_name(level: str) -> str:
    """Per-level mesh name. The Unity loader treats each as its own
    GameObject so the surgeon can highlight/select individual vertebrae."""
    return f"vertebra_{level}"


LABEL_NAMES: dict[int, str] = {
    LABEL_SKIN: "skin",
    LABEL_SOFT_TISSUE: "soft_tissue",
    LABEL_DISC: "disc",
    LABEL_DURA: "dura",
    LABEL_CORD: "spinal_cord",
}
for _lvl in LUMBAR_LEVELS:
    LABEL_NAMES[vertebra_label(_lvl)] = vertebra_structure_name(_lvl)

# Material hint passed through to the manifest so the Unity side can pick
# the right shader/material variant at load time. All vertebrae share
# the same `bone` hint so Unity can apply one bone material; the per-level
# split is only about selectability, not appearance.
MATERIAL_HINTS: dict[int, str] = {
    LABEL_SKIN: "skin",
    LABEL_SOFT_TISSUE: "soft_tissue",
    LABEL_DISC: "disc",
    LABEL_DURA: "soft_tissue",
    LABEL_CORD: "cord",
}
for _lvl in LUMBAR_LEVELS:
    MATERIAL_HINTS[vertebra_label(_lvl)] = "bone"

# Set of all bone label IDs for code paths that need "any vertebra".
# (e.g. cortical-shell logic in ct_synthesis, bone-vs-disc precedence.)
VERTEBRA_LABELS: frozenset[int] = frozenset(
    vertebra_label(lvl) for lvl in LUMBAR_LEVELS
)

# Floor on degenerated disc height — full collapse would zero out a label
# segment and confuse marching cubes. 1 mm keeps the disc renderable and
# is below clinical "severe" thresholds anyway.
_DEGEN_DISC_FLOOR_MM = 1.0
# Severity 1.0 reduces disc height by this fraction. Picked so severity
# 0.5 ~= moderate degeneration, 1.0 ~= advanced, neither is fully zero.
_DEGEN_DISC_MAX_REDUCTION = 0.85


@dataclass(frozen=True)
class PhantomVolume:
    """Output of `generate`: voxels + the affine that maps voxel index -> mm."""

    voxels: np.ndarray  # (Z, Y, X) uint8, label IDs
    affine: np.ndarray  # 4x4 float64, voxel -> mm in patient coordinates
    spacing_mm: float


@dataclass(frozen=True)
class _LevelPlacement:
    """Where one vertebra sits in the volume after pathology offsets."""

    level: str
    body_z_lo: float
    body_z_hi: float
    y_offset_mm: float  # anterior translation (spondylolisthesis)


@dataclass(frozen=True)
class _DiscPlacement:
    pair: str  # e.g. 'L4-L5'
    z_lo: float
    z_hi: float
    y_offset_mm: float  # tracks the upper vertebra's slip


def _resolve_offsets(
    spec: PhantomSpec,
) -> tuple[list[_LevelPlacement], list[_DiscPlacement], float]:
    """Compute Z extents and Y offsets per level/disc, accounting for
    degenerative disc collapse and spondylolisthesis.

    Levels in `spec.levels` are convention superior-to-inferior. We place
    the inferior end (e.g. S1) at z=0 and stack upward, so the loop in
    `generate` doesn't have to think about the inversion.
    """

    patho: Pathology = spec.pathology
    levels = spec.levels  # superior -> inferior in name order
    pairs = _disc_pair_keys(levels)

    # Per-level Y offset from spondylolisthesis. A slip at pair
    # (above, below) translates `above` and all levels superior to it.
    # `below` and everything inferior stays put (S1/sacrum is the anchor).
    y_offset_per_level: dict[str, float] = {lvl: 0.0 for lvl in levels}
    for pair, slip_mm in patho.spondylolisthesis.items():
        above, _below = pair.split("-")
        above_idx = levels.index(above)
        for k in range(above_idx + 1):  # 0..above_idx inclusive (more superior)
            y_offset_per_level[levels[k]] += slip_mm

    # Per-disc-pair height with degeneration applied.
    disc_height_per_pair: dict[str, float] = {}
    for pair in pairs:
        sev = patho.degenerative_disc.get(pair, 0.0)
        h = spec.disc_height_mm * (1.0 - sev * _DEGEN_DISC_MAX_REDUCTION)
        disc_height_per_pair[pair] = max(_DEGEN_DISC_FLOOR_MM, h)

    # Walk inferior -> superior placing bodies and discs.
    placements: list[_LevelPlacement] = []
    discs: list[_DiscPlacement] = []
    z = 0.0
    for i, lvl in enumerate(reversed(levels)):  # i=0 is most inferior
        body_z_lo = z
        body_z_hi = z + spec.body_height_mm
        placements.append(
            _LevelPlacement(
                level=lvl,
                body_z_lo=body_z_lo,
                body_z_hi=body_z_hi,
                y_offset_mm=y_offset_per_level[lvl],
            )
        )
        z = body_z_hi
        # The disc above this body connects this level to the next one up.
        # Skip after the last (most superior) body.
        if i < len(levels) - 1:
            superior_lvl = levels[len(levels) - 2 - i]
            pair = f"{superior_lvl}-{lvl}"
            h = disc_height_per_pair[pair]
            discs.append(
                _DiscPlacement(
                    pair=pair,
                    z_lo=z,
                    z_hi=z + h,
                    # Disc Y offset interpolates between the two bodies it
                    # connects so it doesn't hang in space if one slipped.
                    y_offset_mm=0.5
                    * (
                        y_offset_per_level[lvl]
                        + y_offset_per_level[superior_lvl]
                    ),
                )
            )
            z += h

    return placements, discs, z  # z at this point == column height


def _scoliosis_apex_z(
    placements: list[_LevelPlacement],
    apex_level: str | None,
) -> float | None:
    if apex_level is None:
        return None
    for p in placements:
        if p.level == apex_level:
            return 0.5 * (p.body_z_lo + p.body_z_hi)
    return None


def generate(spec: PhantomSpec) -> PhantomVolume:
    """Build a labelled uint8 volume from a `PhantomSpec`.

    Determinism: spec values + `spec.seed` fully determine the output. Two
    runs with the same spec produce byte-identical volumes (and therefore
    byte-identical glTF after the deterministic mesh stages).
    """

    rng = np.random.default_rng(spec.seed)
    patho = spec.pathology

    placements, discs, column_height_mm = _resolve_offsets(spec)
    apex_z = _scoliosis_apex_z(placements, patho.scoliosis_apex_level)

    margin_mm = 30.0
    extent_x_mm = 2 * (spec.skin_radius_lat_mm + margin_mm)
    extent_y_mm = 2 * (spec.skin_radius_ap_mm + margin_mm)
    extent_z_mm = column_height_mm + 2 * margin_mm

    sp = spec.voxel_size_mm
    nx = int(math.ceil(extent_x_mm / sp))
    ny = int(math.ceil(extent_y_mm / sp))
    nz = int(math.ceil(extent_z_mm / sp))

    affine = np.eye(4)
    affine[0, 0] = sp
    affine[1, 1] = sp
    affine[2, 2] = sp
    affine[0, 3] = -extent_x_mm / 2.0
    affine[1, 3] = -extent_y_mm / 2.0
    affine[2, 3] = -margin_mm

    z_coords = (np.arange(nz, dtype=np.float32) + 0.5) * sp + affine[2, 3]
    y_coords = (np.arange(ny, dtype=np.float32) + 0.5) * sp + affine[1, 3]
    x_coords = (np.arange(nx, dtype=np.float32) + 0.5) * sp + affine[0, 3]
    Z, Y, X = np.meshgrid(z_coords, y_coords, x_coords, indexing="ij")

    voxels = np.zeros((nz, ny, nx), dtype=np.uint8)

    # Skin envelope. Doesn't currently follow scoliosis — the abdomen
    # ellipsoid stays centred. Future: warp envelope with the curve.
    rx = spec.skin_radius_lat_mm
    ry = spec.skin_radius_ap_mm
    inside_skin = (X / rx) ** 2 + (Y / ry) ** 2 <= 1.0
    inside_z = (Z >= 0) & (Z <= column_height_mm)
    voxels[inside_skin & inside_z] = LABEL_SOFT_TISSUE

    skin_thickness = 3.0
    inside_skin_inner = (
        (X / (rx - skin_thickness)) ** 2 + (Y / (ry - skin_thickness)) ** 2 <= 1.0
    )
    voxels[inside_skin & ~inside_skin_inner & inside_z] = LABEL_SKIN

    # Lordosis: smooth Y offset peaking near the middle of the column.
    lordosis_apex_z = column_height_mm * 0.45
    lord_max = (
        math.tan(math.radians(spec.lordosis_deg) / 2.0) * column_height_mm * 0.25
    )
    sag_offset = lord_max * (
        1.0 - ((Z - lordosis_apex_z) / (column_height_mm / 2.0)) ** 2
    )
    sag_offset = np.clip(sag_offset, 0.0, lord_max)

    # Scoliosis: smooth X offset peaking at apex_z, sign from cobb_deg.
    if apex_z is not None and patho.scoliosis_cobb_deg != 0.0:
        scol_max = (
            math.tan(math.radians(abs(patho.scoliosis_cobb_deg)) / 2.0)
            * column_height_mm
            * 0.25
        )
        scol_sign = 1.0 if patho.scoliosis_cobb_deg > 0 else -1.0
        scoliosis_offset = (
            scol_sign
            * scol_max
            * np.maximum(
                0.0,
                1.0 - ((Z - apex_z) / (column_height_mm / 2.0)) ** 2,
            )
        )
    else:
        scoliosis_offset = np.zeros_like(Z)

    body_radius = spec.body_radius_mm
    disc_radius = body_radius * 0.95

    # Bodies — each vertebra gets its own label so it meshes as its own
    # selectable structure on the Unity side.
    for p in placements:
        in_z = (Z >= p.body_z_lo) & (Z < p.body_z_hi)
        radial = (
            (X - scoliosis_offset) ** 2
            + (Y - sag_offset - p.y_offset_mm) ** 2
        ) ** 0.5
        voxels[in_z & (radial <= body_radius)] = vertebra_label(p.level)

    # Discs (after bodies so a body never overwrites a disc, but degenerated
    # discs that sit inside body z-range are already prevented by
    # _resolve_offsets stacking them between body extents).
    for d in discs:
        in_z = (Z >= d.z_lo) & (Z < d.z_hi)
        radial = (
            (X - scoliosis_offset) ** 2
            + (Y - sag_offset - d.y_offset_mm) ** 2
        ) ** 0.5
        voxels[in_z & (radial <= disc_radius)] = LABEL_DISC

    # Cord + dura. Only emit cord through the most superior vertebra and
    # the disc immediately below it — that's roughly L1 + L1-L2 disc when
    # spec.levels starts at L1. Conus medullaris is at L1-L2 in real anatomy.
    if placements:
        top = placements[-1]  # most superior after reversed iteration
        cord_lower_z = top.body_z_lo - (
            discs[-1].z_hi - discs[-1].z_lo if discs else 0.0
        )
        cord_z = (Z >= cord_lower_z) & (Z <= column_height_mm)

        canal_offset_y = -12.0
        cord_radial = (
            (X - scoliosis_offset) ** 2
            + (Y - sag_offset - canal_offset_y) ** 2
        ) ** 0.5
        dura_thickness = 2.0
        in_dura = cord_radial <= (spec.cord_radius_mm + dura_thickness)
        in_cord = cord_radial <= spec.cord_radius_mm
        voxels[in_dura & cord_z] = LABEL_DURA
        voxels[in_cord & cord_z] = LABEL_CORD

    # Tiny stochastic noise to break perfect symmetry in marching cubes
    # output. No-op when seed=0 so the default case stays deterministic
    # at the byte level.
    if spec.seed != 0:
        jitter = rng.integers(0, 2, size=voxels.shape, dtype=np.uint8)
        edge = (voxels > 0) & (jitter == 1)
        voxels[edge & (voxels == LABEL_SOFT_TISSUE)] = LABEL_SOFT_TISSUE

    return PhantomVolume(voxels=voxels, affine=affine, spacing_mm=sp)
