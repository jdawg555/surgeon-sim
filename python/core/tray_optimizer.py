"""
Dragonfly Tray Optimizer
========================
Reduces a standard 120-implant spine tray to the minimum viable set for a
specific case, cutting sterilization cost and OR setup time.

Standard spine tray baseline: 120 implants (industry norm across major vendors).
Dragonfly output: only the sizes required for this patient + safety buffer.

Usage::

    from src.dragonfly.tray_optimizer import TrayOptimizer
    from src.dragonfly.implant_predictor import ImplantPredictor

    plan  = ImplantPredictor().predict(...)
    tray  = TrayOptimizer().optimize(plan, catalog=plan.screws.values())
    print(f"Tray reduced by {tray.reduction_pct:.1f}%")
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from src.dragonfly.implant_predictor import ImplantPlan, ScrewSpec

# Industry cost estimate per implant unit for sterilization / set maintenance
_STERILIZATION_COST_PER_UNIT_USD = 2.50
_STANDARD_TRAY_BASELINE = 120


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class TrayItem:
    """A single line-item in the optimized tray."""
    diameter_mm: float
    length_mm:   int
    quantity:    int
    role:        str   # "primary" | "backup" | "buffer"

    def label(self) -> str:
        return (f"⌀{self.diameter_mm}mm × {self.length_mm}mm  "
                f"qty={self.quantity}  [{self.role}]")


@dataclass
class TrayConfiguration:
    """
    Optimized implant tray for a single surgical case.

    Attributes
    ----------
    items                       : deduplicated line-items with quantities
    total_implants              : total screw count in optimized tray
    standard_baseline           : always 120 (industry standard tray size)
    reduction_pct               : percentage reduction vs. standard tray
    rod_specs                   : human-readable rod descriptors
    estimated_sterilization_cost_usd : items × $2.50 per unit
    warnings                    : advisory messages from optimizer
    """
    items:                            list[TrayItem]
    total_implants:                   int
    standard_baseline:                int
    reduction_pct:                    float
    rod_specs:                        list[str]
    estimated_sterilization_cost_usd: float
    warnings:                         list[str]


# ── Optimizer ─────────────────────────────────────────────────────────────────

class TrayOptimizer:
    """
    Builds the minimum viable implant tray for a given ImplantPlan.

    Algorithm
    ---------
    For each unique (diameter, length) combination across primary + backup
    screws::

        count = primary_count
              + backup_count
              + (safety_margin × primary_count)   # buffer copies

    Only sizes with count > 0 are included.  The resulting tray is compared
    against the 120-unit industry baseline to compute reduction.
    """

    def optimize(
        self,
        plan:          ImplantPlan,
        catalog:       object = None,   # unused — kept for API compatibility
        safety_margin: int = 2,
    ) -> TrayConfiguration:
        """
        Parameters
        ----------
        plan          : ImplantPlan from ImplantPredictor.predict()
        catalog       : ignored (reserved for future catalog-matching feature)
        safety_margin : extra copies of each primary size added as buffer

        Returns
        -------
        TrayConfiguration
        """
        warnings: list[str] = []

        # ── 1. Count primary screws per (dia, len) ────────────────────────────
        primary_counts: dict[tuple, int] = defaultdict(int)
        for screw in plan.screws.values():
            primary_counts[(screw.diameter_mm, screw.length_mm)] += 1

        # ── 2. Count backup screws per (dia, len) ─────────────────────────────
        backup_counts: dict[tuple, int] = defaultdict(int)
        for backup_list in plan.backup_screws.values():
            for screw in backup_list:
                backup_counts[(screw.diameter_mm, screw.length_mm)] += 1

        # ── 3. Merge into optimized counts ───────────────────────────────────
        # Union of all sizes that appear in primary OR backup sets
        all_sizes: set[tuple] = set(primary_counts) | set(backup_counts)

        items: list[TrayItem] = []
        for (dia, lng) in sorted(all_sizes):
            p_count = primary_counts.get((dia, lng), 0)
            b_count = backup_counts.get((dia, lng), 0)
            buf     = safety_margin * p_count

            total_qty = p_count + b_count + buf
            if total_qty == 0:
                continue

            # Determine dominant role for labelling
            if p_count > 0:
                role = "primary" if b_count == 0 else "primary+backup"
            else:
                role = "backup"

            items.append(TrayItem(
                diameter_mm=dia,
                length_mm=lng,
                quantity=total_qty,
                role=role,
            ))

        total = sum(i.quantity for i in items)

        # ── 4. Reduction vs. standard 120-unit tray ───────────────────────────
        reduction_pct = max(0.0, (1.0 - total / _STANDARD_TRAY_BASELINE) * 100.0)
        if total > _STANDARD_TRAY_BASELINE:
            warnings.append(
                f"Optimized tray ({total} units) exceeds standard baseline "
                f"({_STANDARD_TRAY_BASELINE}); consider splitting into two trays."
            )
            reduction_pct = 0.0

        # ── 5. Rod descriptors ────────────────────────────────────────────────
        rod_specs = _build_rod_specs(plan)

        # ── 6. Sterilization cost estimate ────────────────────────────────────
        sterilization_cost = total * _STERILIZATION_COST_PER_UNIT_USD

        return TrayConfiguration(
            items=items,
            total_implants=total,
            standard_baseline=_STANDARD_TRAY_BASELINE,
            reduction_pct=round(reduction_pct, 1),
            rod_specs=rod_specs,
            estimated_sterilization_cost_usd=round(sterilization_cost, 2),
            warnings=warnings,
        )


# ── Rod spec builder ──────────────────────────────────────────────────────────

def _build_rod_specs(plan: ImplantPlan) -> list[str]:
    """
    Generate human-readable rod descriptor strings.
    Standard construct uses two parallel rods (bilateral).
    """
    mat  = plan.rod_material
    lgth = plan.rod_length_mm
    curv = plan.rod_curvature_deg
    # Bilateral construct — one rod each side
    spec = f"{mat}  {lgth:.0f} mm  {curv:.1f}° pre-bend"
    return [f"Left rod:  {spec}", f"Right rod: {spec}"]
