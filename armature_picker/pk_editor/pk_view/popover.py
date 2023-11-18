from bpy.types import Context, Panel

from armature_picker.pk_editor.poll import poll_check


attr_widget_types = (
    # Widgets.
    ("bone_picker", "Bone Picker"),
    ("bone_picker_geo", "Bone Picker Geo"),
    (None, None),
    ('toggle', "Toggle"),
    (None, None),
    ("slider_linear", "Slider Lineal"),
    ("slider_linear_2d", "Slider Lineal 2D"),
    ("slider_radial", "Slider Radial"),
    (None, None),
    # Others.
    ("label", "Label"),
    ("image", "Image"),
    (None, None),
    ('button_script', "Button Script"),
)


class AP_PT_widget_type_visibility(Panel):
    bl_idname = 'AP_PT_widget_type_visibility'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'HEADER'
    bl_label = "View Object Types"
    bl_ui_units_x = 7

    @classmethod
    def get_icon(cls, context: Context) -> str:
        if not poll_check(context, 'ANY', use_picker_editor=True):
            return 'NONE'

        node_tree = context.space_data.node_tree
        if node_tree is None:
            return 'VIS_SEL_11'

        picker_view = node_tree.picker_view

        vis_state = 1
        sel_state = 1

        for attr, _attr_name in attr_widget_types:
            if attr is None:
                continue

            if vis_state == 1:
                attr_v = "show_widget_" + attr
                vis_state = 1 if getattr(picker_view, attr_v) else 0
            elif sel_state == 1:
                attr_s = "show_widget_select_" + attr
                sel_state = 1 if getattr(picker_view, attr_s) else 0

            if vis_state == 0 and sel_state == 0:
                break

        return f'VIS_SEL_{vis_state}{sel_state}'

    @classmethod
    def draw_in_layout(cls, context: Context, layout) -> None:
        layout.popover(
            panel=cls.bl_idname,
            icon=cls.get_icon(context),
            text="",
        )

    # Allows derived classes to pass view child other than context.space_data.
    # This is used by the official VR add-on, which passes XrSessionSettings
    # since VR has a 3D view that only exists for the duration of the VR session.
    def draw(self, context):
        if not poll_check(context, 'ANY', use_active_object=True, use_picker_editor=True):
            return

        node_tree = context.space_data.node_tree
        if node_tree is None:
            return

        picker_view = node_tree.picker_view
        show_select = node_tree.picker_mode == 'EDIT'

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.label(text="Widget Types Visibility")
        layout.separator()
        col = layout.column()

        for attr, attr_name in attr_widget_types:
            if attr is None:
                col.separator()
                continue

            attr_v = "show_widget_" + attr
            icon_v = 'HIDE_OFF' if getattr(picker_view, attr_v) else 'HIDE_ON'

            row = col.row(align=True)
            row.alignment = 'RIGHT'

            row.label(text=attr_name)
            row.prop(picker_view, attr_v, text="", icon=icon_v, emboss=False)

            if show_select:
                attr_s = "show_widget_select_" + attr
                icon_s = 'RESTRICT_SELECT_OFF' if getattr(picker_view, attr_s) else 'RESTRICT_SELECT_ON'

                rowsub = row.row(align=True)
                rowsub.active = getattr(picker_view, attr_v)
                rowsub.prop(picker_view, attr_s, text="", icon=icon_s, emboss=False)
