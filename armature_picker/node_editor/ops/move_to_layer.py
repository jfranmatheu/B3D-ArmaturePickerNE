import bpy
from bpy.types import Context, Event, Operator, UILayout
from bpy.props import EnumProperty, StringProperty

from armature_picker.node_editor.poll import poll_check
from armature_picker.utils.operator import OpsReturn



class AP_OT_move_selected_to_another_layer(Operator):
    bl_idname = 'armature_picker.move_selected_to_another_layer'
    bl_label = 'Move Selected to Picker Layer'
    bl_description = "Move Selected Widgets to another Picker Layer"

    def get_picker_layers(self, context) -> tuple[tuple[str, str, str]]:
        active_index_str = str(context.space_data.node_tree.active_picker_layer_index)
        return tuple(l for l in context.space_data.node_tree.get_picker_layers(context) if l[0] != active_index_str)

    picker_layer: EnumProperty(
        name="Picker Layers",
        items=get_picker_layers
    )

    @classmethod
    def poll(cls, context: Context):
        if not poll_check(context, 'EDIT', use_active_object=False, use_picker_editor=True, use_active_node=True):
            return False
        if len(context.space_data.node_tree.picker_layers) <= 1:
            return False
        if context.selected_nodes is None:
            return False
        active_picker_layer_id = context.space_data.node_tree.active_picker_layer_id
        return len([node for node in context.selected_nodes if node.picker_layer == active_picker_layer_id]) != 0

    def invoke(self, context: Context, _event: Event) -> OpsReturn:
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: Context) -> OpsReturn:
        from armature_picker.node_editor.node_tree import AP_NodeTree
        picker: AP_NodeTree = context.space_data.node_tree
        picker_layer_id = picker.picker_layers[int(self.picker_layer)].uuid
        for widget in picker.widgets_selected:
            widget.picker_layer = picker_layer_id
        picker.active_picker_layer_index = int(self.picker_layer)
        return OpsReturn.FINISH
