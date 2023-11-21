# /ops.py
# Code automatically generated!
from enum import Enum, auto

from armature_picker.ackit._auto_code_gen.ops import OpTypeEnum

__all__ = ["Ops",]




class Ops(OpTypeEnum, Enum):
	PickLayoutButton = auto()
	PickLayoutProperty = auto()
	LoadCustomShapeFromGeometry = auto()
	AlignWidgets = auto()
	AsignActiveBoneToBonePicker = auto()
	CenterView = auto()
	LoadImageForActiveNode = auto()


''' Usage example:
from addon_module.ops import Ops
Ops.PickLayoutButton() # directly run execute the operator.
Ops.PickLayoutButton.operator.run_invoke() # access to the operator class and run invoke the operator.
'''