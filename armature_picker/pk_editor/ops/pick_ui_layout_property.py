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
        global picked_data_path
        if context is None:
            picked_data_path = ''
            return
        if context.property is None:
            picked_data_path = ''
            return

        print("Pick Property under cursor:", context.property)
        datablock, datapath, index = context.property

        if index != -1:
            # ARRAY.
            picked_data_path = ''
            return

        if isinstance(datablock, Object):
            pre = 'active_object'
        elif isinstance(datablock, Armature):
            pre = 'active_object.data'
        elif isinstance(datablock, Pose):
            pre = 'active_object.pose'
        elif isinstance(datablock, NodeTree):
            pre = 'space_data.node_tree'
        else:
            picked_data_path = ''
            return

        try:
            prop = datablock.path_resolve(datapath)
        except ValueError:
            print("ERROR! Could not resolve property")
            picked_data_path = ''
            return
        if not isinstance(prop, bool):
            picked_data_path = ''
            return

        print('\t>', pre + '.' + datapath)
        if datapath.startswith('['):
            data_path = pre + datapath
        else:
            data_path = pre + '.' + datapath

        picked_data_path = data_path # context.property[1]

    def modal_start(self, context: Context) -> None:
        self.active_node = context.space_data.node_tree.nodes.active
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
            context.region.tag_redraw()
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
        Cursor.wrap(0, 0, context=context)
        Cursor.wrap(*self.start_cursor, context=context)
        # def recover_mouse_pos(mouse_pos: tuple[int, int]):
        #     Cursor.wrap(*mouse_pos, context=bpy.context)
        # bpy.app.timers.register(partial(recover_mouse_pos, self.start_cursor.to_tuple()), first_interval=.2)

        if cancel:
            return

        global picked_data_path
        if picked_data_path is not None:
            ## print("\t> Picked data path is...", picked_data_path)
            self.active_node.data_path = picked_data_path
            picked_data_path = None

        # bpy.ops.ui.copy_data_path_button('INVOKE_DEFAULT', full_path=True)
        # print(bpy.context.window_manager.clipboard)
