import bpy
import gpu
import blf
from bpy.types import Image
from gpu import state
from gpu.types import GPUShader, GPUBatch, GPUTexture, GPUOffScreen, GPUVertFormat, GPUVertBuf
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_circle_2d
from mathutils import Vector, Matrix, Euler, Quaternion
from gpu.texture import from_image as get_gputex_from_image

from colorsys import rgb_to_hsv
from uuid import uuid4
from math import cos, sin, radians, pi
import textwrap
from collections import defaultdict
from typing import Tuple
from functools import partial

from .offscreen import draw_offscreen, get_offscreen
from ..utils.geometry import rotate_point
from .shaders import SHADERS
from ..utils.math import map_value


RGBA = Tuple[float, float, float, float]


# ----------------------------------------------------------------

SHADER_UNIFORM_COLOR: GPUShader = gpu.shader.from_builtin('UNIFORM_COLOR')
SHADER_IMAGE: GPUShader = gpu.shader.from_builtin('IMAGE')
SHADER_POLYLINE_UNIFORM_COLOR: GPUShader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')


# ----------------------------------------------------------------

def get_text_dim(text: str, size: int):
    blf.size(0, size)
    return blf.dimensions(0, text)

blf.size(0, 11)
TEXT_11P_HEIGHT = blf.dimensions(0, 'X')[1]


# ----------------------------------------------------------------

_batch_cache: dict[str, dict[str, GPUBatch]] = defaultdict(dict)

def get_batch_from_cache(data_id: str, graphic_id: str) -> GPUBatch | None:
    return _batch_cache[data_id].get(graphic_id, None)

def set_batch_to_cache(data_id: str, graphic_id: str, batch: GPUBatch) -> None:
    _batch_cache[data_id][graphic_id] = batch


# ----------------------------------------------------------------

_gputex_cache: dict[str, GPUTexture] = {}

def get_gputex(bl_image: Image) -> GPUBatch | None:
    if 'uuid' not in bl_image:
        bl_image['uuid'] = uuid4().hex
    if bl_image['uuid'] not in _gputex_cache:
        _gputex_cache[bl_image['uuid']] = get_gputex_from_image(bl_image)
    return _gputex_cache[bl_image['uuid']]


def set_image(image: Image, _shader: SHADERS.IMA) -> bool:
    t=get_gputex(image) if isinstance(image, Image) else image
    if t is None:
        return False
    state.blend_set('ALPHA')
    _shader.uniform_sampler('image', t)
    return True


# ----------------------------------------------------------------

def get_rect_coords(rect) -> dict:
    return {'pos': rect.coords_rotated}

def get_rect_uv_coords(rect) -> dict:
    return {
        'pos': rect.coords_rotated,
        'texco': tex_uv_indices
    }

def get_rect_coords(rect) -> dict:
    return {'pos': rect.coords_rotated}


def get_rect_cage_coords(rect, margin: float = 0) -> dict:
    if margin == 0:
        co = rect.coords_rotated
        return {'pos': (co[0], co[1], co[2], co[3])}

    co = rect.coords
    co_mar = (Vector(co[0]) + Vector((-margin, margin)),
                    Vector(co[1]) + Vector((-margin, -margin)),
                    Vector(co[2]) + Vector((margin, -margin)),
                    Vector(co[3]) + Vector((margin, margin)))
    o = Vector(rect.origin)
    co_mar = tuple(rotate_point(_co, o, rect.rotation) for _co in co_mar)
    return {'pos': co_mar}

def get_cage_coords(x, y, w, h, p) -> dict:
    return {'pos': (
        (x + p, y + h - p),
        (x + p, y + p),
        (x + w - p, y + p),
        (x + w - p, y + h - p)
    )}


# ----------------------------------------------------------------

get_tex_coords = lambda _p, _s: (
    (_p.x,_p.y+_s.y),_p,
    (_p.x+_s.x,_p.y),_p+_s
)
get_rotated_tex_coords = lambda pos, size, origin, angle: tuple(rotate_point(Vector(co), origin, angle).to_tuple() for co in get_tex_coords(pos, size))

tex_uv_indices = ((0,1),(0,0),(1,0),(1,1))
tex_indices = ((0,1,2),(2,3,0))


