import bpy
from bpy.types import NodeTree, Context, Event, Node, PoseBone
from bpy.props import BoolProperty, EnumProperty, StringProperty, PointerProperty, IntProperty, CollectionProperty
from mathutils import Vector
import gpu

from time import time
from uuid import uuid4
from typing import List, Tuple, Type, Dict, Set, Union
from collections import defaultdict
from dataclasses import dataclass
from math import cos, sin, radians, degrees

from armature_picker.layers.pg import PG_PickerLayer
from armature_picker.data.pg.picker_view import AP_PG_PickerView
from armature_picker.ui.header_menus.widget_types_visibility import attr_widget_types
from armature_picker.utils.cursor import Cursor, CursorIcon
from armature_picker.utils.event import Mouse, EventType, EventValue
from armature_picker.paths import Paths
from armature_picker.ui.context_menu import AP_MT_context_menu
from ..gpu import draw
from .nodes._base import AP_Node, RectTransform
from ..utils.node_editor import get_node_editor_view_size, set_node_editor_visible_view_box, center_node_editor_view, get_node_editor_zoom, get_node_editor_view_point, get_node_editor_offset, get_node_editor_region_coord, get_node_editor_visible_view_box
from ..utils.armature import deselect_all_bones_from_active
from ..utils.geometry import angle_signed, rect_overlap, Box, point_inside_rect
from armature_picker.prefs import get_active_theme_style, get_prefs_wg_settings


# ----------------------------------------------------------------

# GLOBALS.
G_active_node = ''
G_hovered_node = ''
G_on_hover_tabs_area = False
nodes_count: int = -1
G_clipboard_nodes = None

TABS_HEADER_HEIGHT = draw.get_text_dim('Xy', 12)[1]

region_loc: Vector = Vector((-1, -1))
view_loc: Vector = Vector((-100000, -100000))
view_size: Vector = Vector((0, 0))

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
        # node_tree.active_node = None
        # node_tree.modal_nodes = None
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
    # Filter widgets visibility.
    nodes: List[AP_Node] = node_tree.widgets_visible # node_tree.nodes

    sorted_nodes_cache[node_tree.uuid].clear()

    if len(nodes) == 0:
        ## print("No nodes")
        return

    active_node = node_tree.nodes.active

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

def select_node(node_tree: 'AP_NodeTree', node: AP_Node, make_active: bool = False) -> None:
    if test_node_sel_locked(node_tree, node):
        return
    node.select = True
    if make_active:
        node_tree.nodes.active = node

def test_node_sel_locked(node_tree: 'AP_NodeTree', node: AP_Node) -> bool:
    return not node.locked and getattr(node_tree.picker_view, 'show_widget_select_' + node.wg_type)

def test_node_sel(node_tree: 'AP_NodeTree', node: AP_Node) -> bool:
    return getattr(node_tree.picker_view, 'show_widget_select_' + node.wg_type)

def test_node_visibility(node_tree: 'AP_NodeTree', node: AP_Node) -> bool:
    return node.visible and getattr(node_tree.picker_view, 'show_widget_' + node.wg_type) # node.visible and

def get_visible_widget_types(node_tree: 'AP_NodeTree') -> set[str]:
    picker_view = node_tree.picker_view
    visible_widget_types = set()
    for (wg_type, _attr_name) in attr_widget_types:
        if wg_type is None:
            continue
        if getattr(picker_view, 'show_widget_' + wg_type):
            visible_widget_types.add(wg_type)
    return visible_widget_types

