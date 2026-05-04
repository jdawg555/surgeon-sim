"""
Score and rank catalog implants against a patient's disc space measurement.
All scores are 0–100 (higher = better fit).
"""
from __future__ import annotations
import math
import logging
from typing import Optional

from ..core.models import (
    ImplantSpec, DiscSpaceMeasurement, FitScore, ImplantType, SpineLevel
)
from ..core.catalog import FULL_CATALOG, get_catalog

log = logging.getLogger(__name__)

# Weighting for composite score
_WEIGHT_FOOTPRINT = 0.40
_WEIGHT_HEIGHT    = 0.35
_WEIGHT_LORDOSIS  = 0.25


def _footprint_score(implant: ImplantSpec, meas: DiscSpaceMeasurement) -> tuple[float, float, float]:
    """
    Score how well the implant footprint matches the patient endplate.

    Returns (score 0–1, overhang_mm, coverage_fraction).

    Perfect score: implant covers ~85–95% of endplate with ≤1 mm overhang.
    """
    # Approximate endplate as ellipse
    endplate_a = meas.ap_depth_mm / 2.0
    endplate_b = meas.ml_width_mm / 2.0
    endplate_area = math.pi * endplate_a * endplate_b

    # Approximate implant footprint as ellipse
    imp_a = implant.ap_depth_mm / 2.0
    imp_b = implant.ml_width_mm / 2.0
    imp_area = math.pi * imp_a * imp_b

    # Intersection area (two co-centered ellipses, both axis-aligned)
    # = pi * min(a1,a2) * min(b1,b2) if one contains the other, else approximate
    intersect_a = min(endplate_a, imp_a)
    intersect_b = min(endplate_b, imp_b)
    intersect_area = math.pi * intersect_a * intersect_b

    coverage = intersect_area / endplate_area if endplate_area > 0 else 0.0
    overhang_ap = max(0.0, imp_a - endplate_a)
    overhang_ml = max(0.0, imp_b - endplate_b)
    overhang_mm = math.sqrt(overhang_ap**2 + overhang_ml**2)

    # Ideal coverage: 0.80 – 0.95
    if 0.80 <= coverage <= 0.95:
        cov_score = 1.0
    elif coverage < 0.80:
        cov_score = coverage / 0.80
    else:
        # over-coverage (implant larger than endplate)
        cov_score = max(0.0, 1.0 - (coverage - 0.95) * 3.0)

    # Overhang penalty
    overhang_penalty = min(1.0, overhang_mm / 5.0)  # 5mm overhang → 0 score
    score = cov_score * (1.0 - overhang_penalty * 0.8)

    return max(0.0, score), overhang_mm, coverage


def _height_score(implant: ImplantSpec, meas: DiscSpaceMeasurement) -> float:
    """
    Score how well the implant height restores disc space.

    Ideal: implant height = disc height mean + 0–2 mm (slight distraction).
    """
    target_h = meas.disc_height_mean_mm + 1.0  # 1 mm distraction target
    actual_h = implant.height_mm

    # First check if this height is within the product family range
    if not (implant.height_min_mm <= actual_h <= implant.height_max_mm):
        return 0.0

    deviation = abs(actual_h - target_h)
    # Score decays linearly: ±2mm = excellent, ±5mm = poor, >8mm = 0
    if deviation <= 2.0:
        return 1.0
    elif deviation <= 5.0:
        return 1.0 - (deviation - 2.0) / 3.0
    elif deviation <= 8.0:
        return max(0.0, 0.1 - (deviation - 5.0) / 30.0)
    return 0.0


def _lordosis_score(implant: ImplantSpec, meas: DiscSpaceMeasurement) -> float:
    """
    Score how well the implant's built-in lordosis matches the patient's natural lordosis.
    """
    natural = meas.natural_lordosis_deg
    built_in = implant.lordotic_angle_deg

    # Best available angle from the product family
    best_angle = min(implant.available_angles_deg, key=lambda a: abs(a - natural))
    deviation = abs(best_angle - natural)

    if deviation <= 2.0:
        return 1.0
    elif deviation <= 5.0:
        return 1.0 - (deviation - 2.0) / 3.0 * 0.5
    elif deviation <= 10.0:
        return 0.5 - (deviation - 5.0) / 5.0 * 0.4
    return max(0.0, 0.1 - (deviation - 10.0) / 50.0)


