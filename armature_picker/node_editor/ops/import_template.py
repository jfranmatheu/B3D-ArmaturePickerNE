import bpy
from bpy.types import Context, Event, Operator, UILayout
from bpy.props import EnumProperty, StringProperty

from armature_picker.node_editor.poll import poll_check
from armature_picker.utils.operator import OpsReturn
from armature_picker.paths import Paths

from os import listdir



class AP_OT_import_template(Operator):
    bl_idname = 'armature_picker.import_template'
    bl_label = 'Import Template'
    bl_description = "Import ArmaturePicker Template"

    template_name: StringProperty(name="Template", default='', options={'HIDDEN', 'SKIP_SAVE'})
    template_preset: EnumProperty(
        name="Template Preset",
        items=lambda op, _ctx: tuple(
            (filename, filename.replace('_', ' ').title(), "") for filename in listdir(Paths.LIB_TEMPLATES(op.template_name))
        )
    )

    @classmethod
    def draw_templates_in_layout(cls, layout: UILayout) -> None:
        for filename in listdir(Paths.LIB_TEMPLATES()):
            layout.operator(cls.bl_idname, text=filename.replace('_', ' ').title()).template_name = filename


    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'ANY', use_active_object=False, use_picker_editor=True)

    def invoke(self, context: Context, event: Event) -> OpsReturn:
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: Context) -> OpsReturn:
        template_path = Paths.LIB_TEMPLATES(self.template_name, self.template_preset + '.blend', as_path=True)
        if not template_path.exists() or not template_path.is_file():
            self.report({'ERROR'}, "Template could not be found")
            return OpsReturn.CANCEL

        bpy.ops.wm.append(
            filepath=str(template_path.joinpath('NodeGroup', 'Picker')),
            directory=str(template_path.joinpath('NodeGroup')),
            filename=self.template_name.replace('_', ' ').title() + '[' + self.template_preset + ']'
        )

        context.space_data.node_tree = bpy.data.node_groups[-1]
        return OpsReturn.FINISH
