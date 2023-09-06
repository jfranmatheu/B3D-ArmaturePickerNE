from ._base import AP_Node, Node

from blf import size as set_text_size, dimensions as get_text_dimensions
from bpy.types import Context, Armature, Bone, Event, UILayout
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty
from mathutils import Vector, Matrix, Quaternion

from ...gpu import draw
from ...utils.geometry import point_inside_rect, rotate_point
from ...utils.armature import deselect_all_bones_from_active
from ...utils.node_editor import get_node_editor_view_point



def poll_select(context: Context) -> None:
    if context.active_object is None:
        return False
    if context.active_object.type != 'ARMATURE':
        return False
    if context.mode != 'POSE':
        return False
    for area in context.window.screen.areas:
        if area.type == 'VIEW_3D':
            return True
    return False


class AP_BonePickerNode(AP_Node, Node):
    bl_idname = 'AP_NODE_bone_picker'
    bl_label = 'Bone Picker'
    bl_icon = 'CONSTRAINT_BONE'


    def init(self, context: Context) -> None:
        super().init(context)

        pass

    # METHODS
    # ----------------------------------------------------------------
    def invoke(self, context: Context, event: Event) -> None:
        if event.type != 'LEFTMOUSE':
            return

        if not poll_select(context):
            print("BAD POOLING!")
            return

        armature: Armature = context.active_object.data
        bones = armature.bones
        bone: Bone
        if bone := bones.get(self.bone_name, None):
            deselect_all_bones_from_active(context)
            bone.select = True
            bones.active = bone

        self.select = True
        self.node_tree.nodes.active = self

    def test_select(self, context: Context, loc: Vector, zoom: float, offset: Vector) -> bool:
        return point_inside_rect(loc, self.position, self.size, self.rotation)

    def draw(self, context: Context, scale: float, active: bool) -> None:
        draw.rectangle(
            self.uuid, 'BUTTON_BASE', self.dirty, # CACHE.
            self.position, self.size, self.rotation, # TRANSFORM.
            # *self.get_pos_size_at_graph(zoom, offset), # TRANSFORM NODE GRAPH. NOW using gpu.matrix instead.
            self.color # STYLE.
        )

        padding = 4 * scale

        draw.text(
            Vector(self.location) if self.rotation == 0 else rotate_point(Vector(self.position) + Vector((padding, padding)), self.location, self.rotation),
            self.label,
            self.text_size,
            scale=1.0,
            pivot=(0.5, 0.5) if self.rotation == 0 else (0, 0),
            angle=self.rotation,
            color=self.text_color
        )

        if active:
            draw.box(
                self.uuid, 'BUTTON_BOX_ACTIVE', self.dirty,
                self.position, self.size, self.rotation,
                line_thickness=2.5 * scale,
                color=(.32, .6, .94, 1.0)
            )



    # UPDATE FUNCTIONS
    # ----------------------------------------------------------------
    def update_bone_name(self, context: Context) -> None:
        if self.label == '':
            self.label = self.bone_name.replace('_', ' ').replace('.', ' ').title()

    def update_dimensions(self, context: Context) -> None:
        if self.fit_to_text and self.label == '':
            return

        if self.fit_to_text:
            ui_scale = context.preferences.system.ui_scale
            padding = 4 * ui_scale
            padding *= 2

            set_text_size(0, self.text_size)
            text_dim = get_text_dimensions(0, self.label)
            self.dimensions = (
                text_dim[0] + padding,
                text_dim[1] + padding
            )

        else:
            # USER-EDITED-DIMENSIONS: self.edit_dimensions
            # INTERNAL DIMENSIONS: self.dimensions
            self.dimensions = (
                self.edit_dimensions[0] * self.scale[0],
                self.edit_dimensions[1] * self.scale[1]
            )

    def update_graphics(self, context: Context) -> None:
        self.dirty = True


    # TRANSFORM PROPERTIES
    # ----------------------------------------------------------------
    location: FloatVectorProperty(
        name="Location",
        description="Picker button position inside the NodeGraph 2D view",
        default=(0, 0),
        size=2,
        subtype='XYZ',
        update=update_graphics
    )

    rotation: FloatProperty(
        name="Rotation",
        description="Picker button rotation in the NodeGraph 2D view",
        default=0,
        subtype='ANGLE',
        unit='ROTATION',
        update=update_graphics
    )

    scale: FloatVectorProperty(
        name="Scale",
        description="Picker button scale",
        default=(1, 1),
        size=2,
        update=update_dimensions
    )

    dimensions: FloatVectorProperty(
        name="Dimensions",
        min=0,
        size=2,
        options={'HIDDEN'},
        update=update_graphics
    )

    edit_dimensions: FloatVectorProperty(
        name="Dimensions",
        description="Picker button size in the NodeGraph 2D view",
        default=(20, 20),
        min=20,
        size=2,
        update=lambda node, ctx: node.update_dimensions(ctx) if not node.fit_to_text else None
    )

    @property
    def position(self) -> Vector:
        x, y = self.location
        w, h = self.dimensions
        w_div2 = int(w / 2)
        h_div2 = int(h / 2)
        return Vector((x - w_div2, y - h_div2))

    @property
    def size(self) -> Vector:
        return Vector(self.dimensions)

    def get_pos_size_at_graph(self, context, zoom: float, offset: Vector) -> tuple[Vector, Vector]:
        view_dimensions = self.size # * 1/zoom

        view_location = Vector(self.location)
        view_location.x -= int(view_dimensions.x / 2)
        view_location.y -= int(view_dimensions.y / 2)

        return (
            view_location,
            view_dimensions
        )


    # BUTTON PROPERTIES
    # ----------------------------------------------------------------
    label: StringProperty(
        name="Label",
        description="Button label",
        update=update_dimensions,
        options={'TEXTEDIT_UPDATE'}
    )

    bone_name: StringProperty(
        name="Bone Name",
        description="Name of the bone to control",
        update=update_bone_name
    )


    # STYLE PROPERTIES
    # ----------------------------------------------------------------
    fit_to_text: BoolProperty(
        name="Fit To Text",
        description="Whether to fit button dimensions to label text box size",
        default=True,
    )

    color: FloatVectorProperty(
        name="Background Color",
        description="Background Color of the button",
        default=(1, .8, .4, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    text_size: IntProperty(
        name='Text Size',
        description="Label text size",
        default=12,
        update=update_dimensions
    )

    text_color: FloatVectorProperty(
        name='Text Color',
        description="Label text color",
        default=(.0, .0, .0, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )


    def draw_buttons_ext(self, context: Context, layout: UILayout) -> None:
        layout.prop(self, 'label')
        layout.prop(self, 'bone_name')

        section_t = self.draw_section(layout, 'Transform', icon='ORIENTATION_VIEW')
        section_t.prop(self, 'location')
        section_t.prop(self, 'rotation')
        _sub = section_t.column()
        _sub.enabled = not self.fit_to_text
        _sub.prop(self, 'scale')
        _sub.prop(self, 'edit_dimensions')

        section_t.separator()

        section_t.prop(self, 'fit_to_text')

        section_style = self.draw_section(layout, 'Style', icon='ORIENTATION_VIEW')
        # TODO: self.use_bone_color
        section_style.prop(self, 'color')
        section_style.prop(self, 'text_size')
        section_style.prop(self, 'text_color')
