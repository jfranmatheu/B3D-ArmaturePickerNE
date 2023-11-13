from bpy.types import Context, Event, Node, Operator
from mathutils import Vector

from ...utils.operator import OpsReturn, add_modal_handler
from ...utils.event import get_mouse_pos, EventType, EventValue
from armature_picker.pk_editor.poll import poll_check
from ...utils.node_editor import get_node_editor_zoom, get_node_editor_offset, get_node_editor_region_coord, get_node_editor_view_point
from armature_picker.pk_editor.widgets._bone_picker_common import APNODE_BonePicker_Common
from armature_picker.pk_editor.widgets._base import AP_Node, RectTransform


class MoveNodesModal:
    modal_nodes: list[Node] | None = None

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
        zoom = get_node_editor_zoom(context)
        self.zoom = 1/zoom
        self.offset = get_node_editor_offset(context)

        # ----------------------------------------------------------------
        # Process bone picker widgets with mirror node. (L/R) support.
        view_pos = get_node_editor_view_point(context, mouse_pos)
        preferred_side: str = 'LEFT' if view_pos < 0 else 'RIGHT'
        to_remove_nodes = set()
        self.mirror_nodes = {}
        for node in reversed(self.modal_nodes):
            if not isinstance(node, APNODE_BonePicker_Common):
                continue
            if node in to_remove_nodes:
                continue
            if node.bone_loc_constraint not in {'LEFT', 'RIGHT'}:
                continue

            # Get mirror node and determine if current node is in the preferred side or not.
            keep_curr_node = preferred_side == node.bone_loc_constraint
            mirror_node = node.get_mirror_node()

            # Exclude mirror node (or current node, depending on the prefered side)
            # to avoid moving both L/R widgets at the same time (CAOS!)
            if mirror_node in self.modal_nodes:
                if keep_curr_node:
                    self.mirror_nodes[node] = mirror_node
                    to_remove_nodes.add(mirror_node)
                else:
                    self.mirror_nodes[mirror_node] = node
                    to_remove_nodes.add(node)
            else:
                self.mirror_nodes[node] = mirror_node

        # Safely remove widgets from the non-prefered side of the picker
        # when we detect that both L and R widgets are selected for this modal.
        if len(to_remove_nodes) != 0:
            for to_remove_node in to_remove_nodes:
                self.modal_nodes.remove(to_remove_node)

        # ----------------------------------------------------------------

        if self.modal_nodes is None:
            self.modal_nodes = list(context.selected_nodes)
        self.prev_node_location = [get_node_editor_region_coord(context, node.rect_transform.origin) for node in self.modal_nodes]
        if mouse_pos is None:
            if hasattr(self, 'mouse_pos'):
                mouse_pos = self.mouse_pos
            else:
                mouse_pos = Vector((context.area.width / 2, context.area.height / 2))
        self.node_location_offset = [prev_node_loc - mouse_pos for prev_node_loc in self.prev_node_location]

    def modal__move_node__update(self, context: Context, event: Event, mouse_pos: Vector) -> int:
        move_node = self.move_node
        zoom = self.zoom
        offset = self.offset
        {move_node(node, (mouse_pos - offset + node_loc_offset) * zoom) for (node, node_loc_offset) in zip(self.modal_nodes, self.node_location_offset)}
        self.apply_custom_constraints()


    def move_node(self, node: AP_Node, pos: Vector):
        rect: RectTransform = node.rect_transform

        # Apply Axis and Mirror Constraints to BonePicker Widgets.
        if isinstance(node, APNODE_BonePicker_Common):
            if node.bone_loc_constraint == 'CENTER':
                pos.x = 0 # Lock to Y axis at X=0.
            elif node.bone_loc_constraint == 'LEFT':
                dim_right_to_origin = rect.dimensions[0] * (1 - rect.pivot[0])
                right = pos.x + dim_right_to_origin
                if right > 0:
                    pos.x = - dim_right_to_origin
            elif node.bone_loc_constraint == 'RIGHT':
                dim_left_to_origin = rect.dimensions[0] * rect.pivot[0]
                left = pos.x - dim_left_to_origin
                if left < 0:
                    pos.x = dim_left_to_origin

            # Move mirror node accordingly if existing.
            if node.bone_loc_constraint in {'LEFT', 'RIGHT'} and\
                (_mirror_node := self.mirror_nodes.get(node, None)) is not None:
                mirror_pos = pos.copy()
                mirror_pos.x *= -1
                _mirror_node.rect_transform.move_to(mirror_pos)

        rect.move_to(pos)

    def modal__move_node__exit(self, context: Context, mouse_pos: Vector, cancel: bool) -> None:
        if cancel:
            from ..node_tree import ensure_nodes_cache
            ensure_nodes_cache(context.space_data.node_tree)

            for (node, prev_node_loc) in zip(self.modal_nodes, self.prev_node_location):
                node.rect_transform.move_to(prev_node_loc)
            del self.prev_node_location
            del self.node_location_offset

        self.modal_nodes = None

    def apply_custom_constraints(self) -> None:
        pass



class AP_OT_move_selected_nodes(Operator):
    bl_idname = 'armature_picker.move_selected_nodes'
    bl_label = 'Move Selected Nodes'

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_object=False)

    def invoke(self, context: Context, event: Event) -> OpsReturn:
        self.modal_nodes = context.space_data.node_tree.get_selected_nodes(context, include_active=True)
        return add_modal_handler(context, self)
