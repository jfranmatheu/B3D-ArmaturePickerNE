from bpy.types import Context, Event, Operator, Node
from bpy.props import StringProperty
from mathutils import Vector
import bpy

from ....utils.operator import OpsReturn, add_modal_handler
from ....utils.event import get_mouse_pos, EventType, EventValue
from ....ops.poll import poll_node_editor
from ....utils.node_editor import get_node_editor_zoom, get_node_editor_offset, get_node_editor_region_coord


class AP_OT_add_node(Operator):
    bl_idname = 'armature_picker.add_node'
    bl_label = 'Add Node'
    bl_description = "Add new node, drag it and place it where you want"

    node_idname: StringProperty()

    @classmethod
    def poll(cls, context: Context):
        return poll_node_editor(context)

    def invoke(self, context: Context, event: Event) -> OpsReturn:
        mouse_pos = get_mouse_pos(event)
        self.modal_nodes = (self.new_node(context, self.node_idname, event), )
        self.modal__move_node__enter(context, event, mouse_pos)
        return add_modal_handler(context, self)

    def new_node(self, context: Context, type: str, event: Event | Vector | None = None) -> Node:
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

    def modal(self, context: Context, event: Event) -> OpsReturn:
        mouse_pos = get_mouse_pos(event)

        if event.type == EventType.LEFTMOUSE and event.value == EventValue.RELEASE:
            self.modal__move_node__exit(context, mouse_pos, cancel=False)
            return OpsReturn.FINISH

        if event.type in {EventType.RIGHTMOUSE, EventType.ESC}:
            self.modal__move_node__exit(context, mouse_pos, cancel=True)
            return OpsReturn.CANCEL

        if event.type in {EventType.MOUSEMOVE, EventType.INBETWEEN_MOUSEMOVE}:
            self.modal__move_node__update(context, event, mouse_pos)

        return OpsReturn.RUN


    def modal__move_node__enter(self, context: Context, event: Event, mouse_pos: Vector) -> None:
        self.prev_node_location = [get_node_editor_region_coord(context, node.rect_transform.origin) for node in self.modal_nodes]
        self.node_location_offset = [prev_node_loc - mouse_pos for prev_node_loc in self.prev_node_location]

    def modal__move_node__update(self, context: Context, event: Event, mouse_pos: Vector) -> int:
        zoom = get_node_editor_zoom(context)
        inv_zoom = 1/zoom
        offset = get_node_editor_offset(context)

        def move_node(_node: Node, _node_loc_offset: Vector):
            _node.rect_transform.move_to((mouse_pos - offset + _node_loc_offset) * inv_zoom)

        {move_node(node, node_loc_offset) for (node, node_loc_offset) in zip(self.modal_nodes, self.node_location_offset)}

    def modal__move_node__exit(self, context: Context, mouse_pos: Vector, cancel: bool) -> None:
        if cancel:
            from ...node_tree import ensure_nodes_cache
            ensure_nodes_cache(context.space_data.node_tree)

            for (node, prev_node_loc) in zip(self.modal_nodes, self.prev_node_location):
                node.rect_transform.move_to(prev_node_loc)
            del self.prev_node_location
            del self.node_location_offset

        self.modal_nodes = None
