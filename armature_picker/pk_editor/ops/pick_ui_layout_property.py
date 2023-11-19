from bpy import types as bpy_types
from bpy.types import Context, Event, ID, Object, NodeTree, Armature, Pose
from bpy.app import timers
import bpy

from functools import partial

from armature_picker.ops import Ops as AP_OPS
from armature_picker.ackit import ACK, GLOBALS
from armature_picker.ackit._register.reg_types.ops.operator import OpsReturn
from armature_picker.utils.cursor import Cursor, CursorIcon
from armature_picker.utils.event import Mouse, EventType, EventValue, isEventType, isEventValue, GEvent
from armature_picker.utils.node_editor import center_node_editor_view, get_armature_picker_editor
from armature_picker.pk_editor.poll import poll_check
from armature_picker.utils.operator import OpsReturn, ModalEventTrigger

from ..widgets import APNODE_Toggle
from ..widgets._bone_picker_common import APNODE_BonePicker_Common
from ..widgets._slider_common import APNODE_Slider_Common


active_node = None
picked_data_path: str | None = None



class PickLayoutProperty(ACK.Type.OPS.MODAL):
    label = 'Pick UI Layout Property'
    tooltip = "Select a Blender layout property to be controlled by your active widget\tUse RightClick to pick up the property under the mouse cursor"

    # active_property: tuple[ID, str, int]
    modal_cursor: CursorIcon = CursorIcon.EYEDROPPER
    modal_use_timer: bool = True
    modal_cancel_events: tuple[ModalEventTrigger] = (
        ModalEventTrigger(EventType.ESC, EventValue.ANY),
    )
    modal_finish_events: tuple[ModalEventTrigger] = (
        ModalEventTrigger(EventType.RIGHTMOUSE, EventValue.CLICK),
    )

    @classmethod
    def poll(cls, context: Context):
        # context.property is not None and
        return poll_check(context, 'EDIT', use_active_node=(APNODE_Toggle, APNODE_Slider_Common, APNODE_BonePicker_Common), allow_foreign_area=True)

    @classmethod
    def pick_property_from_context(cls, context: Context) -> None:
        global active_node
        global picked_data_path

        datablock: ID = None
        data_path: str = None
        index: int = -1

        def _poll():
            if not hasattr(context, 'button_pointer'):
                return False

            if not poll_check(context, 'EDIT', use_active_node=(APNODE_Toggle, APNODE_Slider_Common, APNODE_BonePicker_Common), allow_foreign_area=True):
                return False

            is_slider = isinstance(active_node, APNODE_Slider_Common)
            is_toggle = not is_slider

            prop_type: str = context.button_prop.type

            if context.button_prop.is_array:
                if is_toggle:
                    return False
                # NOTE: There is an issue with some vector float/int which crashes Blender
                # when accessing context.property...
                # We can prevent this if the target widget is a toggle, but not for sliders...
            elif prop_type == 'BOOLEAN' and is_toggle:
                pass
            else:
                return False

            if context.property is None:
                return False

            nonlocal datablock
            nonlocal data_path
            nonlocal index
            prop: tuple[ID, str, int] = context.property
            datablock, data_path, index = prop

            if is_toggle and index != -1:
                return False

            if not isinstance(datablock, (Object, Armature, Pose, NodeTree)):
                return False

            return True

        if not _poll():
            picked_data_path = ''
            return

        # bpy.ops.ui.copy_data_path_button(full_path=True)
        # picked_data_path = context.window_manager.clipboard

        # Resolve datablock prefix data-path.
        if isinstance(datablock, Object):
            pre = 'active_object'
        elif isinstance(datablock, Armature):
            pre = 'active_object.data'
        elif isinstance(datablock, Pose):
            pre = 'active_object.pose'
        elif isinstance(datablock, NodeTree):
            pre = 'space_data.node_tree'

        # Resolve full data-path.
        if data_path.startswith('['):
            data_path = pre + data_path
        else:
            data_path = pre + '.' + data_path

        # Set widget data-path.
        # Signal to stop the modal operator.
        picked_data_path = data_path
        PickLayoutProperty.stop_instance(cancel=False)


    def modal_start(self, context: Context) -> None:
        global active_node
        self.active_node = active_node = context.space_data.node_tree.nodes.active
        self.is_menu_opened = False
        self.is_finished = False
        self.is_wrapped_cursor = False
        self.start_cursor = GEvent.get_mouse_window_pos()

        global picked_data_path
        picked_data_path = None

    def modal__mouse_move(self, context: Context, mouse: Mouse) -> None:
        ## print("> MODAL MOUSE MOVE")
        # ALLOW USER TO FREELY MOVE CURSOR, PASS EVENTS TO BLENDER.
        Cursor.set_icon(context, CursorIcon.EYEDROPPER)
        if self.is_menu_opened:
            return OpsReturn.RUN
        return OpsReturn.PASS

    def modal_update(self, context: Context) -> OpsReturn:
        ## print("> MODAL UPDATE")
        if self.is_menu_opened:
            return OpsReturn.RUN

        # PASS EVENT TO BLENDER SO IT TRIGGERS CONTEXT MENU.
        if isEventType.RIGHTMOUSE:
            print("\t> Opening menu...")
            self.is_menu_opened = True
            return OpsReturn.PASS

    def modal_timer(self, context: Context) -> None:
        # print(context.property)
        ## print("> TIMER")
        global picked_data_path
        if picked_data_path is not None:
            print("\t> Picked datapath found!", picked_data_path)
            # INVALID PROPERTY WAS PICKED! RESET AND TRY AGAIN...
            if picked_data_path == '':
                print("\t> Picked datapath is invalid! Reseting...")
                self.is_menu_opened = False
                picked_data_path = None
                return OpsReturn.RUN
            # GOOD PROPERTY! LET'S FINISH THIS.
            print("\t> Picked datapath is VALID!")
            return OpsReturn.FINISH

    def modal_end(self, context: Context, cancel: bool) -> None:
        ## print("> MODAL END")
        context.region.tag_redraw()
        Cursor.wrap(0, 0, context=context)
        Cursor.wrap(*self.start_cursor, context=context)
        # def recover_mouse_pos(mouse_pos: tuple[int, int]):
        #     Cursor.wrap(*mouse_pos, context=bpy.context)
        # bpy.app.timers.register(partial(recover_mouse_pos, self.start_cursor.to_tuple()), first_interval=.2)

        global active_node
        global picked_data_path
        active_node = None

        if cancel:
            picked_data_path = None
            return

        if picked_data_path is not None:
            self.active_node.data_path = picked_data_path
        picked_data_path = None
