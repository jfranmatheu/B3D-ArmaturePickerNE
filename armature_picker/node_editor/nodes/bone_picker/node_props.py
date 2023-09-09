from bpy.types import Context, UILayout
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty

from ....utils.ui_layout import draw_section


class APNODE_BonePicker_NodeProps:

    # UPDATE FUNCTIONS
    # ----------------------------------------------------------------
    def update_label(self, context: Context) -> None:
        self.update_dimensions(context)
        self.dirty_label = True
        self.update_graphics(context)

    def update_bone_name(self, context: Context) -> None:
        if self.label == '':
            self.label = self.bone_name.replace('_', ' ').replace('.', ' ').title()


    # BUTTON PROPERTIES
    # ----------------------------------------------------------------
    label: StringProperty(
        name="Label",
        description="Button label",
        update=update_label,
        options={'TEXTEDIT_UPDATE'}
    )

    bone_name: StringProperty(
        name="Bone Name",
        description="Name of the bone to control",
        update=update_bone_name
    )

    def draw_buttons_ext(self, context: Context, layout: UILayout) -> None:
        layout.prop(self, 'label')
        layout.prop(self, 'bone_name')