# ----------------------------------------------------------------

def _draw_batch(batch: GPUBatch, shader: GPUShader, **uniforms) -> None:
    for key, value in uniforms.items():
        shader.uniform_float(key, value)
    batch.draw(shader)


def draw_bb(owner: object, graphic_id: str, bbox: list[Vector], shader: GPUShader, use_uv: bool = False, **uniforms):
    if not owner.dirty and (batch := get_batch_from_cache(owner.uuid, graphic_id)) is not None:
        pass
    else:
        if use_uv:
            _input = {'pos': bbox, 'texco': tex_uv_indices}
        else:
            _input = {'pos': bbox}
        batch = batch_for_shader(shader, 'TRIS',
                                    _input,
                                    indices=tex_indices)
        set_batch_to_cache(owner.uuid, graphic_id, batch)
    _draw_batch(batch, shader, **uniforms)


def draw(owner: object, graphic_id: str, pos: Vector, size: Vector, angle: float, shader: GPUShader, origin: Vector | None = None, dirty: bool | None = None, use_uv: bool = False, wg: bool = False, **uniforms):
    if graphic_id is None:
        is_dirty = True
    else:
        is_dirty = dirty or owner.dirty if dirty is not None else owner.dirty
    if not is_dirty and (batch := get_batch_from_cache(owner.uuid, graphic_id)) is not None:
        pass
    else:
        coords = get_tex_coords(pos, size) if angle == 0 else get_rotated_tex_coords(pos, size, origin if origin is not None else pos+size*0.5, angle)
        if use_uv:
            _input = {'pos': coords, 'texco': tex_uv_indices}
        else:
            _input = {'pos': coords}
        batch = batch_for_shader(shader, 'TRIS',
                                 _input,
                                 indices=tex_indices)
        if graphic_id is not None:
            set_batch_to_cache(owner.uuid, graphic_id, batch)
    if wg:
        shader.uniform_float('u_dimensions', size)
    _draw_batch(batch, shader, **uniforms)


def draw_point(owner: object, graphic_id: str, pos: Vector, psize: float, angle: float, shader: GPUShader, dirty: bool | None = None, **uniforms):
    gpu.state.point_size_set(psize)
    is_dirty = dirty or owner.dirty if dirty is not None else owner.dirty
    if not is_dirty and (batch := get_batch_from_cache(owner.uuid, graphic_id)) is not None:
        pass
    else:
        batch = batch_for_shader(shader, 'POINTS',
                                {'pos': [pos]})
        set_batch_to_cache(owner.uuid, graphic_id, batch)
    _draw_batch(batch, shader, **uniforms)


def draw_node(node: object, graphic_id: str, shader: GPUShader, use_uv: bool = False, wg: bool = False, **uniforms):
    if graphic_id is None:
        is_dirty = True
    else:
        is_dirty = node.dirty
    if not is_dirty and (batch := get_batch_from_cache(node.uuid, graphic_id)) is not None:
        pass
    else:
        batch = batch_for_shader(shader, 'TRIS',
                                 get_rect_uv_coords(node.rect_transform) if use_uv else get_rect_coords(node.rect_transform),
                                 indices=tex_indices)
        if graphic_id is not None:
            set_batch_to_cache(node.uuid, graphic_id, batch)
    if wg:
        shader.uniform_float('u_dimensions', node.rect_transform.dimensions)
    _draw_batch(batch, shader, **uniforms)


def draw_node_cage(node: object, graphic_id: str, shader: GPUShader, margin: float, thickness: float | None = None, **uniforms):
    if not node.dirty and (batch := get_batch_from_cache(node.uuid, graphic_id)) is not None:
        pass
    else:
        batch = batch_for_shader(shader, 'LINE_LOOP', get_rect_cage_coords(node.rect_transform, margin))
        set_batch_to_cache(node.uuid, graphic_id, batch)
    for key, value in uniforms.items():
        shader.uniform_float(key, value)
    if thickness: state.line_width_set(thickness)
    batch.draw(shader)
    if thickness: state.line_width_set(1.0)


