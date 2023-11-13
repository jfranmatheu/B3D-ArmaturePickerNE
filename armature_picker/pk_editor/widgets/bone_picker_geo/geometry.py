from bpy.types import PropertyGroup, Mesh, Object
from bpy.props import CollectionProperty, IntVectorProperty, FloatVectorProperty

import numpy as np
from collections import defaultdict

import gpu
from gpu import state
from gpu.types import GPUShader, GPUBatch, GPUFrameBuffer
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, geometry

from armature_picker.utils.geometry import check_point_in_convex_hull, is_point_inside_triangle
from armature_picker.gpu.draw import RGBA, SHADERS, SHADER_POLYLINE_UNIFORM_COLOR

# ----------------------------------------------------------------


class RectTranform:
    origin: Vector

class BonePickerGeo:
    geo_scale: float
    geometry: 'AP_PG_Geometry'
    color: tuple[float, float, float, float]
    geo_precision: str
    rect_transform: RectTranform


default_coords = (
    (-1, 1),
    (-1, -1),
    (1, -1),
    (1, 1)
)
defaults_indices = (
    (0, 1, 2),
    (2, 3, 0)
)

_batch_cache: dict[int, dict[str, GPUBatch]] = defaultdict(dict)
_instances: dict[int, 'RuntimeGeometryData'] = {}

class RuntimeGeometryData:
    coords: list[tuple[float, float]]

    coords_rel: np.ndarray = None
    indices: tuple[tuple[int, int, int]] = None

    convex_hull_indices: list[int] = None

    _batch: GPUBatch
    _batch_outline: GPUBatch

    @classmethod
    def get(cls, geo: 'AP_PG_Geometry') -> 'RuntimeGeometryData':
        uuid = str(hash(geo))
        if uuid not in _instances:
            _instances[uuid] = cls()
        return _instances[uuid]


    @property
    def convex_hull_coords(self):
        coords = self.coords
        return tuple(coords[idx] for idx in self.convex_hull_indices)

    @property
    def batch(self) -> GPUBatch:
        return _batch_cache[id(self)]['POLY']

    @property
    def batch_outline(self) -> GPUBatch:
        return _batch_cache[id(self)]['OUTLINE']

    @batch.setter
    def batch(self, batch: GPUBatch) -> None:
        _batch_cache[id(self)]['POLY'] = batch

    @batch_outline.setter
    def batch_outline(self, batch_outline: GPUBatch) -> None:
        _batch_cache[id(self)]['OUTLINE'] = batch_outline

    def __init__(self) -> None:
        ## print("Create Runtime Geometry Data")
        self.available = False

    def update_coords(self, node: BonePickerGeo, geo: 'AP_PG_Geometry') -> None:
        if self.convex_hull_indices is None:
            self.update_convex_hull(geo)

        ## print("UPDATE coords")
        offset = np.array(node.rect_transform.origin)
        coords_rel = geo.coords_rel
        scale = node.geo_scale
        self.coords = (coords_rel * scale + offset).tolist()
        # print(self.coords)

    def update_convex_hull(self, geo: 'AP_PG_Geometry') -> None:
        # UPDATE CONVEX HULL.
        ## print("UPDATE convex_hull_indices")
        self.convex_hull_indices = geometry.convex_hull_2d(geo.coords_rel)

    def update_batch(self, node: BonePickerGeo, geo: 'AP_PG_Geometry') -> None:
        self.update_coords(node, geo)
        ## print("UPDATE batch")

        # print("update_batch")
        batch: GPUBatch = batch_for_shader(
            SHADERS.COLOR_UNIFORM, 'TRIS',
            {"pos": self.coords}, # , "color": vertex_colors
            indices=geo.indices,
        )
        batch.program_set(SHADERS.COLOR_UNIFORM)
        batch_outline: GPUBatch = batch_for_shader(
            SHADERS.COLOR_UNIFORM, 'LINE_LOOP',
            {"pos": self.convex_hull_coords}
        )
        batch_outline.program_set(SHADER_POLYLINE_UNIFORM_COLOR)

        self.batch = batch
        self.batch_outline = batch_outline

        self.available = True


class AP_PG_Vert(PropertyGroup):
    ''' Geometry child for BonePickerGeo Widgets. '''
    co: FloatVectorProperty(name="Vertex Relative-To-Origin Coordinate", default=(0, 0), size=2)


class AP_PG_Tri(PropertyGroup):
    ''' Geometry child for BonePickerGeo Widgets. '''
    vert_indices: IntVectorProperty(name="Tri Vertices Indices", default=(-1, -1, -1), size=3, min=-1)


