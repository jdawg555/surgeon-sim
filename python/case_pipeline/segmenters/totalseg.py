"""TotalSegmentator-backed volume source.

Runs TotalSegmentator's `total` task on a synthetic CT (or eventually a
real anonymised CT) and remaps its per-vertebra labels into our shared
taxonomy. The disc / dura / skin / soft tissue gap is filled by
combining TotalSegmentator's bone + cord masks with geometric envelopes
from the parametric phantom.

TotalSegmentator is a heavy optional dependency (~2 GB of model weights
plus a PyTorch/nnUNet stack). Install with:

    pip install TotalSegmentator nibabel scipy

This module imports `totalsegmentator` lazily and raises a clear
ImportError with install instructions if it isn't available, so the
parametric phantom path keeps working on installations that haven't
opted into the heavier deps.

This PR's structure is the integration architecture; with a synthetic
CT input the segmented bone shapes are still close to the parametric
phantom's cylinders. Realism gain unlocks when a real CT is fed in
(future PR), at which point the same wrapper just consumes a different
NIfTI.
"""

from __future__ import annotations

import os
import tempfile

import numpy as np

from case_pipeline.ct_synthesis import CtVolume, write_nifti
from case_pipeline.models import PhantomSpec, TotalSegmentatorConfig
from case_pipeline.phantom import (
    LABEL_CORD,
    LABEL_DISC,
    LABEL_DURA,
    LABEL_SKIN,
    LABEL_SOFT_TISSUE,
    LABEL_VERTEBRAL_BODY,
    PhantomVolume,
    generate as generate_phantom,
)


# TotalSegmentator class names (subset we care about) for the lumbar
# block. Names follow TS v2 conventions; if the upstream renames classes
# in a future major version, this is the only constant that needs editing.
TS_VERTEBRA_CLASSES: tuple[str, ...] = (
    "vertebrae_L1",
    "vertebrae_L2",
    "vertebrae_L3",
    "vertebrae_L4",
    "vertebrae_L5",
    "sacrum",
)
TS_CORD_CLASS = "spinal_cord"
TS_REQUESTED_ROI: tuple[str, ...] = TS_VERTEBRA_CLASSES + (TS_CORD_CLASS,)


_INSTALL_HINT = (
    "TotalSegmentator is not installed. Install with:\n"
    "    pip install TotalSegmentator nibabel scipy\n"
    "First run will download ~2 GB of model weights to ~/.totalsegmentator/."
)


def is_available() -> bool:
    """True when the TotalSegmentator package can be imported. Smoke
    tests use this to skip the TS path on machines without the dep."""
    try:
        import totalsegmentator  # noqa: F401
        import nibabel  # noqa: F401
        return True
    except ImportError:
        return False


