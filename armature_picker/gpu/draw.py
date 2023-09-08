import bpy
import gpu
import blf
from bpy.types import Image
from gpu import state
from gpu.types import GPUShader, GPUBatch, GPUTexture, GPUOffScreen
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from gpu.texture import from_image as get_gputex_from_image

from uuid import uuid4
from math import cos, sin
import textwrap
from collections import defaultdict
from typing import Tuple
from functools import partial

from .text_offscreen import draw_offscreen, get_offscreen
from ..utils.geometry import rotate_point


RGBA = Tuple[float, float, float, float]


# ----------------------------------------------------------------

SHADER_UNIFORM_COLOR: GPUShader = gpu.shader.from_builtin('UNIFORM_COLOR')
SHADER_IMAGE: GPUShader = gpu.shader.from_builtin('IMAGE')


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


# ----------------------------------------------------------------

get_rect_coords = lambda x, y, w, h: (
    (x, y), (x + w, y),
    (x, y + h), (x + w, y + h)
)
get_rotated_rect_coords = lambda pos, size, origin, angle: tuple(rotate_point(Vector(co), origin, angle).to_tuple() for co in get_rect_coords(*pos, *size))

rect_indices = ((0, 1, 2), (2, 1, 3))


get_cage_coords = lambda pos, size: (
    pos, (pos.x + size.x, pos.y),
    pos + size, (pos.x, pos.y + size.y)
)
get_rotated_cage_coords = lambda pos, size, origin, angle: tuple(rotate_point(Vector(co), origin, angle).to_tuple() for co in get_cage_coords(pos, size))

get_tex_coords = lambda _p, _s: (
    (_p.x,_p.y+_s.y),_p,
    (_p.x+_s.x,_p.y),_p+_s
)
get_rotated_tex_coords = lambda pos, size, origin, angle: tuple(rotate_point(Vector(co), origin, angle).to_tuple() for co in get_tex_coords(pos, size))

tex_uv_indices = ((0,1),(0,0),(1,0),(1,1))
tex_indices = ((0,1,2),(2,3,0))

# ----------------------------------------------------------------


def rectangle(data_id: str,
              graphic_id: str,
              dirty: bool,
              pos: Vector,
              size: Vector,
              angle: float,
              color: RGBA,
              _shader=SHADER_UNIFORM_COLOR) -> None:
    if not dirty and (batch := get_batch_from_cache(data_id, graphic_id)) is not None:
        pass
    else:
        batch: GPUBatch = batch_for_shader(_shader, 'TRIS',
            {"pos": get_rect_coords(*pos, *size) if angle == 0 else
                    get_rotated_rect_coords(pos, size, pos+size*0.5, angle)},
            indices=rect_indices)
        set_batch_to_cache(data_id, graphic_id, batch)
    _shader.uniform_float("color", color)
    batch.draw(_shader)


def text(pos: Vector,
         text: str,
         size: int,
         pivot: tuple[float, float] = (0, 0),
         angle: float = 0.0,
         color: tuple[float, float, float] = (.92, .92, .92),
         alpha: float = 1.0,
         width=0) -> Vector:
    if size < 10:
        return

    blend_state = state.blend_get()
    blf.size(0, size, 72)
    text_dim = None
    if width:
        text_dim = blf.dimensions(0, text)
        # print(text_dim[0], rect.width)
        if text_dim[0] > width:
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
    blf.draw(0, text)
    if angle != 0:
        blf.disable(0, blf.ROTATION)
        blf.rotation(0, 0)
    state.blend_set(blend_state)
    return pos


def text_cached(data_id: str,
                graphic_id: str,
                dirty: bool,
                dirty_text: bool,
                _pos: Vector,
                _text_pos: Vector,
                _text: str,
                _size: int,
                pivot: tuple[float, float] = (0, 0),
                angle: float = 0.0,
                color: tuple[float, float, float] = (.92, .92, .92),
                alpha: float = 1.0,
                width=0,
                render_scale: float = 3.0) -> Vector:
    if _size < 10:
        return

    if not dirty_text and (off := get_offscreen(data_id)) is not None:
        offscreen(data_id, graphic_id, dirty, _pos, Vector(get_text_dim(_text, _size)), angle, off)
        ## print("Drawing cached text")
    else:
        draw_offscreen(data_id, partial(text, Vector((0, 0)), _text, _size*10*render_scale, (0, 0), 0, color, alpha, 0), *get_text_dim(_text, _size*render_scale))
        text(_text_pos, _text, _size, pivot, angle, color, alpha, width)


def box(data_id: str, graphic_id: str, dirty: bool, pos: Vector, size: Vector, angle: float, line_thickness: float, color: RGBA, _shader=SHADER_UNIFORM_COLOR):
    if not dirty and (batch := get_batch_from_cache(data_id, graphic_id)) is not None:
        pass
    else:
        coords = get_cage_coords(pos, size) if angle == 0 else get_rotated_cage_coords(pos, size, pos+size*0.5, angle)
        batch: GPUBatch = batch_for_shader(_shader, 'LINE_LOOP', {'pos': coords})
        set_batch_to_cache(data_id, graphic_id, batch)
    state.line_width_set(line_thickness)
    _shader.uniform_float('color', color)
    batch.draw(_shader)
    state.line_width_set(1.0)


def image(data_id: str, graphic_id: str, dirty: bool, pos: Vector, size: Vector, angle: float, image: Image | GPUTexture, _shader=SHADER_IMAGE) -> None:
    if not isinstance(image, (Image, GPUTexture)):
        return
    state.blend_set('ALPHA')
    t=get_gputex(image) if isinstance(image, Image) else image

    if not dirty and (batch := get_batch_from_cache(data_id, graphic_id)) is not None:
        pass
    else:
        coords = get_tex_coords(pos, size) if angle == 0 else get_rotated_tex_coords(pos, size, pos+size*0.5, angle)
        batch=batch_for_shader(_shader, 'TRIS',
        {'pos': coords,
         'texCoord': tex_uv_indices},
        indices=tex_indices)
        set_batch_to_cache(data_id, graphic_id, batch)

    _shader.uniform_sampler('image', t)
    batch.draw(_shader)


def offscreen(data_id: str, graphic_id: str, dirty: bool, pos: Vector, size: Vector, angle: float, off: GPUOffScreen) -> None:
    if not isinstance(off, GPUOffScreen):
        return
    image(data_id, graphic_id, dirty, pos, size, angle, off.texture_color)
