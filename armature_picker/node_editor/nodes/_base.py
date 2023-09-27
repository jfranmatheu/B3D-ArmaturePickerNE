import bpy
from bpy.types import Node, UILayout, NodeTree, Context, Event, Armature, Bone
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty
from mathutils import Vector

from collections import defaultdict
from uuid import uuid4

from ...utils.event import Mouse, EventType, EventValue
from ...utils.operator import OpsReturn
from ...utils.armature import deselect_all_bones_from_active
from ...utils.geometry import point_inside_rect
from armature_picker.node_editor.poll import poll_check
from armature_picker.gpu import draw

from ._transform_props import NodeTransformProps, RectTransform


# ----------------------------------------------------------------
# Global variables.

_hovered_node: str = None


# ----------------------------------------------------------------
# In-Modal state.

_in_modal_cache: dict[str, bool] = {}
def set_in_modal_state(uuid: str, state: bool) -> None:
    _in_modal_cache[uuid] = state


# ----------------------------------------------------------------
# Dirty state.

_dirty_cache: dict[str, bool] = {}
def set_dirty_state(uuid: str, state: bool) -> None:
    _dirty_cache[uuid] = state


# ----------------------------------------------------------------
# Dirty state.

_dirty_label_cache: dict[str, bool] = {}
def set_dirty_label_state(uuid: str, state: bool) -> None:
    _dirty_label_cache[uuid] = state


# ----------------------------------------------------------------
# Generic state cache.

_state_cache: dict[str, dict[str, bool]] = defaultdict(dict)


# ----------------------------------------------------------------