def draw_cage(node: object, graphic_id: str, pos: Vector, size: Vector, pad: float, shader: GPUShader, thickness: float | None = None, **uniforms):
    if not node.dirty and (batch := get_batch_from_cache(node.uuid, graphic_id)) is not None:
        pass
    else:
        batch = batch_for_shader(shader, 'LINE_LOOP', get_cage_coords(*pos, *size, pad))
        set_batch_to_cache(node.uuid, graphic_id, batch)
    for key, value in uniforms.items():
        shader.uniform_float(key, value)
    if thickness: state.line_width_set(thickness)
    batch.draw(shader)
    if thickness: state.line_width_set(1.0)


# ----------------------------------------------------------------

def rectangle_ui(node: object, graphic_id: str, color: RGBA, _shader=SHADER_UNIFORM_COLOR) -> None:
    if color[-1] != 1.0:
        state.blend_set('ALPHA')
    draw_node(node, graphic_id, _shader, color=color)


def rectangle(node: object, graphic_id: str, pos: Vector, size: Vector, rotation: float, color: RGBA, origin: Vector | None = None, _shader=SHADER_UNIFORM_COLOR) -> None:
    if color[-1] != 1.0:
        state.blend_set('ALPHA')
    draw(node, graphic_id, pos, size, rotation, _shader, origin=origin, color=color)


def rectangle_bbox(node: object, graphic_id: str, bbox, color: RGBA, _shader=SHADER_UNIFORM_COLOR) -> None:
    if color[-1] != 1.0:
        state.blend_set('ALPHA')
    draw_bb(node, graphic_id, bbox, _shader, color=color)


def text(pos: Vector,
         text: str,
         size: int,
         pivot: tuple[float, float] = (0, 0),
         angle: float = 0.0,
         color: tuple[float, float, float] = (.92, .92, .92),
         alpha: float = 1.0,
         width=0,
         word_wrap=True,
         use_shadow: bool = False,
         shadow_level: int = 3, # 3, 5, 0
         shadow_color: tuple[float, float, float, float] = (0, 0, 0, .9),
         shadow_offset: tuple = (1, -1)) -> Vector:
    if size < 10:
        return

    blend_state = state.blend_get()
    blf.size(0, size)
    text_dim = None
    if width != 0:
        text_dim = blf.dimensions(0, text)
        # print(text_dim[0], rect.width)
        if text_dim[0] > width:
            if word_wrap:
                blf.enable(0, blf.WORD_WRAP)
                blf.word_wrap(0, width)
            else:
                char_count = len(text)
                target_char_count = max(int(char_count * width / text_dim[0]), 3)
                cut_text = textwrap.shorten(text, width=target_char_count, placeholder="...")
                if target_char_count > len(cut_text):
                    diff = target_char_count-len(cut_text)
                    if len(cut_text) == 3:
                        text = text[:diff] + cut_text
                    else:
                        off = len(cut_text)-3
                        text = cut_text[:-3] + text[off:off+diff] + '...'
                else:
                    text = cut_text
        else:
            word_wrap = False
    if pivot[0] != 0 or pivot[1] != 0:
        if pivot[0] != 0:
            text_dim = blf.dimensions(0, text)
            pos.x -= text_dim[0] * pivot[0]
        if pivot[1] != 0:
            text_h = TEXT_11P_HEIGHT * size / 11 # blf.dimensions(0, 'X')
            pos.y -= text_h * pivot[1]
    if angle != 0:
        blf.enable(0, blf.ROTATION)
        blf.rotation(0, angle)
    blf.position(0, *pos, 0)
    if len(color) == 4:
        blf.color(0, *color)
    else:
        blf.color(0, *color, alpha)
    if use_shadow:
        blf.enable(0, blf.SHADOW)
        blf.shadow(0, shadow_level, *shadow_color)
        blf.shadow_offset(0, *shadow_offset)
    blf.draw(0, text)
    if use_shadow:
        blf.disable(0, blf.SHADOW)
    if angle != 0:
        blf.disable(0, blf.ROTATION)
        blf.rotation(0, 0)
    if width != 0 and word_wrap:
        blf.disable(0, blf.WORD_WRAP)
    state.blend_set(blend_state)
    return pos


