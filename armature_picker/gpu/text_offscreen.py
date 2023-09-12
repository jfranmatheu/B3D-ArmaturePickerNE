import bpy
import gpu
from bpy.app import timers
from mathutils import Matrix, Vector
from gpu.types import GPUOffScreen
from math import ceil


_offscreen_cache: dict[str, GPUOffScreen] = {}

_caching: set[str] = set()


def get_offscreen(data_id: str) -> GPUOffScreen | None:
    return _offscreen_cache.get(data_id, None)


def draw_offscreen(data_id: str, draw_callback: callable, _width: int, _height: int):
    ''' 'draw_callback' is typically a functools.partial function. '''

    width = ceil(_width)
    height = ceil(_height)

    wnd = bpy.context.window
    wnd_size = wnd.width, wnd.height

    def _wrapper():
        offscreen = GPUOffScreen(width, height)

        with offscreen.bind():
            fb = gpu.state.active_framebuffer_get()
            fb.clear(color=(0.0, 0.0, 0.0, 0.0))
            with gpu.matrix.push_pop():
                # reset matrices -> use normalized device coordinates [-1, 1]
                gpu.matrix.load_matrix(Matrix.Identity(4))
                ## gpu.matrix.load_projection_matrix(Matrix.Identity(4))
                ## gpu.matrix.translate(Vector((-1, -1)))
                ## gpu.matrix.scale(Vector((0.00394/(width/50), 0.018/(height/10))))

                gpu.matrix.scale((wnd_size[0] / _width * 1 / 10.25, wnd_size[1] / _height * 1 / 10.25))

                # blf.size(0, 20*10)

                draw_callback()

            ## x, y, w, h = fb.viewport_get()
            ## buffer = fb.read_color(x, y, w, h, 4, 0, 'FLOAT')

        ## offscreen.free()
        if off := get_offscreen(data_id):
            off.free()
        _offscreen_cache[data_id] = offscreen

        _caching.remove(data_id)

        ## print("Redraw Offscreen")

        ## image = bpy.data.images.get('tmp', None)
        ## if image is None:
        ##     image = bpy.data.images.new('tmp', width, height, alpha=True)
        ## image.scale(width, height)
        ## buffer.dimensions = width * height * 4
        ## image.pixels = [v / 255 for v in buffer]

    if data_id not in _caching:
        _caching.add(data_id)
        timers.register(_wrapper)
