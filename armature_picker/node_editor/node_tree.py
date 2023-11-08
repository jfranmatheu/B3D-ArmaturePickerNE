from bpy import ops as OPS
from bpy.types import NodeTree, Context, Event, Node, PoseBone
from bpy.props import BoolProperty, EnumProperty, StringProperty, PointerProperty, IntProperty, CollectionProperty
from mathutils import Vector
import gpu

from time import time
from uuid import uuid4
from typing import List, Tuple, Type, Dict, Set, Union
from collections import defaultdict
from dataclasses import dataclass

from armature_picker.layers.pg import PG_PickerLayer
from armature_picker.data.pg.picker_view import AP_PG_PickerView
from armature_picker.ui.header_menus.widget_types_visibility import attr_widget_types
from armature_picker.utils.event import isEventType, isEventValue, EventType, EventValue, isEvent
from armature_picker.utils.operator import OpsReturn
from armature_picker.ui.context_menu import AP_MT_context_menu
from ..gpu import draw
from .nodes._base import AP_Node, RectTransform
from ..utils.node_editor import get_node_editor_view_size, set_node_editor_visible_view_box, center_node_editor_view, get_node_editor_zoom, get_node_editor_view_point, get_node_editor_offset, get_node_editor_region_coord, get_node_editor_visible_view_box
from ..utils.armature import deselect_all_bones_from_active
from ..utils.geometry import angle_signed, rect_overlap, Box, point_inside_rect
from armature_picker.prefs import get_active_theme_style, get_prefs_wg_settings
from .transform_modals import PickerTransformModals, PickerModal


# ----------------------------------------------------------------

# GLOBALS.
G_active_node = ''
G_hovered_node = ''
G_on_hover_tabs_area = False
nodes_count: int = -1
G_clipboard_nodes = None

TABS_HEADER_HEIGHT = draw.get_text_dim('Xy', 12)[1]

ARROW_DIRECTIONS = {
    EventType.LEFT_ARROW: Vector((-1, 0)),
    EventType.RIGHT_ARROW: Vector((1, 0)),
    EventType.DOWN_ARROW: Vector((0, -1)),
    EventType.UP_ARROW: Vector((0, 1))
}

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

    in_edit = node_tree.picker_mode == 'EDIT'

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

        if in_edit:
            if active_node in _nodes:
                _nodes.remove(active_node)
                active_on_top = True
            else:
                active_on_top = False

        sorted_nodes.append(
            sorted(_nodes, key=lambda node: node.draw_depth)
        )

        if in_edit:
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


