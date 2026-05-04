"""
Dragonfly Implant Predictor
============================
Core clinical intelligence module.  Takes geometry derived from DICOM/STL
and outputs a statistically-validated pedicle screw + rod configuration for
lumbar spinal fusion.

Statistical prior: Zindrick et al. 1987 (Spine), Mirkovic et al. 1997 (Spine)
  — normative pedicle morphometry data used when measured landmarks are absent.

Usage::

    from src.dragonfly.implant_predictor import ImplantPredictor

    predictor = ImplantPredictor()
    plan = predictor.predict(
        landmarks    = landmarks_3d,      # dict from LandmarkDetector
        spinopelvic  = sp_dict,           # dict from SpinopelvicAnalyser
        density_hu   = 523.0,             # mean HU of pedicle cortex
        fused_levels = ["L4-L5", "L5-S1"],
        sex          = "M",
        age          = 58,
    )
    result = validate_implant_plan(plan)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

# ── Normative pedicle width data ──────────────────────────────────────────────
# Source: Zindrick et al. 1987; Mirkovic et al. 1997
# Values are mean transverse pedicle isthmus width in mm.
NORMATIVE_PEDICLE_WIDTH: dict[str, dict[str, float]] = {
    "L1": {"M": 8.7,  "F": 7.8},
    "L2": {"M": 8.9,  "F": 7.9},
    "L3": {"M": 10.2, "F": 9.0},
    "L4": {"M": 12.6, "F": 11.2},
    "L5": {"M": 15.4, "F": 13.8},
}

# Normative vertebral body AP depth (mm) — used when landmark bounds unavailable.
# Source: Panjabi et al. 1992 (Spine) — average adult lumbar vertebral body depths.
NORMATIVE_VB_DEPTH: dict[str, float] = {
    "L1": 38.0,
    "L2": 38.5,
    "L3": 39.0,
    "L4": 40.0,
    "L5": 40.5,
    "S1": 38.0,
}

# Standard implant catalogues (mm)
STANDARD_DIAMETERS: list[float] = [4.5, 5.5, 6.5, 7.5]
STANDARD_LENGTHS:   list[int]   = [35, 40, 45, 50, 55]

# Clinical safety ceilings
MAX_SCREW_DIAMETER_MM = 8.5
MAX_SCREW_LENGTH_MM   = 55
SAFETY_MARGIN_FACTOR  = 0.80   # screw fills 80 % of pedicle width
LENGTH_TARGET_FACTOR  = 0.80   # target 80 % of vertebral body AP depth
ROD_OVERHANG_MM       = 20.0   # extra length per rod end

# Cortical Density Index threshold for CoCr rod selection
CDI_COBALT_CR_THRESHOLD = 600.0


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ScrewSpec:
    """Specification for a single pedicle screw."""
    diameter_mm: float
    length_mm: int
    level: str           # "L4", "L5", "S1"
    side: str            # "left" or "right"
    basis: str           # "measured" | "normative"

    def label(self) -> str:
        return f"{self.level}-{self.side}  ⌀{self.diameter_mm}mm × {self.length_mm}mm  [{self.basis}]"


@dataclass
class ImplantPlan:
    """
    Complete pedicle screw + rod plan for a lumbar fusion construct.

    Attributes
    ----------
    fused_levels    : disc-space level names, e.g. ["L4-L5", "L5-S1"]
    screws          : primary screws keyed by "{level}-{side}"
    rod_length_mm   : estimated rod length including overhang
    rod_curvature_deg : lordosis angle to pre-bend into the rod
    rod_material    : "Ti" (default) or "CoCr" (high-density bone)
    backup_screws   : one size up and one size down per screw key
    confidence      : per-vertebra-level confidence score 0–1
    warnings        : clinical advisory messages
    """
    fused_levels:       list[str]
    screws:             dict[str, ScrewSpec]
    rod_length_mm:      float
    rod_curvature_deg:  float
    rod_material:       str
    backup_screws:      dict[str, list[ScrewSpec]]
    confidence:         dict[str, float]
    warnings:           list[str]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _landmark_distance(lm: dict, key_a: str, key_b: str) -> Optional[float]:
    """
    Euclidean distance (mm) between two named landmarks.
    Returns None if either landmark is missing.
    """
    a = lm.get(key_a)
    b = lm.get(key_b)
    if a is None or b is None:
        return None
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return float(np.linalg.norm(b - a))


def _vert_from_level(level: str) -> list[str]:
    """
    Return the vertebra names that carry screws for a fusion level.
    "L4-L5" → ["L4", "L5"];  "L5-S1" → ["L5", "S1"]
    """
    parts = level.split("-")
    return parts  # both vertebrae in the disc-space name need screws


def _select_diameter(pedicle_width_mm: float) -> float:
    """
    Choose the largest standard diameter that does not exceed 80 % of pedicle
    width.  Always rounds DOWN — never exceed the safety margin.
    """
    target = pedicle_width_mm * SAFETY_MARGIN_FACTOR
    # Filter to sizes ≤ target, pick the largest
    viable = [s for s in STANDARD_DIAMETERS if s <= target]
    if not viable:
        return STANDARD_DIAMETERS[0]  # smallest available
    return max(viable)


def _select_length(vb_depth_mm: float) -> int:
    """
    Choose the standard screw length closest to 80 % of vertebral body depth.
    """
    target = vb_depth_mm * LENGTH_TARGET_FACTOR
    return min(STANDARD_LENGTHS, key=lambda l: abs(l - target))


def _backup_diameters(chosen: float) -> list[float]:
    """One size down and one size up from chosen (clamped to catalogue)."""
    idx = STANDARD_DIAMETERS.index(chosen) if chosen in STANDARD_DIAMETERS else 0
    backups = []
    if idx > 0:
        backups.append(STANDARD_DIAMETERS[idx - 1])
    if idx < len(STANDARD_DIAMETERS) - 1:
        backups.append(STANDARD_DIAMETERS[idx + 1])
    return backups


def _backup_lengths(chosen: int) -> list[int]:
    """One step shorter and one step longer (clamped to catalogue)."""
    idx = STANDARD_LENGTHS.index(chosen) if chosen in STANDARD_LENGTHS else 0
    backups = []
    if idx > 0:
        backups.append(STANDARD_LENGTHS[idx - 1])
    if idx < len(STANDARD_LENGTHS) - 1:
        backups.append(STANDARD_LENGTHS[idx + 1])
    return backups


def _level_vertices_ordered(fused_levels: list[str]) -> list[str]:
    """
    Return the ordered, deduplicated list of vertebral body names involved
    in the fusion construct.
    E.g. ["L4-L5", "L5-S1"] → ["L4", "L5", "S1"]
    """
    seen: list[str] = []
    for lvl in fused_levels:
        for v in _vert_from_level(lvl):
            if v not in seen:
                seen.append(v)
    return seen


# ── Main predictor ────────────────────────────────────────────────────────────

class ImplantPredictor:
    """
    Predicts pedicle screw sizes and rod specifications for a lumbar fusion
    construct using published normative morphometry as the statistical prior
    (Zindrick et al. 1987; Mirkovic et al. 1997).

    When 3-D landmark data is available the measured pedicle width takes
    priority; normative tables are used as a fallback per level/side.
    """

    def predict(
        self,
        landmarks:   dict,
        spinopelvic: dict,
        density_hu:  float,
        fused_levels: list[str],
        sex:  str = "M",
        age:  int = 50,
    ) -> ImplantPlan:
        """
        Parameters
        ----------
        landmarks     : 3-D landmark dict from LandmarkDetector.
                        Keys follow the pattern
                        "{Ln}_left_pedicle_medial" / "{Ln}_left_pedicle_lateral"
                        and "{Ln}_centroid" for vertebral body bounds.
        spinopelvic   : output dict from SpinopelvicAnalyser; expected keys:
                        "lumbar_lordosis_deg", "pelvic_incidence_deg".
        density_hu    : mean Hounsfield Unit of the pedicle cortical region.
        fused_levels  : list of disc-space level strings, e.g. ["L4-L5","L5-S1"].
        sex           : 'M' or 'F' (used for normative lookup).
        age           : patient age (used for confidence scoring and warnings).

        Returns
        -------
        ImplantPlan
        """
        sex = sex.upper()
        if sex not in ("M", "F"):
            sex = "M"

        warnings: list[str] = []

        # ── Vertebrae involved in the construct ───────────────────────────────
        vert_order = _level_vertices_ordered(fused_levels)

        # ── Per-vertebra screw sizing ─────────────────────────────────────────
        screws:        dict[str, ScrewSpec] = {}
        backup_screws: dict[str, list[ScrewSpec]] = {}
        confidence:    dict[str, float] = {}

        for vert in vert_order:
            vert_conf = 1.0

            for side in ("left", "right"):
                key = f"{vert}-{side}"

                # ── a. Pedicle width ─────────────────────────────────────────
                lm_med = f"{vert}_{side}_pedicle_medial"
                lm_lat = f"{vert}_{side}_pedicle_lateral"
                measured_width = _landmark_distance(landmarks, lm_med, lm_lat)

                if measured_width is not None and measured_width > 0:
                    pedicle_width = measured_width
                    basis = "measured"
                else:
                    norm_table = NORMATIVE_PEDICLE_WIDTH.get(vert)
                    if norm_table is None:
                        # S1 not in normative table — use L5 values as proxy
                        norm_table = NORMATIVE_PEDICLE_WIDTH["L5"]
                        warnings.append(
                            f"{vert} not in normative table; "
                            f"using L5 values as proxy for {key}"
                        )
                    pedicle_width = norm_table[sex]
                    basis = "normative"
                    vert_conf *= 0.75   # lower confidence for normative sizing

                # ── b. Screw diameter ─────────────────────────────────────────
                chosen_dia = _select_diameter(pedicle_width)
                if chosen_dia > MAX_SCREW_DIAMETER_MM:
                    chosen_dia = MAX_SCREW_DIAMETER_MM
                    warnings.append(
                        f"{key}: diameter capped at safety ceiling "
                        f"{MAX_SCREW_DIAMETER_MM}mm"
                    )

                # ── c. Screw length ───────────────────────────────────────────
                # Prefer landmark-derived AP vertebral body depth
                centroid_key = f"{vert}_centroid"
                vb_depth = _get_vb_depth(landmarks, vert)
                if vb_depth is None:
                    vb_depth = NORMATIVE_VB_DEPTH.get(vert, 39.0)
                    basis = "normative"
                    vert_conf *= 0.90

                chosen_len = _select_length(vb_depth)

                # ── d. Build spec ─────────────────────────────────────────────
                spec = ScrewSpec(
                    diameter_mm=chosen_dia,
                    length_mm=chosen_len,
                    level=vert,
                    side=side,
                    basis=basis,
                )
                screws[key] = spec

                # Backup sizes
                bdias = _backup_diameters(chosen_dia)
                blens = _backup_lengths(chosen_len)
                backup_list: list[ScrewSpec] = []
                for bd in bdias:
                    for bl in blens:
                        backup_list.append(ScrewSpec(
                            diameter_mm=bd,
                            length_mm=bl,
                            level=vert,
                            side=side,
                            basis=basis,
                        ))
                backup_screws[key] = backup_list

            confidence[vert] = round(max(0.0, min(1.0, vert_conf)), 3)

        # ── Age-related confidence adjustment ─────────────────────────────────
        if age > 70:
            warnings.append(
                "Patient age > 70: cortical thinning may reduce effective "
                "pedicle width; consider intraoperative pedicle sounding."
            )
            for k in confidence:
                confidence[k] = round(confidence[k] * 0.92, 3)
        elif age < 25:
            warnings.append(
                "Patient age < 25: pedicle dimensions may exceed normative "
                "adult range; confirm with direct measurement."
            )

        # ── Rod length estimation ─────────────────────────────────────────────
        rod_length_mm = _estimate_rod_length(
            vert_order, landmarks, fused_levels
        ) + 2 * ROD_OVERHANG_MM

        # ── Rod curvature ─────────────────────────────────────────────────────
        ll_deg = float(spinopelvic.get("lumbar_lordosis_deg", 40.0))
        rod_curvature_deg = ll_deg * 0.75

        # ── Rod material selection ────────────────────────────────────────────
        # CoCr (cobalt-chromium) used for high bone density — stiffer alloy
        # matches cortical stiffness and reduces stress shielding.
        rod_material = "CoCr" if density_hu > CDI_COBALT_CR_THRESHOLD else "Ti"

        # ── Multi-level construct warnings ───────────────────────────────────
        if len(fused_levels) >= 3:
            warnings.append(
                f"{len(fused_levels)}-level construct: consider staged "
                f"surgery or supplemental anterior support."
            )

        pi_deg = float(spinopelvic.get("pelvic_incidence_deg", 50.0))
        pi_ll = pi_deg - ll_deg
        if abs(pi_ll) > 20:
            warnings.append(
                f"PI-LL mismatch {pi_ll:+.1f}° (>20°): sagittal imbalance "
                f"risk — adjust rod curvature intraoperatively."
            )

        return ImplantPlan(
            fused_levels=fused_levels,
            screws=screws,
            rod_length_mm=round(rod_length_mm, 1),
            rod_curvature_deg=round(rod_curvature_deg, 1),
            rod_material=rod_material,
            backup_screws=backup_screws,
            confidence=confidence,
            warnings=warnings,
        )


# ── Private geometry helpers ──────────────────────────────────────────────────

def _get_vb_depth(landmarks: dict, vert: str) -> Optional[float]:
    """
    Derive AP vertebral body depth from landmark bounding box.
    Tries anterior/posterior corner landmarks first; falls back to None.
    """
    ant = landmarks.get(f"{vert}_anterior_corner")
    pos = landmarks.get(f"{vert}_posterior_corner")
    if ant is not None and pos is not None:
        return float(np.linalg.norm(np.asarray(pos) - np.asarray(ant)))
    # Also try centroid-based bounds if stored as {vert}_bounds = (xmin,xmax,ymin,ymax,zmin,zmax)
    bounds = landmarks.get(f"{vert}_bounds")
    if bounds is not None and len(bounds) >= 4:
        # AP extent = Y axis (index 2,3) in RAS
        return float(abs(bounds[3] - bounds[2]))
    return None


def _estimate_rod_length(
    vert_order: list[str],
    landmarks:  dict,
    fused_levels: list[str],
) -> float:
    """
    Estimate inter-pedicle arc length across all fused levels.
    Uses centroid-to-centroid distances when landmarks are present;
    falls back to normative inter-centroid spacing of 35 mm per level.
    """
    NORMATIVE_INTER_MM = 35.0  # average inter-vertebral centroid spacing

    total = 0.0
    for i in range(len(vert_order) - 1):
        a = landmarks.get(f"{vert_order[i]}_centroid")
        b = landmarks.get(f"{vert_order[i + 1]}_centroid")
        if a is not None and b is not None:
            total += float(np.linalg.norm(np.asarray(b) - np.asarray(a)))
        else:
            total += NORMATIVE_INTER_MM

    return total


# ── Validation ────────────────────────────────────────────────────────────────

_CONTIGUOUS_ORDER = ["L1", "L2", "L3", "L4", "L5", "S1"]


def _levels_contiguous(fused_levels: list[str]) -> bool:
    """
    Return True iff the fused levels form a contiguous spinal segment
    (no skipped levels).

    E.g. ["L3-L4", "L4-L5", "L5-S1"] → True
         ["L3-L4", "L5-S1"]           → False (L4-L5 skipped)
    """
    verts = _level_vertices_ordered(fused_levels)
    try:
        indices = [_CONTIGUOUS_ORDER.index(v) for v in verts]
    except ValueError:
        return False  # unknown vertebra name
    return indices == list(range(indices[0], indices[0] + len(indices)))


def validate_implant_plan(plan: ImplantPlan) -> dict:
    """
    Validate an ImplantPlan against clinical safety constraints.

    Checks
    ------
    - All screw diameters are standard catalogue sizes
    - No diameter exceeds 8.5 mm safety ceiling
    - No length exceeds 55 mm
    - Rod length is positive
    - Fused levels are contiguous (no gaps)

    Returns
    -------
    {"valid": bool, "warnings": list[str]}
    """
    issues: list[str] = []

    for key, screw in plan.screws.items():
        if screw.diameter_mm not in STANDARD_DIAMETERS:
            issues.append(
                f"{key}: diameter {screw.diameter_mm}mm not in standard "
                f"catalogue {STANDARD_DIAMETERS}"
            )
        if screw.diameter_mm > MAX_SCREW_DIAMETER_MM:
            issues.append(
                f"{key}: diameter {screw.diameter_mm}mm exceeds safety "
                f"ceiling {MAX_SCREW_DIAMETER_MM}mm"
            )
        if screw.length_mm > MAX_SCREW_LENGTH_MM:
            issues.append(
                f"{key}: length {screw.length_mm}mm exceeds maximum "
                f"{MAX_SCREW_LENGTH_MM}mm"
            )

    if plan.rod_length_mm <= 0:
        issues.append("rod_length_mm must be positive")

    if not _levels_contiguous(plan.fused_levels):
        issues.append(
            f"Fused levels {plan.fused_levels} are not contiguous — "
            f"non-contiguous fusion constructs are not supported"
        )

    return {"valid": len(issues) == 0, "warnings": issues}