def _build_warnings(
    implant: ImplantSpec,
    meas: DiscSpaceMeasurement,
    overhang_mm: float,
    coverage: float,
) -> list[str]:
    warnings = []
    if overhang_mm > 2.0:
        warnings.append(f"Implant overhangs endplate by {overhang_mm:.1f} mm — subsidence risk elevated")
    if coverage < 0.60:
        warnings.append(f"Endplate coverage {coverage*100:.0f}% — implant undersized; consider larger footprint")
    if implant.height_mm > meas.disc_height_mean_mm + 5.0:
        warnings.append("Implant height significantly exceeds disc space — distraction may be excessive")
    if implant.height_mm < meas.disc_height_mean_mm - 2.0:
        warnings.append("Implant height below disc space — may not restore adequate foraminal height")
    if not implant.fda_cleared:
        warnings.append("Not FDA cleared — CE marked only; verify regulatory status for jurisdiction")
    if meas.confidence < 0.5:
        warnings.append("Measurement confidence low — manual verification of dimensions recommended")
    return warnings


def score_implant(implant: ImplantSpec, meas: DiscSpaceMeasurement) -> FitScore:
    """Score a single implant against a disc space measurement."""
    # Check level compatibility
    level_compatible = meas.level in implant.indications
    if not level_compatible:
        return FitScore(
            implant=implant, measurement=meas,
            footprint_score=0.0, height_score=0.0, lordosis_score=0.0,
            overhang_mm=0.0, coverage_fraction=0.0, total_score=0.0,
            warnings=["Implant not indicated for this spinal level"],
        )

    fp_score, overhang_mm, coverage = _footprint_score(implant, meas)
    h_score = _height_score(implant, meas)
    lord_score = _lordosis_score(implant, meas)

    composite = (
        _WEIGHT_FOOTPRINT * fp_score
        + _WEIGHT_HEIGHT * h_score
        + _WEIGHT_LORDOSIS * lord_score
    )
    total = round(composite * 100, 1)

    warnings = _build_warnings(implant, meas, overhang_mm, coverage)

    return FitScore(
        implant=implant,
        measurement=meas,
        footprint_score=round(fp_score, 3),
        height_score=round(h_score, 3),
        lordosis_score=round(lord_score, 3),
        overhang_mm=round(overhang_mm, 2),
        coverage_fraction=round(coverage, 3),
        total_score=total,
        warnings=warnings,
    )


def rank_implants(
    meas: DiscSpaceMeasurement,
    catalog: Optional[list[ImplantSpec]] = None,
    top_n: int = 10,
) -> list[FitScore]:
    """
    Score and rank all compatible implants against a measurement.
    Returns the top_n results sorted by total_score descending.
    """
    if catalog is None:
        # Filter to correct implant type for the level
        implant_type = (
            ImplantType.CERVICAL_TDR if meas.level.is_cervical
            else ImplantType.LUMBAR_TDR
        )
        catalog = get_catalog(implant_type)

    scores = [score_implant(imp, meas) for imp in catalog]
    scores.sort(key=lambda s: s.total_score, reverse=True)

    for rank, s in enumerate(scores[:top_n], start=1):
        s.rank = rank

    log.info(
        f"Ranked {len(scores)} implants for {meas.level.value}. "
        f"Best: {scores[0].implant.product_name} ({scores[0].total_score:.1f})"
        if scores else f"No implants scored for {meas.level.value}"
    )
    return scores[:top_n]


def best_fit(meas: DiscSpaceMeasurement) -> Optional[FitScore]:
    """Convenience: return the single best-fit implant."""
    ranked = rank_implants(meas, top_n=1)
    return ranked[0] if ranked else None
