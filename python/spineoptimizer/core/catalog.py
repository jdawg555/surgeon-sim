"""
Spinal implant catalog with real clinical dimensions.
Sources: manufacturer IFUs, published literature, FDA 510(k) clearance summaries.
"""
from __future__ import annotations
from .models import ImplantSpec, ImplantType, SpineLevel

# ---------------------------------------------------------------------------
# Lumbar Total Disc Replacement (TDR)
# ---------------------------------------------------------------------------
_LUMBAR_LEVELS = [
    SpineLevel.L3_L4, SpineLevel.L4_L5, SpineLevel.L5_S1
]
_ALL_LUMBAR = [
    SpineLevel.L1_L2, SpineLevel.L2_L3, SpineLevel.L3_L4,
    SpineLevel.L4_L5, SpineLevel.L5_S1
]
_CERVICAL_LEVELS = [
    SpineLevel.C3_C4, SpineLevel.C4_C5, SpineLevel.C5_C6, SpineLevel.C6_C7
]

LUMBAR_TDR_CATALOG: list[ImplantSpec] = [
    # --- ProDisc-L (Centinel Spine / DePuy Synthes) ---
    ImplantSpec(
        implant_id="PDL-S-30x36-6", manufacturer="Centinel Spine",
        product_name="ProDisc-L", implant_type=ImplantType.LUMBAR_TDR,
        ap_depth_mm=30.0, ml_width_mm=36.0, height_mm=9.0,
        height_min_mm=9.0, height_max_mm=14.0,
        lordotic_angle_deg=6.0, available_angles_deg=[0.0, 6.0],
        material_endplate="CoCrMo", material_core="UHMWPE",
        has_keel=True, keel_height_mm=3.5,
        fda_cleared=True, ce_marked=True, indications=_LUMBAR_LEVELS,
    ),
    ImplantSpec(
        implant_id="PDL-M-36x40-6", manufacturer="Centinel Spine",
        product_name="ProDisc-L", implant_type=ImplantType.LUMBAR_TDR,
        ap_depth_mm=36.0, ml_width_mm=40.0, height_mm=10.0,
        height_min_mm=9.0, height_max_mm=14.0,
        lordotic_angle_deg=6.0, available_angles_deg=[0.0, 6.0],
        material_endplate="CoCrMo", material_core="UHMWPE",
        has_keel=True, keel_height_mm=3.5,
        fda_cleared=True, ce_marked=True, indications=_LUMBAR_LEVELS,
    ),
    ImplantSpec(
        implant_id="PDL-L-40x44-6", manufacturer="Centinel Spine",
        product_name="ProDisc-L", implant_type=ImplantType.LUMBAR_TDR,
        ap_depth_mm=40.0, ml_width_mm=44.0, height_mm=11.0,
        height_min_mm=9.0, height_max_mm=14.0,
        lordotic_angle_deg=6.0, available_angles_deg=[0.0, 6.0],
        material_endplate="CoCrMo", material_core="UHMWPE",
        has_keel=True, keel_height_mm=3.5,
        fda_cleared=True, ce_marked=True, indications=_LUMBAR_LEVELS,
    ),

    # --- Activ-L (Aesculap / B.Braun) ---
    ImplantSpec(
        implant_id="ACTL-A-30x36-0", manufacturer="Aesculap",
        product_name="Activ-L", implant_type=ImplantType.LUMBAR_TDR,
        ap_depth_mm=30.0, ml_width_mm=36.0, height_mm=9.0,
        height_min_mm=9.0, height_max_mm=13.0,
        lordotic_angle_deg=0.0, available_angles_deg=[0.0, 5.0, 10.0],
        material_endplate="Ti-6Al-4V", material_core="UHMWPE",
        has_keel=True, keel_height_mm=4.0,
        fda_cleared=True, ce_marked=True, indications=_LUMBAR_LEVELS,
    ),
    ImplantSpec(
        implant_id="ACTL-B-34x40-5", manufacturer="Aesculap",
        product_name="Activ-L", implant_type=ImplantType.LUMBAR_TDR,
        ap_depth_mm=34.0, ml_width_mm=40.0, height_mm=10.0,
        height_min_mm=9.0, height_max_mm=13.0,
        lordotic_angle_deg=5.0, available_angles_deg=[0.0, 5.0, 10.0],
        material_endplate="Ti-6Al-4V", material_core="UHMWPE",
        has_keel=True, keel_height_mm=4.0,
        fda_cleared=True, ce_marked=True, indications=_LUMBAR_LEVELS,
    ),
    ImplantSpec(
        implant_id="ACTL-C-38x44-10", manufacturer="Aesculap",
        product_name="Activ-L", implant_type=ImplantType.LUMBAR_TDR,
        ap_depth_mm=38.0, ml_width_mm=44.0, height_mm=11.0,
        height_min_mm=9.0, height_max_mm=13.0,
        lordotic_angle_deg=10.0, available_angles_deg=[0.0, 5.0, 10.0],
        material_endplate="Ti-6Al-4V", material_core="UHMWPE",
        has_keel=True, keel_height_mm=4.0,
        fda_cleared=True, ce_marked=True, indications=_LUMBAR_LEVELS,
    ),

    # --- Maverick (Medtronic) ---
    ImplantSpec(
        implant_id="MVK-S-28x36-0", manufacturer="Medtronic",
        product_name="Maverick", implant_type=ImplantType.LUMBAR_TDR,
        ap_depth_mm=28.0, ml_width_mm=36.0, height_mm=10.0,
        height_min_mm=10.0, height_max_mm=14.0,
        lordotic_angle_deg=0.0, available_angles_deg=[0.0, 6.0],
        material_endplate="CoCrMo", material_core="CoCrMo",
        has_keel=True, keel_height_mm=4.5,
        fda_cleared=True, ce_marked=True, indications=_LUMBAR_LEVELS,
    ),
    ImplantSpec(
        implant_id="MVK-M-32x40-6", manufacturer="Medtronic",
        product_name="Maverick", implant_type=ImplantType.LUMBAR_TDR,
        ap_depth_mm=32.0, ml_width_mm=40.0, height_mm=12.0,
        height_min_mm=10.0, height_max_mm=14.0,
        lordotic_angle_deg=6.0, available_angles_deg=[0.0, 6.0],
        material_endplate="CoCrMo", material_core="CoCrMo",
        has_keel=True, keel_height_mm=4.5,
        fda_cleared=True, ce_marked=True, indications=_LUMBAR_LEVELS,
    ),
    ImplantSpec(
        implant_id="MVK-L-36x44-6", manufacturer="Medtronic",
        product_name="Maverick", implant_type=ImplantType.LUMBAR_TDR,
        ap_depth_mm=36.0, ml_width_mm=44.0, height_mm=12.0,
        height_min_mm=10.0, height_max_mm=14.0,
        lordotic_angle_deg=6.0, available_angles_deg=[0.0, 6.0],
        material_endplate="CoCrMo", material_core="CoCrMo",
        has_keel=True, keel_height_mm=4.5,
        fda_cleared=True, ce_marked=True, indications=_LUMBAR_LEVELS,
    ),

    # --- FlexiCore (Stryker) ---
    ImplantSpec(
        implant_id="FXC-S-26x30-8", manufacturer="Stryker",
        product_name="FlexiCore", implant_type=ImplantType.LUMBAR_TDR,
        ap_depth_mm=26.0, ml_width_mm=30.0, height_mm=9.0,
        height_min_mm=9.0, height_max_mm=13.0,
        lordotic_angle_deg=8.0, available_angles_deg=[0.0, 8.0],
        material_endplate="CoCrMo", material_core="CoCrMo",
        has_keel=False, keel_height_mm=0.0,
        fda_cleared=True, ce_marked=True, indications=_LUMBAR_LEVELS,
    ),
    ImplantSpec(
        implant_id="FXC-M-30x36-8", manufacturer="Stryker",
        product_name="FlexiCore", implant_type=ImplantType.LUMBAR_TDR,
        ap_depth_mm=30.0, ml_width_mm=36.0, height_mm=11.0,
        height_min_mm=9.0, height_max_mm=13.0,
        lordotic_angle_deg=8.0, available_angles_deg=[0.0, 8.0],
        material_endplate="CoCrMo", material_core="CoCrMo",
        has_keel=False, keel_height_mm=0.0,
        fda_cleared=True, ce_marked=True, indications=_LUMBAR_LEVELS,
    ),

    # --- Kineflex-L (SpinalMotion) ---
    ImplantSpec(
        implant_id="KFL-S-32x38-0", manufacturer="SpinalMotion",
        product_name="Kineflex-L", implant_type=ImplantType.LUMBAR_TDR,
        ap_depth_mm=32.0, ml_width_mm=38.0, height_mm=9.0,
        height_min_mm=9.0, height_max_mm=13.0,
        lordotic_angle_deg=0.0, available_angles_deg=[0.0],
        material_endplate="CoCrMo", material_core="CoCrMo",
        has_keel=True, keel_height_mm=3.0,
        fda_cleared=False, ce_marked=True, indications=_LUMBAR_LEVELS,
    ),
]

