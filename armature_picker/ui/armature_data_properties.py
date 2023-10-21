from bl_ui.properties_data_armature import ArmatureButtonsPanel
from bpy.types import Panel


class DATA_PT_armature_picker(ArmatureButtonsPanel, Panel):
    bl_label = "Picker"

    def draw(self, context):
        layout = self.layout

        arm = context.armature

        if arm.picker is not None:
            layout.template_ID(arm, "picker")
        else:
            layout.prop(arm, "picker", text='')
