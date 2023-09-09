from bpy.types import Context, UILayout
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty
from mathutils import Vector

from math import pi


class NodeTransformProps:
    def update_dimensions(self, context: Context) -> None:
        # USER-EDITED-DIMENSIONS: self.edit_dimensions
        # INTERNAL DIMENSIONS: self.dimensions
        self.dimensions = (
            max(self.edit_dimensions[0] * self.scale[0], 10),
            max(self.edit_dimensions[1] * self.scale[1], 10)
        )

    def update_graphics(self, context: Context) -> None:
        self.dirty = True

        context.region.tag_redraw()


    # TRANSFORM PROPERTIES
    # ----------------------------------------------------------------
    origin: FloatVectorProperty( # old location
        name="Location",
        description="Picker button origin location (actually its center) inside the NodeGraph 2D view",
        default=(0, 0),
        size=2,
        subtype='XYZ',
        update=update_graphics
    )

    rotation: FloatProperty(
        name="Rotation",
        description="Picker button rotation in the NodeGraph 2D view",
        default=0,
        min=-pi/2,
        max=pi/2,
        subtype='ANGLE',
        unit='ROTATION',
        update=update_graphics
    )

    scale: FloatVectorProperty(
        name="Scale",
        description="Picker button scale",
        default=(1, 1),
        min=0.5,
        size=2,
        subtype='XYZ',
        update=lambda node, ctx: node.update_dimensions(ctx) # Node subtypes may have different update() behaviours.
    )

    dimensions: FloatVectorProperty(
        name="Dimensions",
        min=0,
        size=2,
        default=(20, 20),
        subtype='XYZ',
        options={'HIDDEN'},
        update=update_graphics
    )

    edit_dimensions: FloatVectorProperty(
        name="Dimensions",
        description="Picker button size in the NodeGraph 2D view",
        default=(20, 20),
        min=20,
        size=2,
        update=lambda node, ctx: node.update_dimensions(ctx)
    )

    @property
    def position(self) -> Vector:
        x, y = self.origin
        w, h = self.dimensions
        w_div2 = int(w / 2)
        h_div2 = int(h / 2)
        return Vector((x - w_div2, y - h_div2))

    @property
    def size(self) -> Vector:
        return Vector(self.dimensions)


    def draw_transform(self, layout: UILayout) -> None:
        layout.prop(self, 'origin') # old location
        layout.prop(self, 'rotation')
        layout.prop(self, 'scale')
        layout.prop(self, 'edit_dimensions')
