from bpy.types import Context, Event, Node
from mathutils import Vector

from ...utils.operator import OpsReturn
from ...utils.event import get_mouse_pos, EventType, EventValue
from ...utils.node_editor import get_node_editor_zoom, get_node_editor_offset, get_node_editor_region_coord


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
        zoom = get_node_editor_zoom(context)
        inv_zoom = 1/zoom
        offset = get_node_editor_offset(context)

        def move_node(_node: Node, _node_loc_offset: Vector):
            _node.rect_transform.move_to((mouse_pos - offset + _node_loc_offset) * inv_zoom)

        {move_node(node, node_loc_offset) for (node, node_loc_offset) in zip(self.modal_nodes, self.node_location_offset)}

    def modal__move_node__exit(self, context: Context, mouse_pos: Vector, cancel: bool) -> None:
        if cancel:
            from ..node_tree import ensure_nodes_cache
            ensure_nodes_cache(context.space_data.node_tree)

            for (node, prev_node_loc) in zip(self.modal_nodes, self.prev_node_location):
                node.rect_transform.move_to(prev_node_loc)
            del self.prev_node_location
            del self.node_location_offset

        self.modal_nodes = None
