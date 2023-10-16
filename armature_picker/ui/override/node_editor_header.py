from bl_ui.space_node import NODE_HT_header
from bpy.types import Context, UILayout

from .override_cache import set_cls_attribute



def draw(self, context: Context):
    if context.space_data.tree_type != 'AP_NODETREE':
        self.old_draw(context)
        return
    
    node_tree = context.space_data.node_tree

    snode = context.space_data
    overlay = snode.overlay

    layout: UILayout = self.layout
    layout.template_header()
    if node_tree is not None:
        layout.prop(node_tree, 'picker_mode', text='')
    
    layout.menu('AP_MT_view', text='View')
    layout.menu('AP_MT_utils', text='Utils')

    layout.separator_spacer()

    layout.template_ID(snode, "node_tree", new="node.new_node_tree")

    layout.separator_spacer()
    
    layout.popover(panel="AP_PT_picker_layers", text="", icon='HIDE_OFF')

    # Overlay toggle & popover
    row = layout.row(align=True)
    row.prop(overlay, "show_overlays", icon='OVERLAY', text="")
    sub = row.row(align=True)
    sub.active = overlay.show_overlays
    sub.popover(panel="NODE_PT_overlay", text="")


def register():
    set_cls_attribute(NODE_HT_header, 'draw', draw)
