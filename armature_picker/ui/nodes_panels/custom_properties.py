from rna_prop_ui import draw, rna_idprop_context_value
from bpy.types import Context, Panel

from ...node_editor.nodes._bone_picker_common import APNODE_BonePicker_Common
from ...utils.ui_layout import draw_section
from armature_picker.node_editor.poll import poll_check



MAX_DISPLAY_ROWS = 8


def draw(layout, context, context_member, property_type, *, use_edit=True):
    rna_item, context_member = rna_idprop_context_value(context, context_member, property_type)
    # poll should really get this...
    if not rna_item:
        return

    from bpy.utils import escape_identifier

    if rna_item.id_data.library is not None:
        use_edit = False
    is_lib_override = rna_item.id_data.override_library and rna_item.id_data.override_library.reference

    assert isinstance(rna_item, property_type)

    items = list(rna_item.items())
    items.sort()

    # TODO: Allow/support adding new custom props to overrides.
    if use_edit and not is_lib_override:
        row = layout.row()
        props = row.operator("wm.properties_add", text="New", icon='ADD')
        props.data_path = context_member
        del row
        layout.separator()

    show_developer_ui = context.preferences.view.show_developer_ui
    rna_properties = {prop.identifier for prop in rna_item.bl_rna.properties if prop.is_runtime} if items else None

    layout.use_property_decorate = False

    for key, value in items:
        is_rna = (key in rna_properties)

        # Only show API defined properties to developers.
        if is_rna and not show_developer_ui:
            continue

        to_dict = getattr(value, "to_dict", None)
        to_list = getattr(value, "to_list", None)

        if to_dict:
            value = to_dict()
        elif to_list:
            value = to_list()

        split = layout.split(factor=0.4, align=True)
        label_row = split.row()
        label_row.alignment = 'RIGHT'
        label_row.label(text=key, translate=False)

        value_row = split.row(align=True)
        value_column = value_row.column(align=True)

        is_long_array = to_list and len(value) >= MAX_DISPLAY_ROWS

        if is_rna:
            value_column.prop(rna_item, key, text="")
        elif to_dict or is_long_array:
            props = value_column.operator("wm.properties_edit_value", text="Edit Value")
            props.data_path = context_member
            props.property_name = key
        else:
            value_column.prop(rna_item, '["%s"]' % escape_identifier(key), text="")

        operator_row = value_row.row()
        operator_row.alignment = 'RIGHT'

        # Do not allow editing of overridden properties (we cannot use a poll function
        # of the operators here since they's have no access to the specific property).
        operator_row.enabled = not (is_lib_override and key in rna_item.id_data.override_library.reference)

        if use_edit:
            if is_rna:
                operator_row.label(text="API Defined")
            elif is_lib_override:
                operator_row.active = False
                operator_row.label(text="", icon='DECORATE_LIBRARY_OVERRIDE')
            else:
                props = operator_row.operator("wm.properties_edit", text="", icon='PREFERENCES', emboss=False)
                props.data_path = context_member
                props.property_name = key
                props = operator_row.operator("wm.properties_remove", text="", icon='X', emboss=False)
                props.data_path = context_member
                props.property_name = key
        else:
            # Add some spacing, so the right side of the buttons line up with layouts with decorators.
            operator_row.label(text="", icon='BLANK1')



class APNODE_PT_custom_properties(Panel):
    bl_idname = 'APNODE_PT_custom_properties'
    bl_label = 'Custom Properties'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Widget'
    bl_options = {'DEFAULT_CLOSED'}

    bl_order = 10

    @classmethod
    def poll(cls, context: Context):    
        return poll_check(context, 'EDIT', use_active_node=APNODE_BonePicker_Common)

    def draw(self, context: Context):
        layout = self.layout
        node = context.space_data.node_tree.nodes.active
        use_edit = True

        if not hasattr(node, 'bone_name'):
            return

        pose_bone = context.active_pose_bone
        if pose_bone is None:
            return

        if pose_bone.name != node.bone_name:
            return

        context_member = f'active_object.pose.bones["{pose_bone.name}"]'
        rna_item = context.path_resolve(context_member)
        # poll should really get this...
        if not rna_item:
            return

        from bpy.utils import escape_identifier

        if rna_item.id_data.library is not None:
            use_edit = False
        is_lib_override = rna_item.id_data.override_library and rna_item.id_data.override_library.reference

        # assert isinstance(rna_item, property_type)

        items = list(rna_item.items())
        items.sort()

        # TODO: Allow/support adding new custom props to overrides.
        if use_edit and not is_lib_override:
            row = layout.row()
            props = row.operator("wm.properties_add", text="New", icon='ADD')
            props.data_path = context_member
            del row
            layout.separator()

        show_developer_ui = context.preferences.view.show_developer_ui
        rna_properties = {prop.identifier for prop in rna_item.bl_rna.properties if prop.is_runtime} if items else None

        layout.use_property_decorate = False

        for key, value in items:
            is_rna = (key in rna_properties)

            # Only show API defined properties to developers.
            if is_rna and not show_developer_ui:
                continue

            to_dict = getattr(value, "to_dict", None)
            to_list = getattr(value, "to_list", None)

            if to_dict:
                value = to_dict()
            elif to_list:
                value = to_list()

            split = layout.split(factor=0.4, align=True)
            label_row = split.row()
            label_row.alignment = 'RIGHT'
            label_row.label(text=key, translate=False)

            value_row = split.row(align=True)
            value_column = value_row.column(align=True)

            is_long_array = to_list and len(value) >= MAX_DISPLAY_ROWS

            if is_rna:
                value_column.prop(rna_item, key, text="")
            elif to_dict or is_long_array:
                props = value_column.operator("wm.properties_edit_value", text="Edit Value")
                props.data_path = context_member
                props.property_name = key
            else:
                value_column.prop(rna_item, '["%s"]' % escape_identifier(key), text="")

            operator_row = value_row.row()
            operator_row.alignment = 'RIGHT'

            # Do not allow editing of overridden properties (we cannot use a poll function
            # of the operators here since they's have no access to the specific property).
            operator_row.enabled = not (is_lib_override and key in rna_item.id_data.override_library.reference)

            if use_edit:
                if is_rna:
                    operator_row.label(text="API Defined")
                elif is_lib_override:
                    operator_row.active = False
                    operator_row.label(text="", icon='DECORATE_LIBRARY_OVERRIDE')
                else:
                    props = operator_row.operator("wm.properties_edit", text="", icon='PREFERENCES', emboss=False)
                    props.data_path = context_member
                    props.property_name = key
                    props = operator_row.operator("wm.properties_remove", text="", icon='X', emboss=False)
                    props.data_path = context_member
                    props.property_name = key
            else:
                # Add some spacing, so the right side of the buttons line up with layouts with decorators.
                operator_row.label(text="", icon='BLANK1')
