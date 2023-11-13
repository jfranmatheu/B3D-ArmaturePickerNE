import bpy
from bpy.types import Context, Event, Operator, NodeTree
from bpy.props import IntProperty, StringProperty

from armature_picker.pk_editor.poll import poll_check
from armature_picker.utils.operator import OpsReturn


class AddPickerLayer(Operator):
    bl_idname = 'armature_picker.add_picker_layer'
    bl_label = 'Add Picker Layer'

    layer_name: StringProperty(name="Layer Name", default='New Layer')

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, use_active_object=False)

    def invoke(self, context: Context, event: Event) -> OpsReturn:
        return context.window_manager.invoke_props_dialog(self, width=300)

    def execute(self, context: Context) -> OpsReturn:
        context.space_data.node_tree.new_layer(name=self.layer_name)
        return OpsReturn.FINISH


class RemoveActivePickerLayer(Operator):
    bl_idname = 'armature_picker.remove_active_picker_layer'
    bl_label = 'W A R N I N G !\nAre you sure you want to remove ALL\nthe associated Widgets to this Layer?'
    bl_desctiption = "Remove Active Picker Layer (and all its associated widgets)\nIMPORTANT! This action can't be undone"

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, use_active_object=False) and len(context.space_data.node_tree.picker_layers) > 1

    def invoke(self, context: Context, event: Event):
        # self.widgets_to_remove = len(context.space_data.node_tree.widgets_from_active_layer)
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context: Context) -> OpsReturn:
        node_tree: NodeTree = context.space_data.node_tree

        if node_tree.active_picker_layer_index == -1:
            return OpsReturn.CANCEL

        if node_tree.active_picker_layer_index >= len(node_tree.picker_layers):
            return OpsReturn.CANCEL

        # Delete picker widgets from active picker layer.
        bpy.ops.node.select_all(False, action='DESELECT')
        widgets = node_tree.widgets_from_active_layer
        if len(widgets) != 0:
            for widget in widgets:
                widget.select = True
            node_tree.nodes.active = widgets[0]
            bpy.ops.node.delete(False)

        # Delete active picker layer from picker.
        node_tree.picker_layers.remove(node_tree.active_picker_layer_index)
        node_tree.active_picker_layer_index = ( len(node_tree.picker_layers) - 1 )
        return OpsReturn.FINISH


class AP_OT_duplicate_active_layer(Operator):
    bl_idname = 'armature_picker.duplicate_active_layer'
    bl_label = 'Duplicate Active Layer'
    bl_description = "Make a duplicate of the active layer and all of its content"

    copy_layer_name: StringProperty(name="Copy Layer Name", default='Layer Copy')

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_object=False, use_picker_editor=True, use_active_node=False)

    def invoke(self, context: Context, _event: Event) -> OpsReturn:
        self.copy_layer_name = context.space_data.node_tree.active_picker_layer.name + '.copy'
        return context.window_manager.invoke_props_dialog(self, width=320)

    def execute(self, context: Context) -> OpsReturn:
        from armature_picker.pk_editor.node_tree import AP_NodeTree, refresh_nodes_cache
        picker: AP_NodeTree = context.space_data.node_tree
        widgets = picker.widgets_from_active_layer
        if len(widgets) == 0:
            return OpsReturn.CANCEL
        bpy.ops.node.select_all(False, action='DESELECT')
        for widget in widgets:
            widget.select = True
        picker.nodes.active = widgets[0]
        picker_layer_id = picker.new_layer(self.copy_layer_name).uuid
        bpy.ops.node.duplicate(False, keep_inputs=False)
        # When copying node, it will get asigned the active layer ID...
        # for copy_node in context.selected_nodes:
        #     copy_node.picker_layer = picker_layer_id
        refresh_nodes_cache(picker)
        return OpsReturn.FINISH
