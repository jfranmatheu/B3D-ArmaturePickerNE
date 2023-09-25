from bpy.types import PropertyGroup, UILayout, Context
from bpy.props import PointerProperty, StringProperty

from ..utils.ui_layout import draw_section
from .styles import *

class PG_ArmaturePickerTheme(PropertyGroup):
    name: StringProperty(default='Theme')

    bone_picker: PointerProperty(type=BonePicker_Style)

    slider_linear: PointerProperty(type=SliderLinear_Style)
    slider_radial: PointerProperty(type=SliderRadial_Style)
    slider_linear_2d: PointerProperty(type=SliderLinear2D_Style)

    image: PointerProperty(type=Image_Style)

    label: PointerProperty(type=Label_Style)


    def draw(self, layout: UILayout) -> None:
        grid = layout.grid_flow(row_major=True)
        self.label.draw(draw_section(grid, 'Label', icon='NONE'), in_prefs_space=True)
        self.image.draw(draw_section(grid, 'Image', icon='IMAGE'), in_prefs_space=True)
        self.bone_picker.draw(draw_section(grid, 'BonePicker', icon='BONE_DATA'), in_prefs_space=True)
        self.slider_linear.draw(draw_section(grid, 'Slider linear', icon='PROPERTIES'), in_prefs_space=True)
        self.slider_radial.draw(draw_section(grid, 'Slideer Radial', icon='NONE'), in_prefs_space=True)
        self.slider_linear_2d.draw(draw_section(grid, 'Slider linear 2D', icon='NONE'), in_prefs_space=True)
