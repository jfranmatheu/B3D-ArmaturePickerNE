import bpy
from bpy.types import Context, PropertyGroup
from bpy.props import BoolProperty, EnumProperty, StringProperty, PointerProperty



class AP_PG_PickerView(PropertyGroup):
    ''' Widget Types Visibility. '''

    # Show.
    show_widget_label: BoolProperty(name="Show Label Types", default=True)
    show_widget_image: BoolProperty(name="Show Image Types", default=True)

    show_widget_bone_picker: BoolProperty(name="Show BonePicker Widget Types", default=True)
    show_widget_bone_picker_geo: BoolProperty(name="Show BonePickerGeo Widget Types", default=True)

    show_widget_slider_linear: BoolProperty(name="Show SliderLineal Widget Types", default=True)
    show_widget_slider_linear_2d: BoolProperty(name="Show SliderLineal2D Widget Types", default=True)
    show_widget_slider_radial: BoolProperty(name="Show SliderRadial Widget Types", default=True)

    show_widget_button_script: BoolProperty(name="Show ButtonScript Widget Types", default=True)

    # Select.
    show_widget_select_label: BoolProperty(name="Can Select Label Types", default=True)
    show_widget_select_image: BoolProperty(name="Can Select Image Types", default=True)

    show_widget_select_bone_picker: BoolProperty(name="Can Select BonePicker Widget Types", default=True)
    show_widget_select_bone_picker_geo: BoolProperty(name="Can Select BonePickerGeo Widget Types", default=True)

    show_widget_select_slider_linear: BoolProperty(name="Can Select SliderLineal Widget Types", default=True)
    show_widget_select_slider_linear_2d: BoolProperty(name="Can Select SliderLineal2D Widget Types", default=True)
    show_widget_select_slider_radial: BoolProperty(name="Can Select SliderRadial Widget Types", default=True)

    show_widget_select_button_script: BoolProperty(name="Can Select ButtonScript Widget Types", default=True)
