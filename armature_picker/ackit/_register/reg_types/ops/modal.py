from enum import Enum, auto

from bpy import types as bpy_types

from .....utils.event import Mouse, EventType, EventValue, set_global_event, GEvent
from .....utils.operator import ModalEventTrigger
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

    modal_cancel_events: tuple[ModalEventTrigger] = (
        ModalEventTrigger(EventType.ESC, EventValue.ANY),
        ModalEventTrigger(EventType.RIGHTMOUSE, EventValue.ANY),
    )
    modal_finish_events: tuple[ModalEventTrigger] = ()

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
        set_global_event(event)
        for event_trigger in self.modal_cancel_events:
            if event_trigger.test_event():
                self.modal_end(context, cancel=True)
                return OpsReturn.CANCEL
        for event_trigger in self.modal_finish_events:
            if event_trigger.test_event():
                self.modal_end(context, cancel=False)
                return OpsReturn.FINISH
        if event.type in {EventType.MOUSEMOVE, EventType.INBETWEEN_MOUSEMOVE}:
            self.mouse.update(event)
            self.modal__mouse_move(context, self.mouse)
            return OpsReturn.RUN
        if res := self.modal_update(context, event):
            if res in {OpsReturn.CANCEL, OpsReturn.FINISH, 0, -1}:
                self.modal_end(context, cancel=res in {OpsReturn.CANCEL, -1})
            if res is None or isinstance(res, int):
                return OpsReturn.RUN
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
