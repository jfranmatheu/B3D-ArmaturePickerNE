# from bl_ui.space_node import NODE_MT_context_menu
from bpy.types import Context, UILayout, Menu

from dataclasses import dataclass


@dataclass
class AlignWidgetOperatorProps:
    name: str
    op_id: str
    axis: str = 'X'
    align_method: str | None = None

    def draw(self, layout: UILayout, name: str | None = None, icon: str = 'NONE') -> None:
        op = layout.operator('armature_picker.align_widgets', text=name if name is not None else self.name, icon=icon)
        op.op = self.op_id
        op.axis = self.axis
        if self.align_method:
            op.align_method = self.align_method



EVEN_DISTRIBUTION_HOR = AlignWidgetOperatorProps(
    'Even Distribution (Horizontal)',
    'EVEN_DISTRIBUTION', 'X'
)
EVEN_DISTRIBUTION_VER = AlignWidgetOperatorProps(
    'Even Distribution (Vertical)',
    'EVEN_DISTRIBUTION', 'Y'
)
ALIGN_VER_ACTIVE = AlignWidgetOperatorProps(
    'Align to Active (Vertical)',
    'ALIGN', 'X',
    align_method='ACTIVE'
)
ALIGN_HOR_ACTIVE  = AlignWidgetOperatorProps(
    'Align to Active (Horizontal)',
    'ALIGN', 'Y',
    align_method='ACTIVE'
)
ALIGN_VER_MEDIAN = AlignWidgetOperatorProps(
    'Align (Vertical)',
    'ALIGN', 'X',
    align_method='MEDIAN'
)
ALIGN_HOR_MEDIAN  = AlignWidgetOperatorProps(
    'Align (Horizontal)',
    'ALIGN', 'Y',
    align_method='MEDIAN'
)
ALIGN_VER_MIN = AlignWidgetOperatorProps(
    'Align to Min (Vertical)',
    'ALIGN', 'X',
    align_method='MIN'
)
ALIGN_HOR_MIN  = AlignWidgetOperatorProps(
    'Align to Min (Horizontal)',
    'ALIGN', 'Y',
    align_method='MIN'
)
ALIGN_VER_MAX = AlignWidgetOperatorProps(
    'Align to Max (Vertical)',
    'ALIGN', 'X',
    align_method='MAX'
)
ALIGN_HOR_MAX  = AlignWidgetOperatorProps(
    'Align to Max (Horizontal)',
    'ALIGN', 'Y',
    align_method='MAX'
)
NORMALIZE_SIZE = AlignWidgetOperatorProps(
    'Normalize Size',
    'NORMALIZE_SIZE'
)
MATCH_ACTIVE_SIZE = AlignWidgetOperatorProps(
    'Match Active Size',
    'MATCH_ACTIVE_SIZE'
)
MATCH_MIN_SIZE = AlignWidgetOperatorProps(
    'Match Min Size',
    'MATCH_MIN_SIZE'
)
MATCH_MAX_SIZE = AlignWidgetOperatorProps(
    'Match Max Size',
    'MATCH_MAX_SIZE'
)
MATCH_ACTIVE_ROTATION = AlignWidgetOperatorProps(
    'Match Active Rotation',
    'MATCH_ACTIVE_ROTATION'
)


class AlignWidgetOpPreset:
    ALIGN_HOR_ACTIVE = ALIGN_HOR_ACTIVE
    ALIGN_VER_ACTIVE = ALIGN_VER_ACTIVE
    ALIGN_HOR_MEDIAN = ALIGN_HOR_MEDIAN
    ALIGN_VER_MEDIAN = ALIGN_VER_MEDIAN
    ALIGN_HOR_MIN = ALIGN_HOR_MIN
    ALIGN_VER_MIN = ALIGN_VER_MIN
    ALIGN_HOR_MAX = ALIGN_HOR_MAX
    ALIGN_VER_MAX = ALIGN_VER_MAX

    EVEN_DISTRIBUTION_HOR = EVEN_DISTRIBUTION_HOR
    EVEN_DISTRIBUTION_VER = EVEN_DISTRIBUTION_VER

    NORMALIZE_SIZE = NORMALIZE_SIZE

    MATCH_ACTIVE_SIZE = MATCH_ACTIVE_SIZE
    MATCH_MIN_SIZE = MATCH_MIN_SIZE
    MATCH_MAX_SIZE = MATCH_MAX_SIZE

    MATCH_ACTIVE_ROTATION = MATCH_ACTIVE_ROTATION


align_widgets_props = (
    EVEN_DISTRIBUTION_HOR,
    EVEN_DISTRIBUTION_VER,
    None,
    ALIGN_VER_ACTIVE,
    ALIGN_HOR_ACTIVE,
    None,
    NORMALIZE_SIZE,
    MATCH_ACTIVE_SIZE,
    MATCH_ACTIVE_ROTATION
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