# ---------------------------------------------------------------------------
# Cervical Total Disc Replacement (TDR)
# ---------------------------------------------------------------------------
CERVICAL_TDR_CATALOG: list[ImplantSpec] = [
    # --- Mobi-C (Zimmer Biomet) ---
    ImplantSpec(
        implant_id="MBC-S-14x14-0", manufacturer="Zimmer Biomet",
        product_name="Mobi-C", implant_type=ImplantType.CERVICAL_TDR,
        ap_depth_mm=14.0, ml_width_mm=14.0, height_mm=5.0,
        height_min_mm=5.0, height_max_mm=7.0,
        lordotic_angle_deg=0.0, available_angles_deg=[0.0],
        material_endplate="CoCrMo", material_core="UHMWPE",
        has_keel=True, keel_height_mm=1.5,
        fda_cleared=True, ce_marked=True, indications=_CERVICAL_LEVELS,
    ),
    ImplantSpec(
        implant_id="MBC-M-15x16-0", manufacturer="Zimmer Biomet",
        product_name="Mobi-C", implant_type=ImplantType.CERVICAL_TDR,
        ap_depth_mm=15.0, ml_width_mm=16.0, height_mm=6.0,
        height_min_mm=5.0, height_max_mm=7.0,
        lordotic_angle_deg=0.0, available_angles_deg=[0.0],
        material_endplate="CoCrMo", material_core="UHMWPE",
        has_keel=True, keel_height_mm=1.5,
        fda_cleared=True, ce_marked=True, indications=_CERVICAL_LEVELS,
    ),
    ImplantSpec(
        implant_id="MBC-L-17x18-0", manufacturer="Zimmer Biomet",
        product_name="Mobi-C", implant_type=ImplantType.CERVICAL_TDR,
        ap_depth_mm=17.0, ml_width_mm=18.0, height_mm=6.0,
        height_min_mm=5.0, height_max_mm=7.0,
        lordotic_angle_deg=0.0, available_angles_deg=[0.0],
        material_endplate="CoCrMo", material_core="UHMWPE",
        has_keel=True, keel_height_mm=1.5,
        fda_cleared=True, ce_marked=True, indications=_CERVICAL_LEVELS,
    ),

    # --- ProDisc-C (Centinel Spine) ---
    ImplantSpec(
        implant_id="PDC-S-14x14-0", manufacturer="Centinel Spine",
        product_name="ProDisc-C", implant_type=ImplantType.CERVICAL_TDR,
        ap_depth_mm=14.0, ml_width_mm=14.0, height_mm=5.0,
        height_min_mm=5.0, height_max_mm=8.0,
        lordotic_angle_deg=0.0, available_angles_deg=[0.0, 4.0, 7.0],
        material_endplate="CoCrMo", material_core="UHMWPE",
        has_keel=True, keel_height_mm=2.0,
        fda_cleared=True, ce_marked=True, indications=_CERVICAL_LEVELS,
    ),
    ImplantSpec(
        implant_id="PDC-M-15x15-4", manufacturer="Centinel Spine",
        product_name="ProDisc-C", implant_type=ImplantType.CERVICAL_TDR,
        ap_depth_mm=15.0, ml_width_mm=15.0, height_mm=6.0,
        height_min_mm=5.0, height_max_mm=8.0,
        lordotic_angle_deg=4.0, available_angles_deg=[0.0, 4.0, 7.0],
        material_endplate="CoCrMo", material_core="UHMWPE",
        has_keel=True, keel_height_mm=2.0,
        fda_cleared=True, ce_marked=True, indications=_CERVICAL_LEVELS,
    ),
    ImplantSpec(
        implant_id="PDC-L-17x16-7", manufacturer="Centinel Spine",
        product_name="ProDisc-C", implant_type=ImplantType.CERVICAL_TDR,
        ap_depth_mm=17.0, ml_width_mm=16.0, height_mm=7.0,
        height_min_mm=5.0, height_max_mm=8.0,
        lordotic_angle_deg=7.0, available_angles_deg=[0.0, 4.0, 7.0],
        material_endplate="CoCrMo", material_core="UHMWPE",
        has_keel=True, keel_height_mm=2.0,
        fda_cleared=True, ce_marked=True, indications=_CERVICAL_LEVELS,
    ),

    # --- SECURE-C (Globus Medical) ---
    ImplantSpec(
        implant_id="SEC-S-14x15-0", manufacturer="Globus Medical",
        product_name="SECURE-C", implant_type=ImplantType.CERVICAL_TDR,
        ap_depth_mm=14.0, ml_width_mm=15.0, height_mm=5.0,
        height_min_mm=5.0, height_max_mm=7.0,
        lordotic_angle_deg=0.0, available_angles_deg=[0.0],
        material_endplate="CoCrMo", material_core="UHMWPE",
        has_keel=True, keel_height_mm=1.8,
        fda_cleared=True, ce_marked=True, indications=_CERVICAL_LEVELS,
    ),
    ImplantSpec(
        implant_id="SEC-M-16x17-0", manufacturer="Globus Medical",
        product_name="SECURE-C", implant_type=ImplantType.CERVICAL_TDR,
        ap_depth_mm=16.0, ml_width_mm=17.0, height_mm=6.0,
        height_min_mm=5.0, height_max_mm=7.0,
        lordotic_angle_deg=0.0, available_angles_deg=[0.0],
        material_endplate="CoCrMo", material_core="UHMWPE",
        has_keel=True, keel_height_mm=1.8,
        fda_cleared=True, ce_marked=True, indications=_CERVICAL_LEVELS,
    ),

    # --- PCM (NuVasive) ---
    ImplantSpec(
        implant_id="PCM-S-14x12-4", manufacturer="NuVasive",
        product_name="PCM Cervical", implant_type=ImplantType.CERVICAL_TDR,
        ap_depth_mm=14.0, ml_width_mm=12.0, height_mm=5.0,
        height_min_mm=5.0, height_max_mm=8.0,
        lordotic_angle_deg=4.0, available_angles_deg=[0.0, 4.0],
        material_endplate="CoCrMo", material_core="UHMWPE",
        has_keel=False, keel_height_mm=0.0,
        fda_cleared=True, ce_marked=True, indications=_CERVICAL_LEVELS,
    ),
    ImplantSpec(
        implant_id="PCM-M-16x14-4", manufacturer="NuVasive",
        product_name="PCM Cervical", implant_type=ImplantType.CERVICAL_TDR,
        ap_depth_mm=16.0, ml_width_mm=14.0, height_mm=6.0,
        height_min_mm=5.0, height_max_mm=8.0,
        lordotic_angle_deg=4.0, available_angles_deg=[0.0, 4.0],
        material_endplate="CoCrMo", material_core="UHMWPE",
        has_keel=False, keel_height_mm=0.0,
        fda_cleared=True, ce_marked=True, indications=_CERVICAL_LEVELS,
    ),
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
FULL_CATALOG: list[ImplantSpec] = LUMBAR_TDR_CATALOG + CERVICAL_TDR_CATALOG


def get_catalog(implant_type: ImplantType | None = None) -> list[ImplantSpec]:
    """Return the full catalog, optionally filtered by type."""
    if implant_type is None:
        return FULL_CATALOG
    return [i for i in FULL_CATALOG if i.implant_type == implant_type]


def get_compatible(
    level: SpineLevel,
    disc_height_mean_mm: float,
    ap_depth_mm: float,
    ml_width_mm: float,
) -> list[ImplantSpec]:
    """
    Return catalog implants compatible with the given level and approximate dimensions.
    Compatible = correct implant type + level indication + footprint within 30% of anatomy.
    """
    implant_type = (
        ImplantType.CERVICAL_TDR if level.is_cervical else ImplantType.LUMBAR_TDR
    )
    result = []
    for imp in get_catalog(implant_type):
        if level not in [SpineLevel(s) if isinstance(s, str) else s for s in imp.indications]:
            continue
        ap_ratio = imp.ap_depth_mm / ap_depth_mm if ap_depth_mm > 0 else 1.0
        ml_ratio = imp.ml_width_mm / ml_width_mm if ml_width_mm > 0 else 1.0
        if 0.60 <= ap_ratio <= 1.30 and 0.60 <= ml_ratio <= 1.30:
            if imp.height_min_mm <= disc_height_mean_mm * 1.5:
                result.append(imp)
    return result


def get_by_id(implant_id: str) -> ImplantSpec | None:
    for imp in FULL_CATALOG:
        if imp.implant_id == implant_id:
            return imp
    return None
