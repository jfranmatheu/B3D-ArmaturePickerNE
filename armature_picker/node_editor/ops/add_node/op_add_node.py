from bpy.types import Context, Event, Operator, Node
from bpy.props import StringProperty
from mathutils import Vector
import bpy

from ....utils.operator import OpsReturn, add_modal_handler
from ....utils.event import get_mouse_pos, EventType, EventValue
from armature_picker.node_editor.poll import poll_check
from ....utils.node_editor import get_node_editor_zoom, get_node_editor_offset, get_node_editor_region_coord
from ..move_nodes import MoveNodesModal


def new_node(context: Context, type: str, event: Event | Vector | None = None) -> Node:
    ''' Pass Event type if the addition should be interactive (performed inside an invoke to run modal).
        Pass a Vector in the event place to indicate the node element final-location manually. '''

    from ...node_tree import ensure_nodes_cache, AP_NodeTree

    bpy.ops.node.select_all(action='DESELECT')

    node_tree: AP_NodeTree = context.space_data.node_tree
    new_node = node_tree.nodes.new(type)
    new_node.select = True
    node_tree.nodes.active = new_node

    ensure_nodes_cache(node_tree)

    if hasattr(new_node, 'bone_name'):
        if context.active_bone is not None:
            new_node.bone_name = context.active_bone.name

    if event is not None:
        if isinstance(event, Event):
            mouse_pos = get_mouse_pos(event)

            zoom = get_node_editor_zoom(context)
            inv_zoom = 1/zoom
            offset = get_node_editor_offset(context)
            
            new_node.rect_transform.move_to((mouse_pos - offset) * inv_zoom)
        elif isinstance(event, Vector):
            new_node.rect_transform.move_to(event)

    new_node.location = (-100000, -100000)

    return new_node


class AP_OT_add_node(MoveNodesModal, Operator):
    bl_idname = 'armature_picker.add_node'
    bl_label = 'Add Node'
    bl_description = "Add new node, drag it and place it where you want"

    node_idname: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_object=False)

    def invoke(self, context: Context, event: Event) -> OpsReturn:
        mouse_pos = get_mouse_pos(event)
        if '@' in self.node_idname:
            self.node_idname, init_preset_func = self.node_idname.split('@')
        else:
            init_preset_func = None
        node = new_node(context, self.node_idname, event)
        if init_preset_func:
            getattr(node, init_preset_func)(context)
        self.modal_nodes = (node, )
        self.modal__move_node__enter(context, event, mouse_pos)
        return add_modal_handler(context, self)
