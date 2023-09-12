from bpy.types import Context, UILayout, Armature, Object
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty, PointerProperty
from blf import size as set_text_size, dimensions as get_text_dimensions

from math import ceil

from ....utils.math import clamp



class APNODE_BonePickerGeo_NodeProps:

    # UPDATE
    # ----------------------------------------------------------------

    def update_dimensions(self, context: Context) -> None:
        pass


    # PROPERTIES
    # ----------------------------------------------------------------

    object: PointerProperty(
        name="Mesh Object",
        description="Object that will be used to render the bone picker button graphics",
        type=Object,
        poll=lambda node, ob: ob.type == 'MESH',
        update=lambda node, ctx: node.update_graphics(ctx)
    )
