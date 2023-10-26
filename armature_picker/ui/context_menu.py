# from bl_ui.space_node import NODE_MT_context_menu
from bpy.types import Context, UILayout, Menu

from dataclasses import dataclass


@dataclass
class AlignWidgetOperatorProps:
    name: str
    op_id: str
    axis: str = 'X'
    align_method: str | None = None
    
    def draw(self, layout: UILayout) -> None:
        op = layout.operator('armature_picker.align_widgets', text=self.name)
        op.op = self.op_id
        op.axis = self.axis
        if self.align_method:
            op.align_method = self.align_method


align_widgets_props = (
    AlignWidgetOperatorProps(
        'Even Distribution (Horizontal)',
        'EVEN_DISTRIBUTION', 'X'
    ),
    AlignWidgetOperatorProps(
        'Even Distribution (Vertical)',
        'EVEN_DISTRIBUTION', 'Y'
    ),
    None,
    AlignWidgetOperatorProps(
        'Align to Active (Vertical)',
        'ALIGN', 'X',
        align_method='ACTIVE'
    ),
    AlignWidgetOperatorProps(
        'Align to Active (Horizontal)',
        'ALIGN', 'Y',
        align_method='ACTIVE'
    ),
    None,
    AlignWidgetOperatorProps(
        'Normalize Size',
        'NORMALIZE_SIZE'
    ),
    AlignWidgetOperatorProps(
        'Match Active Size',
        'MATCH_ACTIVE_SIZE'
    )
)


class AP_MT_context_menu(Menu):
    bl_idname = 'AP_MT_context_menu'
    bl_label = "Context Menu"

    def draw(self, context: Context):
        node_tree = context.space_data.node_tree
        if node_tree is None:
            return
        
        node_count = len(context.selected_nodes)

        layout: UILayout = self.layout

        layout.enabled == node_tree.nodes.active is not None or node_count != 0

        if node_count > 1:
            for op_props in align_widgets_props:
                if op_props is None:
                    layout.separator()
                    continue
                op_props.draw(layout)

        layout.separator()

        layout.operator('node.delete', icon='X')


# def register():
#     set_cls_attribute(NODE_MT_context_menu, 'draw', draw)
