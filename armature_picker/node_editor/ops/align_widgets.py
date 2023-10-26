from bpy.types import Context, Operator
from bpy.props import EnumProperty

from armature_picker.node_editor.poll import poll_check
from armature_picker.utils.operator import OpsReturn
from armature_picker.node_editor.nodes._base import AP_Node


def get_origin_component(_node: AP_Node, axis: int) -> int:
    return _node.rect_transform.origin[axis]

def set_origin_component(_node: AP_Node, axis: int, value: int) -> int:
    _node.rect_transform.origin[axis] = int(value)

def get_size_component(_node: AP_Node, axis: int) -> int:
    return _node.rect_transform.dimensions[axis]

def set_size_component(_node: AP_Node, axis: int, value: int) -> int:
    _node.rect_transform.dimensions[axis] = int(value)


class AP_OT_align_widgets(Operator):
    bl_idname = 'armature_picker.align_widgets'
    bl_label = 'Align/Distribute Widgets'
    bl_description = "Align or Distribute Widgets horizontally or vertically"
    bl_options = {'REGISTER', 'UNDO'}

    op: EnumProperty(
        name="Method",
        items=(
            ('EVEN_DISTRIBUTION', "Even Distribution", ""),
            ('ALIGN', "Align", ""),
            ('NORMALIZE_SIZE', "Normalize Size", "Normalize selected widget sizes"),
            ('MATCH_ACTIVE_SIZE', "Match Active Size", "Copy the size from the active widget"),
            ('MATCH_MIN_SIZE', "Match Minimum Size", "Copy the size from the widget with the minimum size"),
            ('MATCH_MAX_SIZE', "Match Maximum Size", "Copy the size from the active with the maximum size"),
        )
    )

    align_method: EnumProperty(
        name="Align Method",
        items=(
            ('MEDIAN', "Median", "Use the median values of the selected widgets"),
            ('ACTIVE', "Active", "Use the active widget values"),
            ('MIN', "Min", "Use the minimum value from the selected widgets"),
            ('MAX', "Max", "Use the maximum value from the selected widgets"),
        )
    )

    axis: EnumProperty(
        name="Axis",
        items=(
            ('X', "X", ""),
            ('Y', "Y", ""),
        )
    )

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_picker_editor=True, use_active_node=True)

    def even_distribute(self, nodes: list[AP_Node], axis: int) -> None:
        # Short nodes...
        nodes.sort(key=lambda _node: get_origin_component(_node, axis))

        min_node = nodes[0]
        max_node = nodes[-1]
        tot_dist = get_origin_component(max_node, axis) - get_origin_component(min_node, axis)

        even_dist = tot_dist / (len(nodes) - 1)
        start_value = get_origin_component(min_node, axis)

        for index, node in enumerate(nodes[1:-1], start=1):
            set_origin_component(node, axis, start_value + index * even_dist)

    def align(self, active_node: AP_Node, nodes: list[AP_Node], axis: int) -> None:
        if active_node is not None and self.align_method == 'ACTIVE':
            value = get_origin_component(active_node, axis)
            nodes.remove(active_node)
        elif self.align_method == 'MIN':
            value = min([get_origin_component(_node, axis) for _node in nodes])
        elif self.align_method == 'MAX':
            value = max([get_origin_component(_node, axis) for _node in nodes])
        else:
            value = sum([get_origin_component(_node, axis) for _node in nodes]) / len(nodes)

        for node in nodes:
            set_origin_component(node, axis, value)

    def normalize_size(self, nodes: list[AP_Node]) -> None:
        ''' The typical normalization. '''
        average_size = (
            int(sum([get_size_component(_node, 0) for _node in nodes]) / len(nodes)),
            int(sum([get_size_component(_node, 1) for _node in nodes]) / len(nodes))
        )
        for node in nodes:
            node.rect_transform.dimensions = average_size

    def match_active_size(self, active_node: AP_Node, nodes: list[AP_Node]) -> None:
        ''' Actually matching size of active node. '''
        if active_node is None:
            return
        active_node_size = active_node.rect_transform.dimensions
        for node in nodes:
            if node == active_node:
                continue
            node.rect_transform.dimensions = active_node_size
    
    def match_min_size(self, nodes: list[AP_Node]) -> None:
        min_size = (
            int(min([get_size_component(_node, 0) for _node in nodes])),
            int(min([get_size_component(_node, 1) for _node in nodes])),
        )
        for node in nodes:
            node.rect_transform.dimensions = min_size

    def match_max_size(self, nodes: list[AP_Node]) -> None:
        max_size = (
            int(max([get_size_component(_node, 0) for _node in nodes])),
            int(max([get_size_component(_node, 1) for _node in nodes])),
        )
        for node in nodes:
            node.rect_transform.dimensions = max_size

    def execute(self, context: Context) -> OpsReturn:
        node_tree = context.space_data.node_tree
        nodes: list[AP_Node] = list(node_tree.get_selected_nodes(context, include_active=True))
        if len(nodes) < 2:
            return OpsReturn.CANCEL
        
        axis_int = 0 if self.axis == 'X' else 1

        if self.op == 'EVEN_DISTRIBUTION':
            if len(nodes) < 3:
                return OpsReturn.CANCEL
            self.even_distribute(nodes, axis_int)

        elif self.op == 'ALIGN':
            self.align(node_tree.nodes.active, nodes, axis_int)

        elif self.op == 'NORMALIZE_SIZE':
            self.normalize_size(nodes)

        elif self.op == 'MATCH_ACTIVE_SIZE':
            self.match_active_size(node_tree.nodes.active, nodes)

        elif self.op == 'MATCH_MIN_SIZE':
            self.match_min_size(nodes)

        elif self.op == 'MATCH_MAX_SIZE':
            self.match_max_size(nodes)

        return OpsReturn.FINISH