def segment(
    ct: CtVolume,
    spec: PhantomSpec,
    config: TotalSegmentatorConfig,
) -> PhantomVolume:
    """Run TotalSegmentator on `ct`, remap labels, fill gaps, return a
    labelled volume in our taxonomy.

    `spec` is needed for the gap-filling stages (disc geometry between
    vertebrae, skin/soft-tissue envelopes) which reuse the same
    parametric inputs the CT was synthesised from. When real CTs replace
    synthetic ones, those gap fillers need a different source.
    """
    try:
        from totalsegmentator.python_api import totalsegmentator
    except ImportError as e:
        raise ImportError(_INSTALL_HINT) from e

    # TS reads from disk. Write the input CT to a temp NIfTI, run TS,
    # read back its multi-class output. Cleanup happens automatically
    # via TemporaryDirectory.
    with tempfile.TemporaryDirectory(prefix="dragonfly-ts-") as tmpdir:
        ct_path = os.path.join(tmpdir, "input.nii.gz")
        seg_path = os.path.join(tmpdir, "segmentation.nii.gz")
        write_nifti(ct, ct_path)

        totalsegmentator(
            input=ct_path,
            output=seg_path,
            task="total",
            fast=config.fast,
            roi_subset=list(TS_REQUESTED_ROI),
            ml=True,  # multi-label single-file output
            device=config.device,
            quiet=True,
        )

        ts_labels = _load_ts_segmentation(seg_path)

    # Remap TS classes -> our taxonomy. See TS_REQUESTED_ROI for which
    # input classes were requested; ts_labels is keyed by those names.
    bone_mask = _union(ts_labels, TS_VERTEBRA_CLASSES)
    cord_mask = ts_labels.get(TS_CORD_CLASS, _zeros_like_ct(ct))

    # Fall back to phantom geometry where TS gives us nothing.
    pv: PhantomVolume = generate_phantom(spec)

    voxels = np.zeros_like(pv.voxels)
    voxels[pv.voxels == LABEL_SKIN] = LABEL_SKIN
    voxels[pv.voxels == LABEL_SOFT_TISSUE] = LABEL_SOFT_TISSUE
    voxels[pv.voxels == LABEL_DISC] = LABEL_DISC  # geometric, see below
    voxels[pv.voxels == LABEL_DURA] = LABEL_DURA  # geometric envelope

    # Bone wins over disc / soft tissue at boundaries.
    voxels[bone_mask] = LABEL_VERTEBRAL_BODY
    # Discs were written from the phantom but TS bone may overlap; we
    # rewrite disc voxels that aren't bone, after.
    voxels[(pv.voxels == LABEL_DISC) & ~bone_mask] = LABEL_DISC
    # Cord overrides everything else within its mask.
    voxels[cord_mask] = LABEL_CORD

    return PhantomVolume(voxels=voxels, affine=ct.affine.copy(), spacing_mm=ct.spacing_mm)


def _zeros_like_ct(ct: CtVolume) -> np.ndarray:
    return np.zeros(ct.hu.shape, dtype=bool)


def _load_ts_segmentation(seg_path: str) -> dict[str, np.ndarray]:
    """Load TS's multi-label output and return a mask per class.

    With `ml=True`, TS writes a single integer-labelled volume plus a
    JSON sidecar mapping label IDs to class names. We expand that into
    per-class boolean masks, keyed by name, for downstream simplicity.
    Volume is transposed back to (Z, Y, X) to match the rest of the
    pipeline.
    """
    import json

    import nibabel as nib

    img = nib.load(seg_path)
    data_xyz = np.asarray(img.dataobj, dtype=np.uint16)
    data_zyx = np.transpose(data_xyz, (2, 1, 0))

    # TS writes <seg_path>.json next to <seg_path>.nii.gz with the label
    # mapping. Older versions wrote it as <seg_dir>/seg_label_map.json;
    # try both.
    base = seg_path
    if base.endswith(".nii.gz"):
        base = base[: -len(".nii.gz")]
    elif base.endswith(".nii"):
        base = base[: -len(".nii")]
    candidates = [base + ".json", os.path.join(os.path.dirname(seg_path), "seg_label_map.json")]
    label_map: dict[int, str] = {}
    for c in candidates:
        if os.path.exists(c):
            with open(c, "r") as fh:
                raw = json.load(fh)
            # TS uses {label_id: class_name}. Normalise to int keys.
            label_map = {int(k): v for k, v in raw.items()}
            break
    if not label_map:
        raise RuntimeError(
            f"TotalSegmentator label-map JSON not found near {seg_path}; "
            "cannot remap classes."
        )

    masks: dict[str, np.ndarray] = {}
    for label_id, name in label_map.items():
        if name in TS_REQUESTED_ROI:
            masks[name] = data_zyx == label_id
    return masks


def _union(masks: dict[str, np.ndarray], keys: tuple[str, ...]) -> np.ndarray:
    found = [masks[k] for k in keys if k in masks]
    if not found:
        # Fall back to all-False with a sane shape inferred from any
        # provided mask, or an empty array if nothing was returned.
        for v in masks.values():
            return np.zeros_like(v, dtype=bool)
        return np.zeros((1, 1, 1), dtype=bool)
    out = found[0].copy()
    for m in found[1:]:
        out |= m
    return out
