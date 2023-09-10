from bpy.types import Context, Panel

from ...utils.ui_layout import draw_section
from ..poll import poll_node



class APNODE_PT_style(Panel):
    bl_idname = 'APNODE_PT_style'
    bl_label = 'Style'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Node'
    
    bl_order = 5

    @classmethod
    def poll(cls, context: Context):
        return poll_node(context)

    def draw(self, context: Context):
        layout = self.layout
        node = context.space_data.node_tree.nodes.active

        section_style = draw_section(layout, 'Style', icon='COLOR')
        node.draw_styles(section_style)
