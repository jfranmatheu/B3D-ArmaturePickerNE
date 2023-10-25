from .draw import SHADERS, draw_point, just_a_point, Vector, RGBA, GPUShader
from math import sin, cos


SQRT_2 = 1.4142135623730951


def draw_shape(o: Vector, orientation: float, psize: float, stroke_color: RGBA, bg_color: RGBA, line_width: float = 2.0, antialias: float = 1.0, shader: GPUShader = None) -> None:
    u_rotation = Vector((cos(orientation), sin(orientation)))
    v_size = SQRT_2 * psize + 2.0*(line_width + 1.5*antialias)

    just_a_point(
        o, v_size * 0.5,
        shader=shader,
        u_rotation=u_rotation,
        u_size=v_size,
        u_line_width=line_width,
        u_antialias=antialias,
        u_stroke_color=stroke_color,
        u_bg_color=bg_color,
    )


def arrow_ang_90(o: Vector, orientation: float, psize: float, stroke_color: RGBA, bg_color: RGBA, line_width: float = 2.0, antialias: float = 1.0) -> None:
    draw_shape(o, orientation, psize, stroke_color, bg_color, line_width, antialias, SHADERS.SHAPE_ARR_ANG_90)

def chevron(o: Vector, orientation: float, psize: float, stroke_color: RGBA, bg_color: RGBA, line_width: float = 2.0, antialias: float = 1.0) -> None:
    draw_shape(o, orientation, psize, stroke_color, bg_color, line_width, antialias, SHADERS.SHAPE_CHEVRON)
