from bpy.types import Context, Panel

from ...utils.ui_layout import draw_section_h
from ..poll import poll_node



class APNODE_PT_transform(Panel):
    bl_idname = 'APNODE_PT_transform'
    bl_label = 'Transform'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Node'
    
    bl_order = 4

    @classmethod
    def poll(cls, context: Context):
        return poll_node(context)

    def draw(self, context: Context):
        layout = self.layout
        node = context.space_data.node_tree.nodes.active

        header, content = draw_section_h(layout, 'Transform', icon='ORIENTATION_VIEW')
        header.prop(node, 'locked', text="", icon='LOCKED' if node.locked else 'UNLOCKED')
        content.enabled = not node.locked
        node.draw_transform(content, node.rect_transform)
