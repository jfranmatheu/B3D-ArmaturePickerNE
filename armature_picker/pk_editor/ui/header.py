from bpy.types import Context, UILayout
from bl_ui.space_node import NODE_HT_header

from armature_picker.ackit import ACK
from armature_picker.pk_editor.poll import poll_tree_type
from armature_picker.pk_editor.ui.header_menus import ViewMenu, UtilsMenu
from armature_picker.pk_editor.pk_view.popover import AP_PT_widget_type_visibility


@ACK.Deco.UI_OVERRIDE(NODE_HT_header, 'draw', poll=poll_tree_type)
def draw_picker_editor_header(self, context: Context) -> None:
    node_tree = context.space_data.node_tree

    snode = context.space_data
    overlay = snode.overlay

    layout: UILayout = self.layout
    layout.template_header()

    layout = layout.row()
    layout.enabled = context.active_object is not None and context.active_object.type in {
        'ARMATURE'} and context.active_object.mode in {'POSE'}

    if node_tree is not None:
        is_linked = context.space_data.node_tree.library is not None

        layout.prop(node_tree, 'picker_mode', text='')

        ViewMenu.draw_in_layout(layout)

        if node_tree.picker_mode == 'EDIT':
            UtilsMenu.draw_in_layout(layout)
    else:
        is_linked = False

    layout.separator_spacer()

    row = layout.row()
    row.ui_units_x = 9.5
    row.scale_x = .95
    row.template_ID(snode, "node_tree", new="node.new_node_tree", filter='AVAILABLE')

    layout.separator_spacer()

    if node_tree is not None:
        layout.separator()

        # Picker Layers.
        row = layout.row(align=True)
        row.ui_units_x = 6
        # row.popover(panel="AP_PT_picker_layers", text="", icon='RENDERLAYERS') # 'HIDE_OFF')
        row.prop(node_tree, 'active_picker_layer_selector', text='', icon='RENDERLAYERS')
        if not is_linked:
            row.operator('armature_picker.add_picker_layer', text='', icon='ADD')

        # IDEAL SOLUTION!
        # row.prop_tabs_enum(node_tree, 'active_picker_layer_selector')
        # row.operator('armature_picker.add_picker_layer', text='', icon='ADD')
        # row.template_ID_tabs(node_tree, 'picker_layers', new='armature_picker.add_picker_layer')

        # row.prop_with_popover(node_tree, 'active_picker_layer_selector',
        #                       panel="AP_PT_picker_layers",
        #                       text='',
        #                       icon='RENDERLAYERS')
        # text=UILayout.enum_item_name(node_tree, 'active_picker_layer_selector', node_tree.active_picker_layer_selector))

    # Viewport Settings
    if not is_linked:
        AP_PT_widget_type_visibility.draw_in_layout(context, layout)

    # Overlay toggle & popover
    # row = layout.row(align=True)
    # row.prop(overlay, "show_overlays", icon='OVERLAY', text="")
    # sub = row.row(align=True)
    # sub.active = overlay.show_overlays
    # sub.popover(panel="NODE_PT_overlay", text="")
