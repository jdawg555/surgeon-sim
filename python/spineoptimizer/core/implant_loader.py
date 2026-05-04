"""
Load implant CAD files from a user-specified folder.

Supports:
  - .step / .stp  — CadQuery or OCC bounding box extraction
  - .stl          — trimesh bounding box extraction
  - .json sidecar — explicit spec (same stem as CAD file, e.g. ProDiscL_M.json)

Sidecar JSON format (all fields optional except product_name):
{
  "product_name":    "ProDisc-L",
  "manufacturer":    "Centinel Spine",
  "implant_type":    "lumbar_tdr",        // or "cervical_tdr"
  "ap_depth_mm":     36.0,
  "ml_width_mm":     40.0,
  "height_mm":       10.0,
  "height_min_mm":   9.0,
  "height_max_mm":   14.0,
  "lordotic_angle_deg": 6.0,
  "available_angles_deg": [0, 6],
  "material_endplate": "CoCrMo",
  "material_core":   "UHMWPE",
  "has_keel":        true,
  "keel_height_mm":  3.5,
  "fda_cleared":     true,
  "ce_marked":       true,
  "indications":     ["L3-L4", "L4-L5", "L5-S1"]
}

If no sidecar exists, dimensions are estimated from the CAD geometry bounding box.
"""
from __future__ import annotations
import json
import logging
import math
from pathlib import Path
from typing import Optional

from .models import ImplantSpec, ImplantType, SpineLevel

log = logging.getLogger(__name__)

_SUPPORTED_CAD = {".step", ".stp", ".stl"}

# Fallback indications when not specified in sidecar
_DEFAULT_LUMBAR  = [SpineLevel.L3_L4, SpineLevel.L4_L5, SpineLevel.L5_S1]
_DEFAULT_CERVICAL = [SpineLevel.C3_C4, SpineLevel.C4_C5, SpineLevel.C5_C6, SpineLevel.C6_C7]


def _guess_type_from_dims(ap: float, ml: float, h: float) -> ImplantType:
    """Guess lumbar vs cervical from bounding-box size."""
    max_dim = max(ap, ml)
    if max_dim < 22:
        return ImplantType.CERVICAL_TDR
    return ImplantType.LUMBAR_TDR


def _bbox_from_stl(path: Path) -> Optional[tuple[float, float, float]]:
    """Return (ap_depth, ml_width, height) from STL bounding box."""
    try:
        import trimesh
        mesh = trimesh.load(str(path), force="mesh")
        if hasattr(mesh, "geometry"):
            geoms = list(mesh.geometry.values())
            if not geoms:
                return None
            import trimesh as tm
            mesh = tm.util.concatenate(geoms)
        if mesh is None or mesh.is_empty:
            return None
        ext = mesh.extents  # [dx, dy, dz]
        return float(ext[1]), float(ext[0]), float(ext[2])  # AP, ML, H
    except Exception as exc:
        log.warning(f"trimesh failed on {path.name}: {exc}")
        return None


def _bbox_from_step(path: Path) -> Optional[tuple[float, float, float]]:
    """Return (ap_depth, ml_width, height) from STEP file via CadQuery."""
    try:
        import cadquery as cq
        result = cq.importers.importStep(str(path))
        bb = result.val().BoundingBox()
        return float(bb.ylen), float(bb.xlen), float(bb.zlen)
    except Exception as exc:
        log.warning(f"CadQuery STEP bbox failed on {path.name}: {exc}")
        return None


def _load_sidecar(json_path: Path) -> dict:
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as exc:
        log.warning(f"Could not read sidecar {json_path.name}: {exc}")
        return {}