class AP_NodeTree(PickerTransformModals, NodeTree):
    bl_idname = 'AP_NODETREE'
    bl_label = "Armature Picker"
    bl_icon = 'OUTLINER_OB_ARMATURE' # CON_ARMATURE


    def prepare_if_linked(self):
        ''' Configure it so that it works properly when linked. '''
        if self.library is None:
            return

        self.picker_mode = 'POSE'
        for picker_layer in self.picker_layers:
            picker_layer.use_pin = True

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
    active_picker_layer_index: IntProperty(default=-1, name="Active Picker Layer", update=update_active_layer)
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
                if node._test_select(context, not in_pose, node==active_node, view_loc, view_zoom):
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

    def _invoke(self, context: Context, event: Event) -> set[str]:
        EVENT_TYPE, EVENT_VALUE = event.type, event.value
        is_linked = self.library is not None

        # Skip navigation km.
        if EVENT_TYPE in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'T', 'N', 'TAB'}:
            if not isEventValue.PRESS:
                return OpsReturn.PASS
            if EVENT_TYPE == 'WHEELUPMOUSE':
                OPS.view2d.zoom_in('INVOKE_DEFAULT')
                self.on_view_resize(context)
            elif EVENT_TYPE == 'WHEELDOWNMOUSE':
                OPS.view2d.zoom_out('INVOKE_DEFAULT')
                self.on_view_resize(context)
            elif EVENT_TYPE == 'MIDDLEMOUSE':
                OPS.view2d.pan('INVOKE_DEFAULT')
            elif EVENT_TYPE == 'N':
                context.space_data.show_region_ui = not context.space_data.show_region_ui
            elif EVENT_TYPE == 'T':
                context.space_data.show_region_toolbar = not context.space_data.show_region_toolbar
            elif EVENT_TYPE == 'TAB' and not is_linked:
                self.picker_mode = 'POSE' if self.picker_mode == 'EDIT' else 'EDIT'
                refresh_nodes_cache(self)
                context.area.tag_redraw()
            return OpsReturn.FINISH

        if isEventType.S and event.ctrl:
            if isEventValue.RELEASE:
                OPS.wm.save_mainfile(False)
            return OpsReturn.FINISH

        if isEvent(EventType.A, EventValue.PRESS, shift=False):
            if self.picker_mode == 'EDIT':
                for widget in self.widgets_interactable:
                    widget.select = True
            return OpsReturn.FINISH

        global G_on_hover_tabs_area

        if G_on_hover_tabs_area is not None:
            if isEventType.LEFTMOUSE and isEventValue.CLICK:
                for idx, pk_layer in enumerate(self.picker_layers):
                    if pk_layer.uuid == G_on_hover_tabs_area:
                        self.active_picker_layer_index = idx
                        break
            return OpsReturn.FINISH

        global G_hovered_node

        # TO FIX A WEIRD BUG WHERE THE SAME EVENT IS SPAMMED TWICE...
        # ----------------------------------------------------------------
        curr_time_event = time()
        if self.last_event_type == EVENT_TYPE and self.last_event_value == EVENT_VALUE and (curr_time_event - self.last_time_event) <= .2:
            if isEventType.LEFTMOUSE and isEventValue.PRESS and self.picker_mode == 'POSE' and G_hovered_node is not None:
                # An exception... to have the pose tools working...
                pass
            else:
                return OpsReturn.FINISH

        self.last_time_event = curr_time_event
        self.last_event_type = EVENT_TYPE
        self.last_event_value = EVENT_VALUE
        # ----------------------------------------------------------------

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
            return OpsReturn.FINISH

        # Interact with a node.
        if node := self.nodes.get(G_hovered_node, None):
            ret = node._invoke(context, event, self.mouse_pos)
            if isinstance(ret, set):
                if 'RUNNING_MODAL' in ret:
                    self.active_node = node
                return ret

        return OpsReturn.FINISH


    def invoke__pose(self, context: Context, event: Event) -> set[str] | None:
        if isEvent(EventType.RIGHTMOUSE, EventValue.PRESS):
            if context.active_bone is None:
                return OpsReturn.FINISH
            from .ops.insert_keyframe import MT_insert_keyframe
            # context.window_manager.popup_menu_pie(event, MT_insert_keyframe.draw)
            with context.temp_override(window=context.window, area=context.area, bone=context.active_bone):
                OPS.wm.call_menu_pie('INVOKE_DEFAULT', name=MT_insert_keyframe.bl_idname)
            self.dirty = True
            return OpsReturn.FINISH

        global G_hovered_node
        if G_hovered_node is None and isEventType.LEFTMOUSE:
            if isEventValue.CLICK:
                if not event.shift:
                    deselect_all_bones_from_active(context)
                    context.region.tag_redraw()
                return OpsReturn.FINISH

            if isEventValue.CLICK_DRAG:
                return PickerModal.BOX_SELECT(self, context, event, None)


    def invoke__edit(self, context: Context, event: Event) -> set[str] | None:
        EVENT_TYPE, _EVENT_VALUE = event.type, event.value

        if EVENT_TYPE in {'X', 'DEL'}:
            if isEventValue.PRESS:
                OPS.node.delete('INVOKE_DEFAULT')
                ensure_nodes_cache(self)
            return OpsReturn.FINISH

        elif isEventType.M:
            if isEventValue.PRESS:
                if len(self.picker_layers) > 1 and len(self.get_selected_nodes(context, include_active=True)) != 0:
                    OPS.armature_picker.move_selected_to_another_layer('INVOKE_DEFAULT')
            return OpsReturn.FINISH

        elif isEventType.RIGHTMOUSE:
            if isEventValue.PRESS:
                if len(context.selected_nodes) == 0 and context.active_node is None:
                    return OpsReturn.FINISH
                OPS.wm.call_menu('INVOKE_DEFAULT', name=AP_MT_context_menu.bl_idname)
            return OpsReturn.FINISH

        if EVENT_TYPE in {'C', 'V'} and event.ctrl and isEventValue.CLICK:
            global G_clipboard_nodes
            if EVENT_TYPE == 'C':
                sel_nodes = self.get_selected_nodes(context, include_active=True)
                if len(sel_nodes) == 0:
                    print("No selected widgets to copy")
                    return OpsReturn.CANCEL
                G_clipboard_nodes = [node.name for node in sel_nodes]
                print("Copied %i widgets to clipboard" % len(G_clipboard_nodes))
            else:
                if G_clipboard_nodes is None or len(G_clipboard_nodes) == 0:
                    print("No widgets widgets in clipboard")
                    return OpsReturn.CANCEL
                print("Pasted %i widgets from clipboard" % len(G_clipboard_nodes))
                OPS.node.select_all(False, action='DESELECT')
                get_node = self.nodes.get
                for cb_node_name in G_clipboard_nodes:
                    if cb_node := get_node(cb_node_name, None):
                        cb_node.select = True
                G_clipboard_nodes = None
                OPS.node.duplicate('INVOKE_DEFAULT', False)
                sel_nodes = self.get_selected_nodes(context, include_active=True)
                if len(sel_nodes) == 0:
                    return OpsReturn.CANCEL
                for sel_node in sel_nodes:
                    sel_node.locked = False
                ensure_nodes_cache(self)
                return PickerModal.MOVE_NODE_CURSOR(self, context, event, sel_nodes)
            return OpsReturn.FINISH

        global G_hovered_node

        # BLANK SPACE INTERACTION!
        if G_hovered_node is None:
            if isEventType.LEFTMOUSE:
                if isEventValue.RELEASE:
                    OPS.node.select_all(False, action='DESELECT')
                    return OpsReturn.FINISH
                if isEventValue.CLICK_DRAG:
                    return PickerModal.BOX_SELECT(self, context, event, None)

        if EVENT_TYPE == 'A' and isEventValue.RELEASE and event.shift:
            from .ops.add_node.pie_menu import MT_add_node
            OPS.wm.call_menu_pie('INVOKE_DEFAULT', name=MT_add_node.bl_idname)
            return OpsReturn.FINISH

        if EVENT_TYPE == 'D' and isEventValue.RELEASE and event.shift:
            OPS.node.duplicate('INVOKE_DEFAULT', False)
            sel_nodes = self.get_selected_nodes(context, include_active=True)
            if len(sel_nodes) == 0:
                return OpsReturn.CANCEL
            for sel_node in sel_nodes:
                sel_node.locked = False
            ensure_nodes_cache(self)
            return PickerModal.MOVE_NODE(self, context, event, sel_nodes)

        if G_hovered_node is not None:
            hovered_node: AP_Node = self.nodes.get(G_hovered_node, None)

        sel_nodes = self.get_selected_nodes(context, include_active=True)
        sel_nodes = {_node for _node in sel_nodes if test_node_sel_locked(self, _node)}

        if len(sel_nodes) != 0:
            # Move nodes by increments by using arrow keys.
            if EVENT_TYPE in ARROW_DIRECTIONS and isEventValue.PRESS:
                self.move_node_increment(context, sel_nodes, ARROW_DIRECTIONS[EVENT_TYPE])
                return OpsReturn.FINISH

        if self.nodes.active is not None:
            if (EVENT_TYPE == 'G' and isEventValue.RELEASE) or\
               (isEventType.LEFTMOUSE and isEventValue.CLICK_DRAG and G_hovered_node is not None and hovered_node in sel_nodes):
                if G_hovered_node is not None and hovered_node is not None:
                    if hovered_node.locked:
                        return OpsReturn.CANCEL
                    if hovered_node == self.nodes.active and hovered_node.get_state('HOVERED_BORDER', 'NONE') != 'NONE':
                        return PickerModal.RESIZE_NODE(self, context, event, hovered_node)
                return PickerModal.MOVE_NODE(self, context, event, sel_nodes)

            if (EVENT_TYPE == 'R' and isEventValue.RELEASE):
                modal_nodes = [node for node in sel_nodes if node.wg_type != 'bone_picker_geo']
                return PickerModal.ROTATE_NODE(self, context, event, modal_nodes)

            if (EVENT_TYPE == 'S' and isEventValue.RELEASE):
                return PickerModal.SCALE_NODE(self, context, event, sel_nodes)

        if G_hovered_node is not None and hovered_node is not None and isEventType.LEFTMOUSE:
            if isEventValue.CLICK_DRAG and hovered_node not in sel_nodes:
                for sel_node in sel_nodes:
                    sel_node.select = False
                if not test_node_sel_locked(self, hovered_node):
                    return OpsReturn.CANCEL
                self.nodes.active = hovered_node
                hovered_node.select = True
                return self.invoke__edit(context, event)

            if isEventValue.RELEASE:
                if not test_node_sel(self, hovered_node):
                    if hovered_node.select:
                        hovered_node.select = False
                    if self.nodes.active == hovered_node:
                        self.nodes.active = None
                    return OpsReturn.FINISH
                if hovered_node.locked:
                    OPS.node.select_all(False, action='DESELECT')
                    self.nodes.active = hovered_node
                    return OpsReturn.FINISH
                elif hovered_node.select and event.shift and self.nodes.active == hovered_node:
                    self.nodes.active = None
                    hovered_node.select = False
                else:
                    # hovered_node.select_node(context, deselect_all=not event.shift, toggle=False, set_active=True)
                    if not event.shift:
                        OPS.node.select_all(False, action='DESELECT')
                    hovered_node.select = True
                    self.nodes.active = hovered_node


    # ----------------------------------------------------------------


    def _modal(self, context: Context, event: Event, _tweak: str) -> set[str]:
        if self.inject_modal is not None:
            self.mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))
            if self.inject_modal(context, event, self.mouse_pos) == -1:
                self.inject_modal = None
                return OpsReturn.FINISH
            return OpsReturn.RUN

        if self.active_node is not None and self.active_node.in_modal:
            return self.active_node._modal(context, event)

        return OpsReturn.FINISH

    def _exit(self, context: Context, cancel: bool) -> None:
        if self.inject_modal is not None:
            self.inject_modal = None
        elif self.active_node is not None and self.active_node.in_modal:
            self.active_node.modal_exit(context, cancel)
        if self.inject_modal_draw is not None:
            self.inject_modal_draw = None
        if self.inject_modal_exit is not None:
            self.inject_modal_exit(context, self.mouse_pos, cancel)
            self.inject_modal_exit = None
        if self.inject_modal_mouse is not None:
            self.inject_modal_mouse = None
        self.modal_nodes = None

    # ----------------------------------------------------------------

    def draw_base(self, ui_scale: float, in_edit: bool) -> None:
        if in_edit:
            draw.just_a_line(
                (0, -10000),
                (0, 10000),
                line_thickness=1 * ui_scale,
                color=(1, .344, .344, .5)
            )

    def _draw(self, context: Context) -> None:
        if not hasattr(self, 'uuid'):
            self.uuid = uuid4().hex

        ui_scale = context.preferences.system.ui_scale
        in_edit = self.picker_mode == 'EDIT'

        self.draw_base(ui_scale, in_edit)

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

            self.draw_base(ui_scale, in_edit)

            for node_layer_nodes in sorted_nodes_cache[self.uuid]:
                for node in node_layer_nodes:
                    if node.wg_type not in visible_wg_types:
                        continue
                    if not rect_overlap(visible_view_box, node.rect_transform):
                        # Node outside view box.
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
                else:
                    alpha = .9 if is_hovered_layer else .3
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
            tabs_header_pos.x += (tab_size.x + tab_spacing)


    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


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