def text_cached(data_id: str,
                graphic_id: str,
                dirty: bool,
                dirty_text: bool,
                _pos: Vector,
                _text_pos: Vector,
                _text: str,
                _text_size: int,
                _label_dimensions: Vector,
                pivot: tuple[float, float] = (0, 0),
                angle: float = 0.0,
                color: tuple[float, float, float] = (.92, .92, .92),
                alpha: float = 1.0,
                width=0,
                origin: Vector | None = None,
                render_scale: float = 3.0) -> Vector:
    if _text_size < 10:
        return

    if not dirty_text and (off := get_offscreen(data_id)) is not None:
        # offscreen(data_id, graphic_id, dirty, _pos, _label_dimensions, angle, off, origin=origin)

        if not dirty and (batch := get_batch_from_cache(data_id, graphic_id)) is not None:
            pass
        else:
            # _pos = _pos - Vector((_label_dimensions.y * .1, _label_dimensions.y * .1))
            coords = get_tex_coords(_pos, _label_dimensions) if angle == 0 else get_rotated_tex_coords(_pos, _label_dimensions, origin if origin is not None else _pos+_label_dimensions*0.5, angle)
            batch=batch_for_shader(SHADER_IMAGE, 'TRIS',
            {'pos': coords,
            'texCoord': tex_uv_indices},
            indices=tex_indices)
            set_batch_to_cache(data_id, graphic_id, batch)
        state.blend_set('ALPHA')
        SHADER_IMAGE.uniform_sampler('image', off.texture_color)
        batch.draw(SHADER_IMAGE)
    else:
        ts = _text_size*render_scale
        text_dim = get_text_dim(_text, ts)
        # min_text_h = get_text_dim('x', ts)[1]
        max_text_h = get_text_dim('Xy', ts)[1]
        # print("Diff height text:", _text, max_text_h, text_dim[1]) #, min_text_h)
        if max_text_h <= text_dim[1]:
            text_dim = Vector(text_dim)
            t_pos = Vector((0, text_dim.y * 2)) # Fix height.
            #text_dim.y *= 1.1
            # text_dim.x *= .9
            ts *= 0.9
            t_pos.x += (text_dim.x * 0.5)
        else:
            t_pos = Vector((0, 0))
        draw_offscreen(data_id, partial(text, t_pos, _text, ts * 10, (0, 0), 0, color, alpha, 0), *text_dim)
        text(_text_pos, _text, _text_size, pivot, angle, color, alpha, width)


def _box(node: object, graphic_id: str, margin: float, line_thickness: float, color: RGBA, _shader=SHADER_UNIFORM_COLOR):
    draw_node_cage(node, graphic_id, _shader, thickness=line_thickness, color=color)

def box_ui(node: object, graphic_id: str, margin: float, line_thickness: float, color: RGBA, _shader=SHADER_POLYLINE_UNIFORM_COLOR):
    state.blend_set('ALPHA')
    fb = gpu.state.active_framebuffer_get()
    x, y, w, h = fb.viewport_get()
    draw_node_cage(node, graphic_id, _shader, margin=margin, lineWidth=line_thickness, color=color, viewportSize=(w, h))

def box(node: object, graphic_id: str, pos: Vector, size: Vector, padding: float, line_thickness: float, color: RGBA, _shader=SHADER_POLYLINE_UNIFORM_COLOR):
    state.blend_set('ALPHA')
    fb = gpu.state.active_framebuffer_get()
    x, y, w, h = fb.viewport_get()
    draw_cage(node, graphic_id, pos, size, padding, _shader, lineWidth=line_thickness, color=color, viewportSize=(w, h))


def circle_ui(node: object, margin: float, line_thickness: float, color: RGBA):
    ''' Without caching. '''
    if color[-1] != 1.0:
        state.blend_set('ALPHA')
    rect = node.rect_transform
    state.line_width_set(line_thickness)
    draw_circle_2d(rect.origin, color, (rect.dimensions[0] + margin) * 0.5, segments=24)
    state.line_width_set(1.0)


def image(owner: object, graphic_id: str,
       pos: Vector, size: Vector, rotation: float,
       image: Image | GPUTexture,
       origin: Vector | None = None, _shader=SHADERS.IMA) -> None:
    if not set_image(image, _shader): return
    draw(owner, graphic_id, pos, size, rotation, _shader, use_uv=True, wg=False, origin=origin)


