import bpy
from bpy.types import NodeTree, Context, Event
from mathutils import Vector
import gpu

from ..utils.node_editor import get_node_editor_zoom, get_node_editor_view_point, get_node_editor_offset, get_node_editor_region_coord

# Implementation of custom nodes from Python

hovered_node = ''


# Derived from the NodeTree base type, similar to Menu, Operator, Panel, etc.
class AP_NodeTree(NodeTree):
    # Description string
    '''A custom node tree type that will show up in the editor type list'''
    # Optional identifier string. If not explicitly defined, the python class name is used.
    bl_idname = 'AP_NODETREE'
    # Label for nice name display
    bl_label = "Armature Picker"
    # Icon identifier
    bl_icon = 'OUTLINER_OB_ARMATURE' # CON_ARMATURE

    def _test_select(self, context: Context, loc) -> int:
        # FIX SCROLLBARS.
        ui_scale = context.preferences.system.ui_scale
        region = context.region
        scroll_bar_thickness = 10 * ui_scale
        if loc[0] > (region.width - scroll_bar_thickness):
            return -1
        if loc[1] < scroll_bar_thickness:
            return -1

        global hovered_node
        zoom = get_node_editor_zoom(context)
        offset = get_node_editor_offset(context)
        view_loc = get_node_editor_view_point(context, loc)
        for node in self.nodes:
            if hasattr(node, 'test_select'):
                if node.test_select(context, view_loc, zoom, offset):
                    hovered_node = node.uuid
                    print("hovered_node", node.label)
                    return 1
        hovered_node = None
        return 1

    def set_inject_modal(self, context: Context, event: Event, modal_callback: callable, modal_enter_callback: callable = None, modal_exit_callback: callable = None) -> None:
        self.inject_modal = modal_callback
        self.inject_modal_exit = modal_exit_callback
        if modal_enter_callback is not None:
            modal_enter_callback(context, event, self.mouse_pos)

    def _invoke(self, context: Context, event: Event) -> set[str]:
        # Skip navigation km.
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            if event.type == 'WHEELUPMOUSE':
                bpy.ops.view2d.zoom_in('INVOKE_DEFAULT')
            elif event.type == 'WHEELDOWNMOUSE':
                bpy.ops.view2d.zoom_out('INVOKE_DEFAULT')
            elif event.type == 'MIDDLEMOUSE':
                bpy.ops.view2d.pan('INVOKE_DEFAULT')
            return {'PASS_THROUGH'}

        self.mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))

        global hovered_node
        ## print("hovered_node", hovered_node)
        if hovered_node is None:
            # Interact with blank space.
            if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                new_node = self.nodes.new('AP_NODE_bone_picker')
                if context.active_bone is not None:
                    new_node.bone_name = context.active_bone.name
                new_node['new'] = 1
                self.active_node = new_node
                self.set_inject_modal(context, event,
                                      modal_callback=self.modal__move_node__update,
                                      modal_enter_callback=self.modal__move_node__enter,
                                      modal_exit_callback=self.modal__move_node__exit)
                ## print("Create new AP_NODE_bone_picker")
                return {'RUNNING_MODAL'}

        if self.nodes.active is not None:
            if event.type == 'G' and event.value == 'RELEASE':
                self.active_node = self.nodes.active
                self.set_inject_modal(context, event,
                                      modal_callback=self.modal__move_node__update,
                                      modal_enter_callback=self.modal__move_node__enter,
                                      modal_exit_callback=self.modal__move_node__exit)
                return {'RUNNING_MODAL'}

        self.active_node = None
        if hovered_node is None:
            return {'FINISHED'}

        # Interact with a node.
        if node := self.nodes.get(hovered_node, None):
            ## print("hovered Node", node)
            node.invoke(context, event)

        return {'FINISHED'}


    def _modal(self, context: Context, event: Event, tweak: str) -> set[str]:
        self.mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))

        if self.inject_modal is not None:
            if self.inject_modal(context, event, self.mouse_pos) == -1:
                self.inject_modal = None
                return {'FINISHED'}
            return {'RUNNING_MODAL'}

        return {'FINISHED'}

    def _exit(self, context: Context, cancel: bool) -> None:
        if self.inject_modal_exit is not None:
            self.inject_modal_exit(context, self.mouse_pos, cancel)

    def _draw(self, context: Context) -> None:
        refresh: bool = False
        zoom = get_node_editor_zoom(context)
        offset = get_node_editor_offset(context)
        ui_scale = context.preferences.system.ui_scale

        active_node = self.nodes.active
        with gpu.matrix.push_pop():
            gpu.matrix.translate(offset)
            gpu.matrix.scale_uniform(zoom)

            for node in self.nodes:
                if node.dirty:
                    refresh = True
                if hasattr(node, '_draw'):
                    node._draw(context, ui_scale, node==active_node)
            if refresh:
                context.region.tag_redraw()


    # ----------------------------------------------------------------


    # MODAL: Move Node.
    def modal__move_node__enter(self, context: Context, event: Event, mouse_pos: Vector) -> None:
        if 'new' in self.active_node:
            self.prev_node_location = Vector((0, 0))
            self.node_location_offset = Vector((0, 0))
        else:
            self.prev_node_location = get_node_editor_region_coord(context, self.active_node.location)
            self.node_location_offset = self.prev_node_location - mouse_pos

    def modal__move_node__update(self, context: Context, event: Event, mouse_pos: Vector) -> int:
        if self.active_node is None or (event.type == 'LEFTMOUSE' and event.value == 'RELEASE'):
            return -1
        zoom = get_node_editor_zoom(context)
        inv_zoom = 1/zoom
        offset = get_node_editor_offset(context)

        self.active_node.location = (mouse_pos - offset + self.node_location_offset) * inv_zoom
        return 1

    def modal__move_node__exit(self, context: Context, mouse_pos: Vector, cancel: bool) -> None:
        if cancel:
            self.active_node.location = self.prev_node_location
            del self.prev_node_location
            del self.node_location_offset
            
            if 'new' in self.active_node:
                self.nodes.remove(self.active_node)

        elif 'new' in self.active_node:
            del self.active_node['new']

        self.active_node = None
