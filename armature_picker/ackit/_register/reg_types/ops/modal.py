from enum import Enum, auto

from bpy import types as bpy_types

from .....utils.event import Mouse, EventType, EventValue, set_global_event
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

    modal_cancel_events: set[EventType] = {EventType.ESC, EventType.RIGHTMOUSE}

    mouse: Mouse

    def invoke(self, context: bpy_types.Context, event: bpy_types.Event) -> OpsReturn:
        # print("BaseOperator::invoke() -> ", self.bl_idname)
        if not context.window_manager.modal_handler_add(self):
            return OpsReturn.CANCEL
        self.mouse = Mouse.init(event)
        self.event_start_type = event.type
        set_global_event(event)
        self.modal_start(context, event)
        return OpsReturn.RUN

    def modal(self, context: bpy_types.Context, event: bpy_types.Event) -> OpsReturn:
        if event.type in self.modal_cancel_events:
            self.modal_end(context, cancel=True)
            return OpsReturn.CANCEL
        if event.type in {EventType.MOUSEMOVE, EventType.INBETWEEN_MOUSEMOVE}:
            self.mouse.update(event)
            self.modal__mouse_move(context, self.mouse)
            return OpsReturn.RUN
        set_global_event(event)
        if res := self.modal_update(context, event):
            if res in {OpsReturn.CANCEL, OpsReturn.FINISH}:
                self.modal_end(context, cancel=res==OpsReturn.CANCEL)
            return res
        return OpsReturn.RUN

    def modal_start(self, context: bpy_types.Context) -> None:
        pass

    def modal_update(self, context: bpy_types.Context) -> OpsReturn:
        return OpsReturn.RUN

    def modal__mouse_move(self, context: bpy_types.Context, mouse: Mouse) -> None:
        pass

    def modal_end(self, context: bpy_types.Context, cancel: bool) -> None:
        pass

    def execute(self, context: bpy_types.Context) -> OpsReturn:
        return OpsReturn.CANCEL

    #############################

    @classmethod
    def tag_register(deco_cls, flags: set[ModalFlags] = set()) -> 'ModalOperator':
        return super().tag_register()
