import bpy
from bpy.types import NodeTree, Context, Event, Node
from mathutils import Vector
import gpu
from bpy.app import timers

from typing import List, Tuple, Type, Dict, Set
from collections import defaultdict
import functools

from .nodes._base import AP_Node
from ..utils.collections import DefaultOrderedDict
from ..utils.node_editor import get_node_editor_zoom, get_node_editor_view_point, get_node_editor_offset, get_node_editor_region_coord
from ..utils.armature import deselect_all_bones_from_active


# ----------------------------------------------------------------

# GLOBALS.
G_active_node = ''
G_hovered_node = ''
nodes_count: int = -1

# ----------------------------------------------------------------

sorted_nodetree_nodes_cache: List[List[AP_Node]] = []

def ensure_nodes_cache(node_tree: NodeTree):
    # Empty cache? Probably first time?
    if sorted_nodetree_nodes_cache == []:
        return refresh_nodes_cache(node_tree.nodes)
    # Invalid cached nodes?
    first_cached_node = sorted_nodetree_nodes_cache[0][0]
    if first_cached_node is None or not hasattr(first_cached_node, 'uuid'):
        return refresh_nodes_cache(node_tree.nodes)
    # Changes in the node count?
    global nodes_count
    if len(node_tree.nodes) == nodes_count:
        return
    nodes_count = len(node_tree.nodes)
    refresh_nodes_cache(node_tree.nodes)


def refresh_nodes_cache(nodes: List[AP_Node]):
    sorted_nodetree_nodes_cache.clear()

    if len(nodes) == 0:
        ## print("No nodes")
        return

    active_node = nodes.active

    nodes_by_draw_layer: Dict[int, Set[AP_Node]] = defaultdict(set)
    {nodes_by_draw_layer[node.draw_layer].add(node) for node in nodes}

    # print("nodes by draw_layer: {}".format(nodes_by_draw_layer))

    # Sort layer order.
    layer_indices = list(nodes_by_draw_layer.keys())
    layer_indices.sort()

    for node_layer_index in layer_indices:
        # Filter nodes-in-layer by their draw_depth attribute.
        _nodes = nodes_by_draw_layer[node_layer_index]
        if active_node in _nodes:
            _nodes.remove(active_node)
            active_on_top = True
        else:
            active_on_top = False

        sorted_nodetree_nodes_cache.append(
            sorted(_nodes, key=lambda node: node.draw_depth)
        )

        # Add Active Node on top ALWAYS.
        if active_on_top:
            sorted_nodetree_nodes_cache[-1].append(active_node)


# ----------------------------------------------------------------


