from bpy.types import Event, View2D
from mathutils import Vector

from .geometry import rotate_point


class EventValue:
    ANY = 'ANY'
    PRESS = 'PRESS'
    RELEASE = 'RELEASE'
    CLICK = 'CLICK'
    DOUBLE_CLICK = 'DOUBLE_CLICK'
    CLICK_DRAG = 'CLICK_DRAG'
    NORTH = 'NORTH'
    NORTH_EAST = 'NORTH_EAST'
    EAST = 'EAST'
    SOUTH_EAST = 'SOUTH_EAST'
    SOUTH = 'SOUTH'
    SOUTH_WEST = 'SOUTH_WEST'
    WEST = 'WEST'
    NORTH_WEST = 'NORTH_WEST'
    NOTHING = 'NOTHING'


class EventType:
    TIMER = 'TIMER'
    RET = 'RET'
    BACKSPACE = 'BACK_SPACE'
    NONE = 'NONE'
    ESC = 'ESC'
    LEFTMOUSE = 'LEFTMOUSE'
    MIDDLEMOUSE = 'MIDDLEMOUSE'
    RIGHTMOUSE = 'RIGHTMOUSE'
    PEN = 'PEN'
    ERASER = 'ERASER'
    MOUSEMOVE = 'MOUSEMOVE'
    INBETWEEN_MOUSEMOVE = 'INBETWEEN_MOUSEMOVE'
    WHEELUPMOUSE = 'WHEELUPMOUSE'
    WHEELDOWNMOUSE = 'WHEELDOWNMOUSE'
    WHEELINMOUSE = 'WHEELINMOUSE'
    WHEELOUTMOUSE = 'WHEELOUTMOUSE'

    LEFT_CTRL = 'LEFT_CTRL'

    U = 'U'
    Z = 'Z'

    NUM_ONE = 'ONE'
    NUM_TWO = 'TWO'
    NUM_THREE = 'THREE'


class _RectTransform:
    origin: Vector
    size: Vector
    rotation: float



class Mouse:
    current: Vector   # current mouse position.
    prev: Vector      # previous mouse position.
    start: Vector     # initial mouse position.
    offset: Vector    # mouse offset between initial position and current position.
    delta: Vector     # difference of mouse position between prev and current.

    # local: Vector     # local space coordinates.
    local_rel: Vector # local space coordinates, relative factor between [0, 1].
    local_current: Vector # current local space coordinates.
    local_prev: Vector
    local_start: Vector
    local_offset: Vector
    local_delta: Vector
    local_dir: Vector

    view_current: Vector
    view_prev: Vector
    view_start: Vector
    view_offset: Vector
    view_delta: Vector

    dir: Vector       # direction of mouse taking into account previous position.


    @staticmethod
    def init(event: Event, view2d: View2D | None = None, local_space__rect: _RectTransform | None = None) -> 'Mouse':
        mouse = Mouse()
        mouse_region_pos = Vector((event.mouse_region_x, event.mouse_region_y))
        if local_space__rect is not None:
            mouse.local_start = rotate_point(mouse_region_pos, local_space__rect.origin, -local_space__rect.rotation)
            mouse.local_current = mouse_region_pos.copy()
            mouse.local_prev = mouse_region_pos.copy()
            mouse.local_offset = Vector((0, 0))
            mouse.local_delta = Vector((0, 0))
            mouse.local_dir = Vector((0, 0))
            # mouse.local_rel = local_space__rect.size
        mouse.start = mouse_region_pos
        mouse.current = mouse_region_pos.copy()
        mouse.prev = mouse_region_pos.copy()
        mouse.offset = Vector((0, 0))
        mouse.delta = Vector((0, 0))
        mouse.dir = Vector((0, 0))

        if view2d is not None:
            view_pos = view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
            mouse.view_current = Vector(view_pos)
            mouse.view_prev = Vector(view_pos)
            mouse.view_start = Vector(view_pos)
            mouse.view_offset = Vector((0, 0))
            mouse.view_delta = Vector((0, 0))

        return mouse

    def update(self, event: Event, view2d: View2D | None = None, local_space__rect: _RectTransform | None = None) -> None:
        self.prev.x = self.current.x
        self.prev.y = self.current.y
        self.current.x = event.mouse_region_x
        self.current.y = event.mouse_region_y
        self.delta.x = self.current.x - self.prev.x
        self.delta.y = self.current.y - self.prev.y
        self.offset.x = self.current.x - self.start.x
        self.offset.y = self.current.y - self.start.y

        if local_space__rect is not None:
            self.local_prev.x = self.local_current.x
            self.local_prev.y = self.local_current.y
            self.local_current = rotate_point(self.current, local_space__rect.origin, -local_space__rect.rotation)
            self.local_delta.x = self.local_current.x - self.local_prev.x
            self.local_delta.y = self.local_current.y - self.local_prev.y
            self.local_offset.x = self.local_current.x - self.local_start.x
            self.local_offset.y = self.local_current.y - self.local_start.y

        if view2d is not None:
            view_pos = view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
            self.view_delta.x = self.view_current.x - self.view_prev.x
            self.view_delta.y = self.view_current.y - self.view_prev.y
            self.view_prev.x = self.view_current.x
            self.view_prev.y = self.view_current.y
            self.view_current.x = view_pos[0]
            self.view_current.y = view_pos[1]
            self.view_offset.x = self.view_current.x - self.view_start.x
            self.view_offset.y = self.view_current.y - self.view_start.y

        self.dir.x = 0 if self.delta.x==0 else 1 if self.delta.x > 0 else -1
        self.dir.y = 0 if self.delta.y==0 else 1 if self.delta.y > 0 else -1


def get_mouse_pos(event: Event) -> Vector:
    return Vector((event.mouse_region_x, event.mouse_region_y))
