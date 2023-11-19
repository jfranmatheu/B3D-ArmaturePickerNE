# from bl_ui.space_node import NODE_MT_context_menu
from bpy.types import Context, UILayout, Menu, UI_MT_button_context_menu, ID
import bpy

from dataclasses import dataclass

from ..poll import poll_check
from armature_picker.ackit import ACK, GLOBALS
from armature_picker.ops import Ops as AP_OPS
from ..widgets import APNODE_Toggle
from ..widgets._bone_picker_common import APNODE_BonePicker_Common
from ..widgets._slider_common import APNODE_Slider_Common


@dataclass
class AlignWidgetOperatorProps:
    name: str
    op_id: str
    axis: str = 'X'
    align_method: str | None = 'MEDIAN'

    def draw(self, layout: UILayout, name: str | None = None, icon: str = 'NONE', icon_value: int = 0) -> None:
        AP_OPS.AlignWidgets.draw_in_layout(
            layout,
            label=name if name is not None else self.name,
            icon=icon,
            icon_value=icon_value,
            op_props={
                'op': self.op_id,
                'axis': self.axis,
                'align_method': self.align_method,
            }
        )


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


class ContextMenu(ACK.Type.UI.MENU):
    label = "Context Menu"

    def draw_ui(self, context: Context, layout: UILayout):
        node_tree = context.space_data.node_tree
        if node_tree is None:
            return

        node_count = len(context.selected_nodes)

        layout.enabled == node_tree.nodes.active is not None or node_count != 0

        if node_count > 1:
            for op_props in align_widgets_props:
                if op_props is None:
                    layout.separator()
                    continue
                op_props.draw(layout)

        layout.separator()

        layout.operator('node.delete', icon='X')


def poll(context: Context) -> bool:
    # print(context.button_pointer, context.button_prop)
    # print(dir(context.button_prop), type(context.button_prop), context.button_prop.type)
    if context.button_prop.is_array:
        return False
    if context.property is None:
        return False,
    if not poll_check(context, 'EDIT', use_active_node=(APNODE_Toggle, APNODE_Slider_Common, APNODE_BonePicker_Common), allow_foreign_area=True):
        return False
    prop: tuple[ID, str, int] = context.property
    datablock, data_path, index = prop
    if index != -1:
        return False
    print("poll property:", prop)
    try:
        value = datablock.path_resolve(data_path) #, coerce=True)
    except (TypeError, AttributeError):
        print("ERROR: Could not resolve data path:", datablock, data_path)
        return False
    # print(value)
    if not isinstance(value, bool):
        return False
    return True


@ACK.Deco.UI_APPEND(UI_MT_button_context_menu, poll=None, prepend=False)
def ext_UIButtonsContextMenu(menu, context: Context):
    op = AP_OPS.PickLayoutProperty.operator
    if op.is_modal_running:
        op.pick_property_from_context(context)
    return
    if not poll(context):
        return
    row = menu.layout.row()
    row.scale_y = 1.5
    AP_OPS.PickLayoutProperty.draw_in_layout(row, label="To Armature-Picker's Active Widget", icon='EYEDROPPER')
    return
    datablock, data_path, index = context.property
    datablock.keyframe_insert(data_path=data_path, index=index, frame=1)
