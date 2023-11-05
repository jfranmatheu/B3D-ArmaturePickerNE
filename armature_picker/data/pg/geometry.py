from bpy.types import PropertyGroup, Mesh
from bpy.props import CollectionProperty, IntVectorProperty, FloatVectorProperty

import numpy as np


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


class AP_PG_Vert(PropertyGroup):
    ''' Geometry data for BonePickerGeo Widgets. '''
    co: FloatVectorProperty(name="Vertex Relative-To-Origin Coordinate", default=(0, 0), size=2)


class AP_PG_Tri(PropertyGroup):
    ''' Geometry data for BonePickerGeo Widgets. '''
    vert_indices: IntVectorProperty(name="Tri Vertices Indices", default=(-1, -1, -1), size=3, min=-1)


class AP_PG_Geometry(PropertyGroup):
    ''' Geometry data for BonePickerGeo Widgets. '''
    vertices_coll: CollectionProperty(type=AP_PG_Vert)
    tris_coll: CollectionProperty(type=AP_PG_Tri)
    dimensions: FloatVectorProperty(name="Geometry Dimensions", default=(10, 10), min=10, size=2)
    color: FloatVectorProperty(name="Geometry Color", default=(1, 0.9, 0.1, 1), min=0, max=1, size=4, subtype='COLOR')

    @property
    def coords_rel(self):
        return np.array([tuple(v.co) for v in self.vertices_coll])

    @property
    def indices(self):
        return np.array([tuple(tri.vert_indices) for tri in self.tris_coll])

    def init(self) -> None:
        add_vert = self.vertices_coll.add
        add_tri = self.tris_coll.add
        for co in default_coords:
            add_vert().co = co
        for vert_indices in defaults_indices:
            add_tri().vert_indices = vert_indices

    def update(self, mesh: Mesh) -> None:
        self.clear()

        mesh.calc_loop_triangles()
        vertices = np.empty((len(mesh.vertices), 3), 'f')
        indices = np.empty((len(mesh.loop_triangles), 3), 'i')
        mesh.vertices.foreach_get(
            "co", np.reshape(vertices, len(mesh.vertices) * 3))
        mesh.loop_triangles.foreach_get(
            "vertices", np.reshape(indices, len(mesh.loop_triangles) * 3))

        add_vert = self.vertices_coll.add
        add_tri = self.tris_coll.add
        for co in vertices[:,0:2]: # Discard Z coordinate.
            add_vert().co = tuple(co)
        for vert_indices in indices.tolist():
            add_tri().vert_indices = vert_indices

        # print(vertices[:,0:2].tolist())
        # print(indices.tolist())

        # print("........")

        # print(self.coords_rel.tolist())
        # print(self.indices.tolist())


    def clear(self) -> None:
        self.vertices_coll.clear()
        self.tris_coll.clear()
