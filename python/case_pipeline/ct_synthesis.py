"""Synthetic CT generation from a PhantomSpec.

Takes the same parametric inputs as the phantom volume source and produces
a HU-valued float32 volume that looks enough like a CT for TotalSegmentator
to segment. The HU values come from literature means; a small Gaussian
noise is added so the segmenter doesn't see suspiciously clean inputs
(it was trained on real CTs, not perfectly piecewise-constant inputs).

The vertebral body gets a two-tier HU profile (cortical shell + trabecular
interior) because TotalSegmentator's bone segmentation reportedly leans
on edge contrast around the cortex. A flat-HU bone label was tested
during development and segmented less cleanly.

This module produces the input to `case_pipeline.segmenters.totalseg`.
It does not run TotalSegmentator itself.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from case_pipeline.models import PhantomSpec
from case_pipeline.phantom import (
    LABEL_AIR,
    LABEL_CORD,
    LABEL_DISC,
    LABEL_DURA,
    LABEL_SKIN,
    LABEL_SOFT_TISSUE,
    LABEL_VERTEBRAL_BODY,
    PhantomVolume,
    generate as generate_phantom,
)


# Hounsfield units, literature means at 120 kVp:
#   air -1000, fat -100, muscle +40, blood +50, disc nucleus +70-90,
#   trabecular bone +300-400, cortical bone +1000-1500.
HU_AIR = -1000.0
HU_SKIN = -50.0  # skin + subcutaneous fat boundary
HU_SOFT_TISSUE = 40.0
HU_DISC = 80.0
HU_DURA = 35.0
HU_CORD = 30.0
HU_BONE_TRABECULAR = 350.0
HU_BONE_CORTICAL = 1200.0

# Cortical shell thickness (vertebral body cortex is ~1-2 mm in adults).
CORTICAL_SHELL_MM = 2.0


@dataclass(frozen=True)
class CtVolume:
    """A synthetic CT in HU. Shape and affine match a `PhantomVolume`."""

    hu: np.ndarray  # (Z, Y, X) float32, Hounsfield units
    affine: np.ndarray  # 4x4 float64, voxel -> mm
    spacing_mm: float


def synthesize_ct(
    spec: PhantomSpec,
    noise_hu: float = 12.0,
) -> CtVolume:
    """Generate a labelled phantom volume and remap labels to HU.

    `noise_hu` is the standard deviation of additive Gaussian noise. ~10
    HU is realistic for a 120 kVp clinical CT; setting it to 0 makes the
    output deterministic-clean which is helpful for debugging but is a
    poorer input for TotalSegmentator.
    """

    pv: PhantomVolume = generate_phantom(spec)
    hu = np.full(pv.voxels.shape, HU_AIR, dtype=np.float32)

    hu[pv.voxels == LABEL_SKIN] = HU_SKIN
    hu[pv.voxels == LABEL_SOFT_TISSUE] = HU_SOFT_TISSUE
    hu[pv.voxels == LABEL_DISC] = HU_DISC
    hu[pv.voxels == LABEL_DURA] = HU_DURA
    hu[pv.voxels == LABEL_CORD] = HU_CORD

    # Vertebral body: cortical shell + trabecular interior. Erode the bone
    # mask by ~CORTICAL_SHELL_MM to find the interior; the difference is
    # the shell.
    bone_mask = pv.voxels == LABEL_VERTEBRAL_BODY
    if bone_mask.any():
        from scipy.ndimage import binary_erosion

        shell_voxels = max(1, int(round(CORTICAL_SHELL_MM / pv.spacing_mm)))
        # Iterative erosion is fine here; bone meshes are small relative to
        # the volume so this is fast in practice.
        interior = binary_erosion(bone_mask, iterations=shell_voxels)
        shell = bone_mask & ~interior
        hu[interior] = HU_BONE_TRABECULAR
        hu[shell] = HU_BONE_CORTICAL

    if noise_hu > 0:
        rng = np.random.default_rng(spec.seed)
        hu += rng.normal(0.0, noise_hu, size=hu.shape).astype(np.float32)

    return CtVolume(hu=hu, affine=pv.affine.copy(), spacing_mm=pv.spacing_mm)


def write_nifti(ct: CtVolume, path: str) -> None:
    """Write a CtVolume to a NIfTI file. Used as TotalSegmentator input.

    nibabel is required only when calling this function, so installations
    that only use the phantom path don't need to install it.
    """
    import nibabel as nib

    # NIfTI conventionally orders axes (X, Y, Z); our internal volumes are
    # (Z, Y, X) for numpy-marching-cubes compatibility. Transpose to RAS.
    data = np.transpose(ct.hu, (2, 1, 0)).astype(np.float32)
    img = nib.Nifti1Image(data, ct.affine)
    nib.save(img, path)
