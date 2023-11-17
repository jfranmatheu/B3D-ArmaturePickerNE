""" File generated automatically by addon_utils submodule. """
import bpy
from bpy.types import Context


class PG__BonePickerGeo__LocalStyle:
	name: str
	use_object_color: bool
	color_tag: None

class PG_ArmaturePicker_ColorTag:
	name: str
	name: str
	color: tuple[float]

class WM_PG_armature_picker:
	name: str
	active_tool: None

	@classmethod
	def get_data(cls: 'WM_PG_armature_picker', context: Context) -> 'WM_PG_armature_picker':
		return context.window_manager.armature_picker

class PG__BonePicker__Style:
	name: str
	roundness: float
	outline_thickness: float
	outline_color: tuple[float]
	color: tuple[float]
	text_color: tuple[float]

class PG__Image__Style:
	name: str
	opacity: float

class PG__Label__Style:
	name: str
	text_color: tuple[float]

class PG__SliderLinear__Style:
	name: str
	show_handle: bool
	handle_type: None
	bar_line_thickness: float
	bar_type: None
	color: tuple[float]
	fill_color: tuple[float]
	handle_color: tuple[float]
	outline_color: tuple[float]
	roundness: float
	outline_thickness: float

class PG__SliderRadial__Style:
	name: str
	bar_thickness_factor: float
	color: tuple[float]
	fill_color: tuple[float]
	bar_arc_angle: float
	invert_fill_flow: bool

class PG__Slider2D__Style:
	name: str
	color: tuple[float]
	handle_color: tuple[float]
	handle_scale: float
	roundness: float
	outline_thickness: float

class PG__ButtonScript__Style:
	name: str
	roundness: float
	outline_thickness: float
	outline_color: tuple[float]
	color: tuple[float]
	text_color: tuple[float]

class PG__BonePickerGeo__Style:
	name: str
	color_tag_0: PG_ArmaturePicker_ColorTag
	color_tag_1: PG_ArmaturePicker_ColorTag
	color_tag_2: PG_ArmaturePicker_ColorTag
	color_tag_3: PG_ArmaturePicker_ColorTag
	color_tag_4: PG_ArmaturePicker_ColorTag
	color_tag_5: PG_ArmaturePicker_ColorTag
	color_tag_6: PG_ArmaturePicker_ColorTag
	color_tag_7: PG_ArmaturePicker_ColorTag
	color_tag_8: PG_ArmaturePicker_ColorTag
	color_tag_9: PG_ArmaturePicker_ColorTag
	initialized: bool


# ++++++++++++++++++++++++++++++++++++++++++++++++++



class Armature:
	picker: None

class WindowManager:
	armature_picker: None

# ++++++++++++++++++++++++++++++++++++++++++++++++++


class Data:
	WM_PG_armature_picker = WM_PG_armature_picker.get_data

PG = Data # Alias.


# EXAMPLE ++++++++++++++++++++++++++++++++++++++++++++++++++
'''
from armature_picker import types as armature_picker_types

# Your property_group variable will have the correct typing. :-)
property_group = armature_picker_types.WM_PG_armature_picker.get_data(context)
property = property_group.active_tool
print(property)
'''
