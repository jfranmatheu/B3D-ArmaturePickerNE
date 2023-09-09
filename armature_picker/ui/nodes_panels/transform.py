from bpy.types import Context, Panel

from ...utils.ui_layout import draw_section
from ..poll import poll_node



class APNODE_PT_transform(Panel):
    bl_idname = 'APNODE_PT_transform'
    bl_label = 'Transform'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Node'
    
    bl_order = 3

    @classmethod
    def poll(cls, context: Context):
        return poll_node(context)

    def draw(self, context: Context):
        layout = self.layout
        node = context.space_data.node_tree.nodes.active

        section_t = draw_section(layout, 'Transform', icon='ORIENTATION_VIEW')
        node.draw_transform(section_t)
