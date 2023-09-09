from bpy.types import Event, View2D
from mathutils import Vector


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


class Mouse:
    current: Vector   # current mouse position.
    prev: Vector      # previous mouse position.
    start: Vector     # initial mouse position.
    offset: Vector    # mouse offset between initial position and current position.
    delta: Vector     # difference of mouse position between prev and current.

    # local: Vector     # local space coordinates.
    # local_rel: Vector # local space coordinates, relative factor between [0, 1].

    view_current: Vector
    view_prev: Vector
    view_start: Vector
    view_offset: Vector
    view_delta: Vector

    dir: Vector       # direction of mouse taking into account previous position.


    @staticmethod
    def init(event: Event, view2d: View2D | None = None) -> 'Mouse':
        mouse = Mouse()
        mouse.start = Vector((event.mouse_region_x, event.mouse_region_y))
        mouse.current = Vector((event.mouse_region_x, event.mouse_region_y))
        mouse.prev = Vector((event.mouse_region_x, event.mouse_region_y))
        mouse.offset = Vector(0, 0)
        mouse.delta = Vector(0, 0)
        mouse.dir = Vector(0, 0)

        if view2d is not None:
            view_pos = view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
            mouse.view_current = Vector(view_pos)
            mouse.view_prev = Vector(view_pos)
            mouse.view_start = Vector(view_pos)
            mouse.view_offset = Vector(0, 0)
            mouse.view_delta = Vector(0, 0)

        return mouse

    def update(self, event: Event, view2d: View2D | None = None) -> None:
        self.delta.x = self.current.x - self.prev.x
        self.delta.y = self.current.y - self.prev.y
        self.prev.x = self.current.x
        self.prev.y = self.current.y
        self.current.x = event.mouse_region_x
        self.current.y = event.mouse_region_y
        self.offset.x = self.current.x - self.start.x
        self.offset.y = self.current.y - self.start.y

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