class AP_PG_Geometry(PropertyGroup):
    ''' Geometry child for BonePickerGeo Widgets. '''
    vertices_coll: CollectionProperty(type=AP_PG_Vert)
    tris_coll: CollectionProperty(type=AP_PG_Tri)
    dimensions: FloatVectorProperty(name="Geometry Dimensions", default=(2, 2), min=0, size=2)
    color: FloatVectorProperty(name="Geometry Color", default=(1, 0.9, 0.1, 1), min=0, max=1, size=4, subtype='COLOR')

    # _coords_rel: np.ndarray = None
    # _indices: tuple[tuple[int, int, int]] = None

    @property
    def center(self) -> tuple[float, float]:
        return Vector(self.dimensions) * 0.5

    @property
    def coords_rel(self):
        return np.array([tuple(v.co) for v in self.vertices_coll])
        if self.runtime.coords_rel is None:
            self.runtime.coords_rel = np.array([tuple(v.co) for v in self.vertices_coll])
        return self.runtime.coords_rel

    @property
    def indices(self):
        return tuple([tuple(tri.vert_indices) for tri in self.tris_coll])
        if self.runtime.indices is None:
            self.runtime.indices = tuple([tuple(tri.vert_indices) for tri in self.tris_coll])
        return self.runtime.indices

    @indices.setter
    def indices(self, indices_list: list) -> None:
        # print("Set Tris Indices", indices_list)
        self.tris_coll.clear()
        add_tri = self.tris_coll.add
        for vert_indices in indices_list:
            add_tri().vert_indices = vert_indices
        # self.runtime.indices = indices_list

    @coords_rel.setter
    def coords_rel(self, vertices_list: list) -> None:
        ## print("UPDATE coords_rel")
        # print("Set Coordinates Rel", vertices_list)
        self.vertices_coll.clear()
        add_vert = self.vertices_coll.add
        for co in vertices_list: # Discard Z coordinate.
            add_vert().co = tuple(co)

        # self.runtime.coords = vertices_list

        self.update_dimensions()

        self.runtime.update_convex_hull(self)


    @property
    def runtime(self) -> RuntimeGeometryData:
        return RuntimeGeometryData.get(self)


    # ----------------------------------------------------------------

    def init(self, node: BonePickerGeo | None = None) -> None:
        ## print("INIT")

        # LOAD DEFAULT COORDS/INDICES.
        self.coords_rel = default_coords
        self.indices = defaults_indices
        # self.dimensions = (2, 2)
        # self.runtime.convex_hull_indices = (0, 1, 2, 3)

        if node is not None:
            self.update_batch(node)

    def update(self, node: BonePickerGeo, mesh_object: Object, update_batch: bool = True) -> None:
        mesh: Mesh = mesh_object.data

        # UPDATE COLOR.
        self.color = mesh_object.color

        # UPDATE MESH INDICES.
        mesh.calc_loop_triangles()
        indices = np.empty((len(mesh.loop_triangles), 3), 'i')
        mesh.loop_triangles.foreach_get(
            "vertices", np.reshape(indices, len(mesh.loop_triangles) * 3))
        self.indices = indices.tolist()

        # UPDATE MESH COORDINATES.
        vertices = np.empty((len(mesh.vertices), 3), 'f')
        mesh.vertices.foreach_get(
            "co", np.reshape(vertices, len(mesh.vertices) * 3))
        self.coords_rel = vertices[:,0:2].tolist()

        # UPDATE BATCH.
        if update_batch:
            self.update_batch(node)

        ## print("UPDATE:")
        ## print("\t> Vertices Relative:", self.coords_rel)
        ## print("\t> Coords:", self.runtime.coords)
        ## print("\t> Indices:", self.indices)
        ## print("\t> Convex Hull Indices:", self.runtime.convex_hull_indices)


        # print(vertices[:,0:2].tolist())
        # print(indices.tolist())

        # print("........")

        # print(self.coords_rel.tolist())
        # print(self.indices.tolist())

    def update_dimensions(self) -> None:
        ## print("UPDATE DIMENSIONS!")
        vertices = self.coords_rel

        min_x = min(vertices, key=lambda co: co[0])[0]
        max_x = max(vertices, key=lambda co: co[0])[0]
        min_y = min(vertices, key=lambda co: co[1])[1]
        max_y = max(vertices, key=lambda co: co[1])[1]

        self.dimensions = (max_x - min_x, max_y - min_y)

    def update_batch(self, node: BonePickerGeo) -> None:
        self.runtime.update_batch(node, self)


    def on_hover(self, node: BonePickerGeo, p: Vector, force_convex_hull: bool = False) -> bool:
        if not self.runtime.available:
            return False

        # ConvexHull / FAST Method.
        if node.geo_precision == 'CONVEX' or force_convex_hull:
            convex_hull = self.runtime.convex_hull_coords
            if len(convex_hull) == 3:
                A, B, C = convex_hull
                if is_point_inside_triangle(p, A, B, C):
                    return True
                return False
            if check_point_in_convex_hull(convex_hull, p):
                return True
            return False
        # Precise / EXACT Method.
        co = self.runtime.coords
        if co is None:
            return False
        for tri_indices in self.indices:
            A, B, C = tri_indices
            if is_point_inside_triangle(p, co[A], co[B], co[C]):
                return True
        return False


    def draw(self, node: BonePickerGeo, color: RGBA, hovered: bool) -> None:
        if not self.runtime.available:
            ## print("No batch")
            self.update_batch(node)
        state.blend_set('ALPHA')
        SHADERS.COLOR_UNIFORM.uniform_float('u_color', Vector(color) * 1.2 if hovered else color)
        self.runtime.batch.draw()

    def draw_outline(self, _node: BonePickerGeo, color: RGBA, line_thickness: float = 2.0) -> None:
        if not self.runtime.available:
            ## print("No batch_outline")
            return
        fb: GPUFrameBuffer = gpu.state.active_framebuffer_get()
        _x, _y, w, h = fb.viewport_get()
        d = dict(lineWidth=line_thickness, color=color, viewportSize=(w, h))
        for key, value in d.items():
            SHADER_POLYLINE_UNIFORM_COLOR.uniform_float(key, value)
        self.runtime.batch_outline.draw()
