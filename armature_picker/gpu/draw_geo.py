import gpu
from bpy.types import Object, Mesh
from gpu import state
from gpu.types import GPUShader, GPUBatch
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from bgl import glEnable, GL_POLYGON_SMOOTH, glDisable

import numpy as np

from ..utils.geometry import is_inside_triangle
from ..utils.iter import iter_grouper
from .draw import RGBA, SHADER_UNIFORM_COLOR, SHADERS #, get_batch_from_cache, set_batch_to_cache

# ----------------------------------------------------------------


_geo_cache: dict[str, 'Geometry'] = {}


class Geometry:
    uuid: str
    origin: np.ndarray

    coords_rel: np.ndarray
    coords: np.ndarray
    indices: np.ndarray

    batch: GPUBatch


    @classmethod
    def get(cls, node, safe_context: bool = True) -> 'Geometry':
        if (geo := _geo_cache.get(node.uuid, None)) is not None:
            if safe_context:
                if node.dirty_geo:
                    geo.update_geometry(node)
                    geo.update_batch(node)
                elif node.dirty:
                    geo.update_batch(node)
            return geo
        _geo_cache[node.uuid] = cls(node)
        return _geo_cache[node.uuid]

    def __init__(self, node) -> None:
        self.uuid = node.uuid
        self.update_geometry(node)
        self.update_batch(node)

    def update_origin(self, object: Object) -> None:
        self.origin = np.array((object.location.x, object.location.y))

    def update_geometry(self, node) -> None:
        self.update_origin(node.object)
        mesh: Mesh = node.object.data
        mesh.calc_loop_triangles()
        vertices = np.empty((len(mesh.vertices), 3), 'f')
        indices = np.empty((len(mesh.loop_triangles), 3), 'i')
        mesh.vertices.foreach_get(
            "co", np.reshape(vertices, len(mesh.vertices) * 3))
        mesh.loop_triangles.foreach_get(
            "vertices", np.reshape(indices, len(mesh.loop_triangles) * 3))
        self.indices = indices
        self.coords_rel = vertices[:, :2].round(2)

    def update_batch(self, node) -> None:
        scale = node.geo_scale
        self.coords = self.coords_rel * scale + np.array(node.rect_transform.origin)
        # print(self.coords)
        self.batch = batch_for_shader(
            SHADER_UNIFORM_COLOR, 'TRIS',
            {"pos": self.coords.tolist()}, # , "color": vertex_colors
            indices=self.indices.tolist(),
        )


    def on_hover(self, p: Vector) -> bool:
        co = self.coords
        for tri_indices in self.indices:
            A, B, C = tri_indices
            if is_inside_triangle(*co[A], *co[B], *co[C], *p):
                return True
        return False


    def draw(self, node) -> None:
        state.blend_set('ALPHA')
        SHADER_UNIFORM_COLOR.uniform_float('color', node.color)
        self.batch.draw(SHADER_UNIFORM_COLOR)