# Mix-in class for all custom nodes in this tree type.
# Defines a poll function to enable instantiation.
class AP_Node(NodeTransformProps):
    bl_label = ''
    bl_icon = 'NONE'
    bl_height_max = 0
    bl_width_max = 0
    bl_width_min = 0
    bl_height_min = 0
    bl_width_default = 0
    bl_height_default = 0

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Internal Properties.
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    default_width = 20
    default_height = 20

    interactable: bool = True

    # Properties to store in Node datablock.
    uuid: StringProperty(name="UUID", default='')
    # dirty: BoolProperty(default=True, options={'HIDDEN'}) # BUG: AttributeError (can't modify in drawing state).


    # VISIBILITY LAYERS
    # ----------------------------------------------------------------
    def update_locked(self, context: Context) -> None:
        if self.locked:
            self.select = False

    locked: BoolProperty(name="Locked", default=False, update=update_locked)
    visible: BoolProperty(name="Visible", default=True)

    def update_picker_layer(self, context: Context) -> None:
        if picker_layer := self.node_tree.picker_layers.get(self.picker_layer, None):
            self.visible = picker_layer.enabled
        else:
            self.visible = True

    picker_layer_items = [('NONE', 'NONE', 'No layer. Will be always visible')]
    def get_picker_layers(self, context: Context) -> list:
        return self.picker_layer_items + [
            (picker_layer.uuid, picker_layer.edit_name, '') for picker_layer in self.node_tree.picker_layers
        ]

    picker_layer: EnumProperty(name="Picker Layer", items=get_picker_layers, update=update_picker_layer)


    # DRAW LAYERS
    # ----------------------------------------------------------------
    # Props to sort node elements by layers and depth for drawing and logic sorting.
    # draw_layer: IntProperty(default=0, min=0, max=100, options={'HIDDEN'}) # BUG: draw_layer should be a class property.
    draw_layer = 0
    draw_depth: IntProperty(name="Draw Depth",
                            description="Defines the depth this element should be drawn. The greater the value, the more preference will have over the rest of elements",
                            default=0, min=-1000, max=1000, options={'HIDDEN'})

    use_override_theme: BoolProperty(name="Override Theme", default=False)

    def get_style(self, theme):
        raise NotImplementedError

    def update_graphics(self, context: Context) -> None:
        # Set Dirty.
        self.dirty = True
        context.area.tag_redraw()
        # self.node_tree.dirty = True


    # Temporal State variables.
    # ----------------------------------------------------------------
    def set_state(self, state_name: str, state_value: bool) -> None:
        _state_cache[self.uuid][state_name] = state_value

    def get_state(self, state_name: str, default: bool = False) -> None:
        if self.uuid not in _state_cache:
            return default
        return _state_cache[self.uuid].get(state_name, default)


    # Useful/utility Properties and temporal properties.
    def is_hovered(self) -> bool:
        global _hovered_node
        return _hovered_node == self.uuid

    def set_hovered(self, state: bool) -> None:
        global _hovered_node
        if _hovered_node == self.uuid:
            if not state:
                _hovered_node = ''
        else:
            if state:
                if _hovered_node != '':
                    for node in self.node_tree.nodes:
                        if node.uuid == _hovered_node:
                            # Trigger on_hover_exit()
                            node.on_hover_exit(bpy.context)
                            break
                _hovered_node = self.uuid

    @property
    def node_tree(self) -> NodeTree:
        return self.id_data

    @property
    def dirty(self) -> bool:
        return _dirty_cache.get(self.uuid, False)

    @dirty.setter
    def dirty(self, state: bool) -> bool:
        set_dirty_state(self.uuid, state)

    @property
    def dirty_label(self) -> bool:
        return _dirty_label_cache.get(self.uuid, False)

    @dirty_label.setter
    def dirty_label(self, state: bool) -> bool:
        set_dirty_label_state(self.uuid, state)

    @property
    def in_modal(self) -> bool:
        return _in_modal_cache.get(self.uuid, False)

    @in_modal.setter
    def in_modal(self, state: bool) -> bool:
        _in_modal_cache[self.uuid] = state


    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Node type functions.
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'AP_NODETREE'

    def init(self, context):
        self.name = self.uuid = uuid4().hex

        self.rect_transform.node_idname = self.uuid

        self.dirty = True
        self.mute = True
        self.hide = True
        self.dirty_label = True

        if self.default_width != 20 and self.default_height != 20:
            self.rect_transform.edit_dimensions = (self.default_width, self.default_height)

        print("New node ", self)

    # Copy function to initialize a copied node from an existing one.
    def copy(self, node):
        self.name = self.uuid = uuid4().hex
        self.dirty = True
        self.dirty_label = True
        self.rect_transform.node_idname = self.uuid
        print("Copying from node ", node)

    # Free function to clean up on removal.
    def free(self):
        print("Removing node ", self, ", Goodbye!")


    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # UI Layout drawing.
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def draw_visibility(self, layout: UILayout) -> None:
        layout.prop(self, 'picker_layer', expand=False)

    def draw_styles(self, panel_layout: UILayout, section_layout: UILayout) -> None:
        ''' From Node. '''
        section_layout.enabled = self.use_override_theme
        self.style.draw(section_layout, in_prefs_space=False)


    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # UI utility functions.
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def draw_section(self, layout: UILayout, title: str, icon: str = 'NONE', align_content: bool = False) -> UILayout:
        section = layout.column(align=True)
        header = section.box().row(align=True)
        header.label(text=title, icon=icon)
        content = section.box().column(align=align_content)
        return content


    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Gizmo Methods.
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # ----- ON HOVER --------------------------------

    def _test_select(self, context: Context, region_loc: Vector, view_loc: Vector, view_zoom: float, reg_offset: Vector) -> bool:
        ''' Internal. '''
        if self.on_hover(context, self.rect_transform, region_loc, view_loc, view_zoom, reg_offset):
            context.region.tag_redraw()
            self.set_hovered(True)
            self.on_hover_enter(context, region_loc, view_loc)
            return True
        elif self.is_hovered():
            context.region.tag_redraw()
            self.set_hovered(False)
            self.on_hover_exit(context)
        return False

    def on_hover(self, context: Context, rect: RectTransform, region_loc: Vector, view_loc: Vector, view_zoom: float, reg_offset: Vector) -> bool:
        return point_inside_rect(view_loc, rect.bottom_left, rect.size, rect.rotation)

    def on_hover_enter(self, context: Context, region_loc: Vector, view_loc: Vector) -> None:
        pass

    def on_hover_exit(self, context: Context | None = None) -> None:
        pass

    # ----- INTERNAL UTILS --------------------------------

    def update_mouse(self, context: Context, event: Event) -> None:
        if hasattr(self, 'mouse'):
            self.mouse.update(event, context, local_space__rect=self.rect_transform)
        else:
            self.mouse = Mouse.init(event, context, local_space__rect=self.rect_transform)

    # ----- INVOKE --------------------------------

    def _invoke(self, context: Context, event: Event, mouse_pos: Vector) -> set[str]:
        ''' Internal. '''
        if poll_check(context, 'POSE'):
            if event.type != EventType.LEFTMOUSE:
                return
            invoke = self.invoke__pose
            modal = self.modal__pose
            modal_enter = self.modal_enter__pose
            modal_exit = self.modal_exit__pose
        elif poll_check(context, 'EDIT'):
            invoke = self.invoke__edit
            modal = self.modal__edit
            modal_enter = self.modal_enter__edit
            modal_exit = self.modal_exit__edit

        ret = invoke(context, event, mouse_pos)
        if ret is None:
            return {'FINISHED'}

        if ret == OpsReturn.RUN:
            # --- MODAL ENTER ---
            self.update_mouse(context, event)
            self.modal_enter = modal_enter
            self.modal = modal
            self.modal_exit = modal_exit
            self.modal_enter(context, event, self.mouse)
            self.in_modal = True

        return ret

    def invoke__pose(self, context: Context, event: Event, mouse_pos: Vector) -> set[str] | None:
        ''' Invoke method in POSE mode context. '''
        pass

    def invoke__edit(self, context: Context, event: Event, mouse_pos: Vector) -> set[str] | None:
        ''' Invoke method in EDIT mode context. '''
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.locked:
                self.node_tree.nodes.active = self
            else:
                self.select_node(context, deselect_all=not event.shift, set_active=True)

    # ----- SELECT METHODS --------------------------------

    def select_node(self, context: Context, deselect_all: bool = True, set_active: bool = True) -> None:
        if deselect_all:
            bpy.ops.node.select_all(False, action='DESELECT')
            # deselect_all_nodes(context, nullify_active=True)
            self.node_tree.nodes.active = None
        self.select = True
        if set_active:
            self.node_tree.nodes.active = self


    # ----- MODAL --------------------------------

    def _modal(self, context: Context, event: Event) -> set[str]:
        ''' Internal. '''
        if event.type in {EventType.MOUSEMOVE, EventType.INBETWEEN_MOUSEMOVE}:
            self.update_mouse(context, event)
        modal_ret = self.modal(context, event, self.mouse)
        if isinstance(modal_ret, int) and modal_ret < 1:
            # --- MODAL EXIT ---
            cancelled = modal_ret == -1
            self.modal_exit(context, event, self.mouse, cancel=cancelled)
            self.in_modal = False
            return OpsReturn.CANCEL if cancelled else OpsReturn.FINISH
        return OpsReturn.RUN

    def modal_enter__pose(self, context: Context, event: Event, mouse: Mouse) -> None:
        pass

    def modal_enter__edit(self, context: Context, event: Event, mouse: Mouse) -> None:
        pass

    def modal__pose(self, context: Context, event: Event, mouse: Mouse) -> set[str] | int:
        ''' Modal method in POSE mode context. Returns 0 for finish, 1 for continue and -1 for cancel. '''
        pass

    def modal__edit(self, context: Context, event: Event, mouse: Mouse) -> set[str] | int:
        ''' Modal method in EDIT mode context. Returns 0 for finish, 1 for continue and -1 for cancel. '''
        pass

    def modal_exit__pose(self, context: Context, cancel: bool) -> None:
        pass

    def modal_exit__edit(self, context: Context, cancel: bool) -> None:
        pass

    # ----- DRAWING --------------------------------

    def draw__pose(self, context: Context, rect: RectTransform, style, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        ''' Specific drawing for POSE mode '''
        pass

    def draw__edit(self, context: Context, rect: RectTransform, style, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        ''' Specific drawing for EDIT mode. '''
        if active or selected:
            if self.locked:
                color = (.5, .5, .5, .5)
            else:
                color = (1.0, 1.0, .1, 1.0) if active else (1.0, .6, .1, 1.0)
            draw.box_ui(
                self, 'SELECT_CAGE',
                margin=2,
                line_thickness=2 * scale,
                color=color
            )

    def draw_common(self, context: Context, rect: RectTransform, style, scale: float, active: bool, selected: bool, hovered: bool) -> None:
        ''' Shader drawing between POSE and EDIT. '''
        pass

    def _draw(self, context: Context, style, scale: float, active: bool, selected: bool, in_edit: bool) -> None:
        ''' Internal. '''
        hovered = self.is_hovered()
        rect = self.rect_transform
        self.draw_common(context, rect, style, scale, active, selected, hovered)
        if in_edit:
            self.draw__edit(context, rect, style, scale, active, selected, hovered)
        else:
            self.draw__pose(context, rect, style, scale, active, selected, hovered)

        if self.dirty:
            set_dirty_state(self.uuid, False)
        if self.dirty_label:
            set_dirty_label_state(self.uuid, False)
            self.update_graphics(context)

    def modal_draw__edit(self, context: Context, rect: RectTransform, style, ui_scale: float) -> None:
        pass

    def modal_draw__pose(self, context: Context, rect: RectTransform, style, ui_scale: float) -> None:
        pass

    # ----- UI LAYOUT DRAWING --------------------------------

    def draw_buttons_ext(self, context: Context, layout: UILayout) -> None:
        if not poll_check(context, 'ANY', use_active_object=True):
            return
        mode = self.node_tree.picker_mode
        if mode == 'POSE':
            self.draw_ui__pose(context, layout)
        elif mode == 'EDIT':
            self.draw_ui__edit(context, layout)

    def draw_ui__pose(self, context: Context, layout: UILayout) -> None:
        pass

    def draw_ui__edit(self, context: Context, layout: UILayout) -> None:
        pass



def reset_globals():
    # Reset All globals.
    global _hovered_node
    _hovered_node = None
    
    _dirty_cache.clear()
    _state_cache.clear()
    _dirty_label_cache.clear()
    _in_modal_cache.clear()
