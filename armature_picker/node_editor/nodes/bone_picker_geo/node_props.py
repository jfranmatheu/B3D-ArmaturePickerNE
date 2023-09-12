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

    def draw_ui__pose(self, context: Context, layout: UILayout) -> None:
        if context.active_object.animation_data is None:
            layout.label(text="No animation data")
            return

        col = layout.column(align=False)
        col.use_property_decorate = True
        col.use_property_split = True
        if action := context.active_object.animation_data.action:
            drawn_attr = set()
            for fcu in action.fcurves:
                data_path: str = fcu.data_path
                if data_path.startswith('pose.bones'):
                    if self.bone_name == data_path.split('"')[1]:
                        attr = data_path.split('.')[-1]
                        if attr in drawn_attr:
                            continue
                        drawn_attr.add(attr)
                        col.prop(self.get_bone(context, from_pose_data=True), attr)