def image_bbox(owner: object, graphic_id: str,
               bbox_coords: Vector, image: Image | GPUTexture, _shader=SHADERS.IMA) -> None:
    if not set_image(image, _shader): return
    draw_bb(owner, graphic_id, bbox_coords, _shader, use_uv=True)


def image_ui(node: object, graphic_id: str, image: Image | GPUTexture, origin: Vector | None = None, _shader=SHADERS.IMA, **extra_uniforms) -> None:
    if not isinstance(image, (Image, GPUTexture)): return
    if not set_image(image, _shader): return
    draw_node(node, graphic_id, _shader, use_uv=True, **extra_uniforms)

def image_ui_opa(node: object, graphic_id: str, image: Image | GPUTexture, opa: float, _shader=SHADERS.IMA_OPA, **extra_uniforms) -> None:
    image_ui(node, graphic_id, image, None, _shader, o=opa)


def image_ui_outline(node: object, graphic_id: str, image: Image | GPUTexture, outline_color: RGBA, origin: Vector | None = None, _shader=SHADERS.IMA_OUTLINE) -> None:
    image_ui(node, graphic_id, image, origin, _shader, u_outline_color=outline_color)


def offscreen(node: object, graphic_id: str, off: GPUOffScreen, origin: Vector | None = None) -> None:
    if not isinstance(off, GPUOffScreen): return
    image_ui(node, graphic_id, off.texture_color, origin=origin)


def just_a_point(pos: Vector, radius: int, color: RGBA = None, rotation: float = 0, shader=SHADER_UNIFORM_COLOR, **uniforms) -> None:
    with gpu.matrix.push_pop():
        # gpu.matrix.translate(Vector(pos) * -1)
        # gpu.matrix.multiply_matrix(Matrix.Rotation(rotation, 4, 'Z'))
        gpu.matrix.translate(pos)
        gpu.matrix.scale_uniform(radius)
        state.point_size_set(int(radius*2))
        fmt = GPUVertFormat()
        pos_id = fmt.attr_add(id="pos", comp_type='F32', len=2, fetch_mode='FLOAT')
        vbo = GPUVertBuf(len=1, format=fmt)
        vbo.attr_fill(id=pos_id, data=[(0, 0)])
        batch = GPUBatch(type='POINTS', buf=vbo)
        batch.program_set(shader)
        if color is not None:
            shader.uniform_float("color", color)
        for key, value in uniforms.items():
            shader.uniform_float(key, value)
        batch.draw()
        state.point_size_set(1.0)

    # batch: GPUBatch = batch_for_shader(_shader, 'POINTS', {'pos': [pos]})
    # _shader.uniform_float('color', color)
    # state.point_size_set(int(radius*2))
    # batch.draw(_shader)
    # state.point_size_set(1.0)


# ----------------------------------------------------------------


def wg(owner: object, graphic_id: str,
       pos: Vector, size: Vector, rotation: float,
       roundness: float, outline_thickness: float, bg_color: RGBA,
       origin: Vector | None = None, dirty: bool | None = None, _shader=SHADERS.WG) -> None:
    ''' Uniforms:
        ---------------
        - ``vec2`` u_dimensions;
        - ``vec4`` u_color;
        - ``float`` u_radius;
        - ``float`` u_outline;
    '''
    if bg_color[-1] != 1.0:
        state.blend_set('ALPHA')
    rad = min(*size) * 0.5 * roundness
    value = rgb_to_hsv(bg_color[0], bg_color[1], bg_color[2])[-1]
    outline_color_factor = 1 + pow(value, 2)
    draw(owner, graphic_id, pos, size, rotation, _shader, use_uv=True, wg=True, origin=origin, dirty=dirty,
              u_color=bg_color, u_radius=rad, u_outline=outline_thickness, u_outline_color_factor=outline_color_factor)


def wg_ui(node: object, graphic_id: str, roundness: float, outline_thickness: float, bg_color: RGBA, _shader=SHADERS.WG) -> None:
    ''' Uniforms:
        ---------------
        - ``vec2`` u_dimensions;
        - ``vec4`` u_color;
        - ``float`` u_radius;
        - ``float`` u_outline;
    '''
    if bg_color[-1] != 1.0:
        state.blend_set('ALPHA')
    rad = min(*node.rect_transform.dimensions) * 0.5 * roundness
    value = rgb_to_hsv(bg_color[0], bg_color[1], bg_color[2])[-1]
    outline_color_factor = 1 + pow(value, 2)
    draw_node(node, graphic_id, _shader, use_uv=True, wg=True,
              u_color=bg_color, u_radius=rad, u_outline=outline_thickness, u_outline_color_factor=outline_color_factor)


