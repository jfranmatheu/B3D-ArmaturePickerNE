from bpy.types import Context
import bpy

from armature_picker.ackit import ACK
from armature_picker.ackit._register.reg_types.ops.operator import OpsReturn
from armature_picker.utils.cursor import Cursor, CursorIcon
from armature_picker.utils.event import Mouse, EventType, EventValue, isEventType, GEvent
from armature_picker.pk_editor.poll import poll_check
from armature_picker.utils.operator import OpsReturn, ModalEventTrigger

from ..widgets import APNODE_ButtonScript


active_node = None
picked_op_idname: str | None = None


class PickLayoutButton(ACK.Type.OPS.MODAL):
    label = 'Pick UI Layout Button'
    tooltip = "Select a Blender layout button/operator to be executed by your active button widget\tUse RightClick to pick up the button/operator under the mouse cursor"

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
        return poll_check(context, 'EDIT', use_active_node=APNODE_ButtonScript, allow_foreign_area=True)

    @classmethod
    def pick_from_context(cls, context: Context) -> None:
        # global active_node
        global picked_op_idname

        if not hasattr(context, 'button_operator'):
            picked_op_idname = ''
            return

        # op.data_path -> eg: 'active_pose_pose'

        op = context.button_operator
        if hasattr(op, 'idname_py'):
            picked_op_idname = op.idname_py()
        elif hasattr(op, 'bl_idname'):
            picked_op_idname = op.bl_idname
        else:
            identifier = op.bl_rna.identifier
            if '_OT_' in identifier:
                ops_module, op_id = identifier.split('_OT_')
                picked_op_idname = f'{ops_module.lower()}.{op_id}'
            else:
                PickLayoutButton.stop_instance(cancel=True)
                return
        PickLayoutButton.stop_instance(cancel=False)


    def modal_start(self, context: Context) -> None:
        global active_node
        self.active_node = active_node = context.space_data.node_tree.nodes.active
        self.is_menu_opened = False
        self.is_finished = False
        self.is_wrapped_cursor = False
        self.start_cursor = GEvent.get_mouse_window_pos()

        global picked_op_idname
        picked_op_idname = None

    def modal__mouse_move(self, context: Context, mouse: Mouse) -> None:
        # ALLOW USER TO FREELY MOVE CURSOR, PASS EVENTS TO BLENDER.
        Cursor.set_icon(context, CursorIcon.EYEDROPPER)
        if self.is_menu_opened:
            return OpsReturn.RUN
        return OpsReturn.PASS

    def modal_update(self, context: Context) -> OpsReturn:
        if self.is_menu_opened:
            return OpsReturn.RUN

        # PASS EVENT TO BLENDER SO IT TRIGGERS CONTEXT MENU.
        if isEventType.RIGHTMOUSE:
            print("\t> Opening menu...")
            self.is_menu_opened = True
            return OpsReturn.PASS

    def modal_timer(self, context: Context) -> None:
        global picked_op_idname
        if picked_op_idname is not None:
            print("\t> Picked button found!", picked_op_idname)
            # INVALID PROPERTY WAS PICKED! RESET AND TRY AGAIN...
            if picked_op_idname == '':
                print("\t> Picked button is invalid! Reseting...")
                self.is_menu_opened = False
                picked_op_idname = None
                return OpsReturn.RUN
            # GOOD PROPERTY! LET'S FINISH THIS.
            print("\t> Picked button is VALID!")
            return OpsReturn.FINISH

    def modal_end(self, context: Context, cancel: bool) -> None:
        context.region.tag_redraw()
        Cursor.wrap(0, 0, context=context)
        Cursor.wrap(*self.start_cursor, context=context)

        global active_node
        global picked_op_idname
        active_node = None

        if cancel:
            picked_op_idname = None
            return

        if picked_op_idname is not None:
            self.active_node.op_module, self.active_node.op_id = picked_op_idname.split('.')
        picked_op_idname = None
