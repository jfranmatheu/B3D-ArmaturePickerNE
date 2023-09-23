from math import hypot, dist, cos, sin, acos
from mathutils import Vector, Matrix
from dataclasses import dataclass
from bpy.types import Object
import bmesh
from bmesh.types import BMesh, BMFace

import numpy as np

from .math import dotproduct, length, cross


@dataclass
class Box:
    x_min: int
    y_min: int
    x_max: int
    y_max: int

    @property
    def pos(self) -> Vector:
        return Vector((self.x_min, self.y_min))

    @property
    def min(self) -> Vector:
        return Vector((self.x_min, self.y_min))

    @property
    def max(self) -> Vector:
        return Vector((self.x_max, self.y_max))

    @property
    def size(self) -> Vector:
        return Vector((self.x_max - self.x_min, self.y_max - self.y_min))


def distance_between(_p1, _p2):
    return dist(_p1, _p2)
    return hypot(_p1[0] - _p2[0], _p1[1] - _p2[1])

def point_inside_circle(point, c, radius):
    return distance_between(point, c) < radius


def get_point_in_rect_space(p: Vector, rect, invert: bool = False) -> Vector:
    if rect.rotation != 0:
        _p = p.copy()
        # rotate around rectangle center by -rectAngle
        s = sin(rect.rotation) if invert else sin(-rect.rotation)
        c = cos(rect.rotation) if invert else cos(-rect.rotation)
        rect_center: Vector = Vector(rect.origin)
        # set origin to rect center
        _p -= rect_center
        # rotate
        _p = Vector((p.x * c - p.y * s, p.x * s + p.y * c))
        # put origin back
        _p += rect_center
    else:
        _p = p.copy()

    return _p


def rect_overlap(rect_A, rect_B) -> bool:
    R1 = (rect_A.x_min, rect_A.y_min, rect_A.x_max, rect_A.y_max)
    R2 = (rect_B.x_min, rect_B.y_min, rect_B.x_max, rect_B.y_max)
    if ((R1[0]>=R2[2]) or (R1[2]<=R2[0]) or (R1[3]<=R2[1]) or (R1[1]>=R2[3])):
        return False
    return True


# A utility function to calculate area
# of triangle formed by (x1, y1),
# (x2, y2) and (x3, y3)
def triangle_area(x1, y1, x2, y2, x3, y3):
    return abs((x1 * (y2 - y3) + x2 * (y3 - y1)
                + x3 * (y1 - y2)) / 2.0)

# A function to check whether point P(x, y)
# lies inside the triangle formed by
# A(x1, y1), B(x2, y2) and C(x3, y3)
def is_inside_triangle(x1, y1, x2, y2, x3, y3, x, y):
    # Calculate area of triangle ABC
    A = triangle_area(x1, y1, x2, y2, x3, y3)
    # Calculate area of triangle PBC
    A1 = triangle_area(x, y, x2, y2, x3, y3)
    # Calculate area of triangle PAC
    A2 = triangle_area(x1, y1, x, y, x3, y3)
    # Calculate area of triangle PAB
    A3 = triangle_area(x1, y1, x2, y2, x, y)
    # Check if sum of A1, A2 and A3
    # is same as A
    if (A == A1 + A2 + A3):
        return True
    else:
        return False



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


def check_point_in_convex_hull(convex_hull: list[Vector], point: Vector) -> bool:
    def _is_inside() -> bool:
        for idx in range(1, len(convex_hull)):
            if cross(convex_hull[idx - 1], convex_hull[idx], point) < 0:
                return False
        return True

    # visualize results
    # draw_results(convex_hull, point, _is_inside())
    return _is_inside()


def get_center(pos: Vector, size: Vector) -> Vector:
    return pos + size * 0.5


def rotate_point(p: Vector, o: Vector, angle: float) -> Vector:
    if angle == 0:
        return p
    qx = o.x + cos(angle) * (p.x - o.x) - sin(angle) * (p.y - o.y)
    qy = o.y + sin(angle) * (p.x - o.x) + cos(angle) * (p.y - o.y)
    return Vector((qx, qy))


def angle_between(v1: Vector, v2: Vector) -> float:
    return acos(dotproduct(v1, v2) / (length(v1) * length(v2)))


def distance_between(_p1, _p2) -> float:
    return hypot(_p1[0] - _p2[0], _p1[1] - _p2[1])
    #return math.sqrt((_p1[1] - _p1[0])**2 + (_p2[1] - _p2[0])**2)

def direction_from_to(_p1: Vector, _p2: Vector, _norm=True) -> Vector:
    if _norm:
        return (_p1 - _p2).normalized()
    else:
        return _p1 - _p2


def unit_vector(vector):
    """ Returns the unit vector of the vector"""
    return vector / np.linalg.norm(vector)

def angle_signed(vector1, vector2):
    """ Returns the angle in radians between given vectors"""
    v1_u = unit_vector(vector1)
    v2_u = unit_vector(vector2)
    minor = np.linalg.det(
        np.stack((v1_u[-2:], v2_u[-2:]))
    )
    if minor == 0:
        return 0
        raise NotImplementedError('Too odd vectors =(')
    return np.sign(minor) * np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))


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
