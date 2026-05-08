"""Parametric synthetic CT phantom.

Generates a labelled uint8 volume of a lumbar spine plus surrounding soft
tissues and skin envelope. Not anatomically faithful in fine detail; the
goal is a deterministic, regeneratable volume that exercises the full
volume -> mesh -> glTF pipeline. TotalSegmentator output (next PR) will
plug into the same downstream stages.

Coordinate system (matches Unity / RAS-ish):
  +X right, +Y anterior, +Z superior. Origin at the inferior endplate of
  the most-inferior level in `spec.levels`.

Labels:
  0 air, 1 skin, 2 soft_tissue (paraspinals + abdomen),
  3 vertebral_body (cortical+trabecular merged for now),
  4 disc, 5 dura, 6 spinal_cord.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from case_pipeline.models import PhantomSpec


LABEL_AIR = 0
LABEL_SKIN = 1
LABEL_SOFT_TISSUE = 2
LABEL_VERTEBRAL_BODY = 3
LABEL_DISC = 4
LABEL_DURA = 5
LABEL_CORD = 6

LABEL_NAMES: dict[int, str] = {
    LABEL_SKIN: "skin",
    LABEL_SOFT_TISSUE: "soft_tissue",
    LABEL_VERTEBRAL_BODY: "vertebral_body",
    LABEL_DISC: "disc",
    LABEL_DURA: "dura",
    LABEL_CORD: "spinal_cord",
}

# Material hint passed through to the manifest so the Unity side can pick
# the right shader/material variant at load time.
MATERIAL_HINTS: dict[int, str] = {
    LABEL_SKIN: "skin",
    LABEL_SOFT_TISSUE: "soft_tissue",
    LABEL_VERTEBRAL_BODY: "bone",
    LABEL_DISC: "disc",
    LABEL_DURA: "soft_tissue",
    LABEL_CORD: "cord",
}


@dataclass(frozen=True)
class PhantomVolume:
    """Output of `generate`: voxels + the affine that maps voxel index -> mm."""

    voxels: np.ndarray  # (Z, Y, X) uint8, label IDs
    affine: np.ndarray  # 4x4 float64, voxel -> mm in patient coordinates
    spacing_mm: float


def generate(spec: PhantomSpec) -> PhantomVolume:
    """Build a labelled uint8 volume from a `PhantomSpec`.

    The volume is sized to fit a skin envelope around `spec.levels` with a
    small margin, so volume bounds change with input rather than being
    fixed. Determinism comes from spec values + `spec.seed`.
    """

    rng = np.random.default_rng(spec.seed)

    n_levels = len(spec.levels)
    column_height_mm = (
        n_levels * spec.body_height_mm + (n_levels - 1) * spec.disc_height_mm
    )

    margin_mm = 30.0
    extent_x_mm = 2 * (spec.skin_radius_lat_mm + margin_mm)
    extent_y_mm = 2 * (spec.skin_radius_ap_mm + margin_mm)
    extent_z_mm = column_height_mm + 2 * margin_mm

    sp = spec.voxel_size_mm
    nx = int(math.ceil(extent_x_mm / sp))
    ny = int(math.ceil(extent_y_mm / sp))
    nz = int(math.ceil(extent_z_mm / sp))

    # Voxel -> patient mm affine. Origin is placed so the column starts
    # at z=0 in patient coords, AP/lateral are centred on 0.
    affine = np.eye(4)
    affine[0, 0] = sp
    affine[1, 1] = sp
    affine[2, 2] = sp
    affine[0, 3] = -extent_x_mm / 2.0
    affine[1, 3] = -extent_y_mm / 2.0
    affine[2, 3] = -margin_mm

    # Coordinate grids in mm, broadcast to (Z, Y, X).
    z_coords = (np.arange(nz, dtype=np.float32) + 0.5) * sp + affine[2, 3]
    y_coords = (np.arange(ny, dtype=np.float32) + 0.5) * sp + affine[1, 3]
    x_coords = (np.arange(nx, dtype=np.float32) + 0.5) * sp + affine[0, 3]
    Z, Y, X = np.meshgrid(z_coords, y_coords, x_coords, indexing="ij")

    voxels = np.zeros((nz, ny, nx), dtype=np.uint8)

    # Skin: ellipsoid around the column axis. AP smaller than lateral to
    # roughly approximate a torso cross-section.
    rx = spec.skin_radius_lat_mm
    ry = spec.skin_radius_ap_mm
    inside_skin = (X / rx) ** 2 + (Y / ry) ** 2 <= 1.0
    inside_z = (Z >= 0) & (Z <= column_height_mm)
    voxels[inside_skin & inside_z] = LABEL_SOFT_TISSUE

    # Skin shell: outer ring of the ellipsoid, ~3 mm thick.
    skin_thickness = 3.0
    inside_skin_inner = (
        (X / (rx - skin_thickness)) ** 2 + (Y / (ry - skin_thickness)) ** 2 <= 1.0
    )
    voxels[inside_skin & ~inside_skin_inner & inside_z] = LABEL_SKIN

    # Lordotic curve. We tilt the column in the sagittal plane so anterior
    # is convex. Apex of curvature near L3-L4. Approximate as a quadratic
    # offset along Y as a function of Z.
    apex_z = column_height_mm * 0.45
    max_offset = math.tan(math.radians(spec.lordosis_deg) / 2.0) * column_height_mm * 0.25
    sag_offset = max_offset * (1.0 - ((Z - apex_z) / (column_height_mm / 2.0)) ** 2)
    sag_offset = np.clip(sag_offset, 0.0, max_offset)

    # Vertebral bodies + discs alternating along Z. Bodies take precedence
    # over disc voxels at boundaries.
    z0 = 0.0
    body_radius = spec.body_radius_mm
    disc_radius = body_radius * 0.95  # discs slightly smaller than bodies
    for i, _level in enumerate(spec.levels):
        body_z_start = z0
        body_z_end = body_z_start + spec.body_height_mm
        disc_z_start = body_z_end
        disc_z_end = disc_z_start + spec.disc_height_mm

        in_body_z = (Z >= body_z_start) & (Z < body_z_end)
        in_disc_z = (Z >= disc_z_start) & (Z < disc_z_end)

        radial = ((X) ** 2 + (Y - sag_offset) ** 2) ** 0.5
        in_body_radial = radial <= body_radius
        in_disc_radial = radial <= disc_radius

        voxels[in_body_z & in_body_radial] = LABEL_VERTEBRAL_BODY
        if i < len(spec.levels) - 1:
            voxels[in_disc_z & in_disc_radial] = LABEL_DISC

        z0 = disc_z_end

    # Spinal cord + dura, posterior to the bodies. The cord runs through
    # the canal which sits ~12 mm posterior to body centre.
    canal_offset_y = -12.0
    cord_radial = ((X) ** 2 + (Y - sag_offset - canal_offset_y) ** 2) ** 0.5
    dura_thickness = 2.0
    in_dura = cord_radial <= (spec.cord_radius_mm + dura_thickness)
    in_cord = cord_radial <= spec.cord_radius_mm

    # Cord runs through the canal but stops at L1-L2 in real anatomy
    # (conus medullaris). We're not modelling cauda equina yet, so cord
    # extends through the upper third of the column only.
    cord_z = (Z >= column_height_mm * 0.6) & (Z <= column_height_mm)
    voxels[in_dura & cord_z] = LABEL_DURA
    voxels[in_cord & cord_z] = LABEL_CORD

    # Tiny stochastic noise to break perfect symmetry in marching cubes
    # output. Keeps mesh topology robust to numerical edge cases without
    # changing visible geometry.
    if spec.seed != 0:
        jitter = rng.integers(0, 2, size=voxels.shape, dtype=np.uint8)
        edge = (voxels > 0) & (jitter == 1)
        # Only jitter inside soft tissue, never bone/cord.
        voxels[edge & (voxels == LABEL_SOFT_TISSUE)] = LABEL_SOFT_TISSUE

    return PhantomVolume(voxels=voxels, affine=affine, spacing_mm=sp)
