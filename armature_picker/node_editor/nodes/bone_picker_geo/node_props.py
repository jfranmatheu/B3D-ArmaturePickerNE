from bpy.types import Context, UILayout, Armature, Image
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
