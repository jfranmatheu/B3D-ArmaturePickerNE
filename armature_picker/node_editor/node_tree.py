import bpy
from bpy.types import NodeTree, Context, Event, Node
from bpy.props import BoolProperty, EnumProperty, StringProperty
from mathutils import Vector
import gpu

from uuid import uuid4
from typing import List, Tuple, Type, Dict, Set, Union
from collections import defaultdict
from dataclasses import dataclass

from armature_picker.paths import Paths
from ..gpu import draw
from .nodes._base import AP_Node
from ..utils.node_editor import get_node_editor_zoom, get_node_editor_view_point, get_node_editor_offset, get_node_editor_region_coord, get_node_editor_visible_view_box
from ..utils.armature import deselect_all_bones_from_active
from ..utils.geometry import angle_signed, rect_overlap, Box
from armature_picker.prefs import get_active_theme_style


# ----------------------------------------------------------------

# GLOBALS.
G_active_node = ''
G_hovered_node = ''
nodes_count: int = -1

# ----------------------------------------------------------------

@dataclass
class DummyNode:
    uuid: str
    dirty: bool = True

graphic_users: dict[str, dict[str, DummyNode]] = defaultdict(dict)

# ----------------------------------------------------------------

sorted_nodes_cache: Dict[str, List[List[AP_Node]]] = defaultdict(list)

def ensure_nodes_cache(node_tree: 'AP_NodeTree'):
    # Empty cache? Probably first time?
    if len(sorted_nodes_cache[node_tree.uuid]) == 0:
        return refresh_nodes_cache(node_tree)
    # Invalid cached nodes?
    first_cached_node = sorted_nodes_cache[node_tree.uuid][0][0]
    if first_cached_node is None or not hasattr(first_cached_node, 'uuid'):
        return refresh_nodes_cache(node_tree)
    # Changes in the node count?
    global nodes_count
    if len(node_tree.nodes) == nodes_count:
        return
    nodes_count = len(node_tree.nodes)
    refresh_nodes_cache(node_tree)


