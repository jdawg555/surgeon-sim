"""Marching cubes per-label, plus mesh cleanup.

scikit-image gives us marching_cubes; trimesh handles decimation, smoothing,
and is also our glTF writer (see export.py). Both are widely-used libraries
with permissive licenses and pure-Python fallbacks where needed.

We mesh each label as its own structure rather than producing one big
multi-material mesh — Unity loads each as its own GameObject so we can
toggle/highlight structures independently in the sim.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import trimesh
from skimage import measure

from case_pipeline.phantom import LABEL_NAMES, MATERIAL_HINTS, PhantomVolume


# Per-label decimation targets. Bone meshes need more triangles than the
# skin envelope; cord is small. These are upper bounds — final counts will
# be lower if the source mask is small.
_DECIMATE_TARGETS: dict[str, int] = {
    "skin": 8000,
    "soft_tissue": 12000,
    "vertebral_body": 6000,
    "disc": 2000,
    "dura": 2000,
    "spinal_cord": 1500,
}

_LAPLACIAN_ITERS: dict[str, int] = {
    "skin": 6,
    "soft_tissue": 8,
    "vertebral_body": 2,
    "disc": 4,
    "dura": 6,
    "spinal_cord": 6,
}


@dataclass(frozen=True)
class StructureMesh:
    name: str
    material_hint: str
    mesh: trimesh.Trimesh


def extract_meshes(volume: PhantomVolume) -> list[StructureMesh]:
    """Extract one mesh per non-background label, in voxel order.

    Skips labels that are absent from the volume (e.g. cord above L2 if
    only S1-L1 is meshed). Vertices are returned in patient mm coordinates.
    """

    voxels = volume.voxels
    spacing = (volume.spacing_mm,) * 3
    origin_mm = volume.affine[:3, 3]

    meshes: list[StructureMesh] = []
    for label_id, name in LABEL_NAMES.items():
        mask = voxels == label_id
        if not mask.any():
            continue

        # marching_cubes wants (Z, Y, X). Pad by 1 so the mesh closes at
        # volume edges; otherwise structures touching the boundary leak.
        padded = np.pad(mask, 1, mode="constant", constant_values=False)
        verts_zyx, faces, _normals, _values = measure.marching_cubes(
            padded.astype(np.float32),
            level=0.5,
            spacing=spacing,
        )
        # Undo the padding offset and remap (Z, Y, X) -> (X, Y, Z) for trimesh.
        verts_zyx -= np.array(spacing, dtype=np.float32)
        verts_xyz = verts_zyx[:, [2, 1, 0]] + origin_mm.astype(np.float32)

        mesh = trimesh.Trimesh(vertices=verts_xyz, faces=faces, process=False)
        mesh = _cleanup(mesh, name)

        meshes.append(
            StructureMesh(
                name=name,
                material_hint=MATERIAL_HINTS[label_id],
                mesh=mesh,
            )
        )

    return meshes


def _cleanup(mesh: trimesh.Trimesh, name: str) -> trimesh.Trimesh:
    """Decimate + smooth + drop tiny disconnected components."""

    # Drop disconnected fragments smaller than 1% of the largest. Marching
    # cubes can produce stray voxel-size islands at noisy edges.
    components = mesh.split(only_watertight=False)
    if len(components) > 1:
        biggest = max(c.area for c in components)
        kept = [c for c in components if c.area >= biggest * 0.01]
        mesh = trimesh.util.concatenate(kept) if kept else mesh

    target = _DECIMATE_TARGETS.get(name, 4000)
    if len(mesh.faces) > target:
        # Quest 3 cannot ship 800k-tri meshes; decimation is mandatory, not
        # a nice-to-have. trimesh dispatches to `fast-simplification` (pure
        # C++, MIT) which is declared in case_pipeline/README.md.
        mesh = mesh.simplify_quadric_decimation(face_count=target)

    iters = _LAPLACIAN_ITERS.get(name, 4)
    if iters > 0:
        trimesh.smoothing.filter_laplacian(mesh, lamb=0.5, iterations=iters)

    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()
    return mesh
