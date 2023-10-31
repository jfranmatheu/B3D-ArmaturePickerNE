from bpy.types import Context, Panel

from ...utils.ui_layout import draw_section, draw_section_h
from armature_picker.node_editor.poll import poll_check
from ...node_editor.nodes.bone_picker.node import AP_BonePickerNode
from ..context_menu import AlignWidgetOpPreset as AlignOpPreset
from armature_picker.icons import Icons as _Icons

Icons = _Icons.ALIGN



class APTOOL_PT_align_widgets(Panel):
    bl_idname = 'APTOOL_PT_align_widgets'
    bl_label = 'Align Widgets'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    bl_options = {'HIDE_HEADER'}

    bl_order = 0

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_object=False, use_active_node=True)

    def draw(self, context: Context):
        layout = self.layout
        layout.scale_y = 1.2

        content_align = draw_section(layout,'A l i g n m e n t', icon='ALIGN_CENTER')
        first_row = content_align.row(align=False)
        col1 = first_row.column(align=True)
        col2 = first_row.column(align=True)
        col3 = first_row.column(align=True)

        col1.label(text="", icon='BLANK1')
        col2.label(text="Horizontal")
        col3.label(text="Vertical")

        col1.label(text="To Active")
        col1.label(text="Min")
        col1.label(text="Median")
        col1.label(text="Max")

        AlignOpPreset.ALIGN_HOR_ACTIVE.draw(col2, name='', icon_value=Icons.ALIGN_MIDDLE_ACTIVE.icon_id)
        AlignOpPreset.ALIGN_VER_ACTIVE.draw(col3, name='', icon_value=Icons.ALIGN_CENTER_ACTIVE.icon_id)

        AlignOpPreset.ALIGN_HOR_MIN.draw(col2, name='', icon_value=Icons.ALIGN_BOTTOM.icon_id)
        AlignOpPreset.ALIGN_VER_MIN.draw(col3, name='', icon_value=Icons.ALIGN_LEFT.icon_id)

        AlignOpPreset.ALIGN_HOR_MEDIAN.draw(col2, name='', icon_value=Icons.ALIGN_MIDDLE.icon_id)
        AlignOpPreset.ALIGN_VER_MEDIAN.draw(col3, name='', icon_value=Icons.ALIGN_CENTER.icon_id)

        AlignOpPreset.ALIGN_HOR_MAX.draw(col2, name='', icon_value=Icons.ALIGN_TOP.icon_id)
        AlignOpPreset.ALIGN_VER_MAX.draw(col3, name='', icon_value=Icons.ALIGN_RIGHT.icon_id)

        # ----------------------------------------------------------------

        content_distrib = draw_section(layout,'E v e n   D i s t r i b u t i o n', icon='COLLAPSEMENU')
        content_distrib = content_distrib.row()

        AlignOpPreset.EVEN_DISTRIBUTION_HOR.draw(content_distrib, name='Horizontal')
        AlignOpPreset.EVEN_DISTRIBUTION_VER.draw(content_distrib, name='Vertical')

        # ----------------------------------------------------------------

        content_others = draw_section(layout, 'O t h e r s', icon='UV_ISLANDSEL')

        AlignOpPreset.NORMALIZE_SIZE.draw(content_others, name='Normalize Sizes')

        col = content_others.column(align=True, heading='Match Size')
        col.label(text='Match Size from...')
        row = col.row()
        AlignOpPreset.MATCH_ACTIVE_SIZE.draw(row, name='Active')
        AlignOpPreset.MATCH_MIN_SIZE.draw(row, name='Min')
        AlignOpPreset.MATCH_MAX_SIZE.draw(row, name='Max')

        content_others.separator()

        AlignOpPreset.MATCH_ACTIVE_ROTATION.draw(content_others, name='Match Active Rotation')