def refresh_nodes_cache(node_tree: 'AP_NodeTree'):
    nodes: List[AP_Node] = node_tree.nodes

    sorted_nodes_cache[node_tree.uuid].clear()

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

    sorted_nodes: List[List[AP_Node]] = []
    for node_layer_index in layer_indices:
        # Filter nodes-in-layer by their draw_depth attribute.
        _nodes = nodes_by_draw_layer[node_layer_index]
        if active_node in _nodes:
            _nodes.remove(active_node)
            active_on_top = True
        else:
            active_on_top = False

        sorted_nodes.append(
            sorted(_nodes, key=lambda node: node.draw_depth)
        )

        # Add Active Node on top ALWAYS.
        if active_on_top:
            sorted_nodes[-1].append(active_node)

    sorted_nodes_cache[node_tree.uuid] = sorted_nodes

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

    active_node: Union[AP_Node, Node] = None
    modal_nodes: Union[List[AP_Node], List[Node]] = None
    inject_modal: callable = None
    inject_modal_exit: callable = None
    inject_modal_draw: callable = None
    picker_mode: str

    dirty: bool

    bl_use_exclude_layers = False
    bl_use_postprocess = False
    bl_use_preview = False
    bl_use_save_buffers = False
    bl_use_shading_nodes = False
    bl_use_shading_nodes_custom = False
    bl_use_spherical_stereo = False
    bl_use_texture_preview = False


    # @classmethod
    # def poll(cls, context: Context) -> bool:
    #     return poll_check(context)


    def __init__(self):
        self.uuid = uuid4().hex

    def __del__(self):
        pass

    def get_graphic_user(self, user_id: str) -> None:
        if user_id not in graphic_users[self.uuid]:
            graphic_users[self.uuid][user_id] = DummyNode(user_id, dirty=True)
        return graphic_users[self.uuid][user_id]

    def on_region_resize(self, context: Context) -> None:
        for graphic in graphic_users[self.uuid].values():
            graphic.dirty = True


    # ----------------------------------------------------------------

    def get_selected_nodes(self, context: Context, include_active: bool = True) -> set[AP_Node]:
        sel_nodes = set(context.selected_nodes)
        if include_active:
            if act_node := self.nodes.active:
                sel_nodes.add(act_node)
        return sel_nodes


    def update_nodes_depth(self) -> None:
        ''' We can call this after active node is changed. '''
        # TODO: support partial update, pass Node here and change its order in a more smart way.
        refresh_nodes_cache(self)


    def _test_select(self, context: Context, region_loc) -> int:
        if self.dirty:
            context.area.tag_redraw()

        # FIX SCROLLBARS.
        ui_scale = context.preferences.system.ui_scale
        region = context.region
        scroll_bar_thickness = 10 * ui_scale
        if region_loc[0] > (region.width - scroll_bar_thickness):
            return -1
        if region_loc[1] < scroll_bar_thickness:
            return -1

        region_loc = Vector(region_loc)

        global G_active_node
        active_node = self.nodes.active
        if active_node is not None and G_active_node != active_node.uuid:
            # Active Node is updated !
            G_active_node = active_node.uuid
            refresh_nodes_cache(self)
        else:
            ensure_nodes_cache(self)

        in_pose = self.picker_mode == 'POSE'

        global G_hovered_node
        view_zoom = get_node_editor_zoom(context)
        region_offset = get_node_editor_offset(context)
        view_loc = get_node_editor_view_point(context, region_loc)

        for node_layer_nodes in reversed(sorted_nodes_cache[self.uuid]):
            for node in reversed(node_layer_nodes):
                if not node.visible:
                    continue
                if in_pose and not node.interactable:
                    continue
                if node._test_select(context, region_loc, view_loc, view_zoom, region_offset):
                    G_hovered_node = node.uuid
                    #### print("hovered_node", node.label)
                    return 1

        G_hovered_node = None
        return 1


    # ----------------------------------------------------------------


    def set_inject_modal(self, context: Context, event: Event, modal_callback: callable, modal_enter_callback: callable = None, modal_exit_callback: callable = None, modal_draw_callback: callable = None) -> None:
        self.inject_modal = modal_callback
        self.inject_modal_exit = modal_exit_callback
        self.inject_modal_draw = modal_draw_callback
        if modal_enter_callback is not None:
            modal_enter_callback(context, event, self.mouse_pos)

    def _invoke(self, context: Context, event: Event) -> set[str]:
        # Skip navigation km.
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'T', 'N', 'TAB', 'X'}:
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
            elif event.type == 'X':
                bpy.ops.node.delete('INVOKE_DEFAULT')
                ensure_nodes_cache(self)
            elif event.type == 'TAB':
                self.picker_mode = 'POSE' if self.picker_mode == 'EDIT' else 'EDIT'
                context.area.tag_redraw()
            return {'FINISHED'}

        if event.type == 'A' and not event.shift and event.value == 'PRESS':
            bpy.ops.node.select_all(action='TOGGLE')
            return {'FINISHED'}

        self.mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))

        self.modal_nodes = None
        self.active_node = None

        if self.picker_mode == 'POSE':
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
            if isinstance(ret, set):
                if 'RUNNING_MODAL' in ret:
                    self.active_node = node
                return ret

        return {'FINISHED'}


    def invoke__pose(self, context: Context, event: Event) -> set[str] | None:
        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            if context.active_bone is None:
                return {'FINISHED'}
            from .ops.insert_keyframe import MT_insert_keyframe
            # context.window_manager.popup_menu_pie(event, MT_insert_keyframe.draw)
            with context.temp_override(window=context.window, area=context.area, bone=context.active_bone):
                bpy.ops.wm.call_menu_pie('INVOKE_DEFAULT', name=MT_insert_keyframe.bl_idname)
            self.dirty = True
            return {'FINISHED'}

        global G_hovered_node
        if G_hovered_node is None:
            deselect_all_bones_from_active(context)


    def invoke__edit(self, context: Context, event: Event) -> set[str] | None:
        global G_hovered_node
        ## print("hovered_node", G_hovered_node)
        if G_hovered_node is None:
            # Interact with blank space.
            if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                # deselect_all_nodes(context, nullify_active=True)
                bpy.ops.node.select_all(False, action='DESELECT')
                return {'RUNNING_MODAL'}
            if event.type == 'LEFTMOUSE' and event.value == 'CLICK_DRAG':
                self.set_inject_modal(context, event,
                                      modal_callback=self.modal__box_select__update,
                                      modal_enter_callback=self.modal__box_select__enter,
                                      modal_exit_callback=self.modal__box_select__exit,
                                      modal_draw_callback=self.modal__box_select__draw)
                return {'RUNNING_MODAL'}

        if event.type == 'A' and event.value == 'RELEASE' and event.shift:
            from .ops.add_node.pie_menu import MT_add_node
            # context.window_manager.popup_menu_pie(event, MT_add_node.draw)
            bpy.ops.wm.call_menu_pie('INVOKE_DEFAULT', name=MT_add_node.bl_idname)
            return {'FINISHED'}

        if event.type == 'D' and event.value == 'RELEASE' and event.shift:
            bpy.ops.node.duplicate('INVOKE_DEFAULT', False)
            sel_nodes = self.get_selected_nodes(context, include_active=True)
            if len(sel_nodes) == 0:
                return {'CANCELLED'}
            ensure_nodes_cache(self)
            self.modal_nodes = sel_nodes
            self.set_inject_modal(context, event,
                                  modal_callback=self.modal__move_node__update,
                                  modal_enter_callback=self.modal__move_node__enter,
                                  modal_exit_callback=self.modal__move_node__exit)
            return {'RUNNING_MODAL'}

        if G_hovered_node is not None:
            hovered_node: AP_Node = self.nodes.get(G_hovered_node, None)

        sel_nodes = self.get_selected_nodes(context, include_active=True)

        # print("Selected nodes", sel_nodes)

        if self.nodes.active is not None:
            if (event.type == 'G' and event.value == 'RELEASE') or\
               (event.type == 'LEFTMOUSE' and event.value == 'CLICK_DRAG' and G_hovered_node is not None and hovered_node in sel_nodes):
                if all([node.locked for node in sel_nodes]):
                    # All nodes are locked!
                    return {'CANCELLED'}
                self.modal_nodes = sel_nodes
                self.set_inject_modal(context, event,
                                      modal_callback=self.modal__move_node__update,
                                      modal_enter_callback=self.modal__move_node__enter,
                                      modal_exit_callback=self.modal__move_node__exit)
                return {'RUNNING_MODAL'}

            if (event.type == 'R' and event.value == 'RELEASE'): # and self.active_node is not None:
                if all([node.locked for node in sel_nodes]):
                    # All nodes are locked!
                    return {'CANCELLED'}
                self.modal_nodes = sel_nodes
                self.set_inject_modal(context, event,
                                      modal_callback=self.modal__rotate_node__update,
                                      modal_enter_callback=self.modal__rotate_node__enter,
                                      modal_exit_callback=self.modal__rotate_node__exit,
                                      modal_draw_callback=self.modal__rotate_node__draw)
                return {'RUNNING_MODAL'}

        if G_hovered_node is not None and hovered_node is not None and hovered_node not in sel_nodes and not hovered_node.locked:
            if event.type == 'LEFTMOUSE' and event.value == 'CLICK_DRAG':
                for sel_node in sel_nodes:
                    sel_node.select = False
                self.nodes.active = hovered_node
                hovered_node.select = True
                return self.invoke__edit(context, event)


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
        self.inject_modal = None
        if self.inject_modal_draw is not None:
            self.inject_modal_draw = None
        if self.inject_modal_exit is not None:
            self.inject_modal_exit(context, self.mouse_pos, cancel)
            self.inject_modal_exit = None
        elif self.active_node is not None and self.active_node.in_modal:
            self.active_node.modal_exit(context, cancel)


    # ----------------------------------------------------------------


    def _draw(self, context: Context) -> None:
        if not hasattr(self, 'uuid'):
            self.uuid = uuid4().hex

        if context.active_object.mode != 'POSE':
            draw.rectangle(
                self, None,
                Vector((0, 0)), Vector((context.region.width, context.region.height)), 0,
                color=(0.25, 0.1, 0.1, .2),
            )
            image = bpy.data.images.get('...tmp_overlay_image')
            if not image:
                image = bpy.data.images.load(Paths.LIB_IMAGES('icons8-human-bones-64.png'))
                image.name = '...tmp_overlay_image'
            aspect_ratio = image.size[1] / image.size[0]
            w = min(int(context.region.width * 0.5), 128)
            h = w * aspect_ratio

            ipos = Vector((context.region.width * 0.5 - w * 0.5, context.region.height * 0.5 - h * 0.5))
            draw.image(
                self, None,
                ipos, Vector((w, h)), 0,
                image=image
            )
            draw.text(
                Vector((ipos.x + w - 25, ipos.y + h)),
                "Let's pose!",
                16,
                (0.0, 0.0),
                width=int(context.region.width * 0.9),
                color=(.8, .3, .75, 1.0)
            )
            draw.text(
                Vector((context.region.width * 0.5, ipos.y - h * 0.5)), # Vector((context.region.width * 0.5, context.region.height - 40)), # 
                "Pose me please :'v",
                24,
                (0.5, 1.0),
                width=int(context.region.width * 0.9)
            )
            return


        in_edit = self.picker_mode == 'EDIT'
        if in_edit:
            draw.box(
                self.get_graphic_user('EDIT_CAGE'), 'EDIT_CAGE',
                Vector((0, 0)), Vector((context.region.width, context.region.height)),
                padding=8,
                line_thickness=1,
                color=(.9, .3, .1, .5)
            )

        refresh: bool = False
        zoom = get_node_editor_zoom(context)
        offset = get_node_editor_offset(context)
        ui_scale = context.preferences.system.ui_scale

        active_node: AP_Node = self.nodes.active
        sel_nodes: set[AP_Node] = self.get_selected_nodes(context)
        
        visible_view_box = get_node_editor_visible_view_box(context)
        
        theme_style = get_active_theme_style(context)

        with gpu.matrix.push_pop():
            gpu.matrix.translate(offset)
            gpu.matrix.scale_uniform(zoom)

            for node_layer_nodes in sorted_nodes_cache[self.uuid]:
                for node in node_layer_nodes:
                    if not node.visible:
                        continue
                    if not rect_overlap(visible_view_box, node.rect_transform):
                        print("Node outside view", node.label)
                        continue
                    if node.dirty:
                        refresh = True
                    node._draw(context, node.get_style(theme_style), ui_scale, active=node==active_node, selected=node in sel_nodes, in_edit=in_edit)

            if self.active_node is not None and self.active_node.in_modal:
                draw_callback = self.active_node.modal_draw__edit if in_edit else self.active_node.modal_draw__pose
                draw_callback(context, self.active_node.rect_transform, self.active_node.get_style(theme_style), ui_scale)

            if self.inject_modal_draw is not None:
                self.inject_modal_draw(context, ui_scale, sel_nodes, in_edit=in_edit, in_view2d=True)


            if refresh:
                context.region.tag_redraw()

        if self.inject_modal_draw is not None:
            self.inject_modal_draw(context, ui_scale, sel_nodes, in_edit=in_edit, in_view2d=False)


    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


    # MODAL: Move Selected Nodes.
    # ----------------------------------------------------------------

    def modal__move_node__enter(self, context: Context, event: Event, mouse_pos: Vector) -> None:
        self.prev_node_location = [get_node_editor_region_coord(context, node.rect_transform.origin) for node in self.modal_nodes]
        self.node_location_offset = [prev_node_loc - mouse_pos for prev_node_loc in self.prev_node_location]

    def modal__move_node__update(self, context: Context, event: Event, mouse_pos: Vector) -> int:
        if self.modal_nodes is None or (event.type == 'LEFTMOUSE' and event.value == 'RELEASE'):
            return -1
        zoom = get_node_editor_zoom(context)
        inv_zoom = 1/zoom
        offset = get_node_editor_offset(context)

        def move_node(_node: Node, _node_loc_offset: Vector):
            if _node.locked:
                return
            _node.rect_transform.move_to((mouse_pos - offset + _node_loc_offset) * inv_zoom)

        {move_node(node, node_loc_offset) for (node, node_loc_offset) in zip(self.modal_nodes, self.node_location_offset)}
        return 1

    def modal__move_node__exit(self, context: Context, mouse_pos: Vector, cancel: bool) -> None:
        if cancel:
            for (node, prev_node_loc) in zip(self.modal_nodes, self.prev_node_location):
                node.rect_transform.move_to(prev_node_loc)
            del self.prev_node_location
            del self.node_location_offset

        self.modal_nodes = None


    # MODAL: Rotate Selected Nodes.
    # ----------------------------------------------------------------

    def modal__rotate_node__enter(self, context: Context, event: Event, mouse_pos: Vector) -> None:
        self.prev_node_rotation = [node.rect_transform.rotation for node in self.modal_nodes]
        # self.start_mouse_pos = mouse_pos
        orig = Vector((0, 0))
        for node in self.modal_nodes:
            orig += Vector(node.rect_transform.origin)
        orig /= len(self.modal_nodes)
        self.modal_rotation_origin_view = orig
        orig = get_node_editor_region_coord(context, orig)
        self.modal_rotation_origin_region = orig
        self.modal_rotation_start_vec = (orig - mouse_pos)#.normalized()

    def modal__rotate_node__update(self, context: Context, event: Event, mouse_pos: Vector) -> int:
        if self.modal_nodes is None or (event.type == 'LEFTMOUSE' and event.value == 'RELEASE'):
            return -1

        curr_rotation_vec = (self.modal_rotation_origin_region - mouse_pos)#.normalized()
        angle_offset = angle_signed(self.modal_rotation_start_vec, curr_rotation_vec)

        def rotate_node(_node: Node, _rot: float):
            if _node.locked:
                return
            _node.rect_transform.rotation = _rot

        {rotate_node(node, orig_rot + angle_offset) for (node, orig_rot) in zip(self.modal_nodes, self.prev_node_rotation)}
        return 1

    def modal__rotate_node__exit(self, context: Context, mouse_pos: Vector, cancel: bool) -> None:
        if cancel:
            for (node, prev_node_rot) in zip(self.modal_nodes, self.prev_node_rotation):
                node.rect_transform.rotation = prev_node_rot

        del self.prev_node_rotation
        del self.modal_rotation_origin_region
        del self.modal_rotation_origin_view
        del self.modal_rotation_start_vec

        self.modal_nodes = None


    def modal__rotate_node__draw(self, context: Context, ui_scale: float, sel_nodes: list[Node], in_edit: bool, in_view2d: bool) -> None:
        if not in_view2d or not in_edit:
            return
        draw.text(self.modal_rotation_origin_view.copy(), 'o', 12, (0.5, 0.5), color=(1, 0, 0, 1))
        return
        print(self.modal_rotation_origin_region)
        draw.just_a_point(
            self.modal_rotation_origin_region,
            5 * ui_scale,
            color=(1, 0, 0, 1.0)
        )


    # ----------------------------------------------------------------

    def modal__box_select__enter(self, context: Context, event: Event, mouse_pos: Vector) -> None:
        self.box = Box(mouse_pos.x, mouse_pos.y, mouse_pos.x, mouse_pos.y)
        self.box_origin = mouse_pos.copy()
        self.dummy_node = DummyNode('MODAL_BOX_SELECT')
        self.prev_sel_nodes = self.get_selected_nodes(context, include_active=True)

    def modal__box_select__update(self, context: Context, event: Event, mouse_pos: Vector) -> int:
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            return -1

        if event.type != 'MOUSEMOVE':
            return 1

        ori_x, ori_y = self.box_origin
        curr_x, curr_y = mouse_pos

        if curr_x > ori_x:
            self.box.x_max = curr_x
        elif curr_x < ori_x:
            self.box.x_max = ori_x
            self.box.x_min = curr_x

        if curr_y > ori_y:
            self.box.y_max = curr_y
        elif curr_y < ori_y:
            self.box.y_max = ori_y
            self.box.y_min = curr_y

        proj_box = Box(*(get_node_editor_view_point(context, self.box.min)),
                       *(get_node_editor_view_point(context, self.box.max)))

        for node in self.nodes:
            rect = node.rect_transform
            if rect_overlap(proj_box, rect):
                node.select = True
            elif node.select:
                node.select = False

        context.region.tag_redraw()
        return 1

    def modal__box_select__exit(self, context: Context, mouse_pos: Vector, cancel: bool) -> None:
        if cancel:
            for sel_node in self.prev_sel_nodes:
                sel_node.select = True

        else:
            sel_nodes = self.get_selected_nodes(context)
            if len(sel_nodes) != 0:
                self.nodes.active = sel_nodes.pop()
                del sel_nodes

        del self.box
        del self.box_origin
        del self.dummy_node
        del self.prev_sel_nodes


    def modal__box_select__draw(self, context: Context, ui_scale: float, sel_nodes: list[Node], in_edit: bool, in_view2d: bool) -> None:
        if in_view2d or not in_edit:
            return
        draw.box(
            self.dummy_node, 'BOX_SELECT',
            self.box.pos, self.box.size,
            padding=0,
            line_thickness=2.0,
            color=(1, 1, 1, .92)
        )


def register():
    NodeTree.uuid = StringProperty()
    NodeTree.dirty = BoolProperty()

    NodeTree.picker_mode = EnumProperty(
        name='Picker Mode',
        items=(
            ('EDIT', 'Edit Mode', "Edit Mode", 'GREASEPENCIL', 0),
            ('POSE', 'Pose Mode', "Pose Mode", 'POSE_HLT', 1),
        ),
        default='EDIT'
    )
    
    NodeTree.picker_update_flags = set()

def unregister():
    del NodeTree.uuid
    del NodeTree.dirty
    del NodeTree.picker_mode
    
    del NodeTree.picker_update_flags
    
    sorted_nodes_cache.clear()
