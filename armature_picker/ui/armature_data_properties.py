from bl_ui.properties_data_armature import ArmatureButtonsPanel
from bpy.types import Panel


class DATA_PT_armature_picker(ArmatureButtonsPanel, Panel):
    bl_label = "Picker"

    def draw(self, context):
        layout = self.layout

        arm = context.armature

        layout.prop(arm, "picker", text='')
