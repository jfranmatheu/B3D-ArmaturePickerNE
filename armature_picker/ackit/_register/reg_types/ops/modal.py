from enum import Enum, auto

from bpy import types as bpy_types

from .....utils.event import Mouse, EventType, EventValue
from .operator import Operator, OpsReturn


class ModalFlags(Enum):
    ''' Use as decorator over an Operator subclass. '''
    class Raycast(Enum):
        BVHTREE = auto()
        SCENE = auto()
        OBJECT = auto()

    DRAW_2D = auto()
    DRAW_3D = auto()

    def __call__(self, deco_cls: 'ModalOperator'):
        deco_cls.modal_flags.add(self)
        return deco_cls


class ModalOperator(Operator):
    # Blender props.
    bl_cursor_pending: str

    # --------------------------------
    # Properties you should set in your subclasses.
    modal_flags: set[ModalFlags]

    # --------------------------------

    mouse: Mouse

    def invoke(self, context: bpy_types.Context, event: bpy_types.Event) -> OpsReturn:
        # print("BaseOperator::invoke() -> ", self.bl_idname)
        if not context.window_manager.modal_handler_add(self):
            return OpsReturn.CANCEL
        self.mouse = Mouse.init(event)
        self.event_start_type = event.type
        self.modal_start(context, event)
        return OpsReturn.RUN

    def modal(self, context: bpy_types.Context, event: bpy_types.Event) -> OpsReturn:
        if event.type in {EventType.MOUSEMOVE, EventType.INBETWEEN_MOUSEMOVE}:
            self.mouse.update(event)
            self.modal__mouse_move(context, self.mouse)
            return OpsReturn.RUN
        if res := self.modal_update(context, event):
            return res
        return OpsReturn.RUN

    def modal_start(self, context: bpy_types.Context, event: bpy_types.Event) -> None:
        pass

    def modal_update(self, context: bpy_types.Context, event: bpy_types.Event) -> OpsReturn:
        if event.type in {EventType.ESC, EventType.RIGHTMOUSE}:
            return OpsReturn.CANCEL
        if event.type == self.event_start_type and event.value == EventValue.RELEASE:
            return OpsReturn.FINISH
        return OpsReturn.RUN

    def modal__mouse_move(self, context: bpy_types.Context, mouse: Mouse) -> None:
        pass

    def modal_end(self, context: bpy_types.Context, event: bpy_types.Event, cancel: bool) -> None:
        pass

    def execute(self, context: bpy_types.Context) -> OpsReturn:
        return OpsReturn.CANCEL

    #############################

    @classmethod
    def tag_register(deco_cls, flags: set[ModalFlags] = set()) -> 'ModalOperator':
        return super().tag_register()