class AP_NodeTree(NodeTree):
    # Description string
    '''A custom node tree type that will show up in the editor type list'''
    # Optional identifier string. If not explicitly defined, the python class name is used.
    bl_idname = 'AP_NODETREE'
    # Label for nice name display
    bl_label = "Armature Picker"
    # Icon identifier
    bl_icon = 'OUTLINER_OB_ARMATURE' # CON_ARMATURE


    def get_selected_nodes(self, context: Context) -> set[AP_Node]:
        return set(context.selected_nodes)


    def new_node(self, context: Context, type: str | Type[AP_Node], event: Event | None = None) -> AP_Node:
        ''' Pass Event type if the addition should be interactive (performed inside an invoke to run modal).
            Pass a Vector in the event place to indicate the node element final-location manually. '''
        new_node = self.nodes.new(type)
        ensure_nodes_cache(self)

        if hasattr(new_node, 'bone_name'):
            if context.active_bone is not None:
                new_node.bone_name = context.active_bone.name

        if isinstance(event, Event):
            # --- Interactive Add Node. ---
            new_node['new'] = 1
            self.modal_nodes = (new_node, )
            self.set_inject_modal(context, event,
                                    modal_callback=self.modal__move_node__update,
                                    modal_enter_callback=self.modal__move_node__enter,
                                    modal_exit_callback=self.modal__move_node__exit)
        else:
            self.nodes.active = new_node

            # Specified the node element location manually ?
            if isinstance(event, Vector):
                new_node.location = event

        return new_node


    def update_nodes_depth(self) -> None:
        ''' We can call this after active node is changed. '''
        # TODO: support partial update, pass Node here and change its order in a more smart way.
        refresh_nodes_cache(self.nodes)


    def _test_select(self, context: Context, region_loc) -> int:
        # FIX SCROLLBARS.
        ui_scale = context.preferences.system.ui_scale
        region = context.region
        scroll_bar_thickness = 10 * ui_scale
        if region_loc[0] > (region.width - scroll_bar_thickness):
            return -1
        if region_loc[1] < scroll_bar_thickness:
            return -1

        global G_active_node
        active_node = self.nodes.active
        if active_node is not None and G_active_node != active_node.uuid:
            # Active Node is updated !
            G_active_node = active_node.uuid
            refresh_nodes_cache(self.nodes)
        else:
            ensure_nodes_cache(self)

        global G_hovered_node
        view_zoom = get_node_editor_zoom(context)
        region_offset = get_node_editor_offset(context)
        view_loc = get_node_editor_view_point(context, region_loc)

        for node_layer_nodes in reversed(sorted_nodetree_nodes_cache):
            for node in reversed(node_layer_nodes):
                if not node.visible:
                    continue
                if node._test_select(context, region_loc, view_loc, view_zoom, region_offset):
                    G_hovered_node = node.uuid
                    print("hovered_node", node.label)
                    return 1

        G_hovered_node = None
        return 1


    # ----------------------------------------------------------------


    def set_inject_modal(self, context: Context, event: Event, modal_callback: callable, modal_enter_callback: callable = None, modal_exit_callback: callable = None) -> None:
        self.inject_modal = modal_callback
        self.inject_modal_exit = modal_exit_callback
        if modal_enter_callback is not None:
            modal_enter_callback(context, event, self.mouse_pos)

    def _invoke(self, context: Context, event: Event) -> set[str]:
        # Skip navigation km.
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'T', 'N', 'TAB'}:
            if event.value != 'PRESS':
                return {'PASS_THROUGH'}
            if event.type == 'WHEELUPMOUSE':
                bpy.ops.view2d.zoom_in('INVOKE_DEFAULT')
            elif event.type == 'WHEELDOWNMOUSE':
                bpy.ops.view2d.zoom_out('INVOKE_DEFAULT')
            elif event.type == 'MIDDLEMOUSE':
                bpy.ops.view2d.pan('INVOKE_DEFAULT')
            elif event.type == 'N':
                context.space_data.show_region_ui = not context.space_data.show_region_ui
            elif event.type == 'T':
                context.space_data.show_region_toolbar = not context.space_data.show_region_toolbar
            # elif event.type == 'TAB':
            #     view3d_set_mode(context, 'EDIT' if context.active_object.mode == 'POSE' else 'POSE')
            return {'PASS_THROUGH'}

        self.mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))
        
        self.modal_nodes = None
        self.active_node = None

        if context.active_object.mode == 'POSE':
            ret = self.invoke__pose(context, event)
        else:
            ret = self.invoke__edit(context, event)

        if ret is not None:
            return ret

        global G_hovered_node
        
        if G_hovered_node is None:
            return {'FINISHED'}

        # Interact with a node.
        if node := self.nodes.get(G_hovered_node, None):
            ret = node._invoke(context, event, self.mouse_pos)
            if ret == 'RUNNING_MODAL':
                self.active_node = node
            return ret

        return {'FINISHED'}


    def invoke__pose(self, context: Context, event: Event) -> set[str] | None:
        global G_hovered_node
        if G_hovered_node is None:
            deselect_all_bones_from_active(context)


    def invoke__edit(self, context: Context, event: Event) -> set[str] | None:
        global G_hovered_node
        ## print("hovered_node", G_hovered_node)
        if G_hovered_node is None:
            # Interact with blank space.
            if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                self.new_node(context, 'AP_NODE_bone_picker', event=event)
                ## print("Create new AP_NODE_bone_picker")
                return {'RUNNING_MODAL'}

        if self.nodes.active is not None:
            if (event.type == 'G' and event.value == 'RELEASE') or\
               (event.type == 'LEFTMOUSE' and event.value == 'CLICK_DRAG' and G_hovered_node is not None):
                self.modal_nodes = context.selected_nodes
                self.set_inject_modal(context, event,
                                      modal_callback=self.modal__move_node__update,
                                      modal_enter_callback=self.modal__move_node__enter,
                                      modal_exit_callback=self.modal__move_node__exit)
                return {'RUNNING_MODAL'}


    # ----------------------------------------------------------------


    def _modal(self, context: Context, event: Event, tweak: str) -> set[str]:
        ## print("Modal", event.type, event.value)
        if self.inject_modal is not None:
            self.mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))
            if self.inject_modal(context, event, self.mouse_pos) == -1:
                self.inject_modal = None
                return {'FINISHED'}
            return {'RUNNING_MODAL'}

        if self.active_node is not None and self.active_node.in_modal:
            return self.active_node._modal(context, event)

        return {'FINISHED'}

    def _exit(self, context: Context, cancel: bool) -> None:
        if self.inject_modal_exit is not None:
            self.inject_modal_exit(context, self.mouse_pos, cancel)
        elif self.active_node is not None and self.active_node.in_modal:
            self.active_node.modal_exit(context, cancel)


    # ----------------------------------------------------------------


    def _draw(self, context: Context) -> None:
        refresh: bool = False
        zoom = get_node_editor_zoom(context)
        offset = get_node_editor_offset(context)
        ui_scale = context.preferences.system.ui_scale

        in_edit = context.mode == 'EDIT_ARMATURE'
        active_node: AP_Node = self.nodes.active
        sel_nodes: set[AP_Node] = self.get_selected_nodes(context)

        with gpu.matrix.push_pop():
            gpu.matrix.translate(offset)
            gpu.matrix.scale_uniform(zoom)

            for node_layer_nodes in sorted_nodetree_nodes_cache:
                for node in node_layer_nodes:
                    if not node.visible:
                        continue
                    if node.dirty:
                        refresh = True
                    node._draw(context, ui_scale, active=node==active_node, selected=node in sel_nodes, in_edit=in_edit)

            if refresh:
                context.region.tag_redraw()


    # ----------------------------------------------------------------


    # MODAL: Move Node.
    def modal__move_node__enter(self, context: Context, event: Event, mouse_pos: Vector) -> None:
        if 'new' in self.modal_nodes[0]:
            self.prev_node_location = [Vector((0, 0))]
            self.node_location_offset = [Vector((0, 0))]
        else:
            self.prev_node_location = [get_node_editor_region_coord(context, node.location) for node in self.modal_nodes]
            self.node_location_offset = [prev_node_loc - mouse_pos for prev_node_loc in self.prev_node_location]

    def modal__move_node__update(self, context: Context, event: Event, mouse_pos: Vector) -> int:
        if self.modal_nodes is None or (event.type == 'LEFTMOUSE' and event.value == 'RELEASE'):
            return -1
        zoom = get_node_editor_zoom(context)
        inv_zoom = 1/zoom
        offset = get_node_editor_offset(context)
        
        def move_node(_node: Node, _node_loc_offset: Vector):
            _node.location = (mouse_pos - offset + _node_loc_offset) * inv_zoom

        {move_node(node, node_loc_offset) for (node, node_loc_offset) in zip(self.modal_nodes, self.node_location_offset)}
        return 1

    def modal__move_node__exit(self, context: Context, mouse_pos: Vector, cancel: bool) -> None:
        if cancel:
            for (node, prev_node_loc) in zip(self.modal_nodes, self.prev_node_location):
                node.location = prev_node_loc
            del self.prev_node_location
            del self.node_location_offset

            if 'new' in self.active_node:
                self.nodes.remove(self.active_node)

        elif 'new' in self.modal_nodes[0]:
            new_node = self.modal_nodes[0]
            self.nodes.active = new_node
            del new_node['new']

        self.modal_nodes = None
