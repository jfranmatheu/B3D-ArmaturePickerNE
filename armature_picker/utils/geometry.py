from math import hypot, dist, cos, sin
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

def point_inside_rect(_p, _pos, _size, _angle=0, origin: Vector | None = None):
    ''' NOTE: '_angle' should be given in radians.
        '_p', '_pos' and '_size' should be Vector type.
        '_pos' should be the lower left corner of the rectangle.
    '''
    if _angle != 0:
        p = _p.copy()
        # rotate around rectangle center by -rectAngle
        s = sin(-_angle)
        c = cos(-_angle)
        if origin is not None:
            rect_center: Vector = origin
        else:
            rect_center: Vector = _pos + _size * 0.5
        # set origin to rect center
        p -= rect_center
        # rotate
        p = Vector((p.x * c - p.y * s, p.x * s + p.y * c))
        # put origin back
        p += rect_center
    else:
        p = _p

    return ((_pos[0] + _size[0]) > p[0] > _pos[0]) and ((_pos[1] + _size[1]) > p[1] > _pos[1])


def get_center(pos: Vector, size: Vector) -> Vector:
    return pos + size * 0.5


def rotate_point(p: Vector, o: Vector, angle: float) -> Vector:
    if angle == 0:
        return p
    qx = o.x + cos(angle) * (p.x - o.x) - sin(angle) * (p.y - o.y)
    qy = o.y + sin(angle) * (p.x - o.x) + cos(angle) * (p.y - o.y)
    return Vector((qx, qy))


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
