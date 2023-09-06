from math import hypot, dist
from mathutils import Vector, Matrix
from dataclasses import dataclass
from bpy.types import Object
import bmesh
from bmesh.types import BMesh, BMFace


def distance_between(_p1, _p2):
    return dist(_p1, _p2)
    return hypot(_p1[0] - _p2[0], _p1[1] - _p2[1])

def point_inside_circle(point, c, radius):
    return distance_between(point, c) < radius 

def point_inside_rect(_p, _pos, _size):
    return ((_pos[0] + _size[0]) > _p[0] > _pos[0]) and ((_pos[1] + _size[1]) > _p[1] > _pos[1])


@dataclass
class Circle:
    origin: Vector
    radius: float

    def point_inside(self, point: Vector) -> bool:
        return point_inside_circle(self.origin, self.radius, point)


def object_to_face(face_ob: Object, ob_to_align: Object):
    bm: BMesh = BMesh.from_object(face_ob)
    face: BMFace = bm.faces[0]

    n = face.normal
    t = face.calc_tangent_edge().normalized()
    bt = n.cross(t).normalized()
    mat = face_ob.matrix_world @ Matrix([t, bt, n]).transposed().to_4x4()

    ob_to_align.matrix_world = mat @ ob_to_align.matrix_world
    bm.free()
