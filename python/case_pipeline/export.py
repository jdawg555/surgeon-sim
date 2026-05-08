"""Write meshes + manifest to disk in a layout the Unity Addressables side
will consume.

Output directory layout:

    <out_dir>/
      manifest.json
      meshes/
        skin.glb
        soft_tissue.glb
        vertebral_body.glb
        disc.glb
        dura.glb
        spinal_cord.glb

glTF binary (.glb) is the right interchange format here: single-file per
structure, well-supported by Unity's `glTFast` importer, no Y-up/Z-up
fights at load time. We emit one structure per file rather than one big
scene because the Unity loader treats each as an addressable.
"""

from __future__ import annotations

import os

from case_pipeline.meshing import StructureMesh
from case_pipeline.models import CaseManifest, StructureManifest


PIPELINE_VERSION = "0.1.0"


def write_meshes(meshes: list[StructureMesh], out_dir: str) -> list[StructureManifest]:
    """Write each structure as a .glb under `<out_dir>/meshes/` and return
    manifest entries pointing at them.
    """

    meshes_dir = os.path.join(out_dir, "meshes")
    os.makedirs(meshes_dir, exist_ok=True)

    entries: list[StructureManifest] = []
    for sm in meshes:
        rel = os.path.join("meshes", f"{sm.name}.glb")
        abs_path = os.path.join(out_dir, rel)
        sm.mesh.export(abs_path, file_type="glb")
        entries.append(
            StructureManifest(
                name=sm.name,
                mesh_path=rel,
                vertex_count=int(len(sm.mesh.vertices)),
                triangle_count=int(len(sm.mesh.faces)),
                material_hint=sm.material_hint,
            )
        )
    return entries


def write_manifest(
    manifest: CaseManifest,
    out_dir: str,
) -> str:
    path = os.path.join(out_dir, "manifest.json")
    manifest.write(path)
    return path
