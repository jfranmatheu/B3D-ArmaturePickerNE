from bpy import types as bpy_types
from bpy.types import Context, Event, ID, Object, NodeTree, Armature, Pose
from bpy.app import timers
import bpy

from armature_picker.ackit import ACK
from armature_picker.ackit._register.reg_types.ops.operator import OpsReturn
from armature_picker.utils.cursor import Cursor, CursorIcon
from armature_picker.utils.event import Mouse, EventType, EventValue, isEventType, isEventValue
from armature_picker.utils.node_editor import center_node_editor_view, get_armature_picker_editor
from armature_picker.pk_editor.poll import poll_check
from armature_picker.utils.operator import OpsReturn, ModalEventTrigger

from ..widgets import APNODE_Toggle
from ..widgets._bone_picker_common import APNODE_BonePicker_Common
from ..widgets._slider_common import APNODE_Slider_Common



class PickLayoutProperty(ACK.Type.OPS.ACTION):
    label = 'Pick UI Layout Property'
    tooltip = "Select a Blender layout property to be controlled by your active widget\tUse RightClick to pick up the property under the mouse cursor"

    # active_property: tuple[ID, str, int]
    # modal_use_timer: bool = True
    # modal_cancel_events: tuple[ModalEventTrigger] = (
    #     ModalEventTrigger(EventType.ESC, EventValue.ANY),
    # )
    # modal_finish_events: tuple[ModalEventTrigger] = (
    #     ModalEventTrigger(EventType.RIGHTMOUSE, EventValue.PRESS),
    # )

    @classmethod
    def poll(cls, context: Context):
        return context.property is not None and poll_check(context, 'EDIT', use_active_node=(APNODE_Toggle, APNODE_Slider_Common, APNODE_BonePicker_Common), allow_foreign_area=True)

    def action(self, context: Context) -> None:
        print("Pick Property:", context.property)
        datablock, datapath, index = context.property

        if isinstance(datablock, Object):
            pre = 'active_object'
        elif isinstance(datablock, Armature):
            pre = 'active_object.data'
        elif isinstance(datablock, Pose):
            pre = 'active_object.pose'
        elif isinstance(datablock, NodeTree):
            pre = 'space_data.node_tree'
        else:
            return

        try:
            prop = datablock.path_resolve(datapath)
        except ValueError:
            return
        if not isinstance(prop, bool):
            return

        print(pre + '.' + datapath)
        if context.area == 'NODE_EDITOR' and context.space_data.tree_type == 'AP_NODETREE':
            space_data = context.space_data
        else:
            space_data = get_armature_picker_editor(context)
        active_node: APNODE_Toggle = space_data.node_tree.nodes.active
        if datapath.startswith('['):
            data_path = pre + datapath
        else:
            data_path = pre + '.' + datapath
        active_node.data_path = data_path # context.property[1]

    '''
    def modal_start(self, context: Context) -> None:
        Cursor.set_icon(context, CursorIcon.EYEDROPPER)
        self.active_node = context.space_data.node_tree.nodes.active

    def modal__mouse_move(self, context: Context, mouse: Mouse) -> None:
        # self.active_property: tuple[ID, str, int] = context.property
        # print(context.property)
        return OpsReturn.PASS

    def modal_update(self, context: Context) -> OpsReturn:
        # print(context.property)
        # if isEventType.RIGHTMOUSE:
        #     return OpsReturn.PASS
        pass

    def modal_timer(self, context: Context) -> None:
        # print(context.property)
        pass

    def modal_end(self, context: Context, cancel: bool) -> None:
        Cursor.set_icon(context, CursorIcon.DEFAULT)

        if cancel:
            return

        bpy.ops.ui.copy_data_path_button('INVOKE_DEFAULT', full_path=True)
        print(bpy.context.window_manager.clipboard)
    '''