def load_implant_from_file(cad_path: Path) -> Optional[ImplantSpec]:
    """
    Load a single implant from a CAD file (+ optional sidecar JSON).
    Returns None if the file cannot be parsed.
    """
    cad_path = Path(cad_path)
    if cad_path.suffix.lower() not in _SUPPORTED_CAD:
        return None

    # Try sidecar
    sidecar_path = cad_path.with_suffix(".json")
    meta = _load_sidecar(sidecar_path) if sidecar_path.exists() else {}

    # Get bounding box from geometry if dimensions not in sidecar
    ap = meta.get("ap_depth_mm")
    ml = meta.get("ml_width_mm")
    h  = meta.get("height_mm")

    if None in (ap, ml, h):
        suffix = cad_path.suffix.lower()
        bbox = (
            _bbox_from_stl(cad_path) if suffix == ".stl"
            else _bbox_from_step(cad_path)
        )
        if bbox:
            ap_b, ml_b, h_b = bbox
            ap = ap or round(ap_b, 1)
            ml = ml or round(ml_b, 1)
            h  = h  or round(h_b, 1)
        else:
            ap = ap or 35.0
            ml = ml or 40.0
            h  = h  or 10.0

    ap, ml, h = float(ap), float(ml), float(h)

    # Determine implant type
    type_str = meta.get("implant_type", "")
    if type_str == "lumbar_tdr":
        imp_type = ImplantType.LUMBAR_TDR
    elif type_str == "cervical_tdr":
        imp_type = ImplantType.CERVICAL_TDR
    else:
        imp_type = _guess_type_from_dims(ap, ml, h)

    # Indications
    raw_inds = meta.get("indications", [])
    if raw_inds:
        indications = []
        for s in raw_inds:
            try:
                indications.append(SpineLevel(s))
            except ValueError:
                pass
    else:
        indications = (
            _DEFAULT_CERVICAL if imp_type == ImplantType.CERVICAL_TDR
            else _DEFAULT_LUMBAR
        )

    implant_id = f"CUSTOM-{cad_path.stem}"
    product_name = meta.get("product_name", cad_path.stem.replace("_", " ").replace("-", " "))

    angles = meta.get("available_angles_deg", [0.0, 6.0])
    if not angles:
        angles = [0.0]

    return ImplantSpec(
        implant_id=implant_id,
        manufacturer=meta.get("manufacturer", "Custom / Uploaded"),
        product_name=product_name,
        implant_type=imp_type,
        ap_depth_mm=ap,
        ml_width_mm=ml,
        height_mm=h,
        height_min_mm=float(meta.get("height_min_mm", max(5.0, h - 3.0))),
        height_max_mm=float(meta.get("height_max_mm", h + 4.0)),
        lordotic_angle_deg=float(meta.get("lordotic_angle_deg", angles[0])),
        available_angles_deg=angles,
        material_endplate=meta.get("material_endplate", "Unknown"),
        material_core=meta.get("material_core", "Unknown"),
        has_keel=bool(meta.get("has_keel", True)),
        keel_height_mm=float(meta.get("keel_height_mm", 3.0)),
        fda_cleared=bool(meta.get("fda_cleared", False)),
        ce_marked=bool(meta.get("ce_marked", False)),
        indications=indications,
    )


def load_implants_from_folder(folder: Path) -> tuple[list[ImplantSpec], list[str]]:
    """
    Scan a folder for CAD files and return (implants, errors).
    Skips JSON files (those are sidecars).
    """
    folder = Path(folder)
    implants: list[ImplantSpec] = []
    errors: list[str] = []

    cad_files = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in _SUPPORTED_CAD
    ]

    if not cad_files:
        return [], [f"No CAD files (.step/.stp/.stl) found in {folder}"]

    for cad_file in sorted(cad_files):
        try:
            imp = load_implant_from_file(cad_file)
            if imp:
                imp._cad_path = cad_file  # attach path for 3D viewer loading
                implants.append(imp)
                log.info(f"Loaded implant: {imp.product_name} from {cad_file.name}")
            else:
                errors.append(f"Skipped: {cad_file.name}")
        except Exception as exc:
            errors.append(f"Error loading {cad_file.name}: {exc}")
            log.warning(f"Failed to load {cad_file}: {exc}")

    return implants, errors
