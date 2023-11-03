import bpy
from bpy.types import Context, Event, Operator, Armature
from mathutils import Vector

from armature_picker.node_editor.poll import poll_check
from armature_picker.utils.operator import OpsReturn, add_modal_handler
from armature_picker.utils.event import EventType, EventValue, get_mouse_pos
from armature_picker.node_editor.node_tree import refresh_nodes_cache
from .add_node.op_add_node import new_node
from .move_nodes import MoveNodesModal
from armature_picker.node_editor.nodes._bone_picker_common import APNODE_BonePicker_Common


class AP_OT_import_selected_bones(MoveNodesModal, Operator):
    bl_idname = 'armature_picker.import_selected_bones'
    bl_label = 'Import Selected Bones'
    bl_description = "Imports the selected bones in the 3d viewport and converts them into bone picker widgets in the picker editor"

    @classmethod
    def poll(cls, context: Context):
        return poll_check(context, 'EDIT', use_active_object=True, use_picker_editor=True, use_active_node=False)

    def invoke(self, context: Context, event: Event) -> OpsReturn:
        selected_bones = context.selected_pose_bones_from_active_object
        if selected_bones is None or len(selected_bones) == 0:
            return OpsReturn.CANCEL
        self.armature: Armature = context.active_object.data
        self.get_node = context.space_data.node_tree.nodes.get
        self.get_bone = get_bone = self.armature.bones.get
        self.selected_bones = set([get_bone(bone.name) for bone in selected_bones])
        self.created_nodes = []
        self.next_node(context, event)
        return add_modal_handler(context, self)

    def create_bone_picker(self, context: Context, event: Event, bone) -> APNODE_BonePicker_Common:
        self.armature.bones.active = bone
        return new_node(context, 'AP_NODE_bone_picker', event)

    def next_node(self, context: Context, event: Event):
        if len(self.selected_bones) == 0:
            return

        bone = self.selected_bones.pop()
        if bone is None:
            return self.next_node(context, event)

        # SKIP THIS BONE IF THERE'S A BONE-PICKER NODE FOR IT ALREADY!
        if node := self.get_node(bone.name, None):
            return self.next_node(context, event)

        # Create BonePicker out of this bone.
        node = self.create_bone_picker(context, event, bone)
        print(node.mirror_bone_name)

        if mirror_bone := node.get_mirror_bone(context):
            print(mirror_bone)
            # If the mirror bone is in the modal selection set, remove it!
            # to avoid duplicate since we will process L/R bones together.
            if mirror_bone in self.selected_bones:
                self.selected_bones.remove(mirror_bone)

            # Skip creating mirror node if it already exist.
            if node.get_mirror_node() is None:
                self.create_bone_picker(context, event, mirror_bone)

        refresh_nodes_cache(context.space_data.node_tree)

        # Start modal process :-)
        self.modal_nodes = [node]
        self.created_nodes.append(node)
        self.modal__move_node__enter(context, event, get_mouse_pos(event))
        context.region.tag_redraw()

    def modal(self, context: Context, event: Event) -> OpsReturn:
        if event.type in {EventType.RIGHTMOUSE, EventType.ESC}:
            remove_node = context.space_data.node_tree.nodes.remove
            for node in self.created_nodes:
                remove_node(node)
            refresh_nodes_cache(context.space_data.node_tree)
            del self.created_nodes
            del self.modal_nodes
            return OpsReturn.CANCEL

        if event.type == EventType.LEFTMOUSE and event.value == EventValue.RELEASE:
            if len(self.selected_bones) == 0:
                self.modal__move_node__exit(context, get_mouse_pos(event), cancel=False)
                return OpsReturn.FINISH
            else:
                self.next_node(context, event)
                return OpsReturn.RUN

        if event.type in {EventType.MOUSEMOVE, EventType.INBETWEEN_MOUSEMOVE}:
            self.modal__move_node__update(context, event, get_mouse_pos(event))

        return OpsReturn.RUN
