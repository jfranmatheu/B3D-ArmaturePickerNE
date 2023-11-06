import gpu
from bpy.types import Object, Mesh
from gpu import state
from gpu.types import GPUShader, GPUBatch
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, geometry

import numpy as np

from ..utils.geometry import is_inside_triangle, check_point_in_convex_hull
from ..utils.iter import iter_grouper
from .draw import RGBA, SHADERS, SHADER_POLYLINE_UNIFORM_COLOR #, get_batch_from_cache, set_batch_to_cache
from ..data.pg.geometry import AP_PG_Geometry

# ----------------------------------------------------------------


_geo_cache: dict[str, 'Geometry'] = {}


class BonePickerGeo:
    uuid: str
    object: Object
    dirty: bool
    dirty_geo: bool
    geo_scale: float
    geometry: AP_PG_Geometry
    color: tuple[float, float, float, float]
    geo_precision: str


class Geometry:
    uuid: str
    origin: np.ndarray

    coords_rel: np.ndarray
    coords: np.ndarray
    indices: np.ndarray

    batch: GPUBatch
    batch_outline: GPUBatch

    convex_hull: tuple
    convex_hull_indices: list[int]

    @property
    def convex_hull(self):
        return tuple(self.coords[idx] for idx in self.convex_hull_indices)


    @classmethod
    def get(cls, node: BonePickerGeo, safe_context: bool = True) -> 'Geometry':
        if (geo := _geo_cache.get(node.uuid, None)) is not None:
            if node.dirty_geo:
                geo.update_geometry(node)
                geo.update_batch(node)
            elif node.dirty:
                geo.update_batch(node)
            return geo
        _geo_cache[node.uuid] = cls(node)
        return _geo_cache[node.uuid]

    def __init__(self, node: BonePickerGeo) -> None:
        self.uuid = node.uuid
        self.update_geometry(node)
        self.update_batch(node)

    def update_geometry(self, node: BonePickerGeo) -> None:
        self.indices = node.geometry.indices
        self.coords_rel = node.geometry.coords_rel # vertices[:, :2].round(2)
        self.convex_hull_indices = geometry.convex_hull_2d(self.coords_rel) # Also used for the outline.

    def update_batch(self, node: BonePickerGeo) -> None:
        scale = node.geo_scale
        self.coords = (self.coords_rel * scale + np.array(node.rect_transform.origin)).tolist()
        # print(self.coords)
        self.batch = batch_for_shader(
            SHADERS.COLOR_UNIFORM, 'TRIS',
            {"pos": self.coords}, # , "color": vertex_colors
            indices=self.indices.tolist(),
        )
        self.batch.program_set(SHADERS.COLOR_UNIFORM)
        self.batch_outline: GPUBatch = batch_for_shader(
            SHADERS.COLOR_UNIFORM, 'LINE_LOOP',
            {"pos": self.convex_hull}
        )
        self.batch_outline.program_set(SHADER_POLYLINE_UNIFORM_COLOR)

    def on_hover(self, node: BonePickerGeo, p: Vector, force_convex_hull: bool = False) -> bool:
        ''' - precision: 'FAST' or 'EXACT' '''
        # ConvexHull / FAST Method.
        if node.geo_precision == 'CONVEX_HULL' or force_convex_hull:
            convex_hull = self.convex_hull
            if len(convex_hull) == 3:
                A, B, C = convex_hull
                if is_inside_triangle(*A, *B, *C, *p):
                    return True
                return False
            if check_point_in_convex_hull(convex_hull, p):
                return True
            return False

        # Precise / EXACT Method.
        co = self.coords
        for tri_indices in self.indices:
            A, B, C = tri_indices
            if is_inside_triangle(*co[A], *co[B], *co[C], *p):
                return True
        return False


    def draw(self, node: BonePickerGeo, color: RGBA, hovered: bool) -> None:
        state.blend_set('ALPHA')
        SHADERS.COLOR_UNIFORM.uniform_float('u_color', Vector(color) * 1.2 if hovered else color)
        self.batch.draw()

    def draw_outline(self, node: BonePickerGeo, color: RGBA, line_thickness: float = 2.0) -> None:
        fb = gpu.state.active_framebuffer_get()
        x, y, w, h = fb.viewport_get()
        d = dict(lineWidth=line_thickness, color=color, viewportSize=(w, h))
        for key, value in d.items():
            SHADER_POLYLINE_UNIFORM_COLOR.uniform_float(key, value)
        self.batch_outline.draw()
