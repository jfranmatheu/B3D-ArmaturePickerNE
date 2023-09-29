from bpy.types import AnyType, PropertyGroup, UILayout, Context, UIList
from bpy.props import FloatVectorProperty, BoolProperty, CollectionProperty, StringProperty, EnumProperty, IntProperty

from ._base import SettingsBase


class PG_BonePickerGeo_Settings(SettingsBase, PropertyGroup):
    display_on_hover_only: BoolProperty(name="Show only on hover", description="(While in POSE mode) Display this element only when hovering over it", default=False)

    def draw(self, layout: UILayout) -> None:
        layout.prop(self, 'display_on_hover_only')