def wg_grid_ui(node: object, graphic_id: str, roundness: float, outline_thickness: float,
               bg_color: RGBA, offset: Vector = Vector((0, 0)), scale: float = 1.0, _shader=SHADERS.WG_GRID) -> None:
    ''' Uniforms:
        ---------------
        - ``vec2`` u_dimensions;
        - ``vec4`` u_color;
        - ``float`` u_radius;
        - ``float`` u_outline;
    '''
    if bg_color[-1] != 1.0:
        state.blend_set('ALPHA')
    rad = min(*node.rect_transform.dimensions) * 0.5 * roundness
    value = rgb_to_hsv(bg_color[0], bg_color[1], bg_color[2])[-1]
    outline_color_factor = 1 + pow(value, 2)
    draw_node(node, graphic_id, _shader, use_uv=True, wg=True,
              u_color=bg_color, u_radius=rad, u_outline=outline_thickness, u_outline_color_factor=outline_color_factor, u_offset=offset, u_scale=scale)


def wg_grid(owner: object, graphic_id: str,
       pos: Vector, size: Vector, rotation: float,
       roundness: float, outline_thickness: float, bg_color: RGBA,
       offset: Vector = Vector((0, 0)), scale: float = 1.0,
       origin: Vector | None = None, dirty: bool | None = None, _shader=SHADERS.WG_GRID) -> None:
    ''' Uniforms:
        ---------------
        - ``vec2`` u_dimensions;
        - ``vec4`` u_color;
        - ``float`` u_radius;
        - ``float`` u_outline;
    '''
    if bg_color[-1] != 1.0:
        state.blend_set('ALPHA')
    rad = min(*size) * 0.5 * roundness
    value = rgb_to_hsv(bg_color[0], bg_color[1], bg_color[2])[-1]
    outline_color_factor = 1 + pow(value, 2)
    draw(owner, graphic_id, pos, size, rotation, _shader, use_uv=True, wg=True, origin=origin, dirty=dirty,
              u_color=bg_color, u_radius=rad, u_outline=outline_thickness, u_outline_color_factor=outline_color_factor,
              u_offset=offset, u_scale=scale)


def wg_sld_ui(node: object, graphic_id: str, factor: float, roundness: float, bg_color: RGBA, fill_color: RGBA, _shader=SHADERS.WG_SLD) -> None:
    ''' Uniforms:
        ---------------
        - ``vec2`` u_dimensions;
        - ``float`` u_factor;
        - ``vec4`` u_color;
        - ``vec4`` u_fill_color;
        - ``float`` u_radius;
    '''
    if bg_color[-1] != 1.0:
        state.blend_set('ALPHA')
    rad = min(*node.rect_transform.dimensions) * 0.5 * roundness
    draw_node(node, graphic_id, _shader, use_uv=True, wg=True,
              u_factor=factor,
              u_radius=rad, # u_outline=outline_thickness,
              u_color=bg_color, u_fill_color=fill_color)


def wg_sld_rng_ui(node: object, graphic_id: str, factor: float, arc_angle: float, thickness_factor: float, invert_angle: bool, bg_color: RGBA, fill_color: RGBA, _shader=SHADERS.WG_SLD_RNG) -> None:
    ''' Uniforms:
        ---------------
        - ``float`` u_angle;
        - ``vec4`` u_color;
        - ``vec4`` u_fill_color;
        - ``float`` u_thickness;
    '''
    if bg_color[-1] != 1.0:
        state.blend_set('ALPHA')
    u_arc_angle = radians(arc_angle)
    u_angle = u_arc_angle * factor
    draw_node(node, graphic_id, _shader, use_uv=True, wg=False,
              u_arc_angle=u_arc_angle,
              u_angle=u_angle,
              u_invert_angle=float(invert_angle),
              u_thickness=thickness_factor,
              u_color=bg_color, u_fill_color=fill_color)