def get_selectable_widget_types(node_tree: 'AP_NodeTree') -> set[str]:
    picker_view = node_tree.picker_view
    selectable_widget_types = set()
    for (wg_type, _attr_name) in attr_widget_types:
        if wg_type is None:
            continue
        if getattr(picker_view, 'show_widget_select_' + wg_type):
            selectable_widget_types.add(wg_type)
    return selectable_widget_types


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


    #----------------------------------------------------------------
    # ID Properties.
    
    def get_layer(self, target_layer: str | int) -> PG_PickerLayer | None:
        if isinstance(target_layer, int):
            if target_layer < 0 or target_layer >= len(self.picker_layers):
                return None
            return self.picker_layers[target_layer]
        elif isinstance(layer, str):
            for layer in self.picker_layers:
                if layer.uuid == target_layer:
                    return layer
        return None

    # def set_active_layer_index(self, value):
    #     self.prev_picker_layer_index = self.active_picker_layer_index
    #     self["active_picker_layer_index"] = value

    def update_active_layer(self, context: Context):
        if not hasattr(context.space_data, 'node_tree'):
            return
        self.layer_selector_lock_update = True
        active_picker_layer = self.active_picker_layer
        self.active_picker_layer_selector = active_picker_layer_id = active_picker_layer.uuid
        for widget in self.widgets:
            if active_picker_layer_id == widget.picker_layer:
                widget.visible = True
            else:
                widget.visible = False
                widget.select = False
        refresh_nodes_cache(self)
        if self.use_preserve_picker_layer_view:
            # center_node_editor_view(context)
            if self.prev_picker_layer_index != -1:
                if prev_layer := self.get_layer(self.prev_picker_layer_index):
                    prev_layer.view2d_box = get_node_editor_visible_view_box(context).to_tuple()
                set_node_editor_visible_view_box(context, active_picker_layer.view2d_box)
        self.prev_picker_layer_index = self.active_picker_layer_index
        context.region.tag_redraw()
        self.layer_selector_lock_update = False

    def update_active_picker_layer_selector(self, context: Context) -> None:
        if not self.layer_selector_lock_update:
            layer_id = self.active_picker_layer_selector
            for idx, pk_layer in enumerate(self.picker_layers):
                if pk_layer.uuid == layer_id:
                    self.active_picker_layer_index = idx
                    break

    def get_picker_layers(self, _context: Context) -> list[PG_PickerLayer]:
        if len(self.picker_layers) == 0:
            return [('NONE', 'NONE', ""),]
        return ((pk_layer.uuid, pk_layer.name, pk_layer.name) for index, pk_layer in enumerate(self.picker_layers))

    uuid: StringProperty()
    dirty: BoolProperty()
    picker_mode: EnumProperty(
        name='Picker Mode',
        description='Use TAB key to quickly toggle between both picker modes',
        items=(
            ('EDIT', 'Edit Mode', "Edit Mode", 'GREASEPENCIL', 0),
            ('POSE', 'Pose Mode', "Pose Mode", 'POSE_HLT', 1),
        ),
        default='EDIT'
    )
    picker_view: PointerProperty(name='Picker View', type=AP_PG_PickerView)
    prev_picker_layer_index: IntProperty(default=-1)
    active_picker_layer_index: IntProperty(default=-1, name="Active Picker Layer", update=update_active_layer) #, set=set_active_layer_index)
    picker_layers: CollectionProperty(type=PG_PickerLayer)
    active_picker_layer_selector: EnumProperty(
        name="Active Picker Layer Selector",
        items=get_picker_layers,
        update=update_active_picker_layer_selector
    )
    layer_selector_lock_update = False

    use_preserve_picker_layer_view: BoolProperty(name="Preserve Picker-Layer View", description="Save and link picker view to picker layers\nand preserve that view on layer switching", default=True)


    #----------------------------------------------------------------
    # On-Top Layer.

    @property
    def active_picker_layer_id(self) -> str:
        return self.active_picker_layer.uuid

    @property
    def sorted_nodes_cache(self) -> Dict[str, List[List[AP_Node]]]:
        return sorted_nodes_cache[self.uuid]

    @property
    def active_picker_layer(self) -> PG_PickerLayer:
        return self.picker_layers[self.active_picker_layer_index]

    @property
    def widgets(self) -> list[AP_Node]:
        return self.nodes

    @property
    def widgets_from_active_layer(self) -> list[AP_Node]:
        active_layer_id = self.active_picker_layer.uuid
        return [widget for widget in self.widgets if widget.picker_layer == active_layer_id]

    @property
    def widgets_interactable(self) -> list[AP_Node]:
        return [widget for widget in self.widgets if test_node_visibility(self, widget) and test_node_sel_locked(self, widget)]

    @property
    def widgets_visible(self) -> list[AP_Node]:
        return [widget for widget in self.widgets if test_node_visibility(self, widget)] # widget.visible]

    @property
    def picker_layers_pinned(self) -> list[PG_PickerLayer]:
        return [pk_layer for pk_layer in self.picker_layers if pk_layer.use_pin]

    @property
    def widgets_selected(self) -> list[AP_Node]:
        # Can't select an invisible widget.
        # Can't select an unselectable widget. (BUT can if it has a locked RectTransform, it just can't be transformed)
        return [widget for widget in self.widgets if widget.select and test_node_visibility(self, widget) and test_node_sel(self, widget)]

    def remove_widget(self, widget: AP_Node) -> None:
        self.nodes.remove(widget)


    #----------------------------------------------------------------

    active_node: Union[AP_Node, Node] = None
    modal_nodes: Union[List[AP_Node], List[Node]] = None
    inject_modal: callable = None
    inject_modal_exit: callable = None
    inject_modal_draw: callable = None
    inject_modal_mouse: Mouse = None
    last_event_type: str = 'NONE'
    last_event_value: str = 'NONE'
    last_time_event: float = time()

    picker_update_flags = set()

    # Blender NodeEditor Flags.
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
        pass

    def __del__(self):
        pass

    def get_graphic_user(self, user_id: str) -> None:
        if user_id not in graphic_users[self.uuid]:
            graphic_users[self.uuid][user_id] = DummyNode(user_id, dirty=True)
        return graphic_users[self.uuid][user_id]

    def on_region_resize(self, context: Context) -> None:
        for graphic in graphic_users[self.uuid].values():
            graphic.dirty = True

        self.on_view_resize(context)

    @property
    def view_size(self) -> Vector:
        global view_size
        return view_size

    def on_view_resize(self, context: Context) -> None:
        global view_size
        view_size = get_node_editor_view_size(context)


    # ----------------------------------------------------------------

    def new_layer(self, name: str) -> PG_PickerLayer:
        new_picker_layer: PG_PickerLayer = self.picker_layers.add()
        new_picker_layer.name = name
        new_picker_layer.uuid = uuid4().hex
        self.active_picker_layer_index = (len(self.picker_layers) - 1)
        return new_picker_layer


    # ----------------------------------------------------------------

    def get_selected_nodes(self, context: Context, include_active: bool = True) -> set[AP_Node]:
        sel_nodes = set(context.selected_nodes)
        if include_active:
            if act_node := self.nodes.active:
                sel_nodes.add(act_node)
        return sel_nodes

    def get_selected_bones(self, context: Context, include_active: bool = True) -> set[PoseBone]:
        if context.active_object is None or context.active_object.type != 'ARMATURE':
            return set()
        if not context.selected_bones:
            return set()
        sel_bones = set(context.selected_bones)
        if include_active:
            if active_bone := context.active_bone:
                sel_bones.add(active_bone)
        return sel_bones


    # ----------------------------------------------------------------


    def update_nodes_depth(self) -> None:
        ''' We can call this after active node is changed. '''
        # TODO: support partial update, pass Node here and change its order in a more smart way.
        refresh_nodes_cache(self)


    def _test_select(self, context: Context, loc) -> int:
        if self.dirty:
            context.area.tag_redraw()

        # FIX SCROLLBARS.
        ui_scale = context.preferences.system.ui_scale
        region = context.region
        scroll_bar_thickness = 10 * ui_scale
        if loc[0] > (region.width - scroll_bar_thickness):
            return -1
        if loc[1] < scroll_bar_thickness:
            return -1

        global region_loc
        region_loc = Vector(loc)

        in_pose = self.picker_mode == 'POSE'

        global G_on_hover_tabs_area
        if in_pose:
            res_tabs = self._test_select_tabs(context)
            if res_tabs is not None:
                return res_tabs
        G_on_hover_tabs_area = None

        global G_active_node
        active_node = self.nodes.active
        if active_node is not None and G_active_node != active_node.uuid:
            # Active Node is updated !
            G_active_node = active_node.uuid
            if self.uuid in sorted_nodes_cache:
                refresh_nodes_cache(self)
            else:
                # Cache was refreshed! (on_load_post or dev environment reload)
                ensure_nodes_cache(self)
        else:
            ensure_nodes_cache(self)

        global G_hovered_node
        global view_loc
        view_zoom = get_node_editor_zoom(context)
        region_offset = get_node_editor_offset(context)
        view_loc = get_node_editor_view_point(context, region_loc)

        # A set of the widget types that are visible.
        visible_wg_types = get_visible_widget_types(self)
        selectable_wg_types = get_selectable_widget_types(self)

        for node_layer_nodes in reversed(sorted_nodes_cache[self.uuid]):
            for node in reversed(node_layer_nodes):
                if in_pose and not node.interactable:
                    continue
                if node.wg_type not in visible_wg_types:
                    continue
                if node.wg_type not in selectable_wg_types:
                    continue
                if node._test_select(context, not in_pose, region_loc, view_loc, view_zoom, region_offset):
                    G_hovered_node = node.uuid
                    #### print("hovered_node", node.label)
                    return 1

        G_hovered_node = None
        return 1


    def _test_select_tabs(self, context: Context) -> bool | None:
        # LAYER TABS.
        pinned_layers = self.picker_layers_pinned
        pinned_layer_count = len(pinned_layers)
        if pinned_layer_count < 2:
            return None

        global region_loc
        global G_on_hover_tabs_area
        ui_scale = context.preferences.system.ui_scale

        tabs_size = Vector((0, 0))
        for pinned_layer in pinned_layers:
            if pinned_layer.label_dimensions is None:
                tabs_size += (Vector((draw.get_text_dim(pinned_layer.name, 12)[0], TABS_HEADER_HEIGHT)) * ui_scale)
            else:
                tabs_size += (Vector((pinned_layer.label_dimensions.x, TABS_HEADER_HEIGHT)) * ui_scale)
        pad = 4 * ui_scale
        tab_spacing = 6 * ui_scale
        tabs_header_size = (
            tabs_size.x + tab_spacing * 2 * pinned_layer_count + tab_spacing * (pinned_layer_count - 1),
            TABS_HEADER_HEIGHT * ui_scale + pad * 2 # tabs_size.y + pad * 2
        )
        tabs_header_pos = Vector((
            tab_spacing * 2,
            context.region.height - tab_spacing * 2 - tabs_header_size[1]
        ))
        if point_inside_rect(region_loc, tabs_header_pos, tabs_header_size, 0):
            tab_size_pad = Vector((tab_spacing * 2, pad * 2))
            for pinned_layer in pinned_layers:
                if pinned_layer.label_dimensions is None:
                    tab_size = Vector((draw.get_text_dim(pinned_layer.name, 12)[0], TABS_HEADER_HEIGHT)) * ui_scale + tab_size_pad
                else:
                    tab_size = Vector((pinned_layer.label_dimensions.x, TABS_HEADER_HEIGHT)) * ui_scale + tab_size_pad
                if point_inside_rect(region_loc, tabs_header_pos, tab_size, 0):
                    G_on_hover_tabs_area = pinned_layer.uuid
                    return True
                tabs_header_pos.x += (tab_size.x + tab_spacing)
            G_on_hover_tabs_area = None
            return False


    # ----------------------------------------------------------------

    def set_inject_modal(self,
                         context: Context,
                         event: Event,
                         modal_callback: callable,
                         modal_enter_callback: callable = None,
                         modal_exit_callback: callable = None,
                         modal_draw_callback: callable = None,
                         use_advanced_mouse: bool = False) -> None:

        if use_advanced_mouse and self.active_node is not None:
            self.inject_modal_mouse = Mouse.init(event, context, local_space__rect=self.active_node.rect_transform)
            def _modal_update_wrapper(context: Context, event: Event, mouse_pos: Vector):
                self.inject_modal_mouse.update(event, context, local_space__rect=self.active_node.rect_transform)
                return modal_callback(context, event, self.inject_modal_mouse)
            self.inject_modal = _modal_update_wrapper
        else:
            self.inject_modal = modal_callback
        self.inject_modal_exit = modal_exit_callback
        self.inject_modal_draw = modal_draw_callback
        if modal_enter_callback is not None:
            modal_enter_callback(context, event, self.mouse_pos)


    def _invoke(self, context: Context, event: Event) -> set[str]:
        # Skip navigation km.
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'T', 'N', 'TAB', 'X', 'DEL', 'S', 'M'}:
            if event.value != 'PRESS':
                return {'PASS_THROUGH'}
            if event.type == 'WHEELUPMOUSE':
                bpy.ops.view2d.zoom_in('INVOKE_DEFAULT')
                self.on_view_resize(context)
            elif event.type == 'WHEELDOWNMOUSE':
                bpy.ops.view2d.zoom_out('INVOKE_DEFAULT')
                self.on_view_resize(context)
            elif event.type == 'MIDDLEMOUSE':
                bpy.ops.view2d.pan('INVOKE_DEFAULT')
            elif event.type == 'S' and event.ctrl:
                bpy.ops.wm.save_mainfile(False)
            elif event.type == 'N':
                context.space_data.show_region_ui = not context.space_data.show_region_ui
            elif event.type == 'T':
                context.space_data.show_region_toolbar = not context.space_data.show_region_toolbar
            elif event.type in {'X', 'DEL'}:
                bpy.ops.node.delete('INVOKE_DEFAULT')
                ensure_nodes_cache(self)
            elif event.type == 'TAB':
                self.picker_mode = 'POSE' if self.picker_mode == 'EDIT' else 'EDIT'
                context.area.tag_redraw()
            elif event.type == 'M' and self.picker_mode == 'EDIT':
                if len(self.picker_layers) > 1 and len(self.get_selected_nodes(context, include_active=True)) != 0:
                    bpy.ops.armature_picker.move_selected_to_another_layer('INVOKE_DEFAULT')
            return {'FINISHED'}

        if event.type == 'A' and not event.shift and event.value == 'PRESS':
            # bpy.ops.node.select_all(action='TOGGLE')
            if self.picker_mode == 'EDIT':
                for widget in self.widgets_interactable:
                    widget.select = True
            return {'FINISHED'}

        global G_on_hover_tabs_area

        if G_on_hover_tabs_area is not None:
            if event.type == 'LEFTMOUSE' and event.value == 'CLICK':
                for idx, pk_layer in enumerate(self.picker_layers):
                    if pk_layer.uuid == G_on_hover_tabs_area:
                        self.active_picker_layer_index = idx
                        print("changing active_picker_layer_index")
                        break
            return {'FINISHED'}

        global G_hovered_node

        # TO FIX A WEIRD BUG WHERE THE SAME EVENT IS SPAMMED TWICE...
        curr_time_event = time()
        if self.last_event_type == event.type and self.last_event_value == event.value and (curr_time_event - self.last_time_event) <= .2:
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS' and self.picker_mode == 'POSE' and G_hovered_node is not None:
                # An exception... to have the pose tools working...
                pass
            else:
                return {'FINISHED'}

        self.last_time_event = curr_time_event
        self.last_event_type = event.type
        self.last_event_value = event.value

        self.mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))

        self.modal_nodes = None
        self.active_node = None

        if self.picker_mode == 'POSE':
            ret = self.invoke__pose(context, event)
        else:
            ret = self.invoke__edit(context, event)

        if ret is not None:
            return ret

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

        if event.type == 'LEFTMOUSE':
            global G_hovered_node

            if G_hovered_node is None:
                if event.value == 'CLICK':
                    if not event.shift:
                        deselect_all_bones_from_active(context)
                        context.region.tag_redraw()
                    return {'FINISHED'}

                if event.value == 'CLICK_DRAG':
                    self.set_inject_modal(context, event,
                                      modal_callback=self.modal__box_select__update,
                                      modal_enter_callback=self.modal__box_select__enter,
                                      modal_exit_callback=self.modal__box_select__exit,
                                      modal_draw_callback=self.modal__box_select__draw)
                    return {'RUNNING_MODAL'}


    def invoke__edit(self, context: Context, event: Event) -> set[str] | None:
        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            if len(context.selected_nodes) == 0 and context.active_node is None:
                return {'FINISHED'}
            bpy.ops.wm.call_menu('INVOKE_DEFAULT', name=AP_MT_context_menu.bl_idname)
            return {'FINISHED'}

        if event.type in {'C', 'V'} and event.ctrl and event.value == 'CLICK':
            global G_clipboard_nodes
            if event.type == 'C':
                sel_nodes = self.get_selected_nodes(context, include_active=True)
                if len(sel_nodes) == 0:
                    # self.report({'WARNING'}, "No selected widgets to copy")
                    print("No selected widgets to copy")
                    return {'CANCELLED'}
                # bpy.ops.node.clipboard_copy()
                G_clipboard_nodes = [node.name for node in sel_nodes]
                # self.report({'INFO'}, "Copied %i widgets to clipboard" % len(G_clipboard_nodes))
                print("Copied %i widgets to clipboard" % len(G_clipboard_nodes))
            else:
                # bpy.ops.node.clipboard_paste()
                # sel_nodes = self.get_selected_nodes(context, include_active=True)
                if G_clipboard_nodes is None or len(G_clipboard_nodes) == 0:
                    # self.report({'WARNING'}, "No widgets widgets in clipboard")
                    print("No widgets widgets in clipboard")
                    return {'CANCELLED'}
                # self.report({'INFO'}, "Pasted %i widgets from clipboard" % len(G_clipboard_nodes))
                print("Pasted %i widgets from clipboard" % len(G_clipboard_nodes))
                bpy.ops.node.select_all(False, action='DESELECT')
                get_node = self.nodes.get
                for cb_node_name in G_clipboard_nodes:
                    if cb_node := get_node(cb_node_name, None):
                        cb_node.select = True
                G_clipboard_nodes = None
                bpy.ops.node.duplicate('INVOKE_DEFAULT', False)
                sel_nodes = self.get_selected_nodes(context, include_active=True)
                if len(sel_nodes) == 0:
                    return {'CANCELLED'}
                for sel_node in sel_nodes:
                    sel_node.locked = False
                ensure_nodes_cache(self)
                self.modal_nodes = sel_nodes
                self.set_inject_modal(context, event,
                                    modal_callback=self.modal__move_node__update,
                                    modal_enter_callback=self.modal__move_node_cursor__enter,
                                    modal_exit_callback=self.modal__move_node__exit)
                return {'RUNNING_MODAL'}
            return {'FINISHED'}

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
            for sel_node in sel_nodes:
                sel_node.locked = False
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
        sel_nodes = {_node for _node in sel_nodes if test_node_sel_locked(self, _node)}

        # print("Selected nodes", sel_nodes)

        if self.nodes.active is not None:
            if (event.type == 'G' and event.value == 'RELEASE') or\
               (event.type == 'LEFTMOUSE' and event.value == 'CLICK_DRAG' and G_hovered_node is not None and hovered_node in sel_nodes):
                if G_hovered_node is not None and hovered_node is not None:
                    if hovered_node.locked:
                        return {'CANCELLED'}
                    if hovered_node == self.nodes.active and hovered_node.get_state('HOVERED_BORDER', 'NONE') != 'NONE':
                        self.active_node = hovered_node
                        self.set_inject_modal(context, event,
                                        modal_callback=self.modal__resize_node__update,
                                        modal_enter_callback=self.modal__resize_node__enter,
                                        modal_exit_callback=self.modal__resize_node__exit,
                                        use_advanced_mouse=True)
                        return {'RUNNING_MODAL'}
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
                self.modal_nodes = [node for node in sel_nodes if node.wg_type != 'bone_picker_geo']
                if len(self.modal_nodes) == 0:
                    return {'CANCELLED'}
                self.set_inject_modal(context, event,
                                      modal_callback=self.modal__rotate_node__update,
                                      modal_enter_callback=self.modal__rotate_node__enter,
                                      modal_exit_callback=self.modal__rotate_node__exit,
                                      modal_draw_callback=self.modal__rotate_node__draw)
                return {'RUNNING_MODAL'}

        if G_hovered_node is not None and hovered_node is not None and event.type == 'LEFTMOUSE':
            if event.value == 'CLICK_DRAG' and hovered_node not in sel_nodes:
                for sel_node in sel_nodes:
                    sel_node.select = False
                if not test_node_sel_locked(self, hovered_node):
                    return {'CANCELLED'}
                self.nodes.active = hovered_node
                hovered_node.select = True
                return self.invoke__edit(context, event)

            if event.value == 'RELEASE':
                if not test_node_sel(self, hovered_node):
                    if hovered_node.select:
                        hovered_node.select = False
                    if self.nodes.active == hovered_node:
                        self.nodes.active = None
                    return {'FINISHED'}
                if hovered_node.locked:
                    bpy.ops.node.select_all(False, action='DESELECT')
                    self.nodes.active = hovered_node
                    return {'FINISHED'}
                elif hovered_node.select and event.shift and self.nodes.active == hovered_node:
                    self.nodes.active = None
                    hovered_node.select = False
                else:
                    # hovered_node.select_node(context, deselect_all=not event.shift, toggle=False, set_active=True)
                    if not event.shift:
                        bpy.ops.node.select_all(False, action='DESELECT')
                    hovered_node.select = True
                    self.nodes.active = hovered_node


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
        if self.inject_modal_mouse is not None:
            self.inject_modal_mouse = None


    # ----------------------------------------------------------------


    def _draw(self, context: Context) -> None:
        if not hasattr(self, 'uuid'):
            self.uuid = uuid4().hex

        ui_scale = context.preferences.system.ui_scale
        in_edit = self.picker_mode == 'EDIT'

        refresh: bool = False
        zoom = get_node_editor_zoom(context)
        offset = get_node_editor_offset(context)

        global view_loc

        active_node: AP_Node = self.nodes.active
        sel_nodes: set[AP_Node] = self.get_selected_nodes(context)

        visible_view_box = get_node_editor_visible_view_box(context)

        theme_style = get_active_theme_style(context)
        wg_settings = get_prefs_wg_settings(context)

        # A set of the widget types that are visible.
        visible_wg_types = get_visible_widget_types(self)

        with gpu.matrix.push_pop():
            gpu.matrix.translate(offset)
            gpu.matrix.scale_uniform(zoom)

            for node_layer_nodes in sorted_nodes_cache[self.uuid]:
                for node in node_layer_nodes:
                    if node.wg_type not in visible_wg_types:
                        continue
                    if not rect_overlap(visible_view_box, node.rect_transform):
                        # print("Node outside view", node.label)
                        continue
                    if node.dirty:
                        refresh = True
                    node._draw(context,
                               view_loc,
                               node.get_style(theme_style),
                               node.get_settings(wg_settings),
                               ui_scale,
                               active=node==active_node,
                               selected=node in sel_nodes if in_edit else node.wg_type.startswith('bone_picker') and node.test_bone_selected(context),
                               in_edit=in_edit)

            if self.active_node is not None and self.active_node.in_modal:
                draw_callback = self.active_node.modal_draw__edit if in_edit else self.active_node.modal_draw__pose
                draw_callback(context, self.active_node.rect_transform, self.active_node.get_style(theme_style), ui_scale)

            if self.inject_modal_draw is not None:
                self.inject_modal_draw(context, ui_scale, sel_nodes, in_edit=in_edit, in_view2d=True)


            if refresh:
                context.region.tag_redraw()

        if self.inject_modal_draw is not None:
            self.inject_modal_draw(context, ui_scale, sel_nodes, in_edit=in_edit, in_view2d=False)

        if in_edit:
            draw.box(
                self.get_graphic_user('EDIT_CAGE'), 'EDIT_CAGE',
                Vector((0, 0)), Vector((context.region.width, context.region.height)),
                padding=8,
                line_thickness=1,
                color=(.9, .3, .1, .5)
            )
        else:
            self.draw_layer_tabs(context)


    def draw_layer_tabs(self, context: Context) -> None:
        # LAYER TABS.
        pinned_layers = self.picker_layers_pinned
        pinned_layer_count = len(pinned_layers)
        if pinned_layer_count < 2:
            return

        global G_on_hover_tabs_area
        active_layer_id = self.active_picker_layer.uuid
        ui_scale = context.preferences.system.ui_scale

        tabs_size = Vector((0, 0))
        for pinned_layer in pinned_layers:
            if pinned_layer.label_dimensions is None:
                pinned_layer.update_label_dimensions(context)
            tabs_size += (Vector((pinned_layer.label_dimensions.x, TABS_HEADER_HEIGHT)) * ui_scale)
        pad = 4 * ui_scale
        tab_spacing = 6 * ui_scale
        tabs_header_size = (
            0,
            TABS_HEADER_HEIGHT * ui_scale + pad * 2 # tabs_size.y + pad * 2
        )
        tabs_header_pos = Vector((
            tab_spacing * 2,
            context.region.height - tab_spacing * 2 - tabs_header_size[1]
        ))
        tab_size_pad = Vector((tab_spacing * 2, pad * 2))
        use_default_highlight = all([pinned_layer.color_icon.endswith('9') for pinned_layer in pinned_layers])
        for pinned_layer in pinned_layers:
            layer_color = pinned_layer.color
            is_active_layer = pinned_layer.uuid == active_layer_id
            is_hovered_layer = G_on_hover_tabs_area == pinned_layer.uuid
            tab_size = (Vector((pinned_layer.label_dimensions.x, TABS_HEADER_HEIGHT)) * ui_scale + tab_size_pad)
            if use_default_highlight:
                if is_active_layer:
                    color = (.12, .56, .95, 1.0) if is_hovered_layer else (.12, .56, .95, .75)
                else:
                    color = (.12, .12, .12, 1.0) if is_hovered_layer else (.06, .06, .06, .75)
            else:
                if is_active_layer:
                    alpha = 1.0 if is_hovered_layer else .75
                    # color = layer_color * .9 if is_hovered_layer else layer_color
                else:
                    alpha = .9 if is_hovered_layer else .3
                    # color = layer_color * .9 if is_hovered_layer else layer_color * .75
                color = (*layer_color, alpha)
            draw.wg(
                self.get_graphic_user('TABS'), pinned_layer.uuid,
                tabs_header_pos,
                tab_size,
                rotation=0,
                roundness=.35,
                outline_thickness=1.0,
                bg_color=color
            )
            draw.text(
                tabs_header_pos + tab_size_pad * 0.5 + Vector((0, 1.5 * ui_scale)),
                pinned_layer.name,
                int(12 * ui_scale),
                pivot=(0, 0),
                angle=0,
                color=(.92, .92, .92),
                alpha=.92,
                use_shadow=is_active_layer or is_hovered_layer,
                shadow_level=5,
                shadow_color=(0, 0, 0, 1),
                shadow_offset=(1, -1)
            )
            # if not use_default_highlight and is_active_layer:
            #     draw.box(
            #         self.get_graphic_user('ACTIVE_TAB_CAGE'), pinned_layer.uuid,
            #         tabs_header_pos,
            #         tab_size,
            #         padding=-1.5 * ui_scale,
            #         line_thickness=2.0 * ui_scale,
            #         color=(.12, .56, .95, 1.0) if is_hovered_layer else (.12, .56, .95, .75)
            #     )
            tabs_header_pos.x += (tab_size.x + tab_spacing)


    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


    # MODAL: Move Selected Nodes.
    # ----------------------------------------------------------------

    def modal__move_node__enter(self, context: Context, event: Event, mouse_pos: Vector) -> None:
        self.prev_node_location = [tuple(node.rect_transform.origin) for node in self.modal_nodes]
        node_region_location = [get_node_editor_region_coord(context, node.rect_transform.origin) for node in self.modal_nodes]
        self.node_location_offset = [prev_node_loc - mouse_pos for prev_node_loc in node_region_location]

        Cursor.set_icon(context, CursorIcon.HAND)

    def modal__move_node_cursor__enter(self, context: Context, event: Event, mouse_pos: Vector) -> None:
        zoom = get_node_editor_zoom(context)
        inv_zoom = 1/zoom
        offset = get_node_editor_offset(context)
        mouse_offset = (mouse_pos - offset) * inv_zoom

        # Calculate the center of the selected nodes.
        center = Vector((0, 0))
        for node in self.modal_nodes:
            center += Vector(node.rect_transform.origin)
        center /= len(self.modal_nodes)

        for node in self.modal_nodes:
            node.rect_transform.move_to(mouse_offset + (Vector(node.rect_transform.origin) - center))

        self.modal__move_node__enter(context, event, mouse_pos)

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

        Cursor.set_icon(context, CursorIcon.DEFAULT)


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


    # MODAL: Resize Selected Nodes.
    # ----------------------------------------------------------------

    def modal__resize_node__enter(self, context: Context, event: Event, mouse_pos: Vector) -> None:
        node = self.active_node
        rect: RectTransform = node.rect_transform
        node.in_modal = True

        self.prev_node_coords = list(rect.coords)
        self.node_border_id: str =node.get_state('HOVERED_BORDER', 'NONE')
        self.node_reg_loc = get_node_editor_region_coord(context, rect.origin)
        self.node_reg_loc_offset = self.node_reg_loc - mouse_pos

        self.node_bbox = Box(rect.x_min, rect.y_min, rect.x_max, rect.y_max)

        if self.node_border_id == 'LEFT':
            self.rect_border_attr = 'x_min'
            self.node_start_min = rect.x_min
        elif self.node_border_id == 'BOTTOM':
            self.rect_border_attr = 'y_min'
            self.node_start_min = rect.y_min

        if node.wg_type == 'bone_picker' and node.fit_to_text:
            node.fit_to_text = False

        if ((node.wg_type in {'bone_picker', 'button_script'} and node.use_image) or node.wg_type == 'image') and node.image is not None:
            self.use_keep_image_aspect_ratio = node.keep_aspect_ratio
        else:
            self.use_keep_image_aspect_ratio = False

        Cursor.set_icon(context, CursorIcon.DOT)


    def modal__resize_node__update(self, context: Context, event: Event, mouse: Mouse) -> int:
        if self.active_node is None or (event.type == 'LEFTMOUSE' and event.value == 'RELEASE'):
            return -1

        if event.type not in {EventType.MOUSEMOVE, EventType.INBETWEEN_MOUSEMOVE}:
            return 1

        border_id = self.node_border_id
        is_hor_border = border_id in {'LEFT', 'RIGHT'}
        is_vert_border = border_id in {'BOTTOM', 'TOP'}
        is_max_border = border_id in {'RIGHT', 'TOP'}
        is_min_border = border_id in {'LEFT', 'BOTTOM'}

        if is_hor_border and mouse.local_dir.x == 0:
            return 1
        if is_vert_border and mouse.local_dir.y == 0:
            return 1

        node = self.active_node
        rect: RectTransform = node.rect_transform

        zoom = get_node_editor_zoom(context)
        inv_zoom = 1/zoom
        offset = get_node_editor_offset(context)

        # OLD METHOD
        # BUG ISSUE: looks like local_rect_space Mouse type stuff is wiggling around when modifying the minimum values (x_min, y_min).
        # It works for maximum values (x_max, y_max) tho.

        # print("local_current_prev ->", mouse.local_prev.x, "->", mouse.local_current.x)
        # print("local_delta_int.x ->", mouse.local_delta_int.x)
        # print("local_offset.x ->", mouse.local_offset.x)

        prev_dim = Vector(rect.dimensions)

        if self.use_keep_image_aspect_ratio:
            prev_origin = tuple(rect.origin)

        if is_hor_border:
            rect_dir_v = (rect.bottom_right - rect.bottom_left).normalized()
            if is_min_border:
                rect.x_min = get_node_editor_view_point(context, mouse.current).x ## rect.x_min + mouse.local_delta_int.x * inv_zoom ## self.node_start_min + mouse.local_offset.x * inv_zoom
            elif is_max_border:
                if rect.rotation == 0:
                    rect.x_max = get_node_editor_view_point(context, mouse.current).x
                else:
                    rect.x_max = rect.x_max + mouse.local_delta_int.x * inv_zoom

        elif is_vert_border:
            rect_dir_v = (rect.top_right - rect.top_left).normalized()
            if is_min_border:
                rect.y_min = get_node_editor_view_point(context, mouse.current).y ## rect.y_min + mouse.local_delta_int.y * inv_zoom ## self.node_start_min + mouse.local_offset.y * inv_zoom
            elif is_max_border:
                if rect.rotation == 0:
                    rect.y_max = get_node_editor_view_point(context, mouse.current).y
                else:
                    rect.y_max = rect.y_max + mouse.local_delta_int.y * inv_zoom

        # rect.update_from_coords(context)
        if hasattr(node, 'apply_transform_dimensions_constraints'):
            new_dim = Vector(rect.dimensions)
            if prev_dim != new_dim:
                if constrained_dimensions := node.apply_transform_dimensions_constraints(prev_dim, new_dim):
                    rect.dimensions = constrained_dimensions

        if self.use_keep_image_aspect_ratio:
            rect.origin = prev_origin

        node.update_graphics(context)
        return 1

    def modal__resize_node__exit(self, context: Context, mouse_pos: Vector, cancel: bool) -> None:
        rect: RectTransform = self.active_node.rect_transform

        if cancel:
            rect.coords = self.prev_node_coords
            rect.update_from_coords(context)

        elif rect.rotation != 0 or not rect.can_update_origin_on_redimension:
            v_dir_angle = (Vector(rect.coords_rotated[2]) - Vector(rect.coords_rotated[1])).normalized()

            width, height = rect.dimensions

            origin_in_local = Vector((
                rect.pivot[0] * (width - 2),
                rect.pivot[1] * (height - 1)
            ))
            rotation_angle = rect.rotation
            rotated_offset_x = origin_in_local.x * cos(rotation_angle) - origin_in_local.y * sin(rotation_angle)
            rotated_offset_y = origin_in_local.x * sin(rotation_angle) + origin_in_local.y * cos(rotation_angle)

            rect.origin = (
                int(rect.coords_rotated[1][0] + rotated_offset_x - v_dir_angle.x * .25),
                int(rect.coords_rotated[1][1] + rotated_offset_y - v_dir_angle.y * .25)
            )

        if hasattr(self, 'node_start_min'):
            del self.rect_border_attr
            del self.node_start_min
        del self.node_border_id
        del self.prev_node_coords
        del self.node_reg_loc
        del self.node_reg_loc_offset
        del self.node_bbox
        del self.use_keep_image_aspect_ratio

        self.active_node.in_modal = False
        self.active_node = None

        Cursor.set_icon(context, CursorIcon.DEFAULT)


    # ----------------------------------------------------------------

    def modal__box_select__enter(self, context: Context, event: Event, mouse_pos: Vector) -> None:
        self.box = Box(mouse_pos.x, mouse_pos.y, mouse_pos.x, mouse_pos.y)
        self.box_origin = mouse_pos.copy()
        self.dummy_node = DummyNode('MODAL_BOX_SELECT')
        in_edit = self.picker_mode == 'EDIT'
        self.append_selection = event.shift
        self.modal_nodes = self.widgets_from_active_layer if in_edit else [node for node in self.widgets_from_active_layer if node.wg_type.startswith('bone_picker')]
        if in_edit:
            self.prev_sel_nodes = self.get_selected_nodes(context, include_active=True)
        else:
            self.prev_sel_nodes = {_node for _node in self.modal_nodes if _node.test_bone_selected(context)}

        if self.append_selection:
            if in_edit:
                pass
            else:
                bpy.ops.node.select_all(False, action='DESELECT')
                for prev_sel_node in self.prev_sel_nodes:
                    prev_sel_node.select = True
        else:
            bpy.ops.node.select_all(False, action='DESELECT')
            if not in_edit:
                deselect_all_bones_from_active(context)

        Cursor.set_icon(context, CursorIcon.CROSS)

    def modal__box_select__update(self, context: Context, event: Event, mouse_pos: Vector) -> int:
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            return -1

        if event.type not in {EventType.MOUSEMOVE, EventType.INBETWEEN_MOUSEMOVE}:
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

        for node in self.modal_nodes:
            rect = node.rect_transform
            if rect_overlap(proj_box, rect):
                node.select = True
            elif node.select:
                if self.append_selection and node in self.prev_sel_nodes:
                    continue
                node.select = False

        context.region.tag_redraw()
        return 1

    def modal__box_select__exit(self, context: Context, mouse_pos: Vector, cancel: bool) -> None:
        in_pose = self.picker_mode == 'POSE'

        if cancel:
            deselect_all_bones_from_active(context)
            for sel_node in self.prev_sel_nodes:
                sel_node.select = True

        else:
            sel_nodes = [node for node in self.modal_nodes if node.select]
            if len(sel_nodes) != 0:
                self.nodes.active = sel_nodes.pop()
                if in_pose:
                    self.nodes.active.select_bone(context, deselect_all=True, make_active=True)
                    for node in sel_nodes:
                        node.select_bone(context, deselect_all=False, make_active=False)
                    for sel_node in self.prev_sel_nodes:
                        sel_node.select_bone(context, deselect_all=False, make_active=False)

                del sel_nodes

        Cursor.set_icon(context, CursorIcon.DEFAULT)

        del self.append_selection
        del self.box
        del self.box_origin
        del self.dummy_node
        del self.prev_sel_nodes
        self.modal_nodes = None


    def modal__box_select__draw(self, context: Context, ui_scale: float, sel_nodes: list[Node], in_edit: bool, in_view2d: bool) -> None:
        if in_view2d:
            if in_edit:
                return

            for node in self.modal_nodes:
                if node.select:
                    node.draw_sel_cage((.3, .7, 1.0, .92), cage_thickness=2.5)

        else:
            draw.box(
                self.dummy_node, 'BOX_SELECT',
                self.box.pos, self.box.size,
                padding=0,
                line_thickness=2.0,
                color=(1, 1, 1, .92)
            )

    def reset(self):
        self.active_node = None
        self.modal_nodes = None
        self.inject_modal = None
        self.inject_modal_draw = None
        self.inject_modal_exit = None


# ----------------------------------------------------------------

def reset_globals():
    # Reset All globals.
    sorted_nodes_cache.clear()
    graphic_users.clear()

    global G_active_node
    global G_hovered_node
    global nodes_count
    G_active_node = ''
    G_hovered_node = ''
    nodes_count = -1

    from .nodes._base import reset_globals as reset_node_globals
    reset_node_globals()


# ----------------------------------------------------------------

def register():
    pass


def unregister():
    reset_globals()
